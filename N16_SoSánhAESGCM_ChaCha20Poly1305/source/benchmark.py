"""
benchmark.py - Do hieu nang AEAD: AES-256-GCM va ChaCha20-Poly1305 (TV1, Issue 1-3).
 
Chi dung API AEAD muc cao cua thu vien `cryptography`; khong tu cai dat loi AES/ChaCha.
 
Moi o do = (thuat toan, kich thuoc): goi .encrypt(nonce, data, aad), do bang
time.perf_counter(). Lap 10 lan (100 MB lap 5 lan). Tinh throughput (MB/s),
do tre trung binh va do lech chuan. 2 thuat toan x 4 kich thuoc = 8 o do.
 
Cach chay (mot lenh):
  May 1 : python benchmark.py --label may1
  May 2 : python benchmark.py --label may2
  Chi co 1 may (tat tang toc AES-NI/PCLMULQDQ de so sanh, chi x86):
          python benchmark.py --label may2 --disable-accel
 
Ket qua: results/benchmark_<label>.csv  (+ results/benchmark_<label>_meta.json)
Quy uoc: 1 MB = 1024*1024 byte. Throughput = kich thuoc / thoi gian ma hoa.
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
 
# Che AES-NI + PCLMULQDQ tren x86-64. Bien nay phai duoc dat TRUOC khi OpenSSL nap,
# nen khi dung --disable-accel script tu chay lai chinh no (re-exec) voi bien moi truong nay.
IA32CAP_DISABLE = "~0x200000200000000"
 
HERE = os.path.dirname(os.path.abspath(__file__))  # thu muc chua benchmark.py (source/)
MB = 1024 * 1024
SIZES = [("1KB", 1024), ("1MB", MB), ("10MB", 10 * MB), ("100MB", 100 * MB)]
REPEATS = {"1KB": 10, "1MB": 10, "10MB": 10, "100MB": 5}
AAD = b"benchmark-aad-v1"
NONCE_LEN = 12  # 96 bit
 
CSV_COLUMNS = [
    "environment", "cpu", "os", "python_version", "cryptography_version", "openssl_version",
    "accel_disabled", "algorithm", "size_label", "size_bytes", "repeats", "seed",
    "latency_mean_ms", "latency_std_ms", "throughput_mean_MBps", "throughput_std_MBps",
    "latency_min_ms", "latency_max_ms",
]
 
 
def get_cpu_name() -> str:
    """Ten CPU de ghi vao bang benchmark (Windows / Linux / macOS)."""
    try:
        if sys.platform.startswith("win"):
            import winreg
            key = winreg.OpenKey(winreg.HKEY_LOCAL_MACHINE,
                                 r"HARDWARE\DESCRIPTION\System\CentralProcessor\0")
            return winreg.QueryValueEx(key, "ProcessorNameString")[0].strip()
        if sys.platform == "darwin":
            return subprocess.check_output(
                ["sysctl", "-n", "machdep.cpu.brand_string"], text=True).strip()
        with open("/proc/cpuinfo") as f:
            for line in f:
                if line.startswith(("model name", "Model", "Hardware")):
                    return line.split(":", 1)[1].strip()
    except Exception:
        pass
    return platform.processor() or platform.machine()
 
 
def get_ram_mb():
    try:
        if sys.platform.startswith("win"):
            import ctypes
 
            class MEMSTAT(ctypes.Structure):
                _fields_ = [("dwLength", ctypes.c_ulong), ("dwMemoryLoad", ctypes.c_ulong),
                            ("ullTotalPhys", ctypes.c_ulonglong), ("ullAvailPhys", ctypes.c_ulonglong),
                            ("ullTotalPageFile", ctypes.c_ulonglong), ("ullAvailPageFile", ctypes.c_ulonglong),
                            ("ullTotalVirtual", ctypes.c_ulonglong), ("ullAvailVirtual", ctypes.c_ulonglong),
                            ("ullAvailExtendedVirtual", ctypes.c_ulonglong)]
            m = MEMSTAT()
            m.dwLength = ctypes.sizeof(MEMSTAT)
            ctypes.windll.kernel32.GlobalMemoryStatusEx(ctypes.byref(m))
            return int(m.ullTotalPhys // MB)
        if sys.platform == "darwin":
            return int(int(subprocess.check_output(["sysctl", "-n", "hw.memsize"], text=True)) // MB)
        with open("/proc/meminfo") as f:
            return int(f.readline().split()[1]) // 1024
    except Exception:
        return None
 
 
def get_openssl_version() -> str:
    try:
        from cryptography.hazmat.backends.openssl.backend import backend
        return backend.openssl_version_text()
    except Exception:
        return "unknown"
 
 
def main():
    ap = argparse.ArgumentParser(description=__doc__, formatter_class=argparse.RawDescriptionHelpFormatter)
    ap.add_argument("--label", default="may1", help="ten may/moi truong; file = benchmark_<label>.csv")
    ap.add_argument("--env-name", default=None, help="ten hien thi tren bieu do (mac dinh: tu --label)")
    ap.add_argument("--outdir", default=os.path.join(HERE, "results"),
                    help="mac dinh: <thu muc benchmark.py>/results, khong phu thuoc thu muc dang dung lenh")
    ap.add_argument("--seed", type=int, default=12345, help="seed sinh du lieu va khoa benchmark")
    ap.add_argument("--warmup", type=int, default=2, help="so lan chay khoi dong, khong tinh")
    ap.add_argument("--disable-accel", action="store_true", help="che AES-NI/PCLMULQDQ (OPENSSL_ia32cap, x86)")
    ap.add_argument("--_child", action="store_true", help=argparse.SUPPRESS)
    args = ap.parse_args()
 
    # Re-exec de bien moi truong co hieu luc truoc khi OpenSSL duoc nap.
    if args.disable_accel and not args._child:
        env = dict(os.environ, OPENSSL_ia32cap=IA32CAP_DISABLE)
        argv = [sys.executable, os.path.abspath(__file__)] + sys.argv[1:] + ["--_child"]
        sys.exit(subprocess.call(argv, env=env))
 
    import cryptography
    from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305
 
    cmdline = "python benchmark.py " + " ".join(shlex.quote(a) for a in sys.argv[1:] if a != "--_child")
    env_name = args.env_name or (f"{args.label} (tắt tăng tốc)" if args.disable_accel else args.label)
 
    rng = random.Random(args.seed)
    key = rng.randbytes(32)  # khoa chi dung cho benchmark; sinh tu seed de tai tao duoc
    algos = [("AES-256-GCM", AESGCM(key)), ("ChaCha20-Poly1305", ChaCha20Poly1305(key))]
 
    prefix = rng.randbytes(4)
    counter = 0
 
    def next_nonce():  # 4 byte tien to || 8 byte bo dem -> nonce khong bao gio trung
        nonlocal counter
        counter += 1
        return prefix + counter.to_bytes(8, "big")
 
    common = {
        "environment": env_name,
        "cpu": get_cpu_name(),
        "os": platform.platform(),
        "python_version": platform.python_version(),
        "cryptography_version": cryptography.__version__,
        "openssl_version": get_openssl_version(),
        "accel_disabled": bool(args.disable_accel),
        "seed": args.seed,
    }
    print(f"[{env_name}] {common['cpu']} | {common['os']}")
    print(f"Python {common['python_version']} | cryptography {common['cryptography_version']} | {common['openssl_version']}")
    print(f"Tat tang toc: {common['accel_disabled']} | seed: {args.seed}")
 
    rows = []
    for label, size in SIZES:
        data = rng.randbytes(size)
        reps = REPEATS[label]
        for name, aead in algos:
            for _ in range(args.warmup):
                aead.encrypt(next_nonce(), data, AAD)
            times = []
            gc.collect()
            gc.disable()
            try:
                for _ in range(reps):
                    nonce = next_nonce()
                    t0 = time.perf_counter()
                    aead.encrypt(nonce, data, AAD)
                    t1 = time.perf_counter()
                    times.append(t1 - t0)
            finally:
                gc.enable()
            lat_ms = [t * 1e3 for t in times]
            thr = [(size / MB) / t for t in times]
            row = dict(common)
            row.update({
                "algorithm": name, "size_label": label, "size_bytes": size, "repeats": reps,
                "latency_mean_ms": statistics.fmean(lat_ms),
                "latency_std_ms": statistics.stdev(lat_ms),
                "throughput_mean_MBps": statistics.fmean(thr),
                "throughput_std_MBps": statistics.stdev(thr),
                "latency_min_ms": min(lat_ms), "latency_max_ms": max(lat_ms),
            })
            rows.append(row)
            print(f"  {label:>6} {name:<18} {row['throughput_mean_MBps']:9.1f} +- {row['throughput_std_MBps']:7.1f} MB/s | "
                  f"{row['latency_mean_ms']:10.3f} +- {row['latency_std_ms']:8.3f} ms | n={reps}")
 
    os.makedirs(args.outdir, exist_ok=True)
    csv_path = os.path.join(args.outdir, f"benchmark_{args.label}.csv")
    with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:  # utf-8-sig: Excel doc dung tieng Viet
        w = csv.DictWriter(f, fieldnames=CSV_COLUMNS)
        w.writeheader()
        w.writerows(rows)
 
    meta = dict(common)
    meta.update({
        "timestamp_utc": datetime.now(timezone.utc).isoformat(timespec="seconds"),
        "command": cmdline,
        "OPENSSL_ia32cap": os.environ.get("OPENSSL_ia32cap", ""),
        "ram_mb": get_ram_mb(),
        "cpu_count": os.cpu_count(),
        "aad": AAD.decode(), "nonce_bytes": NONCE_LEN, "key_bits": 256,
        "timer": "time.perf_counter", "warmup": args.warmup, "repeats": REPEATS,
        "mb_definition": "1 MB = 1024*1024 bytes",
    })
    with open(os.path.join(args.outdir, f"benchmark_{args.label}_meta.json"), "w", encoding="utf-8") as f:
        json.dump(meta, f, indent=2, ensure_ascii=False)
    print(f"Da ghi {os.path.abspath(csv_path)} ({len(rows)} o do)")
 
 
if __name__ == "__main__":
    main()