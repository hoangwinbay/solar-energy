# HỆ THỐNG HỖ TRỢ RA QUYẾT ĐỊNH (DSS) CẢNH BÁO CHẤT LƯỢNG KHÔNG KHÍ & KHUYẾN NGHỊ HOẠT ĐỘNG NGOÀI TRỜI

> **Đề tài 2 - Môn học:** Hệ thống Hỗ trợ Ra Quyết định (Decision Support Systems - DSS)  
> **Khu vực áp dụng:** Hà Nội & TP. Hồ Chí Minh  
> **Công nghệ:** Python, Streamlit, Jupyter Notebook, Pandas, Plotly, PyDeck, Open-Meteo APIs  

---

## 1. TỔNG QUAN HỆ THỐNG

Hệ thống được xây dựng theo kiến trúc DSS kinh điển gồm 4 phân hệ:
1. **Phân hệ Quản lý Dữ liệu (Data Management):** Tự động thu thập dữ liệu chuỗi thời gian chất lượng không khí ($PM_{2.5}, PM_{10}, NO_2, O_3, CO$, US AQI) và thời tiết (Nhiệt độ, Độ ẩm, Mưa, Tia UV, Gió) từ Open-Meteo API kết hợp các file dataset CSV lịch sử.
2. **Phân hệ Cơ sở Tri thức & Động cơ Suy diễn (Model & Knowledge Base):** Động cơ suy diễn tập luật If-Then đa tiêu chí, kết hợp tiêu chuẩn US EPA và Bộ TN&MT Việt Nam, cá nhân hóa theo từng nhóm đối tượng (Người lớn khỏe mạnh, Trẻ em, Người già/bệnh nền hô hấp, Vận động viên).
3. **Phân hệ Giao diện Người dùng (User Interface - Web):** Ứng dụng Web Streamlit hiển thị đồng hồ đo AQI tức thời, bộ thiết lập thể trạng (độ tuổi, bệnh nền hô hấp, hen suyễn, tim mạch, phổi) và bảng khuyến nghị sức khỏe trực quan (tập thể dục ngoài trời, mở/đóng cửa sổ, đeo khẩu trang, bật máy lọc không khí) chuẩn phong cách IQAir.
4. **Phân hệ Phân tích & Đánh giá (Analysis Subsystem):** File Jupyter Notebook nghiên cứu khám phá dữ liệu (EDA), phân tích tương quan và kiểm thử độ tin cậy của tập luật.

---

## 2. CẤU TRÚC THƯ MỤC DỰ ÁN

```text
elegant-chandrasekhar/
│
├── data/                               # Thư mục lưu trữ các bộ Dataset CSV
│   ├── air_quality_hanoi.csv           # Dữ liệu chất lượng không khí & thời tiết Hà Nội (792 bản ghi)
│   ├── air_quality_hcm.csv             # Dữ liệu chất lượng không khí & thời tiết TP.HCM (792 bản ghi)
│   ├── weather_forecast.csv            # Dữ liệu dự báo thời tiết tổng hợp (1584 bản ghi)
│   └── dss_decision_rules.csv          # Bảng từ điển mã hóa tập luật If-Then của DSS
│
├── notebooks/                          # Thư mục Notebook nghiên cứu khoa học dữ liệu
│   └── air_quality_dss_analysis.ipynb  # File Jupyter Notebook hoàn chỉnh (EDA, Heatmap, Test luật)
│
├── src/                                # Mã nguồn xử lý nghiệp vụ
│   ├── __init__.py
│   ├── data_fetcher.py                 # Module kết nối Open-Meteo API và tiền xử lý
│   └── rule_engine.py                  # Module động cơ luật If-Then đa tiêu chí
│
├── scripts/
│   └── build_notebook.py               # Script tự động tạo và thực thi notebook
│
├── app.py                              # Ứng dụng Web chính phát triển bằng Streamlit
├── requirements.txt                    # Danh sách thư viện phụ thuộc
└── README.md                           # Tài liệu hướng dẫn sử dụng
```

---

## 3. HƯỚNG DẪN CÀI ĐẶT & CHẠY ỨNG DỤNG

### Bước 1: Cài đặt thư viện cần thiết
Mở terminal trong thư mục dự án và chạy lệnh:
```bash
pip install -r requirements.txt
```

