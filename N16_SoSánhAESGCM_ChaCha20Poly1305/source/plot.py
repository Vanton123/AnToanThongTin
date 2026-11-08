"""
plot.py - Ve bieu do throughput va do tre tu CSV cua benchmark.py (TV1, Issue 4).
 
Moi bieu do co 2 thuat toan x (cac) moi truong; thanh sai so = do lech chuan.
 
Cach chay (mac dinh doc results/benchmark_may1.csv va benchmark_may2.csv):
  python plot.py
  python plot.py --csv results/benchmark_may1.csv results/benchmark_may2.csv --outdir ../thesis/charts
 
Dau ra: <outdir>/throughput.png va <outdir>/latency.png
"""
import argparse
import os
import sys
 
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd
 
HERE = os.path.dirname(os.path.abspath(__file__))  # thu muc chua plot.py (source/)
SIZE_ORDER = ["1KB", "1MB", "10MB", "100MB"]
ALGO_COLORS = {"AES-256-GCM": "#1f77b4", "ChaCha20-Poly1305": "#d95f02"}
HATCHES = ["", "//", "..", "xx"]  # moi truong thu i dung hoa van thu i (de doc ca khi in den trang)
 
 
def load(paths):
    frames = []
    for p in paths:
        if not os.path.exists(p):
            print(f"Canh bao: khong tim thay {p}, bo qua", file=sys.stderr)
            continue
        frames.append(pd.read_csv(p, encoding="utf-8-sig"))
    if not frames:
        sys.exit("Khong co file CSV nao de ve.")
    df = pd.concat(frames, ignore_index=True)
    need = {"environment", "algorithm", "size_label", "throughput_mean_MBps", "throughput_std_MBps",
            "latency_mean_ms", "latency_std_ms"}
    missing = need - set(df.columns)
    if missing:
        sys.exit(f"CSV thieu cot: {sorted(missing)}")
    return df
 
 
def grouped_bars(df, ycol, errcol, ylabel, title, out_path, log_y=False):
    envs = list(dict.fromkeys(df["environment"]))
    algos = [a for a in ALGO_COLORS if a in set(df["algorithm"])]
    series = [(a, e) for e in envs for a in algos]
    n = len(series)
    width = 0.8 / n
    fig, ax = plt.subplots(figsize=(11, 5.8))
    for i, (algo, env) in enumerate(series):
        sub = df[(df["algorithm"] == algo) & (df["environment"] == env)].set_index("size_label")
        xs, ys, es = [], [], []
        for j, s in enumerate(SIZE_ORDER):
            if s in sub.index:
                xs.append(j - 0.4 + width * (i + 0.5))
                ys.append(sub.loc[s, ycol])
                es.append(sub.loc[s, errcol])
        ax.bar(xs, ys, width * 0.95, yerr=es, capsize=3,
               color=ALGO_COLORS[algo], hatch=HATCHES[envs.index(env) % len(HATCHES)],
               edgecolor="black", linewidth=0.6, label=f"{algo} - {env}", error_kw={"elinewidth": 1})
    ax.set_xticks(range(len(SIZE_ORDER)))
    ax.set_xticklabels(SIZE_ORDER)
    ax.set_xlabel("Kích thước dữ liệu")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_y:
        ax.set_yscale("log")
    ax.grid(axis="y", linestyle=":", alpha=0.6, which="both" if log_y else "major")
    ax.set_axisbelow(True)
    # chua cho phia tren de legend khong che cot
    top = ax.get_ylim()[1]
    if log_y:
        ax.set_ylim(top=top * 12)
    else:
        ax.set_ylim(0, top * 1.28)
    ax.legend(fontsize=8.5, loc="upper right", ncol=2, framealpha=0.95)
    fig.tight_layout()
    fig.savefig(out_path, dpi=200)
    plt.close(fig)
    print(f"Da luu {out_path}")
 
 
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--csv", nargs="+", default=[os.path.join(HERE, "results", "benchmark_may1.csv"),
                                          os.path.join(HERE, "results", "benchmark_may2.csv")])
    ap.add_argument("--outdir", default=os.path.join(HERE, "..", "thesis", "charts"))
    args = ap.parse_args()
 
    df = load(args.csv)
    os.makedirs(args.outdir, exist_ok=True)
    grouped_bars(df, "throughput_mean_MBps", "throughput_std_MBps", "Throughput (MB/s)",
                 "Throughput mã hóa AEAD theo kích thước dữ liệu (cao hơn là tốt hơn)",
                 os.path.join(args.outdir, "throughput.png"))
    grouped_bars(df, "latency_mean_ms", "latency_std_ms", "Độ trễ trung bình mỗi lần mã hóa (ms, thang log)",
                 "Độ trễ mã hóa AEAD theo kích thước dữ liệu (thấp hơn là tốt hơn)",
                 os.path.join(args.outdir, "latency.png"), log_y=True)
 
 
if __name__ == "__main__":
    main()