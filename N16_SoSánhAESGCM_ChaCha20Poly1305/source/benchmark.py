"""benchmark.py - Issue 1, 2, 3: Do hieu nang AESGCM va ChaCha20Poly1305."""
import csv
import os
import platform
import statistics
import sys
import time

# Neu chay cho may2 tren cung 1 may: tat tang toc phan cung AES-NI/PCLMULQDQ
LABEL = sys.argv[1] if len(sys.argv) > 1 else "may1"
if LABEL == "may2":
    os.environ["OPENSSL_ia32cap"] = "~0x200000200000000"

import cryptography
from cryptography.hazmat.primitives.ciphers.aead import AESGCM, ChaCha20Poly1305

MB = 1024 * 1024
SIZES = [("1KB", 1024, 10), ("1MB", MB, 10), ("10MB", 10 * MB, 10), ("100MB", 100 * MB, 5)]
AAD = b"header-aad"
HERE = os.path.dirname(os.path.abspath(__file__))


def main():
    key = os.urandom(32)
    algos = [("AESGCM", AESGCM(key)), ("ChaCha20Poly1305", ChaCha20Poly1305(key))]

    cpu_info = platform.processor() or platform.machine()
    os_info = platform.platform()
    py_ver = platform.python_version()
    crypto_ver = cryptography.__version__

    rows = []
    for size_label, size_bytes, repeats in SIZES:
        data = os.urandom(size_bytes)
        for algo_name, aead in algos:
            latencies_ms = []
            throughputs = []
            for _ in range(repeats):
                nonce = os.urandom(12)
                t0 = time.perf_counter()
                aead.encrypt(nonce, data, AAD)
                dt = time.perf_counter() - t0
                latencies_ms.append(dt * 1000)
                throughputs.append((size_bytes / MB) / dt)

            row = {
                "cpu": cpu_info,
                "os": os_info,
                "python_version": py_ver,
                "cryptography_version": crypto_ver,
                "algorithm": algo_name,
                "size": size_label,
                "repeats": repeats,
                "latency_mean_ms": round(statistics.mean(latencies_ms), 4),
                "latency_std_ms": round(statistics.stdev(latencies_ms), 4),
                "throughput_mean_MBps": round(statistics.mean(throughputs), 2),
                "throughput_std_MBps": round(statistics.stdev(throughputs), 2),
            }
            rows.append(row)
            print(f"{size_label:>5} | {algo_name:<16} | "
                  f"{row['throughput_mean_MBps']:8.2f} +- {row['throughput_std_MBps']:6.2f} MB/s | "
                  f"{row['latency_mean_ms']:8.4f} +- {row['latency_std_ms']:6.4f} ms")

    out_path = os.path.join(HERE, "results", f"benchmark_{LABEL}.csv")
    os.makedirs(os.path.dirname(out_path), exist_ok=True)
    with open(out_path, "w", newline="", encoding="utf-8") as f:
        writer = csv.DictWriter(f, fieldnames=list(rows[0].keys()))
        writer.writeheader()
        writer.writerows(rows)
    print("Da ghi:", out_path)


if __name__ == "__main__":
    main()