### Bước 2: Khởi chạy ứng dụng Web DSS (Streamlit)
```bash
streamlit run app.py
```
Sau khi chạy lệnh, trình duyệt web sẽ tự động mở địa chỉ: `http://localhost:8501`.

### Bước 3: Mở file Jupyter Notebook phân tích
```bash
jupyter notebook notebooks/air_quality_dss_analysis.ipynb
```
File notebook đã được chạy sẵn với đầy đủ các bảng dữ liệu thống kê, biểu đồ phân tích 24h, ma trận tương quan (*correlation heatmap*) và 6 kịch bản kiểm thử mẫu.

---

## 4. TÓM TẮT BỘ QUY TẮC QUYẾT ĐỊNH (DECISION MATRIX)

Hệ thống đưa ra 3 khuyến nghị cốt lõi:

| Mức AQI | Điều kiện Khí tượng | 🏃 Chạy bộ / Thể thao | 😷 Đeo khẩu trang | 👶 Trẻ em & Nhóm nhạy cảm |
| :---: | :---: | :--- | :--- | :--- |
| **0 - 50** (Tốt) | Trời tạnh, UV < 6, T < 35°C | **Rất lý tưởng** để chạy bộ tự do | **Không cần** khẩu trang | **Khuyến khích** ra ngoài vui chơi |
| **0 - 50** (Tốt) | Mưa to (≥60%) hoặc Nắng gắt (≥36°C) | **Tạm dừng** ngoài trời (chuyển vào nhà) | Không cần khẩu trang bụi | **Hạn chế** ra ngoài tránh sốc nhiệt |
| **51 - 100** (Trung bình) | Thời tiết bình thường | **Được phép** chạy bộ bình thường | Khẩu trang y tế khi đi đường lớn | **Được phép** ra ngoài (theo dõi nhẹ) |
| **101 - 150** (Kém) | Bất kỳ | **Chỉ tập nhẹ < 30 phút** | Nên đeo **khẩu trang y tế / KN90** | **Hạn chế** ra ngoài, tránh đường lớn |
| **151 - 200** (Xấu) | Bất kỳ | **Cấm vận động mạnh ngoài trời** | Bắt buộc **N95 / KF94** ôm khít mặt | **Nghiêm cấm** ra ngoài, đóng kín cửa |
| **201 - 300** (Rất xấu) | Bất kỳ | **Cấm tuyệt đối mọi hoạt động ngoài trời** | Bắt buộc **N95**, chỉ ra ngoài khi cấp bách | **Ở trong phòng kín tuyệt đối** |
| **> 300** (Nguy hại) | Bất kỳ | **Cảnh báo khẩn cấp** | Đồ bảo hộ hô hấp chuyên dụng | **Ở trong phòng kín có lọc khí** |

---

## 5. TÍNH NĂNG NỔI BẬT ĐẠT ĐIỂM CAO KHI BẢO VỆ ĐỒ ÁN

1. **Đa tiêu chí thực tế:** Không bị cứng nhắc theo một biến AQI mà linh hoạt xử lý nghịch lý khí tượng (ví dụ: không khí sạch nhưng mưa to bão gió hoặc nắng gắt sốc nhiệt thì vẫn khuyến cáo dừng chạy bộ ngoài trời).
2. **Cá nhân hóa theo hồ sơ người dùng:** Phân tách rõ ràng giữa người khỏe mạnh, trẻ nhỏ, người già/hen suyễn và vận động viên chuyên nghiệp.
3. **Bảng khuyến nghị sức khỏe chuẩn IQAir cá nhân hóa:** Tự động đối soát mức độ ô nhiễm và thể trạng cá nhân (độ tuổi, bệnh hen suyễn, tim mạch, phổi...) để đưa ra ngay các chỉ dẫn bảo vệ sức khỏe: tập thể dục ngoài trời, mở/đóng cửa sổ, đeo khẩu trang khi ra ngoài và vận hành máy lọc không khí.
4. **Tìm khung giờ an toàn:** Tự động tính toán điểm rủi ro $Risk = 0.6 \times AQI + 0.2 \times Rain + 0.2 \times (UV \times 10)$ để gợi ý các khung giờ vàng tốt nhất trong ngày.
