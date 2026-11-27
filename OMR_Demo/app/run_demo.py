# -*- coding: utf-8 -*-
"""
run_demo.py
-----------
Chạy demo ở chế độ DÒNG LỆNH (không giao diện). Tự động:
  1) Sinh mẫu phiếu trống   -> mau_phieu/
  2) Sinh các ảnh thử        -> input/
  3) Đọc & chấm TẤT CẢ ảnh trong input/, đối chiếu đáp án, báo cáo độ chính xác
  4) Lưu ảnh kết quả         -> output/

Chạy:  python run_demo.py
"""
import os
import json
import sys

import sheet_config as cfg
from io_utils import INPUT_DIR, OUTPUT_DIR, imwrite_u, TEMPLATE_DIR, ensure_dirs
from generate_sheet import build_sheet
from make_test_photo import generate_all, CASES
from omr_grader import grade_sheet


def prepare():
    ensure_dirs()
    imwrite_u(os.path.join(TEMPLATE_DIR, "mau_phieu_trong.png"), build_sheet())
    print("[1] Mau phieu trong  -> mau_phieu/mau_phieu_trong.png")
    print("[2] Sinh anh thu     -> input/")
    generate_all()
    print()


def load_key():
    kp = os.path.join(INPUT_DIR, "answer_key.json")
    with open(kp, encoding="utf-8") as f:
        return {int(k): v for k, v in json.load(f).items()}


def grade_one(name, key):
    path = os.path.join(INPUT_DIR, name)
    res = grade_sheet(path, save_debug=True)
    answers = res["answers"]
    correct = total = 0
    wrong = []
    for q in range(1, cfg.NUM_QUESTIONS + 1):
        truth = key.get(q)
        got = answers.get(q)
        if truth is not None:
            total += 1
            if got == truth:
                correct += 1
            else:
                wrong.append((q, truth, got))
    acc = 100.0 * correct / total if total else 0
    return correct, total, acc, wrong


def main():
    print("=" * 58)
    print("  DEMO OMR - Cham phieu trac nghiem tu anh chup")
    print("  (Nhom 1 - Xu ly anh)")
    print("=" * 58)
    prepare()
    key = load_key()

    print("[3] Doc & cham tung truong hop:")
    print("    +----------------------------------------+--------+--------+")
    print("    | Truong hop (anh input)                 |  Dung  |  Acc   |")
    print("    +----------------------------------------+--------+--------+")
    all_ok = True
    for name in CASES:
        correct, total, acc, wrong = grade_one(name, key)
        if acc < 100:
            all_ok = False
        print(f"    | {name:<38} | {correct:>2}/{total:<3} | {acc:5.1f}% |")
        for q, truth, got in wrong:
            got_s = got if got is not None else "(trong)"
            print(f"    |    -> Cau {q}: dap an {truth}, may doc {got_s:<8}        |        |        |")
    print("    +----------------------------------------+--------+--------+")
    print(f"\n[4] Anh ket qua da luu tai: {OUTPUT_DIR}")
    print("=" * 58)
    return 0 if all_ok else 1


if __name__ == "__main__":
    sys.exit(main())
