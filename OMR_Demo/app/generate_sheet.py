# -*- coding: utf-8 -*-
"""
generate_sheet.py
-----------------
Vẽ MẪU PHIẾU TRẮC NGHIỆM TRỐNG theo đúng hình học trong sheet_config.py.

Phiếu gồm:
  - 4 ô vuông đen đặc ở 4 góc  (4 đỉnh dùng để canh chỉnh/nắn phối cảnh)
  - Khung viền
  - Tiêu đề + ô ghi họ tên / mã sinh viên (chỉ để demo bố cục)
  - Lưới 20 câu x 4 ô tròn (A, B, C, D), chia 2 cột

Chạy:  python generate_sheet.py
Kết quả:  answer_sheet_template.png  (in ra để tô bằng bút chì)
"""
import os
import cv2
import numpy as np
import sheet_config as cfg
from io_utils import imwrite_u, TEMPLATE_DIR, ensure_dirs

WHITE = (255, 255, 255)
BLACK = (0, 0, 0)
GRAY = (120, 120, 120)


def draw_markers(img):
    """Vẽ 4 ô vuông đen đặc ở 4 góc."""
    s = cfg.MARKER_SIZE
    for (cx, cy) in cfg.MARKER_CENTERS:
        x0 = int(cx - s / 2)
        y0 = int(cy - s / 2)
        cv2.rectangle(img, (x0, y0), (x0 + s, y0 + s), BLACK, -1)


def draw_header(img):
    """Khung viền + tiêu đề + dòng kẻ điền thông tin."""
    cv2.rectangle(img, (15, 15), (cfg.PAGE_W - 15, cfg.PAGE_H - 15), BLACK, 2)

    cv2.putText(img, "PHIEU TRA LOI TRAC NGHIEM (DEMO OMR)",
                (110, 110), cv2.FONT_HERSHEY_SIMPLEX, 0.8, BLACK, 2, cv2.LINE_AA)
    cv2.putText(img, "Ho ten: .............................",
                (110, 150), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1, cv2.LINE_AA)
    cv2.putText(img, "Ma SV : .............................",
                (110, 180), cv2.FONT_HERSHEY_SIMPLEX, 0.6, BLACK, 1, cv2.LINE_AA)
    # Nhãn cột lựa chọn
    cv2.putText(img, "To kin o chi mot o cho moi cau (A/B/C/D)",
                (110, 205), cv2.FONT_HERSHEY_SIMPLEX, 0.45, GRAY, 1, cv2.LINE_AA)


def draw_bubbles(img):
    """Vẽ nhãn số câu, nhãn A/B/C/D và các ô tròn rỗng."""
    centers = cfg.get_bubble_centers()
    for qnum, opts in centers.items():
        # nhãn số câu nằm bên trái ô 'A'
        first_x, y = opts[0]
        cv2.putText(img, f"{qnum:>2}", (int(first_x - 48), int(y + 6)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.55, BLACK, 1, cv2.LINE_AA)
        for k, (x, y) in enumerate(opts):
            cv2.circle(img, (int(x), int(y)), cfg.BUBBLE_RADIUS, BLACK, 2)
            # chữ cái mờ bên trong ô (A/B/C/D) để người tô biết
            cv2.putText(img, cfg.OPTIONS[k], (int(x - 6), int(y + 6)),
                        cv2.FONT_HERSHEY_SIMPLEX, 0.5, GRAY, 1, cv2.LINE_AA)


def build_sheet():
    img = np.full((cfg.PAGE_H, cfg.PAGE_W, 3), 255, dtype=np.uint8)
    draw_header(img)
    draw_bubbles(img)
    draw_markers(img)
    return img


if __name__ == "__main__":
    ensure_dirs()
    sheet = build_sheet()
    out = os.path.join(TEMPLATE_DIR, "mau_phieu_trong.png")
    imwrite_u(out, sheet)
    print(f"[OK] Da tao mau phieu trong: {out}  ({cfg.PAGE_W}x{cfg.PAGE_H})")
