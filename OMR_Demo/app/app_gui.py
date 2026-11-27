# -*- coding: utf-8 -*-
"""
app_gui.py  --  APP DEMO CÓ GIAO DIỆN (Tkinter)
================================================
Luồng dùng:  Chọn ảnh phiếu  ->  bấm "Chấm phiếu"  ->  xem kết quả.

Giao diện gồm:
  - Nút "Chọn ảnh phiếu..."      : mở hộp thoại chọn file ảnh (input)
  - Nút "Chấm phiếu"             : chạy xử lý ảnh OMR
  - Nút "Tạo ảnh mẫu để thử"     : sinh 5 ảnh thử vào input/ nếu chưa có ảnh
  - Khung trái : ảnh gốc + 4 đỉnh phát hiện được
  - Khung phải : ảnh đã nắn thẳng + ô máy đọc (khoanh xanh)
  - Bảng dưới  : đáp án từng câu + điểm (nếu có answer_key.json)

Chạy:  python app_gui.py
"""
import csv
import json
import os
import tkinter as tk
from tkinter import filedialog, messagebox, ttk

import cv2
from PIL import Image, ImageTk

from omr_grader import grade_sheet
from io_utils import imread_u, imwrite_u, INPUT_DIR, OUTPUT_DIR, ensure_dirs
import sheet_config as cfg

PREVIEW_W = 430          # bề rộng tối đa khi hiển thị ảnh


def cv2_to_tk(img_bgr, max_w=PREVIEW_W):
    """Chuyển ảnh OpenCV (BGR) -> ảnh Tkinter, co lại cho vừa khung."""
    h, w = img_bgr.shape[:2]
    scale = min(1.0, max_w / float(w))
    if scale < 1.0:
        img_bgr = cv2.resize(img_bgr, (int(w * scale), int(h * scale)))
    rgb = cv2.cvtColor(img_bgr, cv2.COLOR_BGR2RGB)
    return ImageTk.PhotoImage(Image.fromarray(rgb))


