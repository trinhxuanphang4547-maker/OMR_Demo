# -*- coding: utf-8 -*-
"""
omr_grader.py  --   (Nhóm 1 - Xử lý ảnh)
===========================================================
Đọc ảnh chụp phiếu trắc nghiệm và trả về lựa chọn của từng câu.

CÁC BƯỚC (đúng yêu cầu của giáo viên):
  (1) Tiền xử lý   : xám hoá + làm mờ + nhị phân thích nghi  -> chịu được
                     ảnh thiếu sáng, sáng không đều.
  (2) Phát hiện 4 đỉnh : tìm 4 ô vuông đen đặc ở 4 góc.
  (3) Nắn phối cảnh    : dùng homography đưa ảnh nghiêng về khung phiếu CHUẨN.
  (4) Đọc ô tô         : tại mỗi vị trí ô (đã biết trước trong sheet_config),
                         đo "tỷ lệ điểm đen/xám" trong ô -> biết ô nào được tô.
  (5) Quyết định       : mỗi câu chọn ô có tỷ lệ tô cao nhất, kèm ngưỡng để
                         loại câu bỏ trống và câu tô nhập nhằng (tô 2 ô).

Dùng như thư viện:
    from omr_grader import grade_sheet
    result = grade_sheet("test_photo.jpg")

Hoặc chạy trực tiếp:
    python omr_grader.py test_photo.jpg
"""
import os
import sys
import cv2
import numpy as np
import sheet_config as cfg
from io_utils import imread_u, imwrite_u, OUTPUT_DIR, ensure_dirs

# Ngưỡng quyết định (có thể tinh chỉnh)
FILL_THRESHOLD = 0.35      # tỷ lệ tô tối thiểu để coi 1 ô là "có tô"
AMBIGUOUS_MARGIN = 0.15    # ô nhì phải cách ô nhất ít nhất ngần này, nếu không -> nhập nhằng


# ---------------------------------------------------------------------------
# (1) TIỀN XỬ LÝ
# ---------------------------------------------------------------------------
def preprocess(gray):
    """Làm mờ nhẹ rồi nhị phân thích nghi (adaptive) để chịu ánh sáng không đều."""
    blur = cv2.GaussianBlur(gray, (5, 5), 0)
    binary = cv2.adaptiveThreshold(
        blur, 255, cv2.ADAPTIVE_THRESH_GAUSSIAN_C,
        cv2.THRESH_BINARY_INV, 41, 10)
    return binary


# ---------------------------------------------------------------------------
# (2) PHÁT HIỆN 4 ĐỈNH (4 ô vuông đen ở 4 góc)
# ---------------------------------------------------------------------------
def _order_corners(pts):
    """Sắp xếp 4 điểm theo thứ tự TL, TR, BR, BL."""
    pts = np.array(pts, dtype=np.float32)
    s = pts.sum(axis=1)
    d = np.diff(pts, axis=1).ravel()
    tl = pts[np.argmin(s)]
    br = pts[np.argmax(s)]
    tr = pts[np.argmin(d)]
    bl = pts[np.argmax(d)]
    return np.float32([tl, tr, br, bl])


