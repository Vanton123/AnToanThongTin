# Hướng dẫn cài đặt và chạy thực nghiệm

## 1. Phiên bản công cụ
- Hệ điều hành: Windows 11
- Python: 3.10+ (đã kiểm thử trên Python 3.10 / 3.13)
- Thư viện: `cryptography==50.0.2`, `pandas==2.3.3`, `matplotlib==3.10.7`, `pytest==9.2.0`

## 2. Cài đặt môi trường ảo
Mở terminal tại thư mục gốc `N16_SoSánhAESGCM_ChaCha20Poly1305`:
```powershell
python -m venv .venv
.\.venv\Scripts\activate
pip install -r SETUP/requirements.txt
```

## 3. Lệnh chạy từng file thực nghiệm
Di chuyển vào thư mục mã nguồn:
```powershell
cd source
```

1. **Đo hiệu năng (Issue 1, 2, 3):**
   ```powershell
   python benchmark.py          # Ghi results/benchmark_may1.csv (bật tăng tốc phần cứng)
   python benchmark.py may2     # Ghi results/benchmark_may2.csv (tắt AES-NI qua OPENSSL_ia32cap)
   ```
2. **Vẽ biểu đồ (Issue 4):**
   ```powershell
   python plot.py               # Ghi ../thesis/charts/throughput.png và latency.png
   ```
3. **Kiểm thử âm và ca dương (Issue 5, 6, 7):**
   ```powershell
   pytest test_negative.py -v > results/negative_test.log
   ```
4. **Kiểm thử đóng gói/giải gói (Issue 8, 11):**
   ```powershell
   pytest test_packet.py -v > results/packet_test.log
   ```
5. **Mô phỏng va chạm Nonce (Issue 10):**
   ```powershell
   python nonce_sim.py          # Ghi results/nonce_sim.csv
   ```

## 4. Dữ liệu mẫu và Seed
- `nonce_sim.py`: sử dụng `SEED = 2026` (`random.seed(2026)`) để tái lập kết quả mô phỏng va chạm nonce 16-bit.
- `test_negative.py` và `test_packet.py`: dữ liệu mẫu bản rõ `b"Payload du lieu quan trong"`, AAD `b"Header tin nhan"`.
- `benchmark.py`: dữ liệu ngẫu nhiên sinh bằng `os.urandom` theo 4 kích thước (`1KB`, `1MB`, `10MB`, `100MB`), AAD `b"header-aad"`.

## 5. Quy trình hoàn nguyên (xóa môi trường ảo và cài lại từ đầu)
```powershell
deactivate
Remove-Item -Recurse -Force .venv
python -m venv .venv
.\.venv\Scripts\activate
pip install -r SETUP/requirements.txt
```