class OMRApp:
    def __init__(self, root):
        self.root = root
        self.image_path = None
        self.last_result = None   # kết quả lần chấm gần nhất (để xuất)
        self._imgs = {}      # giữ tham chiếu ảnh kẻo bị thu gom rác

        root.title("Demo OMR - Cham phieu trac nghiem (Nhom 1: Xu ly anh)")
        root.geometry("960x760")
        root.configure(bg="#f2f2f2")
        self._set_window_icon()

        self._build_toolbar()
        self._build_image_area()
        self._build_result_area()
        self._set_status("Hay chon mot anh phieu de bat dau.")

    def _set_window_icon(self):
        """Đổi logo cửa sổ (thay icon lông vũ mặc định của Tkinter)."""
        res_dir = os.path.join(os.path.dirname(os.path.abspath(__file__)),
                               "resources")
        ico = os.path.join(res_dir, "app_icon.ico")
        png = os.path.join(res_dir, "app_icon.png")
        try:
            if os.path.exists(ico):
                self.root.iconbitmap(ico)      # icon đẹp cho Windows
        except Exception:
            pass
        try:
            if os.path.exists(png):
                self._app_icon = ImageTk.PhotoImage(Image.open(png))
                self.root.iconphoto(True, self._app_icon)  # đa nền tảng
        except Exception:
            pass

    # ---------- dựng giao diện ----------
    def _build_toolbar(self):
        bar = tk.Frame(self.root, bg="#2c3e50", pady=8)
        bar.pack(fill="x")

        tk.Button(bar, text="1. Chon anh phieu...", command=self.pick_image,
                  bg="#3498db", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4, relief="flat").pack(side="left", padx=8)

        tk.Button(bar, text="2. CHAM PHIEU", command=self.run_grade,
                  bg="#27ae60", fg="white", font=("Segoe UI", 10, "bold"),
                  padx=10, pady=4, relief="flat").pack(side="left", padx=4)

        self.btn_export = tk.Button(bar, text="3. Xuat ket qua...",
                                    command=self.export_result,
                                    bg="#e67e22", fg="white",
                                    font=("Segoe UI", 10, "bold"),
                                    padx=10, pady=4, relief="flat",
                                    state="disabled")
        self.btn_export.pack(side="left", padx=4)

        tk.Button(bar, text="Tao anh mau de thu", command=self.make_sample,
                  bg="#95a5a6", fg="white", font=("Segoe UI", 10),
                  padx=10, pady=4, relief="flat").pack(side="left", padx=4)

        self.lbl_file = tk.Label(bar, text="(chua chon anh)", bg="#2c3e50",
                                 fg="#ecf0f1", font=("Segoe UI", 9))
        self.lbl_file.pack(side="left", padx=12)

    def _build_image_area(self):
        area = tk.Frame(self.root, bg="#f2f2f2")
        area.pack(fill="both", expand=False, pady=6)

        left = tk.LabelFrame(area, text=" Anh goc + 4 dinh phat hien ",
                             bg="#f2f2f2", font=("Segoe UI", 9, "bold"))
        left.pack(side="left", expand=True, padx=10)
        self.canvas_in = tk.Label(left, bg="#dddddd", width=52, height=20)
        self.canvas_in.pack(padx=6, pady=6)

        right = tk.LabelFrame(area, text=" Anh nan thang + o may doc ",
                              bg="#f2f2f2", font=("Segoe UI", 9, "bold"))
        right.pack(side="left", expand=True, padx=10)
        self.canvas_out = tk.Label(right, bg="#dddddd", width=52, height=20)
        self.canvas_out.pack(padx=6, pady=6)

    def _build_result_area(self):
        wrap = tk.Frame(self.root, bg="#f2f2f2")
        wrap.pack(fill="both", expand=True, padx=10, pady=4)

        self.lbl_score = tk.Label(wrap, text="", bg="#f2f2f2",
                                  font=("Segoe UI", 12, "bold"), fg="#2c3e50")
        self.lbl_score.pack(anchor="w")

        cols = ("cau", "dap_an", "trang_thai")
        self.tree = ttk.Treeview(wrap, columns=cols, show="headings", height=8)
        self.tree.heading("cau", text="Cau")
        self.tree.heading("dap_an", text="May doc")
        self.tree.heading("trang_thai", text="Ghi chu")
        self.tree.column("cau", width=80, anchor="center")
        self.tree.column("dap_an", width=120, anchor="center")
        self.tree.column("trang_thai", width=300, anchor="w")
        self.tree.pack(side="left", fill="both", expand=True)

        sb = ttk.Scrollbar(wrap, orient="vertical", command=self.tree.yview)
        sb.pack(side="left", fill="y")
        self.tree.configure(yscrollcommand=sb.set)

        self.status = tk.Label(self.root, text="", bg="#34495e", fg="white",
                               anchor="w", font=("Segoe UI", 9), padx=10)
        self.status.pack(fill="x", side="bottom")

    def _set_status(self, msg):
        self.status.config(text=msg)
        self.root.update_idletasks()

    # ---------- hành động ----------
    def pick_image(self):
        start_dir = INPUT_DIR if os.path.isdir(INPUT_DIR) else os.getcwd()
        path = filedialog.askopenfilename(
            title="Chon anh phieu tra loi",
            initialdir=start_dir,
            filetypes=[("Anh", "*.jpg *.jpeg *.png *.bmp"), ("Tat ca", "*.*")])
        if not path:
            return
        self.image_path = path
        self.lbl_file.config(text=os.path.basename(path))
        # hiện ảnh gốc ngay (chưa xử lý)
        img = imread_u(path)
        if img is not None:
            self._imgs["in"] = cv2_to_tk(img)
            self.canvas_in.config(image=self._imgs["in"], width=0, height=0)
        self.canvas_out.config(image="", width=52, height=20)
        self._clear_table()
        self.lbl_score.config(text="")
        self._set_status("Da chon anh. Bam 'CHAM PHIEU' de xu ly.")

    def make_sample(self):
        """Sinh bộ ảnh thử (5 trường hợp) vào thư mục input/ nếu chưa có."""
        self._set_status("Dang tao bo anh mau vao input/ ...")
        try:
            from make_test_photo import generate_all
            ensure_dirs()
            generate_all()
            # hiển thị sẵn trường hợp khó nhất để bấm Chấm phiếu ngay
            out = os.path.join(INPUT_DIR, "05_phieu_nghieng_thieu_sang_to_mo.jpg")
            self.image_path = out
            self.lbl_file.config(text=os.path.basename(out))
            img = imread_u(out)
            if img is not None:
                self._imgs["in"] = cv2_to_tk(img)
                self.canvas_in.config(image=self._imgs["in"], width=0, height=0)
            self._set_status("Da tao 5 anh thu trong input/. Bam 'CHAM PHIEU'.")
        except Exception as e:
            messagebox.showerror("Loi", f"Khong tao duoc anh mau:\n{e}")

    def run_grade(self):
        if not self.image_path:
            messagebox.showwarning("Chua co anh",
                                   "Hay chon anh phieu truoc (nut so 1).")
            return
        self._set_status("Dang xu ly anh...")
        try:
            res = grade_sheet(self.image_path, save_debug=True)
        except Exception as e:
            messagebox.showerror("Loi xu ly", str(e))
            self._set_status("Loi: " + str(e))
            return

        # lưu kết quả để có thể xuất
        self.last_result = res
        self.btn_export.config(state="normal")

        # hiện 2 ảnh kết quả
        self._imgs["in"] = cv2_to_tk(res["vis_markers"])
        self._imgs["out"] = cv2_to_tk(res["vis_warped"])
        self.canvas_in.config(image=self._imgs["in"], width=0, height=0)
        self.canvas_out.config(image=self._imgs["out"], width=0, height=0)

        self._fill_table(res["answers"])
        paths = res.get("out_paths", {})
        saved = "  |  ".join(os.path.basename(p) for p in paths.values())
        self._set_status("Xong. Da luu vao output/: " + saved
                         + "   (bam '3. Xuat ket qua' de luu noi khac)")

    # ---------- xuất kết quả ----------
    def export_result(self):
        """Cho người dùng CHỌN nơi lưu, rồi xuất: file CSV đáp án + ảnh kết quả."""
        if not self.last_result:
            messagebox.showwarning("Chua co ket qua",
                                   "Hay cham phieu truoc khi xuat.")
            return

        res = self.last_result
        base = os.path.splitext(os.path.basename(res["image"]))[0]

        # hộp thoại để NGƯỜI DÙNG TỰ CHỌN nơi lưu + tên file
        ensure_dirs()
        csv_path = filedialog.asksaveasfilename(
            title="Chon noi luu ket qua",
            initialdir=OUTPUT_DIR,
            initialfile=f"ket_qua_{base}.csv",
            defaultextension=".csv",
            filetypes=[("File CSV (Excel)", "*.csv"),
                       ("File van ban", "*.txt")])
        if not csv_path:
            return   # người dùng bấm Cancel

        # 1) Ghi bảng đáp án ra CSV
        answers = res["answers"]
        key = self._load_key()
        correct = total = 0
        try:
            with open(csv_path, "w", newline="", encoding="utf-8-sig") as f:
                w = csv.writer(f)
                w.writerow(["Cau", "May doc", "Dap an dung", "Ket qua"])
                for q in range(1, cfg.NUM_QUESTIONS + 1):
                    got = answers.get(q)
                    got_s = got if got is not None else "(trong)"
                    truth = key.get(q) if key else ""
                    verdict = ""
                    if key and truth:
                        total += 1
                        if got == truth:
                            correct += 1
                            verdict = "Dung"
                        else:
                            verdict = "Sai"
                    w.writerow([q, got_s, truth or "", verdict])
                if key and total:
                    w.writerow([])
                    w.writerow(["Tong", f"{correct}/{total} dung",
                                f"{100.0*correct/total:.1f}%", ""])
        except Exception as e:
            messagebox.showerror("Loi ghi CSV", str(e))
            return

        # 2) Lưu kèm 2 ảnh kết quả cạnh file CSV
        folder = os.path.dirname(csv_path)
        img1 = os.path.join(folder, f"{base}__1_phat_hien_dinh.jpg")
        img2 = os.path.join(folder, f"{base}__2_ket_qua_doc.jpg")
        imwrite_u(img1, res["vis_markers"])
        imwrite_u(img2, res["vis_warped"])

        self._set_status("Da xuat: " + os.path.basename(csv_path)
                         + " + 2 anh ket qua")
        messagebox.showinfo(
            "Xuat thanh cong",
            "Da luu:\n"
            f"- {os.path.basename(csv_path)}  (bang dap an)\n"
            f"- {os.path.basename(img1)}\n"
            f"- {os.path.basename(img2)}\n\n"
            f"Tai thu muc:\n{folder}")

    def _load_key(self):
        kp = os.path.join(INPUT_DIR, "answer_key.json")
        if os.path.exists(kp):
            try:
                with open(kp, encoding="utf-8") as f:
                    return {int(k): v for k, v in json.load(f).items()}
            except Exception:
                return None
        return None

    # ---------- bảng kết quả ----------
    def _clear_table(self):
        for i in self.tree.get_children():
            self.tree.delete(i)

    def _fill_table(self, answers):
        self._clear_table()
        # nạp đáp án chuẩn nếu có để chấm điểm
        key = None
        kp = os.path.join(INPUT_DIR, "answer_key.json")
        if os.path.exists(kp):
            try:
                with open(kp, encoding="utf-8") as f:
                    key = {int(k): v for k, v in json.load(f).items()}
            except Exception:
                key = None

        correct = total = 0
        for q in range(1, cfg.NUM_QUESTIONS + 1):
            got = answers.get(q)
            got_s = got if got is not None else "(trong)"
            note = ""
            if got == "?":
                note = "To nhap nhang (>1 o)"
            elif got is None:
                note = "Cau bo trong"
            if key is not None:
                truth = key.get(q)
                if truth is not None:
                    total += 1
                    if got == truth:
                        correct += 1
                        note = "Dung" if not note else note
                    else:
                        note = f"Sai (dap an da to: {truth})"
            self.tree.insert("", "end", values=(q, got_s, note))

        if key is not None and total:
            acc = 100.0 * correct / total
            self.lbl_score.config(
                text=f"Ket qua: doc dung {correct}/{total} cau co to  "
                     f"->  do chinh xac {acc:.1f}%")
        else:
            self.lbl_score.config(
                text="Da doc xong (khong co answer_key.json de doi chieu).")


if __name__ == "__main__":
    root = tk.Tk()
    app = OMRApp(root)
    root.mainloop()