def find_markers(binary):
    """
    Tìm 4 ô vuông đen đặc. Trả về 4 tâm theo thứ tự TL,TR,BR,BL.
    Lọc contour theo: diện tích hợp lý + gần vuông + đặc (fill cao).
    Rồi chọn 4 ứng viên nằm xa nhất về 4 góc ảnh.
    """
    h, w = binary.shape
    contours, _ = cv2.findContours(binary, cv2.RETR_LIST, cv2.CHAIN_APPROX_SIMPLE)

    img_area = h * w
    candidates = []
    for c in contours:
        area = cv2.contourArea(c)
        if area < img_area * 0.0003 or area > img_area * 0.05:
            continue
        x, y, bw, bh = cv2.boundingRect(c)
        if bh == 0:
            continue
        aspect = bw / float(bh)
        if not (0.6 < aspect < 1.4):          # gần vuông
            continue
        extent = area / float(bw * bh)        # độ "đặc"
        if extent < 0.65:
            continue
        cx, cy = x + bw / 2.0, y + bh / 2.0
        candidates.append((cx, cy, area))

    if len(candidates) < 4:
        raise RuntimeError(
            f"Chi tim thay {len(candidates)} dinh (can 4). "
            "Anh qua mo/toi hoac thieu goc.")

    # Chọn 4 ứng viên gần 4 góc ảnh nhất
    corners_ref = [(0, 0), (w, 0), (w, h), (0, h)]
    chosen = []
    used = set()
    for (rx, ry) in corners_ref:
        best, best_d = None, 1e18
        for i, (cx, cy, _a) in enumerate(candidates):
            if i in used:
                continue
            d = (cx - rx) ** 2 + (cy - ry) ** 2
            if d < best_d:
                best_d, best = d, i
        used.add(best)
        chosen.append((candidates[best][0], candidates[best][1]))

    return _order_corners(chosen)


# ---------------------------------------------------------------------------
# (3) NẮN PHỐI CẢNH
# ---------------------------------------------------------------------------
def warp_to_template(gray, markers):
    """Đưa ảnh về đúng khung phiếu chuẩn (PAGE_W x PAGE_H)."""
    dst = np.float32(cfg.DST_MARKER_POINTS)   # TL,TR,BR,BL tâm mốc chuẩn
    M = cv2.getPerspectiveTransform(markers, dst)
    warped = cv2.warpPerspective(gray, M, (cfg.PAGE_W, cfg.PAGE_H),
                                 flags=cv2.INTER_LINEAR,
                                 borderValue=255)
    return warped


# ---------------------------------------------------------------------------
# (4) ĐỌC Ô TÔ  (tỷ lệ điểm đen/xám trong ô)
# ---------------------------------------------------------------------------
def measure_fill(warped_bin, center, radius):
    """
    Đo tỷ lệ pixel được tô trong một ô tròn.
    warped_bin: ảnh nhị phân (nét tô = 255). Trả về giá trị 0..1.
    """
    cx, cy = int(center[0]), int(center[1])
    r = int(radius * 0.72)   # lấy lõi trong, tránh đụng vòng tròn in sẵn
    mask = np.zeros(warped_bin.shape, dtype=np.uint8)
    cv2.circle(mask, (cx, cy), r, 255, -1)
    total = cv2.countNonZero(mask)
    if total == 0:
        return 0.0
    filled = cv2.countNonZero(cv2.bitwise_and(warped_bin, mask))
    return filled / float(total)


def read_answers(warped):
    """
    Với ảnh đã nắn thẳng -> đọc từng câu.
    Trả về (answers, details).
      answers[q] = 'A'/'B'/'C'/'D' | None (trống) | '?' (nhập nhằng)
    """
    # nhị phân trên ảnh đã nắn để đo nét tô (bắt được cả nét xám mờ)
    wb = cv2.adaptiveThreshold(
        cv2.GaussianBlur(warped, (3, 3), 0), 255,
        cv2.ADAPTIVE_THRESH_GAUSSIAN_C, cv2.THRESH_BINARY_INV, 25, 8)

    centers = cfg.get_bubble_centers()
    answers = {}
    details = {}
    for q, opts in centers.items():
        ratios = [measure_fill(wb, pt, cfg.BUBBLE_RADIUS) for pt in opts]
        order = np.argsort(ratios)[::-1]
        top, second = order[0], order[1]
        top_r, second_r = ratios[top], ratios[second]

        if top_r < FILL_THRESHOLD:
            ans = None                      # không ô nào đủ đậm -> bỏ trống
        elif (top_r - second_r) < AMBIGUOUS_MARGIN:
            ans = "?"                       # hai ô xấp xỉ -> nhập nhằng
        else:
            ans = cfg.OPTIONS[top]
        answers[q] = ans
        details[q] = {cfg.OPTIONS[k]: round(ratios[k], 3) for k in range(len(opts))}
    return answers, details


