"""nonce_sim.py - Issue 10: nonce bang bo dem va ngau nhien, mo phong va cham.

"""
import csv
import math
import os
import random

SEED = 2026
BITS = 16                              # khong gian nho de mo phong
SIZES = [64, 128, 256, 301, 512, 1000]  # so nonce rut ra moi lan thu
TRIALS = 2000                          # so lan thu cho moi kich thuoc
OUT = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                   "results", "nonce_sim.csv")


def counter_nonce(counter):
    """Nonce 12 byte tu bo dem (tang dan nen khong trung)."""
    return counter.to_bytes(12, "big")


def random_nonce():
    """Nonce 12 byte ngau nhien tu he dieu hanh."""
    return os.urandom(12)


def birthday(n, space):
    """Xac suat it nhat 2 nonce trung: 1 - exp(-n(n-1)/(2*space))."""
    return -math.expm1(-n * (n - 1) / (2 * space))


def simulate(n, bits, trials):
    """Dem so lan thu (trong 'trials') co it nhat 1 cap nonce trung."""
    space = 2 ** bits
    count = 0
    for _ in range(trials):
        seen = set()
        for _ in range(n):
            x = random.randrange(space)
            if x in seen:
                count += 1
                break
            seen.add(x)
    return count


def main():
    random.seed(SEED)
    rows = []

    # 1. Nonce ngau nhien, khong gian 16 bit: do thuc nghiem so voi cong thuc
    for n in SIZES:
        hits = simulate(n, BITS, TRIALS)
        rows.append(["random_16bit", BITS, n, TRIALS, hits,
                     round(hits / TRIALS, 6), round(birthday(n, 2 ** BITS), 6)])

    # 2. Nonce bo dem: 100000 nonce, dem so nonce bi trung
    n = 100000
    unique = len({counter_nonce(i) for i in range(n)})
    rows.append(["counter", 96, n, 1, n - unique, 0.0, 0.0])

    # 3. Nonce ngau nhien 96 bit: chi tinh theo cong thuc
    for e in (20, 24, 28, 32, 36):
        rows.append(["formula_96bit", 96, 2 ** e, "", "", "",
                     "%.3e" % birthday(2 ** e, 2 ** 96)])

    os.makedirs(os.path.dirname(OUT), exist_ok=True)
    with open(OUT, "w", newline="") as f:
        w = csv.writer(f)
        w.writerow(["mode", "bits", "n", "trials", "collisions",
                    "empirical_p", "theoretical_p"])
        w.writerows(rows)
    print("Da ghi", OUT)


if __name__ == "__main__":
    main()