// Dựng báo cáo Word cho đồ án OMR - chạy: node build_report.js
const fs = require("fs");
const path = require("path");
const {
  Document, Packer, Paragraph, TextRun, HeadingLevel, AlignmentType,
  TableOfContents, PageBreak, ImageRun, Table, TableRow, TableCell,
  WidthType, BorderStyle, ShadingType,
} = require("docx");

const ROOT = path.resolve(__dirname, "..");
const img = (rel) => fs.readFileSync(path.join(ROOT, rel));

// ---------- helpers ----------
const FONT = "Times New Roman";
const MONO = "Consolas";

function p(text, opts = {}) {
  return new Paragraph({
    alignment: opts.align || AlignmentType.JUSTIFIED,
    spacing: { after: 120, line: 276 },
    children: [new TextRun({ text, bold: opts.bold, italics: opts.italic,
      size: opts.size || 26, color: opts.color })],
  });
}
function bullet(text) {
  return new Paragraph({
    bullet: { level: 0 },
    spacing: { after: 80, line: 276 },
    children: [new TextRun({ text, size: 26 })],
  });
}
function h1(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_1,
    children: [new TextRun({ text })] });
}
function h2(text) {
  return new Paragraph({ heading: HeadingLevel.HEADING_2,
    children: [new TextRun({ text })] });
}
function codeLines(lines) {
  return lines.map((ln, i) =>
    new Paragraph({
      spacing: { after: i === lines.length - 1 ? 120 : 0, line: 240 },
      shading: { type: ShadingType.CLEAR, fill: "F3F4F6" },
      children: [new TextRun({ text: ln === "" ? " " : ln, font: MONO, size: 19 })],
    }));
}
function picture(rel, type, w, ratio, caption) {
  const h = Math.round(w * ratio);
  const els = [
    new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { before: 120, after: 40 },
      children: [new ImageRun({ type, data: img(rel),
        transformation: { width: w, height: h } })],
    }),
  ];
  if (caption) {
    els.push(new Paragraph({
      alignment: AlignmentType.CENTER,
      spacing: { after: 160 },
      children: [new TextRun({ text: caption, italics: true, size: 22, color: "555555" })],
    }));
  }
  return els;
}
// bảng 2 cột ảnh cạnh nhau
function twoPics(relA, typeA, capA, relB, typeB, capB, w, ratio) {
  const h = Math.round(w * ratio);
  const cell = (rel, type, cap) => new TableCell({
    width: { size: 50, type: WidthType.PERCENTAGE },
    borders: noBorder(),
    children: [
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new ImageRun({ type, data: img(rel),
          transformation: { width: w, height: h } })] }),
      new Paragraph({ alignment: AlignmentType.CENTER,
        children: [new TextRun({ text: cap, italics: true, size: 20, color: "555555" })] }),
    ],
  });
  return new Table({
    width: { size: 100, type: WidthType.PERCENTAGE },
    borders: noBorder(),
    rows: [new TableRow({ children: [cell(relA, typeA, capA), cell(relB, typeB, capB)] })],
  });
}
function noBorder() {
  const n = { style: BorderStyle.NONE, size: 0, color: "FFFFFF" };
  return { top: n, bottom: n, left: n, right: n, insideHorizontal: n, insideVertical: n };
}

// bảng dữ liệu có viền
function dataTable(header, rows, widths) {
  const thin = { style: BorderStyle.SINGLE, size: 4, color: "999999" };
  const borders = { top: thin, bottom: thin, left: thin, right: thin,
    insideHorizontal: thin, insideVertical: thin };
  const mk = (txt, opts = {}) => new TableCell({
    width: { size: opts.w, type: WidthType.DXA },
    shading: opts.head ? { type: ShadingType.CLEAR, fill: "2C3E50" } : undefined,
    margins: { top: 40, bottom: 40, left: 80, right: 80 },
    children: [new Paragraph({ alignment: opts.align || AlignmentType.LEFT,
      children: [new TextRun({ text: txt, bold: opts.head, size: 23,
        color: opts.head ? "FFFFFF" : "000000" })] })],
  });
  const headRow = new TableRow({ tableHeader: true,
    children: header.map((t, i) => mk(t, { head: true, w: widths[i],
      align: AlignmentType.CENTER })) });
  const bodyRows = rows.map((r) => new TableRow({
    children: r.map((t, i) => mk(String(t), { w: widths[i],
      align: i === 0 ? AlignmentType.LEFT : AlignmentType.LEFT })) }));
  return new Table({ columnWidths: widths, width: { size: widths.reduce((a, b) => a + b, 0), type: WidthType.DXA },
    borders, rows: [headRow, ...bodyRows] });
}