# ---------------------------------------------------------------------------
# HÀM TỔNG HỢP
# ---------------------------------------------------------------------------
def grade_sheet(image_path, save_debug=True):
    """
    Chạy toàn bộ pipeline trên 1 ảnh. Trả về dict kết quả.
    """
    img = imread_u(image_path)
    if img is None:
        raise FileNotFoundError(f"Khong doc duoc anh: {image_path}")
    gray = cv2.cvtColor(img, cv2.COLOR_BGR2GRAY)

    binary = preprocess(gray)
    markers = find_markers(binary)
    warped = warp_to_template(gray, markers)
    answers, details = read_answers(warped)

    vis_markers, vis_warped = _make_vis(img, markers, warped, answers)
    out_paths = {}
    if save_debug:
        ensure_dirs()
        base = os.path.splitext(os.path.basename(image_path))[0]
        p1 = os.path.join(OUTPUT_DIR, f"{base}__1_phat_hien_dinh.jpg")
        p2 = os.path.join(OUTPUT_DIR, f"{base}__2_ket_qua_doc.jpg")
        imwrite_u(p1, vis_markers)
        imwrite_u(p2, vis_warped)
        out_paths = {"markers_img": p1, "result_img": p2}

    return {
        "image": image_path,
        "markers": markers.tolist(),
        "answers": answers,
        "details": details,
        "vis_markers": vis_markers,   # ảnh gốc + 4 đỉnh (BGR)
        "vis_warped": vis_warped,     # ảnh nắn thẳng + ô đọc được (BGR)
        "out_paths": out_paths,       # đường dẫn 2 ảnh đã lưu vào output/
    }


def _make_vis(orig, markers, warped, answers):
    """Tạo 2 ảnh minh hoạ (trả về numpy BGR) để lưu file hoặc hiển thị GUI."""
    # 1) Ảnh gốc + đánh dấu 4 đỉnh đã phát hiện
    vis = orig.copy()
    labels = ["TL", "TR", "BR", "BL"]
    for (px, py), lb in zip(markers, labels):
        cv2.circle(vis, (int(px), int(py)), 14, (0, 0, 255), 3)
        cv2.putText(vis, lb, (int(px) + 12, int(py)),
                    cv2.FONT_HERSHEY_SIMPLEX, 0.7, (0, 0, 255), 2)

    # 2) Ảnh đã nắn thẳng + tô màu kết quả đọc
    warp_bgr = cv2.cvtColor(warped, cv2.COLOR_GRAY2BGR)
    centers = cfg.get_bubble_centers()
    for q, opts in centers.items():
        ans = answers[q]
        for k, (x, y) in enumerate(opts):
            letter = cfg.OPTIONS[k]
            if ans == letter:
                cv2.circle(warp_bgr, (int(x), int(y)),
                           cfg.BUBBLE_RADIUS + 3, (0, 170, 0), 3)   # chọn: xanh
            elif ans == "?":
                cv2.circle(warp_bgr, (int(x), int(y)),
                           cfg.BUBBLE_RADIUS + 1, (0, 140, 255), 1)  # nhập nhằng
    return vis, warp_bgr


def _fmt(answers):
    parts = []
    for q in sorted(answers):
        a = answers[q]
        parts.append(f"Cau {q:>2}: {a if a is not None else '(trong)'}")
    return "\n".join(parts)


if __name__ == "__main__":
    from io_utils import INPUT_DIR
    default = os.path.join(INPUT_DIR, "05_phieu_nghieng_thieu_sang_to_mo.jpg")
    path = sys.argv[1] if len(sys.argv) > 1 else default
    res = grade_sheet(path)
    print(f"Anh: {res['image']}")
    print("4 dinh (TL,TR,BR,BL):")
    for lb, p in zip(["TL", "TR", "BR", "BL"], res["markers"]):
        print(f"   {lb}: ({p[0]:.0f}, {p[1]:.0f})")
    print("-" * 32)
    print(_fmt(res["answers"]))
    print("-" * 32)
    for p in res["out_paths"].values():
        print("Da luu:", p)
