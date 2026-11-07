"""
benchmark.py - Benchmark AES-256-GCM va ChaCha20-Poly1305 (AEAD).
 
Chi dung API AEAD muc cao cua thu vien `cryptography` (OpenSSL phia sau);
KHONG tu cai dat loi AES hay ChaCha.
 
Dau ra (trong thu muc --outdir):
  <label>_raw.csv      moi dong la mot lan do (1 lan encrypt hoac decrypt)
  <label>_summary.csv  thong ke theo (algorithm, operation, size)
  <label>_meta.json    thong tin may, thu vien, tham so, seed, lenh chay
 
Vi du:
  python benchmark.py --label accel_on  --seed 12345
  python benchmark.py --label accel_off --seed 12345 --disable-accel
  python benchmark.py --label quick --sizes 1KB,64KB,1MB --repeats-scale 0.1
"""
import argparse
import csv
import gc
import json
import os
import platform
import random
import shlex
import statistics
import subprocess
import sys
import time
from datetime import datetime, timezone
 
# Cac gia tri OPENSSL_ia32cap che AES-NI + PCLMULQDQ (+ AVX/VAES lien quan) tren x86-64.
# Phai dat TRUOC khi OpenSSL duoc nap, nen script se tu re-exec khi --disable-accel.
IA32CAP_DISABLE = "~0x200000200000000"
 
DEFAULT_SIZES = ["1KB", "4KB", "64KB", "1MB", "10MB", "100MB"]
# So lan lap mac dinh theo kich thuoc (nho -> lap nhieu, lon -> lap it).
DEFAULT_REPEATS = {
    "1KB": 3000, "4KB": 3000, "64KB": 1000,
    "1MB": 200, "10MB": 40, "100MB": 12,
}
AAD = b"benchmark-aad-v1|hdr=0123456789abcdef"  # AAD co dinh, duoc xac thuc nhung khong ma hoa
NONCE_LEN = 12  # 96 bit, chuan cho ca hai thuat toan
 
 
def parse_size(text: str) -> int:
    t = text.strip().upper()
    for suf, mul in (("KB", 1024), ("MB", 1024 ** 2), ("GB", 1024 ** 3), ("B", 1)):
        if t.endswith(suf):
            return int(float(t[: -len(suf)]) * mul)
    return int(t)
 
 
def size_label(n: int) -> str:
    if n >= 1024 ** 2:
        return f"{n // 1024 ** 2}MB"
    if n >= 1024:
        return f"{n // 1024}KB"
    return f"{n}B"
 
 
def percentile(sorted_vals, p):
    """Noi suy tuyen tinh, p trong [0, 100]."""
    if not sorted_vals:
        return float("nan")
    k = (len(sorted_vals) - 1) * p / 100.0
    lo, hi = int(k), min(int(k) + 1, len(sorted_vals) - 1)
    return sorted_vals[lo] + (sorted_vals[hi] - sorted_vals[lo]) * (k - lo)
 
 