// ---------- TRANG BÌA ----------
const cover = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "TRƯỜNG ĐẠI HỌC …………………………", bold: true, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 400 },
    children: [new TextRun({ text: "KHOA CÔNG NGHỆ THÔNG TIN", bold: true, size: 26 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 20 },
    children: [new ImageRun({ type: "png", data: img("app/resources/app_icon.png"),
      transformation: { width: 110, height: 110 } })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 300, after: 120 },
    children: [new TextRun({ text: "BÁO CÁO ĐỒ ÁN", bold: true, size: 40, color: "2C3E50" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 300 },
    children: [new TextRun({
      text: "CHẤM PHIẾU TRẢ LỜI TRẮC NGHIỆM TỪ ẢNH CHỤP ĐIỆN THOẠI (OMR)",
      bold: true, size: 32, color: "1F4E79" })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 500 },
    children: [new TextRun({ text: "Phần: Xử lý ảnh — Nhóm 1", italics: true, size: 28 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "Sinh viên thực hiện:  Nguyễn Hữu Minh", size: 28 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 60 },
    children: [new TextRun({ text: "Lớp:  D23_TH09        Mã đề tài:  V1", size: 28 })] }),
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { before: 500 },
    children: [new TextRun({ text: "Năm 2025", italics: true, size: 26 })] }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- MỤC LỤC ----------
const toc = [
  new Paragraph({ alignment: AlignmentType.CENTER, spacing: { after: 160 },
    children: [new TextRun({ text: "MỤC LỤC", bold: true, size: 30 })] }),
  new TableOfContents("Mục lục", { hyperlink: true, headingStyleRange: "1-2" }),
  new Paragraph({ children: [new PageBreak()] }),
];

// ---------- NỘI DUNG ----------
const body = [];
const A = (...els) => els.forEach((e) => body.push(e));
const AA = (arr) => arr.forEach((e) => body.push(e));

// Chương 1
A(h1("CHƯƠNG 1. GIỚI THIỆU ĐỀ TÀI"));
A(h2("1.1. Đặt vấn đề"));
A(p("Trong dạy và học, việc chấm thủ công các phiếu trả lời trắc nghiệm tốn nhiều thời gian và dễ sai sót. Một giải pháp phổ biến là OMR (Optical Mark Recognition — nhận dạng dấu quang học): máy tính tự đọc các ô được tô trên phiếu. Tuy nhiên, nếu thu nhận phiếu bằng ảnh chụp từ điện thoại thì chất lượng ảnh không ổn định: ảnh bị nghiêng, méo phối cảnh, thiếu sáng hoặc nét tô bút chì mờ. Đề tài tập trung xử lý đúng các tình huống khó này."));
A(h2("1.2. Mục tiêu"));
AA([
  bullet("Thiết kế mẫu phiếu trắc nghiệm có 4 đỉnh ở 4 góc để canh chỉnh và khung lưới ô tô."),
  bullet("Từ ảnh chụp điện thoại: phát hiện 4 đỉnh, nắn phối cảnh ảnh về phiếu chuẩn."),
  bullet("Đọc chính xác các ô được tô bằng phân tích ngưỡng (tỷ lệ điểm đen/xám)."),
  bullet("Xử lý được ảnh nghiêng, thiếu sáng, tô mờ; nhận biết câu bỏ trống và câu tô nhập nhằng."),
  bullet("Có app giao diện: đưa ảnh vào → xử lý → xem và xuất kết quả."),
]);
A(h2("1.3. Phạm vi"));
A(p("Đề tài thực hiện ở mức mẫu demo/thử nghiệm, KHÔNG dùng để chấm thi thật hay sử dụng dữ liệu, phiếu thi thật của người thật. Dữ liệu thử nghiệm là ảnh phiếu do chương trình tự sinh và làm méo để mô phỏng ảnh chụp."));
A(h2("1.4. Phân công nhiệm vụ"));
A(dataTable(
  ["Nhóm", "Thành viên", "Nhiệm vụ"],
  [
    ["Nhóm 1 (Xử lý ảnh)", "Nguyễn Hữu Minh", "Chụp/nhận ảnh, căn chỉnh góc, đọc ô trắc nghiệm, đánh dấu ô chọn (nội dung báo cáo này)."],
    ["Nhóm 2 (Xuất kết quả)", "Trịnh Xuân Phạng", "Xuất bảng điểm CSV và tệp Moodle XML từ kết quả đọc phiếu."],
  ],
  [2200, 2400, 4600]));

// Chương 2
A(h1("CHƯƠNG 2. CƠ SỞ LÝ THUYẾT (NGUYÊN LÝ)"));
A(h2("2.1. Nhận dạng dấu quang học (OMR)"));
A(p("OMR là kỹ thuật nhận biết vị trí nào trên phiếu đã được tô đậm. Thay vì nhận dạng ký tự (OCR), OMR chỉ cần xác định một ô tròn/ô vuông có được tô hay không bằng cách đo mức độ đậm (số điểm ảnh tối) bên trong ô."));
A(h2("2.2. Nguyên lý canh chỉnh bằng 4 đỉnh và 'phiếu chuẩn'"));
A(p("Ý tưởng cốt lõi của đề tài: mọi vị trí ô tô được định nghĩa trước trong một 'không gian phiếu chuẩn' (ảnh phẳng, thẳng, kích thước cố định). Trên phiếu in sẵn 4 ô vuông đen ở 4 góc làm mốc. Khi có một ảnh chụp bị nghiêng, ta chỉ cần tìm 4 mốc này, tính phép biến đổi đưa chúng về đúng vị trí trong phiếu chuẩn, rồi áp dụng cho toàn ảnh. Sau khi 'nắn thẳng', toạ độ của mọi ô tô là cố định và đã biết trước, nên việc đọc ô trở nên đơn giản và chính xác."));
A(h2("2.3. Phép biến đổi phối cảnh (Homography)"));
A(p("Biến đổi phối cảnh mô tả quan hệ giữa cùng một mặt phẳng nhìn từ hai góc khác nhau, biểu diễn bằng ma trận 3×3 (ma trận H). Với 4 cặp điểm tương ứng (4 đỉnh trên ảnh chụp ↔ 4 đỉnh trên phiếu chuẩn) ta giải được H duy nhất. OpenCV cung cấp getPerspectiveTransform để tính H và warpPerspective để nắn ảnh. Công thức biến đổi một điểm (x, y):"));
AA(codeLines([
  "[x']   [h11 h12 h13] [x]",
  "[y'] = [h21 h22 h23] [y]      (toa do thuc = x'/w', y'/w')",
  "[w']   [h31 h32 h33] [1]",
]));
A(h2("2.4. Nhị phân hoá thích nghi và ngưỡng điểm đen/xám"));
A(p("Để tách nét tô khỏi nền trong điều kiện ánh sáng không đều, ta dùng ngưỡng thích nghi (adaptive threshold): ngưỡng được tính riêng cho từng vùng nhỏ của ảnh thay vì một ngưỡng chung. Sau khi nhị phân (nét tô = trắng, nền = đen), mức độ tô của một ô được đo bằng tỷ lệ điểm đã tô:"));
AA(codeLines([
  "ty_le_to = (so diem anh 'da to' trong o) / (tong so diem anh trong o)",
  "         = 0.0  (hoan toan trong)  ...  1.0  (to kin het o)",
]));
A(p("Mỗi câu có 4 ô A, B, C, D. Ô có tỷ lệ tô cao nhất là ô được chọn, với điều kiện vượt ngưỡng tối thiểu (lọc câu bỏ trống) và cách biệt rõ với ô cao nhì (lọc câu tô 2 ô, nhập nhằng). Nhờ so sánh tương đối giữa 4 ô nên nét tô mờ vẫn đọc được."));

// Chương 3
A(h1("CHƯƠNG 3. PHẦN MỀM & CÔNG CỤ SỬ DỤNG"));
A(dataTable(
  ["Công cụ / thư viện", "Phiên bản", "Vai trò trong đề tài"],
  [
    ["Python", "3.14", "Ngôn ngữ lập trình chính."],
    ["OpenCV (opencv-python-headless)", "5.1", "Xử lý ảnh: nhị phân, tìm contour, biến đổi phối cảnh, đọc ô."],
    ["NumPy", "2.5", "Tính toán ma trận, mảng điểm ảnh."],
    ["Pillow (PIL)", "13.0", "Hiển thị ảnh trên giao diện Tkinter, tạo logo."],
    ["Tkinter", "(kèm Python)", "Xây dựng giao diện đồ hoạ (GUI) cho app."],
    ["csv / json (chuẩn)", "(kèm Python)", "Lưu đáp án, xuất bảng điểm CSV."],
  ],
  [3400, 1800, 4000]));
A(p("Cài đặt thư viện: pip install opencv-python-headless numpy pillow", { italic: true, size: 24 }));

// Chương 4
A(h1("CHƯƠNG 4. THIẾT KẾ MẪU PHIẾU"));
A(p("Mẫu phiếu được định nghĩa bằng toạ độ trong file sheet_config.py và vẽ ra bằng OpenCV. Kích thước phiếu chuẩn 800×1100 điểm ảnh, gồm:"));
AA([
  bullet("4 ô vuông đen đặc ở 4 góc (cạnh 50px) — là 4 đỉnh mốc để canh chỉnh."),
  bullet("Khung viền, vùng tiêu đề, dòng ghi Họ tên / Mã SV."),
  bullet("Lưới 20 câu × 4 lựa chọn (A, B, C, D), chia 2 cột (câu 1–10 trái, 11–20 phải)."),
  bullet("Mỗi ô tô là một vòng tròn bán kính 15px, khoảng cách cố định để tính được toạ độ tâm."),
]);
AA(picture("mau_phieu/mau_phieu_trong.png", "png", 300, 1.375,
  "Hình 4.1. Mẫu phiếu trắc nghiệm trống (4 đỉnh đen ở 4 góc + lưới ô A/B/C/D)."));

// Chương 5
A(h1("CHƯƠNG 5. THUẬT TOÁN XỬ LÝ ẢNH"));
A(p("Chương trình xử lý một ảnh qua 5 bước (hàm grade_sheet trong omr_grader.py)."));
A(h2("5.1. Bước 1 — Tiền xử lý"));
A(p("Chuyển ảnh sang xám, làm mờ Gauss để giảm nhiễu, rồi nhị phân thích nghi để nét tô nổi bật kể cả khi ảnh thiếu sáng, sáng không đều."));
AA(codeLines([
  "blur   = cv2.GaussianBlur(gray, (5,5), 0)",
  "binary = cv2.adaptiveThreshold(blur, 255,",
  "            cv2.ADAPTIVE_THRESH_GAUSSIAN_C,",
  "            cv2.THRESH_BINARY_INV, 41, 10)",
]));
A(h2("5.2. Bước 2 — Phát hiện 4 đỉnh"));
A(p("Tìm tất cả contour, lọc ra những khối gần vuông, đặc (tỷ lệ lấp đầy cao) và có diện tích hợp lý. Sau đó chọn 4 ứng viên nằm gần 4 góc ảnh nhất và sắp xếp theo thứ tự TL, TR, BR, BL."));
AA(codeLines([
  "for c in contours:",
  "    area = cv2.contourArea(c)",
  "    x,y,bw,bh = cv2.boundingRect(c)",
  "    aspect = bw/bh                  # gan vuong: 0.6..1.4",
  "    extent = area/(bw*bh)           # do 'dac' > 0.65",
  "    # -> giu lai lam ung vien dinh",
]));
A(h2("5.3. Bước 3 — Nắn phối cảnh"));
A(p("Tính ma trận H từ 4 đỉnh phát hiện được sang 4 đỉnh chuẩn, rồi nắn toàn ảnh về khung 800×1100."));
AA(codeLines([
  "M = cv2.getPerspectiveTransform(markers, dst)",
  "warped = cv2.warpPerspective(gray, M, (800, 1100))",
]));
A(h2("5.4. Bước 4 — Đọc ô tô"));
A(p("Với mỗi ô, lấy một vùng tròn ở lõi ô (bán kính nhỏ hơn vòng in để tránh chạm viền), đếm số điểm ảnh đã tô và chia cho tổng số điểm để ra tỷ lệ tô."));
AA(codeLines([
  "def measure_fill(wb, center, radius):",
  "    mask = zeros; cv2.circle(mask, center, r, 255, -1)",
  "    total  = countNonZero(mask)",
  "    filled = countNonZero(bitwise_and(wb, mask))",
  "    return filled / total      # 0.0 .. 1.0",
]));
A(h2("5.5. Bước 5 — Quyết định đáp án"));
A(p("Với 4 tỷ lệ tô của mỗi câu, áp dụng quy tắc:"));
AA([
  bullet("Nếu ô cao nhất < ngưỡng FILL_THRESHOLD (0.35) → câu bỏ trống."),
  bullet("Nếu (ô cao nhất − ô cao nhì) < AMBIGUOUS_MARGIN (0.15) → nhập nhằng (tô ≥ 2 ô)."),
  bullet("Ngược lại → đáp án là ô có tỷ lệ tô cao nhất (A/B/C/D)."),
]);

// Chương 6
A(h1("CHƯƠNG 6. SƠ ĐỒ KHỐI CHƯƠNG TRÌNH"));
A(p("Sơ đồ khối (flowchart) tổng quát luồng xử lý một ảnh phiếu từ đầu vào đến khi xuất kết quả:"));
AA(picture("Bao_cao/so_do_khoi.png", "png", 440, 1.5,
  "Hình 6.1. Sơ đồ khối thuật toán chấm phiếu."));

// Chương 7
A(h1("CHƯƠNG 7. CẤU TRÚC CHƯƠNG TRÌNH & GIẢI THÍCH CODE"));
A(h2("7.1. Cấu trúc thư mục"));
A(dataTable(
  ["Thư mục / File", "Vai trò"],
  [
    ["app/", "Mã nguồn chương trình (.py)"],
    ["input/", "Ảnh phiếu đầu vào để thử + answer_key.json"],
    ["mau_phieu/", "Mẫu phiếu trống để in"],
    ["output/", "Ảnh kết quả sau xử lý (tự sinh)"],
    ["Bao_cao/", "Báo cáo và sơ đồ"],
  ],
  [3200, 6000]));
A(h2("7.2. Các module trong app/"));
A(dataTable(
  ["File", "Chức năng"],
  [
    ["sheet_config.py", "Khai báo hình học phiếu (4 đỉnh, lưới ô) — dùng chung."],
    ["io_utils.py", "Đọc/ghi ảnh hỗ trợ đường dẫn tiếng Việt + khai báo thư mục."],
    ["generate_sheet.py", "Vẽ mẫu phiếu trống."],
    ["make_test_photo.py", "Sinh ảnh thử (5 trường hợp) để demo."],
    ["omr_grader.py", "Lõi xử lý: phát hiện đỉnh → nắn → đọc ô (hàm grade_sheet)."],
    ["app_gui.py", "Giao diện: chọn ảnh → chấm → xuất kết quả."],
    ["run_demo.py", "Chạy nhanh toàn bộ ở chế độ dòng lệnh."],
  ],
  [2600, 6600]));
A(h2("7.3. Lưu ý kỹ thuật"));
A(p("Trên Windows, hàm cv2.imread/imwrite của OpenCV không đọc/ghi được file khi đường dẫn chứa ký tự tiếng Việt có dấu. Đề tài khắc phục bằng io_utils.py (dùng numpy.fromfile + cv2.imdecode) để đảm bảo chạy đúng với mọi đường dẫn."));

// Chương 8
A(h1("CHƯƠNG 8. GIAO DIỆN & CHỨC NĂNG PHẦN MỀM"));
A(p("App giao diện (app_gui.py) hoạt động theo luồng: (1) Chọn ảnh phiếu → (2) Chấm phiếu → (3) Xuất kết quả. Cửa sổ hiển thị: ảnh gốc kèm 4 đỉnh phát hiện (bên trái), ảnh đã nắn thẳng kèm ô máy đọc được khoanh xanh (bên phải), và bảng đáp án từng câu kèm điểm (bên dưới)."));
AA([
  bullet("Nút 'Chọn ảnh phiếu…': mở hộp thoại chọn file ảnh đầu vào."),
  bullet("Nút 'CHẤM PHIẾU': chạy toàn bộ pipeline xử lý ảnh."),
  bullet("Nút 'Xuất kết quả…': cho người dùng chọn nơi lưu, xuất file CSV (bảng đáp án + điểm, mở được bằng Excel) kèm 2 ảnh kết quả."),
  bullet("Nút 'Tạo ảnh mẫu để thử': tự sinh bộ ảnh thử nếu chưa có."),
]);

// Chương 9
A(h1("CHƯƠNG 9. KẾT QUẢ THỬ NGHIỆM"));
A(p("Thử nghiệm trên 5 ảnh mô phỏng các tình huống khó. Tất cả dùng chung một đáp án, trong đó câu 10 cố ý bỏ trống để kiểm tra khả năng phát hiện câu chưa tô (nên tối đa là 19 câu có tô)."));
A(dataTable(
  ["Trường hợp (ảnh input)", "Mô phỏng", "Kết quả"],
  [
    ["01_phieu_chuan_thang", "Phiếu thẳng, nét đậm", "19/19 — 100%"],
    ["02_phieu_nghieng", "Chụp nghiêng, méo phối cảnh", "19/19 — 100%"],
    ["03_phieu_thieu_sang", "Thiếu sáng, sáng không đều", "19/19 — 100%"],
    ["04_phieu_to_mo", "Nét tô bút chì nhạt/mờ", "19/19 — 100%"],
    ["05_...nghieng_thieu_sang_to_mo", "Kết hợp cả 3 (khó nhất)", "19/19 — 100%"],
  ],
  [3600, 3400, 2200]));
A(h2("9.1. Hình ảnh minh hoạ — trường hợp khó nhất (ảnh nghiêng + thiếu sáng + tô mờ)"));
A(twoPics(
  "output/05_phieu_nghieng_thieu_sang_to_mo__1_phat_hien_dinh.jpg", "jpg",
  "Hình 9.1. Phát hiện 4 đỉnh trên ảnh chụp nghiêng.",
  "output/05_phieu_nghieng_thieu_sang_to_mo__2_ket_qua_doc.jpg", "jpg",
  "Hình 9.2. Ảnh đã nắn thẳng + ô đọc được (khoanh xanh).",
  250, 1.3));
A(h2("9.2. Các trường hợp khác"));
A(twoPics(
  "output/03_phieu_thieu_sang__1_phat_hien_dinh.jpg", "jpg",
  "Hình 9.3. Ca thiếu sáng: vẫn tìm đúng 4 đỉnh.",
  "output/04_phieu_to_mo__2_ket_qua_doc.jpg", "jpg",
  "Hình 9.4. Ca tô mờ: vẫn đọc đúng ô.",
  250, 1.33));
A(p("Nhận xét: nhờ nắn phối cảnh bằng 4 đỉnh và so sánh tỷ lệ tô tương đối giữa 4 ô, chương trình đọc đúng 100% các câu có tô trên cả 5 trường hợp, đồng thời nhận đúng câu bỏ trống.", { bold: true }));

// Chương 10
A(h1("CHƯƠNG 10. KẾT LUẬN & HƯỚNG PHÁT TRIỂN"));
A(h2("10.1. Kết luận"));
AA([
  bullet("Đã xây dựng hoàn chỉnh phần xử lý ảnh (Nhóm 1): thiết kế phiếu 4 đỉnh, phát hiện góc, nắn phối cảnh, đọc ô bằng ngưỡng điểm đen/xám."),
  bullet("Xử lý tốt ảnh nghiêng, thiếu sáng, tô mờ; nhận biết câu bỏ trống và tô nhập nhằng."),
  bullet("Có app giao diện trực quan với chức năng xuất kết quả (CSV + ảnh)."),
]);
A(h2("10.2. Hướng phát triển"));
AA([
  bullet("Thêm OCR (ví dụ Tesseract) để tự đọc Mã sinh viên trên phiếu."),
  bullet("Kết nối phần xuất bảng điểm CSV và Moodle XML (Nhóm 2)."),
  bullet("Hỗ trợ nhiều mẫu phiếu, tăng số câu; chụp theo lô nhiều phiếu."),
  bullet("Thử nghiệm trên ảnh chụp thật nhiều điều kiện để tinh chỉnh ngưỡng."),
]);
A(p("Lưu ý: Đây là sản phẩm demo/thử nghiệm phục vụ học tập, không dùng cho chấm thi thật.", { italic: true }));

// ---------- DOC ----------
const doc = new Document({
  styles: {
    default: {
      document: { run: { font: FONT, size: 26 },
        paragraph: { spacing: { line: 276 } } },
      title: { run: { font: FONT, size: 44, bold: true },
        paragraph: { spacing: { after: 120 } } },
      heading1: { run: { font: FONT, size: 30, bold: true, color: "1F4E79" },
        paragraph: { spacing: { before: 280, after: 140 }, keepNext: true } },
      heading2: { run: { font: FONT, size: 27, bold: true, color: "2C3E50" },
        paragraph: { spacing: { before: 200, after: 100 }, keepNext: true } },
    },
  },
  sections: [{
    properties: { page: { margin: { top: 1440, bottom: 1440, left: 1700, right: 1134 } } },
    children: [...cover, ...toc, ...body],
  }],
});

Packer.toBuffer(doc).then((buf) => {
  const out = path.join(__dirname, "BaoCao_OMR_NguyenHuuMinh.docx");
  fs.writeFileSync(out, buf);
  console.log("Da tao: " + out);
});
