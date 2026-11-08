"""plot.py - Issue 4: Doc CSV bang pandas, ve bieu do throughput va latency."""
import os
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import pandas as pd

HERE = os.path.dirname(os.path.abspath(__file__))
OUT_DIR = os.path.join(HERE, "..", "thesis", "charts")
SIZES = ["1KB", "1MB", "10MB", "100MB"]


def draw_chart(df, mean_col, std_col, ylabel, title, filename, log_scale=False):
    series = [
        ("AESGCM", "may1", "AESGCM - Máy 1 (Bật AES-NI)"),
        ("ChaCha20Poly1305", "may1", "ChaCha20Poly1305 - Máy 1"),
        ("AESGCM", "may2", "AESGCM - Máy 2 (Tắt AES-NI)"),
        ("ChaCha20Poly1305", "may2", "ChaCha20Poly1305 - Máy 2"),
    ]
    width = 0.18
    x_pos = range(len(SIZES))

    fig, ax = plt.subplots(figsize=(10, 5.5))
    for i, (algo, env, label) in enumerate(series):
        sub = df[(df["algorithm"] == algo) & (df["env"] == env)].set_index("size").reindex(SIZES)
        xs = [x + (i - 1.5) * width for x in x_pos]
        ax.bar(xs, sub[mean_col], width, yerr=sub[std_col], capsize=3, label=label)

    ax.set_xticks(list(x_pos))
    ax.set_xticklabels(SIZES)
    ax.set_xlabel("Kích thước dữ liệu")
    ax.set_ylabel(ylabel)
    ax.set_title(title)
    if log_scale:
        ax.set_yscale("log")
    ax.grid(axis="y", linestyle="--", alpha=0.5)
    ax.legend()
    fig.tight_layout()
    out_path = os.path.join(OUT_DIR, filename)
    fig.savefig(out_path, dpi=150)
    plt.close(fig)
    print("Da luu:", out_path)


def main():
    df1 = pd.read_csv(os.path.join(HERE, "results", "benchmark_may1.csv"))
    df1["env"] = "may1"
    df2 = pd.read_csv(os.path.join(HERE, "results", "benchmark_may2.csv"))
    df2["env"] = "may2"
    df = pd.concat([df1, df2], ignore_index=True)

    os.makedirs(OUT_DIR, exist_ok=True)
    draw_chart(df, "throughput_mean_MBps", "throughput_std_MBps",
               "Throughput (MB/s)", "So sánh Throughput mã hóa AEAD", "throughput.png")
    draw_chart(df, "latency_mean_ms", "latency_std_ms",
               "Độ trễ trung bình (ms - thang log)", "So sánh Độ trễ mã hóa AEAD", "latency.png", log_scale=True)


if __name__ == "__main__":
    main()
