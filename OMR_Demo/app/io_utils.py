# -*- coding: utf-8 -*-
"""
io_utils.py
-----------
1) Đọc/ghi ảnh AN TOÀN với đường dẫn có ký tự Unicode (ví dụ "Nguyễn Hữu Minh").
   Trên Windows, cv2.imread()/cv2.imwrite() KHÔNG đọc/ghi được file nếu đường
   dẫn chứa ký tự tiếng Việt có dấu. Dùng numpy.fromfile/imdecode và
   imencode/tofile để tránh hoàn toàn vấn đề này.

2) Khai báo các THƯ MỤC của dự án để mọi file dùng chung (không phụ thuộc
   thư mục đang đứng khi chạy):
        OMR_Demo/
          ├── app/        (mã nguồn - chứa file này)
          ├── input/      (ảnh phiếu để thử)
          ├── mau_phieu/  (mẫu phiếu trống)
          └── output/     (ảnh kết quả xử lý)
"""
import os
import sys
import numpy as np
import cv2

# Ép console in được tiếng Việt (tránh lỗi UnicodeEncodeError trên Windows cp1252)
for _stream in (sys.stdout, sys.stderr):
    try:
        _stream.reconfigure(encoding="utf-8", errors="replace")
    except Exception:
        pass

# --- Thư mục dự án (ROOT = thư mục cha của app/) ---
APP_DIR = os.path.dirname(os.path.abspath(__file__))
ROOT_DIR = os.path.dirname(APP_DIR)
INPUT_DIR = os.path.join(ROOT_DIR, "input")
TEMPLATE_DIR = os.path.join(ROOT_DIR, "mau_phieu")
OUTPUT_DIR = os.path.join(ROOT_DIR, "output")


def ensure_dirs():
    """Tạo các thư mục input/mau_phieu/output nếu chưa có."""
    for d in (INPUT_DIR, TEMPLATE_DIR, OUTPUT_DIR):
        os.makedirs(d, exist_ok=True)


def imread_u(path, flags=cv2.IMREAD_COLOR):
    """Đọc ảnh, hỗ trợ đường dẫn Unicode. Trả về None nếu lỗi."""
    try:
        data = np.fromfile(path, dtype=np.uint8)
        if data.size == 0:
            return None
        return cv2.imdecode(data, flags)
    except Exception:
        return None


def imwrite_u(path, img):
    """Ghi ảnh, hỗ trợ đường dẫn Unicode. Trả về True/False."""
    try:
        ext = "." + path.rsplit(".", 1)[-1] if "." in path else ".png"
        ok, buf = cv2.imencode(ext, img)
        if not ok:
            return False
        buf.tofile(path)
        return True
    except Exception:
        return False
