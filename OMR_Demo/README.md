# Demo Chấm Phiếu Trắc Nghiệm Từ Ảnh Chụp Điện Thoại (OMR)

**Sinh viên:** Nguyễn Hữu Minh — Lớp D23_TH09 — Đề tài V1
**Nhiệm vụ (Nhóm 1 – Xử lý ảnh):** Chụp phiếu → căn chỉnh (nắn phối cảnh) → đọc ô tô.
Xử lý được ảnh **nghiêng, thiếu sáng, tô mờ**. Công cụ: **Python + OpenCV**.

> ⚠️ Đây là **bản demo/thử nghiệm**, không dùng để chấm thi thật hay dữ liệu thật của người thật (theo đúng lưu ý của giáo viên).

---

## 1. Ý tưởng

Mọi vị trí ô tô được định nghĩa trước trong **"không gian phiếu chuẩn"** (ảnh phẳng, thẳng).
Phiếu có **4 ô vuông đen ở 4 góc (4 đỉnh)** làm mốc canh chỉnh. Khi xử lý ảnh chụp bị
nghiêng, chương trình:

1. Phát hiện 4 đỉnh,
2. Dùng **phép biến đổi phối cảnh (homography)** nắn ảnh về đúng khung chuẩn,
3. Tại mỗi vị trí ô (đã biết trước), đo **tỷ lệ điểm đen/xám** để biết ô nào được tô.

Vì sau khi nắn thẳng thì toạ độ mọi ô là cố định, việc "đọc ô" trở nên rất chính xác.

## 2. Các bước xử lý ảnh (pipeline)

| Bước | Kỹ thuật OpenCV | Giải quyết vấn đề |
|------|-----------------|-------------------|
| Tiền xử lý | `cvtColor`, `GaussianBlur`, `adaptiveThreshold` | Ảnh **thiếu sáng / sáng không đều** |
| Phát hiện 4 đỉnh | `findContours` + lọc (vuông, đặc, gần 4 góc ảnh) | Tìm mốc canh chỉnh |
| Nắn phối cảnh | `getPerspectiveTransform`, `warpPerspective` | Ảnh **chụp nghiêng, méo** |
| Đọc ô tô | khoanh vùng tròn + đếm pixel tô (`countNonZero`) | Đo **tỷ lệ xám/đen** |
| Quyết định | ngưỡng tô + khoảng cách ô nhất/nhì | Câu **bỏ trống** & **tô mờ / nhập nhằng** |

## 3. Cấu trúc thư mục

```
OMR_Demo/
├── app/          ← MÃ NGUỒN chương trình (.py)
├── input/        ← ẢNH PHIẾU đầu vào để thử (+ answer_key.json: đáp án đối chiếu)
├── mau_phieu/    ← MẪU PHIẾU TRỐNG để in ra tô
├── output/       ← ẢNH KẾT QUẢ sau khi xử lý (tự sinh)
└── README.md
```

### Thư mục `app/` — mã nguồn

| File | Vai trò |
|------|---------|
| `sheet_config.py` | Định nghĩa hình học chuẩn của phiếu (4 đỉnh + lưới ô) — dùng chung |
| `io_utils.py` | Đọc/ghi ảnh hỗ trợ đường dẫn tiếng Việt có dấu + khai báo các thư mục |
| `generate_sheet.py` | Vẽ mẫu phiếu trống → `mau_phieu/` |
| `make_test_photo.py` | Sinh các ảnh thử (5 trường hợp) → `input/` |
| `omr_grader.py` | **Trái tim đề tài:** đọc ảnh → 4 đỉnh → nắn → đọc ô |
| `app_gui.py` | **App có giao diện:** chọn ảnh → chấm → xem kết quả |
| `run_demo.py` | Chạy nhanh toàn bộ ở chế độ dòng lệnh (không giao diện) |

### Thư mục `input/` — các ảnh thử (tên không dấu, theo từng trường hợp)

| Ảnh | Mô phỏng tình huống |
|-----|---------------------|
| `01_phieu_chuan_thang.jpg` | Phiếu thẳng, nét đậm (dễ nhất) |
| `02_phieu_nghieng.jpg` | Chụp **nghiêng** (méo phối cảnh) |
| `03_phieu_thieu_sang.jpg` | **Thiếu sáng**, ánh sáng không đều |
| `04_phieu_to_mo.jpg` | Tô bút chì **nhạt / mờ** |
| `05_phieu_nghieng_thieu_sang_to_mo.jpg` | **Kết hợp cả 3** (khó nhất) |

