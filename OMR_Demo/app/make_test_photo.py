# -*- coding: utf-8 -*-
"""
make_test_photo.py
------------------
Tạo nhiều ẢNH CHỤP GIẢ LẬP để demo mà không cần in và chụp phiếu thật.
Mỗi ảnh mô phỏng MỘT TRƯỜNG HỢP khó khác nhau, lưu vào thư mục  input/
với tên tiếng Việt KHÔNG DẤU rõ ràng:

    01_phieu_chuan_thang.jpg            - phiếu thẳng, nét đậm (dễ nhất)
    02_phieu_nghieng.jpg                - chụp nghiêng (méo phối cảnh)
    03_phieu_thieu_sang.jpg             - ánh sáng yếu, không đều
    04_phieu_to_mo.jpg                  - tô bút chì nhạt (nét mờ)
    05_phieu_nghieng_thieu_sang_to_mo.jpg - kết hợp cả 3 (khó nhất)

Tất cả dùng chung một ĐÁP ÁN (ANSWER_KEY) -> chỉ cần 1 file input/answer_key.json.

Chạy:  python make_test_photo.py
"""
import os
import json
import cv2
import numpy as np
import sheet_config as cfg
from generate_sheet import build_sheet
from io_utils import imwrite_u, INPUT_DIR, ensure_dirs

# Đáp án mẫu dùng để tô lên phiếu (câu -> lựa chọn).
ANSWER_KEY = {
    1: "A", 2: "C", 3: "B", 4: "D", 5: "A",
    6: "B", 7: "C", 8: "D", 9: "A", 10: "C",
    11: "D", 12: "B", 13: "A", 14: "C", 15: "B",
    16: "D", 17: "A", 18: "B", 19: "C", 20: "D",
}
# Cố ý BỎ TRỐNG câu 10 để kiểm tra phát hiện câu chưa tô
BLANK_QUESTIONS = {10}
# Ở các trường hợp "có vài câu mờ", những câu này được tô nhạt
FAINT_QUESTIONS = {5, 11, 18}

GRAY_DARK = 45     # nét bút chì tô đậm
GRAY_FAINT = 165   # nét bút chì tô nhạt


def fill_bubbles(img, faint="some"):
    """
    Tô các ô theo ANSWER_KEY, mô phỏng nét bút chì tô tay (không đều).
    faint = "none" : tất cả đều đậm
            "some" : chỉ các câu trong FAINT_QUESTIONS là nhạt
            "all"  : tô nhạt toàn bộ
    """
    centers = cfg.get_bubble_centers()
    r = cfg.BUBBLE_RADIUS - 3
    for qnum, ans in ANSWER_KEY.items():
        if qnum in BLANK_QUESTIONS:
            continue
        if faint == "all":
            gray = GRAY_FAINT
        elif faint == "some" and qnum in FAINT_QUESTIONS:
            gray = GRAY_FAINT
        else:
            gray = GRAY_DARK
        k = cfg.OPTIONS.index(ans)
        x, y = centers[qnum][k]
        rng = np.random.default_rng(qnum)
        for _ in range(26):
            dx = int(rng.integers(-r, r))
            dy = int(rng.integers(-r, r))
            jitter = int(rng.integers(-15, 15))
            c = max(0, min(255, gray + jitter))
            cv2.circle(img, (int(x + dx * 0.4), int(y + dy * 0.4)), 4, (c, c, c), -1)
    return img


def put_on_background(img, pad=180, bg=205):
    """Đặt tờ phiếu lên một nền lớn hơn (giống ảnh chụp có nền bàn)."""
    h, w = img.shape[:2]
    canvas = np.full((h + 2 * pad, w + 2 * pad, 3), bg, dtype=np.uint8)
    canvas[pad:pad + h, pad:pad + w] = img
    return canvas, pad


def warp_perspective(img):
    """Làm ảnh nghiêng như chụp lệch góc."""
    h, w = img.shape[:2]
    canvas, pad = put_on_background(img)
    H, W = canvas.shape[:2]
    src = np.float32([[pad, pad], [pad + w, pad],
                      [pad + w, pad + h], [pad, pad + h]])
    dst = np.float32([
        [pad + 60, pad + 40],
        [pad + w - 20, pad + 90],
        [pad + w - 70, pad + h - 30],
        [pad + 30, pad + h - 80],
    ])
    M = cv2.getPerspectiveTransform(src, dst)
    return cv2.warpPerspective(canvas, M, (W, H), borderValue=(205, 205, 205))


def add_uneven_lighting(img):
    """Ánh sáng không đều: tối dần về góc trên-trái (thiếu sáng)."""
    h, w = img.shape[:2]
    yy, xx = np.mgrid[0:h, 0:w]
    grad = 0.55 + 0.45 * (xx / w) * (yy / h)
    grad = np.clip(grad, 0.4, 1.0)[:, :, None]
    return (img.astype(np.float32) * grad).astype(np.uint8)


def add_blur_noise(img, sigma=7):
    img = cv2.GaussianBlur(img, (3, 3), 0)
    noise = np.random.default_rng(0).normal(0, sigma, img.shape).astype(np.float32)
    return np.clip(img.astype(np.float32) + noise, 0, 255).astype(np.uint8)


# --- Định nghĩa các trường hợp cần tạo ---
def _case_chuan_thang():
    img = fill_bubbles(build_sheet(), faint="none")
    img, _ = put_on_background(img)          # vẫn đặt trên nền nhưng không méo
    return add_blur_noise(img, sigma=3)


def _case_nghieng():
    img = fill_bubbles(build_sheet(), faint="none")
    return add_blur_noise(warp_perspective(img), sigma=4)


def _case_thieu_sang():
    img = fill_bubbles(build_sheet(), faint="none")
    img, _ = put_on_background(img)
    return add_blur_noise(add_uneven_lighting(img), sigma=6)


def _case_to_mo():
    img = fill_bubbles(build_sheet(), faint="all")
    img, _ = put_on_background(img)
    return add_blur_noise(img, sigma=4)


def _case_ket_hop():
    img = fill_bubbles(build_sheet(), faint="some")
    return add_blur_noise(add_uneven_lighting(warp_perspective(img)), sigma=7)


CASES = {
    "01_phieu_chuan_thang.jpg": _case_chuan_thang,
    "02_phieu_nghieng.jpg": _case_nghieng,
    "03_phieu_thieu_sang.jpg": _case_thieu_sang,
    "04_phieu_to_mo.jpg": _case_to_mo,
    "05_phieu_nghieng_thieu_sang_to_mo.jpg": _case_ket_hop,
}


def generate_all():
    """Sinh toàn bộ ảnh thử + file đáp án vào thư mục input/."""
    ensure_dirs()
    for name, fn in CASES.items():
        img = fn()
        out = os.path.join(INPUT_DIR, name)
        imwrite_u(out, img)
        print(f"[OK] {name}")
    key = {str(q): a for q, a in ANSWER_KEY.items() if q not in BLANK_QUESTIONS}
    with open(os.path.join(INPUT_DIR, "answer_key.json"), "w", encoding="utf-8") as f:
        json.dump(key, f, ensure_ascii=False, indent=2)
    print(f"[OK] answer_key.json  (bo trong cau {sorted(BLANK_QUESTIONS)})")
    print(f"Tat ca luu tai: {INPUT_DIR}")


if __name__ == "__main__":
    generate_all()
