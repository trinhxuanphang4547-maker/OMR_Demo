# -*- coding: utf-8 -*-
"""
sheet_config.py
---------------
Định nghĩa HÌNH HỌC CHUẨN của mẫu phiếu trắc nghiệm (OMR).

Đây là file dùng chung cho cả 3 khâu:
  - generate_sheet.py  : vẽ phiếu trống theo đúng toạ độ này
  - make_test_photo.py : tô đáp án lên đúng ô này rồi làm méo ảnh để giả lập ảnh chụp
  - omr_grader.py      : sau khi nắn phối cảnh về đúng khung này thì biết ô nằm ở đâu

Ý tưởng cốt lõi:
  Mọi toạ độ ô tô được định nghĩa trong "không gian phiếu chuẩn" (ảnh phẳng, thẳng).
  Khi xử lý ảnh chụp bị nghiêng, ta phát hiện 4 ĐỈNH (4 ô vuông đen ở 4 góc),
  rồi dùng phép biến đổi phối cảnh (homography) để "nắn" ảnh chụp về đúng
  không gian phiếu chuẩn này. Lúc đó vị trí mọi ô tô đã biết trước => chỉ việc đo.
"""

# ---------------------------------------------------------------------------
# 1) Kích thước khung phiếu chuẩn (đơn vị: pixel)
# ---------------------------------------------------------------------------
PAGE_W = 800
PAGE_H = 1100

# ---------------------------------------------------------------------------
# 2) 4 ĐỈNH CANH CHỈNH (fiducial markers) - 4 ô vuông đen đặc ở 4 góc
#    Đây là mốc để phát hiện và nắn phối cảnh.
# ---------------------------------------------------------------------------
MARKER_SIZE = 50     # cạnh ô vuông mốc
MARKER_INSET = 30    # khoảng cách từ mép giấy vào mốc

# Toạ độ TÂM của 4 mốc, theo thứ tự: TL, TR, BR, BL (trên-trái, trên-phải,
# dưới-phải, dưới-trái). Thứ tự này được giữ cố định ở khắp mọi nơi.
_c = MARKER_INSET + MARKER_SIZE / 2.0
MARKER_CENTERS = [
    (_c,          _c),           # TL  trên-trái
    (PAGE_W - _c, _c),           # TR  trên-phải
    (PAGE_W - _c, PAGE_H - _c),  # BR  dưới-phải
    (_c,          PAGE_H - _c),  # BL  dưới-trái
]

# ---------------------------------------------------------------------------
# 3) Lưới ô tô
#    - 20 câu hỏi, mỗi câu 4 lựa chọn A, B, C, D
#    - Chia 2 cột: câu 1-10 bên trái, câu 11-20 bên phải
# ---------------------------------------------------------------------------
NUM_QUESTIONS = 20
OPTIONS = ["A", "B", "C", "D"]
NUM_OPTIONS = len(OPTIONS)

BUBBLE_RADIUS = 15          # bán kính vòng tròn ô tô
OPTION_GAP = 48             # khoảng cách ngang giữa các ô A-B-C-D
ROW_GAP = 46               # khoảng cách dọc giữa các câu
COL1_X = 150               # x của ô 'A' ở cột trái
COL2_X = 520               # x của ô 'A' ở cột phải
FIRST_ROW_Y = 230          # y của câu đầu tiên
ROWS_PER_COL = 10          # số câu mỗi cột


def get_bubble_centers():
    """
    Trả về dict:  {so_cau (1..20): [(x, y) cho A, B, C, D]}
    Toạ độ tâm từng ô tô trong không gian phiếu chuẩn.
    """
    centers = {}
    for i in range(NUM_QUESTIONS):
        if i < ROWS_PER_COL:
            col_x = COL1_X
            row = i
        else:
            col_x = COL2_X
            row = i - ROWS_PER_COL
        y = FIRST_ROW_Y + row * ROW_GAP
        opts = [(col_x + k * OPTION_GAP, y) for k in range(NUM_OPTIONS)]
        centers[i + 1] = opts
    return centers


# Điểm đích để nắn phối cảnh (chính là tâm 4 mốc, theo thứ tự TL,TR,BR,BL)
DST_MARKER_POINTS = MARKER_CENTERS