def collect_meta(args, cmdline):
    import cryptography
    meta = {
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "label": args.label,
        "command": cmdline,
        "seed": args.seed,
        "accel_disabled": bool(args.disable_accel),
        "OPENSSL_ia32cap": os.environ.get("OPENSSL_ia32cap", ""),
        "python": sys.version.split()[0],
        "cryptography": cryptography.__version__,
        "platform": platform.platform(),
        "machine": platform.machine(),
        "processor": platform.processor(),
        "cpu_count": os.cpu_count(),
        "aad_bytes": len(AAD),
        "nonce_bytes": NONCE_LEN,
        "key_bits": 256,
        "algorithms": ["AES-256-GCM", "ChaCha20-Poly1305"],
        "tag_bytes": 16,
    }
    try:
        from cryptography.hazmat.backends.openssl.backend import backend
        meta["openssl"] = backend.openssl_version_text()
    except Exception:
        meta["openssl"] = "unknown"
    # CPU model + co tinh nang tang toc (Linux); cac OS khac chi ghi platform
    try:
        with open("/proc/cpuinfo") as f:
            text = f.read()
        for line in text.splitlines():
            if line.startswith("model name"):
                meta["cpu_model"] = line.split(":", 1)[1].strip()
                break
        flags = set()
        for line in text.splitlines():
            if line.startswith(("flags", "Features")):
                flags = set(line.split(":", 1)[1].split())
                break
        meta["cpu_flags_accel"] = sorted(flags & {"aes", "pclmulqdq", "avx", "avx2", "vaes", "vpclmulqdq", "pmull", "sha1", "sha2", "asimd"})
    except OSError:
        pass
    if sys.platform == "darwin":
        try:
            meta["cpu_model"] = subprocess.check_output(["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        except Exception:
            pass
    try:
        with open("/proc/meminfo") as f:
            kb = int(f.readline().split()[1])
        meta["ram_mb"] = kb // 1024
    except OSError:
        pass
    return meta
 
 
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="run", help="nhan moi truong, vd: laptop_accel_on")
    ap.add_argument("--outdir", default="results")
    ap.add_argument("--sizes", default=",".join(DEFAULT_SIZES), help="vd: 1KB,64KB,1MB,100MB")
    ap.add_argument("--repeats-scale", type=float, default=1.0, help="nhan he so len so lan lap mac dinh")
    ap.add_argument("--warmup", type=int, default=5, help="so lan chay khoi dong khong tinh")
    ap.add_argument("--seed", type=int, default=12345, help="seed cho du lieu va nonce (tai tao ket qua)")
    ap.add_argument("--disable-accel", action="store_true", help="che AES-NI/PCLMULQDQ qua OPENSSL_ia32cap (x86)")
    ap.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
 
    cmdline = "python " + " ".join(shlex.quote(a) for a in sys.argv)
 
    # Che tang toc phan cung: phai dat bien moi truong truoc khi OpenSSL nap -> re-exec.
    if args.disable_accel and not args._child:
        env = dict(os.environ, OPENSSL_ia32cap=IA32CAP_DISABLE)
        argv = [sys.executable, os.path.abspath(__file__)] + [a for a in sys.argv[1:]] + ["--_child"]
        sys.exit(subprocess.call(argv, env=env))
    if args.disable_accel:
        cmdline = cmdline.replace(" --_child", "")
 
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
    from cryptography.exceptions import InvalidTag
 
    sizes = [parse_size(s) for s in args.sizes.split(",")]
    rng = random.Random(args.seed)
    key = rng.randbytes(32)  # khoa chi dung cho benchmark, sinh tu seed de tai tao duoc
    algos = {"AES-256-GCM": AESGCM(key), "ChaCha20-Poly1305": ChaCha20Poly1305(key)}
 
    os.makedirs(args.outdir, exist_ok=True)
    raw_path = os.path.join(args.outdir, f"{args.label}_raw.csv")
    sum_path = os.path.join(args.outdir, f"{args.label}_summary.csv")
    meta_path = os.path.join(args.outdir, f"{args.label}_meta.json")
 
    meta = collect_meta(args, cmdline)
    meta["sizes_bytes"] = sizes
    meta["warmup"] = args.warmup
    meta["repeats_scale"] = args.repeats_scale
    meta["timer"] = "time.perf_counter_ns"
    meta["notes"] = ("Mot lan do = mot lenh encrypt hoac decrypt tren buffer ben trong bo nho; "
                     "moi lan dung nonce moi (bo dem, duy nhat); GC tat trong luc do.")
 
    counter = 0  # nonce = 4 byte prefix (tu seed) || 8 byte bo dem -> khong bao gio trung
    prefix = rng.randbytes(4)
 
    def next_nonce():
        nonlocal counter
        counter += 1
        return prefix + counter.to_bytes(8, "big")
 
    raw_rows = []
    summary_rows = []
 
    print(f"[{args.label}] {meta.get('cpu_model', meta['processor'])} | cryptography {meta['cryptography']} | "
          f"{meta['openssl']} | accel_disabled={meta['accel_disabled']}")
 
    for size in sizes:
        lab = size_label(size)
        reps = max(5, int(DEFAULT_REPEATS.get(lab, 100) * args.repeats_scale))
        data = rng.randbytes(size)
        for name, aead in algos.items():
            # Kiem tra dung dan truoc khi do
            n0 = next_nonce()
            ct = aead.encrypt(n0, data, AAD)
            assert aead.decrypt(n0, ct, AAD) == data, "round-trip loi"
            try:
                aead.decrypt(n0, bytes([ct[0] ^ 1]) + ct[1:], AAD)
                raise SystemExit("LOI: ban ma bi sua van duoc chap nhan")
            except InvalidTag:
                pass
 
            # Khoi dong
            for _ in range(args.warmup):
                n = next_nonce()
                aead.decrypt(n, aead.encrypt(n, data, AAD), AAD)
 
            enc_t, dec_t = [], []
            gc.collect()
            gc.disable()
            try:
                for i in range(reps):
                    n = next_nonce()
                    t0 = time.perf_counter_ns()
                    ct = aead.encrypt(n, data, AAD)
                    t1 = time.perf_counter_ns()
                    pt = aead.decrypt(n, ct, AAD)
                    t2 = time.perf_counter_ns()
                    enc_t.append(t1 - t0)
                    dec_t.append(t2 - t1)
                    raw_rows.append((args.label, name, "encrypt", size, i, t1 - t0))
                    raw_rows.append((args.label, name, "decrypt", size, i, t2 - t1))
            finally:
                gc.enable()
 
            for op, times in (("encrypt", enc_t), ("decrypt", dec_t)):
                s = sorted(times)
                med = statistics.median(s)
                mean = statistics.fmean(s)
                std = statistics.stdev(s) if len(s) > 1 else 0.0
                summary_rows.append({
                    "label": args.label, "algorithm": name, "operation": op,
                    "size_bytes": size, "size_label": lab, "repeats": reps,
                    "mean_us": mean / 1e3, "median_us": med / 1e3, "std_us": std / 1e3,
                    "cv_percent": 100 * std / mean if mean else 0.0,
                    "min_us": s[0] / 1e3,
                    "p5_us": percentile(s, 5) / 1e3, "p95_us": percentile(s, 95) / 1e3,
                    "p99_us": percentile(s, 99) / 1e3, "max_us": s[-1] / 1e3,
                    # throughput = size / thoi gian; dung median (it nhay cam voi ngoai lai) va mean
                    "throughput_median_MBps": size / (med / 1e9) / 1e6,
                    "throughput_mean_MBps": size / (mean / 1e9) / 1e6,
                })
            r = summary_rows[-2]
            print(f"  {lab:>6} {name:<18} enc {r['throughput_median_MBps']:9.1f} MB/s "
                  f"(med {r['median_us']:10.1f} us, cv {r['cv_percent']:4.1f}%) | "
                  f"dec {summary_rows[-1]['throughput_median_MBps']:9.1f} MB/s | n={reps}")
 
    with open(raw_path, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["label", "algorithm", "operation", "size_bytes", "iteration", "time_ns"])
        w.writerows(raw_rows)
    with open(sum_path, "w", newline="") as f:
        w = csv.DictWriter(f, fieldnames=list(summary_rows[0].keys()))
        w.writeheader()
        w.writerows(summary_rows)
    with open(meta_path, "w") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Da ghi: {raw_path}, {sum_path}, {meta_path}")
 
 
if __name__ == "__main__":
    main()