### Thư mục `output/` — kết quả xử lý

Mỗi ảnh input tạo ra 2 ảnh kết quả (tên theo ảnh gốc):
- `<ten_anh>__1_phat_hien_dinh.jpg` — ảnh gốc + 4 đỉnh phát hiện được (vòng đỏ TL/TR/BR/BL)
- `<ten_anh>__2_ket_qua_doc.jpg` — ảnh đã nắn thẳng + ô máy đọc (khoanh xanh)

## 4. Cách chạy

Cài thư viện (một lần):
```powershell
pip install opencv-python-headless numpy pillow
```

> Mọi lệnh dưới đây chạy **bên trong thư mục `app`**. Mở Terminal ở thư mục `OMR_Demo` rồi gõ `cd app` trước.

### Cách A — App có giao diện (khuyên dùng khi demo trước lớp)
```powershell
cd app; python app_gui.py
```
Trong cửa sổ hiện ra:
1. Bấm **"1. Chọn ảnh phiếu..."** → chọn một ảnh trong `input/` (hoặc bấm **"Tạo ảnh mẫu để thử"** nếu `input/` còn trống).
2. Bấm **"2. CHẤM PHIẾU"** → xem ảnh gốc + 4 đỉnh (trái), ảnh đã nắn + ô đọc được (phải), bảng đáp án + điểm (dưới).
3. Bấm **"3. Xuất kết quả..."** → hộp thoại hiện ra để **bạn tự chọn nơi lưu và tên file**. Chương trình xuất:
   - `ket_qua_<tên_ảnh>.csv` — bảng đáp án + điểm (mở được bằng Excel, có dấu tiếng Việt)
   - 2 ảnh kết quả (`__1_phat_hien_dinh.jpg`, `__2_ket_qua_doc.jpg`)

### Cách B — Chạy nhanh bằng dòng lệnh (chấm cả 5 trường hợp)
```powershell
cd app; python run_demo.py
```

### Chạy riêng từng phần
```powershell
cd app
python generate_sheet.py                 # tạo mẫu phiếu trống → mau_phieu/
python make_test_photo.py                # tạo 5 ảnh thử → input/
python omr_grader.py ../input/02_phieu_nghieng.jpg   # đọc một ảnh bất kỳ
```

Đọc **ảnh chụp thật** (sau khi in `mau_phieu/mau_phieu_trong.png` ra, tô bút chì rồi chụp):
```powershell
cd app; python omr_grader.py "duong_dan_anh_cua_ban.jpg"
```

## 5. Kết quả demo

Chạy `run_demo.py`, cả 5 trường hợp đều đọc đúng:

```
| 01_phieu_chuan_thang.jpg               | 19/19  | 100.0% |
| 02_phieu_nghieng.jpg                   | 19/19  | 100.0% |
| 03_phieu_thieu_sang.jpg                | 19/19  | 100.0% |
| 04_phieu_to_mo.jpg                     | 19/19  | 100.0% |
| 05_phieu_nghieng_thieu_sang_to_mo.jpg  | 19/19  | 100.0% |
```
(19/19 vì câu 10 cố ý bỏ trống để kiểm tra khả năng phát hiện câu chưa tô.)

## 6. Tinh chỉnh

Trong `omr_grader.py`:
- `FILL_THRESHOLD` (mặc định 0.35): tỷ lệ tô tối thiểu để tính là "có tô". Tăng nếu hay
  nhận nhầm nét bẩn; giảm nếu đọc hụt nét tô quá nhạt.
- `AMBIGUOUS_MARGIN` (0.15): ngưỡng phân biệt giữa ô chọn và ô nhì; để phát hiện câu tô 2 ô.

Thay đổi số câu / số lựa chọn / bố cục: sửa trong `sheet_config.py` (cả bộ vẽ và bộ đọc
tự cập nhật theo vì dùng chung file này).

## 7. Hướng mở rộng (phần của nhóm khác / làm thêm)

- **OCR mã sinh viên:** đọc phần "Mã SV" bằng Tesseract OCR (phần giáo viên nhắc đến OCR).
- **Xuất kết quả:** CSV bảng điểm và Moodle XML (nhiệm vụ của bạn Trịnh Xuân Phạng).
- Bộ đọc ô (`grade_sheet`) đã trả về dict kết quả sẵn sàng cho các phần này dùng lại.
