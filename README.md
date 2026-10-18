# AnToanThongTin

## Hướng dẫn làm việc nhóm với Git



---

## 1. Nguyên tắc quan trọng

- Không code trực tiếp trên `main`.
- Mỗi người làm trên branch riêng.
- Trước khi làm phải cập nhật `main`.
- Làm xong thì tạo Pull Request để review trước khi merge.
- Mỗi Issue tương ứng với một phần việc.
- Khi làm Issue phải cập nhật trạng thái trên GitHub Project.

  ## 2. Cấu trúc project

```text
N16_SoSánhAESGCM_ChaCha20Poly1305/
├── SETUP/
│   ├── requirements.txt
│   └── README.md
├── SOURCE/
│   ├── benchmark.py
│   ├── plot.py
│   ├── test_negative.py
│   ├── nonce_sim.py
│   ├── packet.py
│   └── results/
│       ├── benchmark_may1.csv
│       ├── benchmark_may2.csv
│       ├── negative_test.log
│       └── nonce_sim.csv
├── THESIS/
│   ├── BaoCao.docx (hoặc .pdf)
│   ├── Slide.pptx
│   ├── charts/
│   │   ├── throughput.png
│   │   └── latency.png
│   └── video_demo.mp4 (nếu có)
├── SOFT/
│   └── (phần mềm liên quan, hoặc file link tải nếu dung lượng lớn)
└── HUONGDAN.PDF
```
## 3. Trước khi bắt đầu làm

### Bước 1: Về `main`

```bash
git checkout main
```

### Bước 2: Cập nhật code mới nhất

```bash
git pull origin main
```

### Bước 3: Tạo branch riêng

Ví dụ:

```bash
git checkout -b feature/lab01-grayscale
```

Kiểm tra đang đứng ở branch nào:

```bash
git branch --show-current
```

Nếu hiện:

```text
main
```

thì **chưa được code**.

---

## 4. Khi đang làm bài

Kiểm tra file đã thay đổi:

```bash
git status
```

Add file:

```bash
git add .
```

Commit:

```bash
git commit -m "feat: add grayscale conversion"
```

Push branch lần đầu:

```bash
git push -u origin feature/lab01-grayscale
```

Các lần sau:

```bash
git push
```

---

## 5. Cách xem Issue của mình

Trên GitHub:

```text
Repository
→ Issues
→ Assignee
→ chọn tên GitHub của mình
```

Mở Issue được giao và đọc:

- Mục tiêu
- Công việc cần làm
- File phụ trách
- Branch
- Checklist
- Reviewer

Khi hoàn thành từng mục, tick:

```markdown
- [x] Hoàn thành mục này
- [ ] Chưa hoàn thành mục này
```

Chỉ tick khi đã code và test xong.

---

## 6. Cập nhật GitHub Project

Trạng thái dùng chung:

```text
TODO
  ↓
IN PROGRESS
  ↓
REVIEW
  ↓
DONE
```

### Khi bắt đầu làm

Chuyển Issue:

```text
TODO → IN PROGRESS
```

### Khi code xong và tạo Pull Request

Chuyển:

```text
IN PROGRESS → REVIEW
```

### Khi PR được approve và merge

Chuyển:

```text
REVIEW → DONE
```

---

## 7. Tạo Pull Request

Sau khi push branch:

1. Vào GitHub.
2. Chọn **Compare & pull request**.
3. Kiểm tra:

```text
base: main
compare: branch-của-bạn
```

4. Viết tiêu đề, ví dụ:

```text
[Lab 01] Grayscale Conversion - Tên thành viên
```

5. Gán ít nhất 1 reviewer.
6. Chờ review rồi mới merge.

Có thể ghi trong PR:

```text
Closes #3
```

để Issue tự đóng sau khi merge.

---

## 8. Reviewer cần kiểm tra

- Code chạy được.
- Notebook chạy từ đầu đến cuối.
- Không dùng đường dẫn cá nhân.
- Output đúng.
- Giải thích đủ.
- Không có file rác.
- Không có conflict.

Reviewer chọn:

```text
Approve
```

hoặc:

```text
Request changes
```

---

## 9. Nếu `main` có thay đổi mới

Đảm bảo đang ở branch của mình:

```bash
git branch --show-current
```

Sau đó:

```bash
git pull origin main
```

Nếu có conflict, xử lý conflict rồi:

```bash
git add .
git commit -m "fix: resolve merge conflict"
git push
```

Không tự ý dùng:

```bash
git push --force
```

---

## 10. Sau khi PR được merge

Quay về `main`:

```bash
git checkout main
```

Cập nhật:

```bash
git pull origin main
```

Sau đó có thể bắt đầu Issue mới.

---

## 11. Checklist nhanh

### Trước khi code

- [ ] Đã `git checkout main`
- [ ] Đã `git pull origin main`
- [ ] Đã chuyển sang branch riêng
- [ ] Đã kiểm tra bằng `git branch --show-current`
- [ ] Đã đọc Issue
- [ ] Đã chuyển Project sang `IN PROGRESS`

### Trước khi tạo PR

- [ ] Code chạy được
- [ ] Notebook Run All không lỗi
- [ ] Không dùng đường dẫn cá nhân
- [ ] Checklist Issue đã tick
- [ ] Đã commit
- [ ] Đã push branch

### Trước khi DONE

- [ ] PR đã được review
- [ ] Reviewer đã approve
- [ ] PR đã merge
- [ ] Issue đã đóng
- [ ] Project = `DONE`

---

## 12. Workflow cần nhớ

```text
Issue
  ↓
Branch riêng
  ↓
Code
  ↓
Commit
  ↓
Push
  ↓
Pull Request
  ↓
Review
  ↓
Merge
  ↓
Done
```

