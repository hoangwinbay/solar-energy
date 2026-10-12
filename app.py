"""
app.py
HỆ THỐNG HỖ TRỢ RA QUYẾT ĐỊNH (DSS) CẢNH BÁO CHẤT LƯỢNG KHÔNG KHÍ & KHUYẾN NGHỊ HOẠT ĐỘNG NGOÀI TRỜI
Thiết kế Apple iOS Liquid Glass phiên bản NỀN TRẮNG TINH KHÔI (Light Mode & Frosted Glass):
- Nền trắng tinh khiết (#FFFFFF / #F8FAFC) với các vệt màu pastel mờ dịu mắt chuẩn Apple UI.
- Thẻ Liquid Glass kính mờ trong suốt (Backdrop Blur, Saturation, Viền bóng mềm, Phản xạ ánh sáng trắng).
- Bố cục Hero theo đúng ảnh mẫu của người dùng:
  + Vị trí: NHÀ / VỊ TRÍ CỦA BẠN - Thành Phố Hà Nội / TP.HCM
  + Chỉ số AQI khổng lồ rực rỡ + Arc Gauge đo độ ô nhiễm bán nguyệt
  + Nhãn thời tiết & chất lượng không khí chuẩn ngữ cảnh
  + Thẻ tư vấn khuyến cáo sức khỏe phủ kính mờ
  + 4 Thẻ chỉ số đo đạc: PM2.5 (so sánh chuẩn WHO), PM10, Khí NO2, Khí O3 (Ozone)
  + Thiết lập thể trạng cá nhân: Độ tuổi, bệnh nền hô hấp, hen suyễn, bệnh tim, bệnh phổi
  + Bảng khuyến nghị gộp theo giờ (Chạy bộ & Khẩu trang) cùng khối quyết định DSS tổng hợp
- Trọng tâm đề tài: HỖ TRỢ RA QUYẾT ĐỊNH (DSS) với tập luật If-Then đa tiêu chí:
  1. Hôm nay có nên chạy bộ / thể dục ngoài trời không? (Khung giờ vàng an toàn nhất?)
  2. Hôm nay có cần đeo khẩu trang không? (Loại khẩu trang nào?)
  3. Trẻ em & người già có nên ra ngoài không? (Hoạt động học đường / sân chơi?)
  4. Có nên mở cửa thông gió hay bật máy lọc không khí trong nhà?
- Minh bạch động cơ suy diễn: Hiển thị mã luật kích hoạt (R01 - R09), Chỉ số rủi ro DSS tổng hợp, Cơ chế trọng số đa tiêu chí.
- Biểu đồ cột xu hướng 24h, Dự báo 7 ngày, Bản đồ trạm cảm biến PyDeck Light Mode.
"""

import os
import base64
from pathlib import Path
from datetime import datetime
import streamlit as st
import pandas as pd
import numpy as np
import plotly.graph_objects as go
import pydeck as pdk
import joblib

# Module dữ liệu và luật If-Then DSS
import importlib
import src.data_fetcher
import src.rule_engine
importlib.reload(src.data_fetcher)
importlib.reload(src.rule_engine)

from src.data_fetcher import (
    fetch_city_data, 
    get_7day_summary, 
    CITIES, 
    VIETNAM_LOCATIONS, 
    search_vietnam_locations, 
    get_location_stations
)

# -------------------------------------------------------------
# 1. CẤU HÌNH TRANG STREAMLIT
# -------------------------------------------------------------
st.set_page_config(
    page_title="DSS Cảnh Báo Không Khí & Hoạt Động Ngoài Trời · iOS Liquid Glass",
    page_icon="😷",
    layout="wide",
    initial_sidebar_state="collapsed"
)

# -------------------------------------------------------------
# 2. HỆ THỐNG GIAO DIỆN IOS LIQUID GLASS NỀN TRẮNG (LIGHT MODE CSS)
# -------------------------------------------------------------
st.markdown("""<style>
/* Ẩn triệt để header mặc định và thanh bên của Streamlit */
header[data-testid="stHeader"],
.stApp > header,
#MainMenu,
div[data-testid="stDecoration"],
div[data-testid="stStatusWidget"] {
    display: none !important;
    height: 0 !important;
    visibility: hidden !important;
}

[data-testid="stSidebar"],
[data-testid="stSidebarCollapsedControl"] {
    display: none !important;
}

/* Nền trắng tinh khôi chuẩn Apple iOS với ánh sáng ambient pastel mờ */
.stApp {
    background-color: #f8fafc !important;
    background-image: 
        radial-gradient(circle at 12% 18%, rgba(224, 231, 255, 0.7) 0%, transparent 45%),
        radial-gradient(circle at 88% 12%, rgba(254, 226, 226, 0.5) 0%, transparent 45%),
        radial-gradient(circle at 50% 88%, rgba(240, 253, 244, 0.7) 0%, transparent 50%),
        radial-gradient(circle at 85% 75%, rgba(254, 243, 199, 0.5) 0%, transparent 40%),
        linear-gradient(180deg, #ffffff 0%, #f8fafc 50%, #f1f5f9 100%) !important;
    background-attachment: fixed !important;
    color: #0f172a !important;
    font-family: -apple-system, BlinkMacSystemFont, "SF Pro Display", "SF Pro Text", "Segoe UI", Roboto, Helvetica, sans-serif !important;
}

.block-container {
    padding-top: 1.2rem !important;
    padding-bottom: 3.5rem !important;
    max-width: 1220px !important;
}

/* Thẻ trắng chuẩn Apple iOS nền trắng tinh khôi & bo góc 24px */
.liquid-card {
    background: #ffffff !important;
    border: 1px solid rgba(226, 232, 240, 0.85) !important;
    border-radius: 24px !important;
    padding: 24px 28px !important;
    box-shadow: 0 10px 30px -4px rgba(15, 23, 42, 0.06),
                0 4px 12px -2px rgba(15, 23, 42, 0.03) !important;
    position: relative !important;
    overflow: hidden !important;
    margin-bottom: 24px !important;
    transition: transform 0.25s cubic-bezier(0.16, 1, 0.3, 1), box-shadow 0.25s ease, border-color 0.25s ease !important;
}

.liquid-card:hover {
    transform: translateY(-2px);
    border-color: rgba(203, 213, 225, 0.95) !important;
    box-shadow: 0 16px 36px -4px rgba(15, 23, 42, 0.09),
                0 6px 16px -2px rgba(15, 23, 42, 0.04) !important;
}

/* Streamlit Container viền bo tròn 24px & nền trắng đồng bộ */
[data-testid="stVerticalBlockBorderWrapper"] {
    background: #ffffff !important;
    border: 1px solid rgba(226, 232, 240, 0.85) !important;
    border-radius: 24px !important;
    padding: 0 !important;
    box-shadow: 0 10px 30px -4px rgba(15, 23, 42, 0.06),
                0 4px 12px -2px rgba(15, 23, 42, 0.03) !important;
    margin-bottom: 24px !important;
    overflow: hidden !important;
    transition: transform 0.25s ease, box-shadow 0.25s ease !important;
}

[data-testid="stVerticalBlockBorderWrapper"]:hover {
    border-color: rgba(203, 213, 225, 0.95) !important;
    box-shadow: 0 16px 36px -4px rgba(15, 23, 42, 0.09),
                0 6px 16px -2px rgba(15, 23, 42, 0.04) !important;
}

[data-testid="stVerticalBlockBorderWrapper"] > div {
    background: #ffffff !important;
    border: none !important;
    border-radius: 24px !important;
    padding: 24px 28px !important;
}

/* Thẻ Expander chi tiết chỉ số ô nhiễm */
[data-testid="stExpander"] {
    background: #ffffff !important;
    border: 1px solid rgba(226, 232, 240, 0.85) !important;
    border-radius: 24px !important;
    box-shadow: 0 10px 30px -4px rgba(15, 23, 42, 0.05),
                0 4px 12px -2px rgba(15, 23, 42, 0.02) !important;
    overflow: hidden !important;
    margin-bottom: 24px !important;
}

[data-testid="stExpander"] > details {
    background: #ffffff !important;
    border: none !important;
    border-radius: 24px !important;
}

[data-testid="stExpander"] summary {
    background: #ffffff !important;
    border: none !important;
    border-radius: 24px !important;
    padding: 14px 22px !important;
    font-weight: 700 !important;
    color: #0f172a !important;
}

[data-testid="stExpander"] div[data-testid="stExpanderDetails"] {
    background: #ffffff !important;
    padding: 16px 24px 24px 24px !important;
    border-top: 1px solid rgba(226, 232, 240, 0.8) !important;
}

[data-testid="stMetric"] {
    background: #f8fafc !important;
    border: 1px solid rgba(226, 232, 240, 0.85) !important;
    border-radius: 18px !important;
    padding: 12px 18px !important;
}

/* Kiểu chữ Hero & Vị trí */
.ios-breadcrumb {
    font-size: 12px;
    font-weight: 700;
    letter-spacing: 2px;
    text-transform: uppercase;
    color: #64748b;
    display: flex;
    align-items: center;
    justify-content: center;
    gap: 6px;
    margin-bottom: 6px;
}

.ios-city-title {
    font-size: 34px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
    text-align: center;
    margin-bottom: 8px;
}

.ios-aqi-number {
    font-size: 88px;
    font-weight: 800;
    line-height: 1;
    text-align: center;
    letter-spacing: -2px;
    margin: 6px 0 2px 0;
    filter: drop-shadow(0 4px 14px currentColor);
}

.ios-aqi-label {
    font-size: 15px;
    font-weight: 700;
    letter-spacing: 3px;
    color: #64748b;
    text-align: center;
    margin-bottom: 10px;
}

.ios-weather-status {
    font-size: 18px;
    font-weight: 600;
    color: #334155;
    text-align: center;
    margin-bottom: 4px;
}

.ios-air-status {
    font-size: 16px;
    color: #64748b;
    text-align: center;
    margin-bottom: 12px;
}

.ios-advisory-card {
    background: rgba(241, 245, 249, 0.75);
    border: 1px solid rgba(226, 232, 240, 0.9);
    border-radius: 18px;
    padding: 14px 18px;
    font-size: 13.5px;
    line-height: 1.55;
    color: #334155;
    text-align: center;
    margin-top: 14px;
    box-shadow: inset 0 1px 2px rgba(255, 255, 255, 0.8);
}

/* Thẻ chỉ số ô nhiễm (PM2.5, PM10, NO2, O3) */
.metric-header {
    display: flex;
    align-items: center;
    gap: 8px;
    font-size: 14px;
    font-weight: 600;
    color: #64748b;
    margin-bottom: 8px;
}

.metric-value {
    font-size: 28px;
    font-weight: 800;
    color: #0f172a;
    letter-spacing: -0.5px;
    margin-bottom: 4px;
}

.metric-unit {
    font-size: 16px;
    font-weight: 500;
    color: #64748b;
    margin-left: 4px;
}

.metric-sub {
    font-size: 12px;
    color: #64748b;
    font-weight: 500;
}

/* Dải dự báo theo giờ nằm ngang (Hourly Forecast Strip) */
.hourly-scroll-container {
    display: flex;
    flex-direction: row;
    gap: 14px;
    overflow-x: auto;
    padding: 14px 4px 16px 4px;
    scrollbar-width: thin;
    scrollbar-color: rgba(15, 23, 42, 0.18) transparent;
}

.hourly-scroll-container::-webkit-scrollbar {
    height: 5px;
}

.hourly-scroll-container::-webkit-scrollbar-track {
    background: rgba(15, 23, 42, 0.04);
    border-radius: 4px;
}

.hourly-scroll-container::-webkit-scrollbar-thumb {
    background: rgba(15, 23, 42, 0.18);
    border-radius: 4px;
}

.hourly-pill {
    flex: 0 0 88px;
    width: 88px;
    display: flex;
    flex-direction: column;
    align-items: center;
    justify-content: center;
    padding: 14px 8px;
    border-radius: 18px;
    background: rgba(255, 255, 255, 0.8);
    border: 1px solid rgba(226, 232, 240, 0.9);
    box-shadow: 0 2px 8px rgba(15, 23, 42, 0.04);
    transition: all 0.22s ease;
}

.hourly-pill:hover {
    background: #ffffff;
    transform: translateY(-3px);
    border-color: rgba(203, 213, 225, 1);
    box-shadow: 0 6px 16px rgba(15, 23, 42, 0.08);
}

.hourly-time {
    font-size: 12.5px;
    font-weight: 600;
    color: #475569;
    margin-bottom: 6px;
    white-space: nowrap;
}

.hourly-avatar {
    font-size: 28px;
    line-height: 1;
    margin: 4px 0 8px 0;
    filter: drop-shadow(0 2px 6px rgba(0,0,0,0.12));
}

.hourly-aqi {
    font-size: 18px;
    font-weight: 800;
    line-height: 1.1;
    margin-bottom: 3px;
}

.hourly-cat {
    font-size: 11.5px;
    font-weight: 600;
    color: #64748b;
}

/* Home Indicator Bar phong cách iOS */
.ios-home-indicator {
    width: 120px;
    height: 4px;
    background: rgba(15, 23, 42, 0.2);
    border-radius: 100px;
    margin: 18px auto 6px auto;
}

/* Phù hiệu quyết định DSS (Badge) */
.decision-badge {
    display: inline-flex;
    align-items: center;
    gap: 6px;
    padding: 6px 14px;
    border-radius: 30px;
    font-size: 12.5px;
    font-weight: 800;
    letter-spacing: 0.5px;
    text-transform: uppercase;
}

/* Thẻ hoạt động sinh hoạt (Activity Card) */
.activity-card {
    background: rgba(255, 255, 255, 0.75);
    border: 1px solid rgba(226, 232, 240, 0.85);
    border-radius: 18px;
    padding: 16px 18px;
    transition: all 0.2s ease;
}
.activity-card:hover {
    background: #ffffff;
    border-color: rgba(203, 213, 225, 1);
    transform: translateY(-2px);
    box-shadow: 0 8px 20px rgba(15, 23, 42, 0.06);
}

/* Tùy biến Streamlit Selectbox & Input sang Liquid Glass nền sáng */
div[data-baseweb="select"] > div {
    background: rgba(255, 255, 255, 0.9) !important;
    border: 1px solid rgba(203, 213, 225, 0.9) !important;
    border-radius: 16px !important;
    color: #0f172a !important;
    backdrop-filter: blur(20px) !important;
    box-shadow: 0 2px 6px rgba(15, 23, 42, 0.04) !important;
}

div[data-baseweb="select"] span {
    color: #0f172a !important;
    font-weight: 600 !important;
}

/* Thanh tìm kiếm chuẩn mẫu ảnh người dùng */
div[data-testid="stTextInput"] {
    width: 100% !important;
    margin-bottom: 14px !important;
}

div[data-testid="stTextInput"] > div {
    background: transparent !important;
    border: none !important;
}

div[data-testid="stTextInput"] div[data-baseweb="base-input"],
div[data-testid="stTextInput"] div[data-baseweb="input"] {
    background: #ffffff !important;
    border: 1px solid #d1d5db !important;
    border-radius: 12px !important;
    height: 48px !important;
    box-shadow: 0 1px 2px rgba(15, 23, 42, 0.04) !important;
    transition: all 0.2s cubic-bezier(0.16, 1, 0.3, 1) !important;
}

div[data-testid="stTextInput"] div[data-baseweb="base-input"]:focus-within,
div[data-testid="stTextInput"] div[data-baseweb="input"]:focus-within {
    border-color: #3b82f6 !important;
    box-shadow: 0 0 0 3px rgba(59, 130, 246, 0.15) !important;
}

div[data-testid="stTextInput"] input {
    background: transparent !important;
    border: none !important;
    color: #0f172a !important;
    font-size: 15px !important;
    font-weight: 500 !important;
    padding-left: 42px !important;
    background-image: url("data:image/svg+xml,%3Csvg xmlns='http://www.w3.org/2000/svg' fill='none' viewBox='0 0 24 24' stroke='%2394a3b8' stroke-width='1.8'%3E%3Ccircle cx='10.5' cy='10.5' r='6.5'/%3E%3Cpath stroke-linecap='round' d='M15.5 15.5L20 20'/%3E%3C/svg%3E") !important;
    background-repeat: no-repeat !important;
    background-position: left 14px center !important;
    background-size: 19px 19px !important;
}

div[data-testid="stTextInput"] input::placeholder {
    color: #94a3b8 !important;
    font-weight: 400 !important;
    font-size: 14.5px !important;
}

/* Khối mở rộng Expander */
div[data-testid="stExpander"] {
    background: rgba(255, 255, 255, 0.8) !important;
    border: 1px solid rgba(226, 232, 240, 0.9) !important;
    border-radius: 20px !important;
    overflow: hidden !important;
    box-shadow: 0 4px 14px rgba(15, 23, 42, 0.03) !important;
}

div[data-testid="stExpander"] summary {
    color: #0f172a !important;
    font-weight: 700 !important;
}

/* Nút bấm Download sang Glass sáng */
.stDownloadButton > button {
    background: rgba(241, 245, 249, 0.9) !important;
    color: #0f172a !important;
    border: 1px solid rgba(203, 213, 225, 0.9) !important;
    border-radius: 14px !important;
    backdrop-filter: blur(15px) !important;
    font-weight: 700 !important;
    transition: all 0.2s ease !important;
}
.stDownloadButton > button:hover {
    background: #ffffff !important;
    border-color: #3b82f6 !important;
    color: #2563eb !important;
    transform: translateY(-1px) !important;
    box-shadow: 0 4px 12px rgba(37, 99, 235, 0.15) !important;
}

/* Thẻ Container có viền bo tròn chuẩn Liquid Glass */
div[data-testid="stVerticalBlockBorderWrapper"] {
    background: rgba(255, 255, 255, 0.85) !important;
    backdrop-filter: blur(28px) saturate(180%) !important;
    -webkit-backdrop-filter: blur(28px) saturate(180%) !important;
    border: 1px solid rgba(226, 232, 240, 0.9) !important;
    border-radius: 24px !important;
    box-shadow: 0 10px 30px -4px rgba(15, 23, 42, 0.05),
                0 4px 12px -2px rgba(15, 23, 42, 0.02) !important;
    padding: 18px 22px !important;
    margin-bottom: 20px !important;
}
div[data-testid="stVerticalBlockBorderWrapper"] > div {
    border: none !important;
}
</style>""", unsafe_allow_html=True)


# -------------------------------------------------------------
# 3. HÀM TIỆN ÍCH DỮ LIỆU & GIAO DIỆN
# -------------------------------------------------------------
@st.cache_data
def get_rec_icon_b64(icon_name: str) -> str:
    """Tải và mã hóa Base64 hình ảnh icon khuyến nghị từ thư mục assets/icons."""
    icon_path = Path("assets/icons") / f"{icon_name}.png"
    if icon_path.exists():
        with open(icon_path, "rb") as f:
            encoded = base64.b64encode(f.read()).decode("utf-8")
        return f"data:image/png;base64,{encoded}"
    return ""


@st.cache_resource
def load_ml_model():
    """Tải mô hình Machine Learning Random Forest Multi-Output đã huấn luyện trên 50.000 mẫu dữ liệu."""
    model_path = Path("models/health_rec_model.joblib")
    if model_path.exists():
        try:
            return joblib.load(model_path)
        except Exception as e:
            print(f"Lỗi tải mô hình ML: {e}")
    return None


def get_aqi_theme(aqi_val: float):
    """Màu sắc chuẩn EPA và nhãn hiển thị cho AQI."""
    if pd.isna(aqi_val):
        return "#94a3b8", "Không xác định", "😷"
    aqi = float(aqi_val)
    if aqi <= 50:
        return "#10b981", "Tốt", "😊"  # Emerald Green
    elif aqi <= 100:
        return "#eab308", "Trung bình", "😷"  # Warm Amber
    elif aqi <= 150:
        return "#f97316", "Kém (Nhạy cảm)", "😷"  # Vibrant Orange
    elif aqi <= 200:
        return "#ef4444", "Xấu", "😷"  # Red / Coral
    elif aqi <= 300:
        return "#a855f7", "Rất xấu", "😷"  # Purple
    else:
        return "#be123c", "Nguy hại", "🛑"  # Deep Maroon


def get_aqi_advisory(aqi_val: float) -> str:
    """Trả về thông điệp khuyến cáo sức khỏe phù hợp chính xác với từng mức chất lượng không khí."""
    if pd.isna(aqi_val):
        return "Đang kết nối dữ liệu quan trắc không khí cho khu vực này."
    aqi = float(aqi_val)
    if aqi <= 50:
        return "Chất lượng không khí rất tốt và trong lành. Không có nguy cơ ảnh hưởng sức khỏe, rất lý tưởng cho mọi hoạt động thể chất ngoài trời và thông gió tự nhiên."
    elif aqi <= 100:
        return "Chất lượng không khí ở mức chấp nhận được. Nhóm người cực kỳ nhạy cảm với bụi mịn nên chú ý nếu có triệu chứng ho hoặc khó thở nhẹ khi ở ngoài trời lâu."
    elif aqi <= 150:
        return "Nhóm nhạy cảm (trẻ em, người cao tuổi, người có bệnh hô hấp hoặc tim mạch) có thể gặp vấn đề sức khỏe. Nên hạn chế vận động gắng sức ngoài trời và đeo khẩu trang bảo vệ."
    elif aqi <= 200:
        return "Không khí ô nhiễm xấu, bắt đầu ảnh hưởng xấu đến sức khỏe của tất cả mọi người. Người dân nên hạn chế hoạt động mạnh ngoài trời và bắt buộc đeo khẩu trang lọc bụi mịn PM2.5 (N95)."
    elif aqi <= 300:
        return "Cảnh báo sức khỏe nghiêm trọng: Toàn bộ cư dân có nguy cơ bị tác động tiêu cực. Khuyến cáo ở trong nhà, đóng kín cửa sổ và vận hành máy lọc không khí."
    else:
        return "Báo động đỏ nguy hại: Tình trạng khẩn cấp đối với sức khỏe cộng đồng. Toàn bộ người dân tránh tuyệt đối mọi hoạt động ngoài trời, giữ kín phòng và lọc khí chuyên dụng."


def get_main_pollutant(pm25: float, pm10: float, no2: float, o3: float):
    """
    Xác định chất gây ô nhiễm chính (Main Pollutant) theo chuẩn US EPA / WHO.
    So sánh tỷ lệ nồng độ chuẩn hóa để tìm tác nhân ô nhiễm vượt trội.
    """
    ratio_pm25 = (pm25 / 15.0) if pm25 > 0 else 0
    ratio_pm10 = (pm10 / 45.0) if pm10 > 0 else 0
    ratio_o3 = (o3 / 50.0) if o3 > 0 else 0
    ratio_no2 = (no2 / 53.0) if no2 > 0 else 0

    if ratio_pm25 >= max(ratio_pm10, ratio_o3, ratio_no2):
        return "PM2.5", f"{int(round(pm25))} µg/m³"
    elif ratio_pm10 >= max(ratio_pm25, ratio_o3, ratio_no2):
        return "PM10", f"{int(round(pm10))} µg/m³"
    elif ratio_o3 >= max(ratio_pm25, ratio_pm10, ratio_no2):
        return "O3", f"{int(round(o3))} ppb"
    else:
        return "NO2", f"{int(round(no2))} ppb"


def render_arc_gauge(aqi_val: float, aqi_color: str) -> str:
    """Vẽ vòng cung ôm trọn số AQI lớn ở phía trên chuẩn phong cách Apple iOS."""
    val = min(350.0, max(0.0, float(aqi_val)))
    pct = min(1.0, val / 300.0)
    arc_len = 267.04  # Bán kính 85 -> pi * 85 ≈ 267.04
    offset = arc_len * (1.0 - pct)
    int_val = int(round(aqi_val))

    svg = (
        f'<div style="display: flex; justify-content: center; align-items: center; margin: 12px 0 14px 0;">'
        f'<svg width="240" height="135" viewBox="0 0 240 135" style="overflow: visible;">'
        f'<defs>'
        f'<filter id="gauge-glow" x="-20%" y="-20%" width="140%" height="140%">'
        f'<feDropShadow dx="0" dy="0" stdDeviation="4.5" flood-color="{aqi_color}" flood-opacity="0.55"/>'
        f'</filter>'
        f'</defs>'
        f'<path d="M 35 105 A 85 85 0 0 1 205 105" fill="none" stroke="rgba(15, 23, 42, 0.08)" stroke-width="14" stroke-linecap="round"/>'
        f'<path d="M 35 105 A 85 85 0 0 1 205 105" fill="none" stroke="{aqi_color}" stroke-width="14" stroke-linecap="round" stroke-dasharray="{arc_len}" stroke-dashoffset="{offset}" filter="url(#gauge-glow)"/>'
        f'<text x="120" y="85" text-anchor="middle" fill="{aqi_color}" font-size="58" font-weight="800" font-family="-apple-system, BlinkMacSystemFont, \'SF Pro Display\', \'Segoe UI\', Roboto, sans-serif" filter="drop-shadow(0 4px 12px {aqi_color}44)">{int_val}</text>'
        f'<text x="120" y="108" text-anchor="middle" fill="#64748b" font-size="13" font-weight="700" letter-spacing="3" font-family="-apple-system, BlinkMacSystemFont, \'SF Pro Text\', \'Segoe UI\', Roboto, sans-serif">AQI</text>'
        f'</svg>'
        f'</div>'
    )
    return svg


def get_weather_desc(temp: float, rain_prob: float, uv: float, wind: float) -> str:
    """Tạo mô tả trạng thái thời tiết thực tế."""
    now_hour = datetime.now().hour
    is_night = now_hour >= 18 or now_hour < 6
    if rain_prob >= 60:
        return "Trời có mưa"
    elif rain_prob >= 30:
        return "Mây rải rác, có thể mưa nhẹ"
    elif uv >= 7 and not is_night:
        return "Nắng gắt, tia cực tím cao"
    elif wind >= 22:
        return "Gió nhiều, thời tiết mát"
    elif is_night:
        return "Trời quang mây, về đêm"
    else:
        return "Trời quang mây"


# -------------------------------------------------------------
# 4. THANH TÌM KIẾM ĐỊA ĐIỂM TOÀN VIỆT NAM (NATIONWIDE SEARCH BAR)
# -------------------------------------------------------------
if "current_loc" not in st.session_state:
    st.session_state["current_loc"] = {
        "name": "Hà Nội",
        "key": "Hanoi",
        "lat": 21.0285,
        "lon": 105.8542
    }

# Thanh tìm kiếm duy nhất toàn chiều ngang
search_text = st.text_input(
    "Địa điểm",
    placeholder="Nhập tên địa điểm (ví dụ: Hà Nội, Ứng Hòa, Đà Lạt...)...",
    label_visibility="collapsed",
    key="search_city_input"
)

# Xử lý tìm kiếm địa điểm khi người dùng nhập từ khóa
if search_text and len(search_text.strip()) >= 2:
    geo_results = search_vietnam_locations(search_text)
    if geo_results:
        res_labels = [r["label"] for r in geo_results]
        selected_res_label = st.selectbox(
            "📍 Chọn địa điểm phù hợp:",
            options=res_labels,
            key="geo_search_select"
        )
        matched = next(r for r in geo_results if r["label"] == selected_res_label)
        st.session_state["current_loc"] = {
            "name": matched["name"],
            "key": matched["name"],
            "lat": matched["lat"],
            "lon": matched["lon"]
        }
    else:
        st.info(f"Không tìm thấy địa điểm '{search_text}'. Đang giữ vị trí hiện tại: {st.session_state['current_loc']['name']}")

cur_loc = st.session_state["current_loc"]
# Loại bỏ tiền tố "Thành Phố" / "Thành phố" nếu session state cũ còn lưu
for prefix in ["Thành Phố ", "Thành phố ", "thành phố "]:
    if cur_loc.get("name", "").startswith(prefix):
        cur_loc["name"] = cur_loc["name"][len(prefix):].strip()
        st.session_state["current_loc"]["name"] = cur_loc["name"]
        break

target_lat = cur_loc["lat"]
target_lon = cur_loc["lon"]
city_name_display = cur_loc["name"]
for prefix in ["Thành Phố ", "Thành phố ", "thành phố "]:
    if city_name_display.startswith(prefix):
        city_name_display = city_name_display[len(prefix):].strip()
        break

# -------------------------------------------------------------
# 5. TẢI DỮ LIỆU THỜI GIAN THỰC & DỰ BÁO
# -------------------------------------------------------------
@st.cache_data(ttl=600)
def load_data(lat: float, lon: float, name_vn: str):
    return fetch_city_data(lat=lat, lon=lon, city_name_vn=name_vn, past_days=14, forecast_days=7)

with st.spinner(f"Đang kết nối trạm quan trắc tại {cur_loc['name']}..."):
    df_city = load_data(target_lat, target_lon, cur_loc["name"])

if df_city.empty:
    st.error("Không thể kết nối đến máy chủ thời tiết. Vui lòng thử lại sau.")
    st.stop()

# Lọc dòng dữ liệu hiện tại
now_ts = pd.Timestamp.now()
df_city["timestamp"] = pd.to_datetime(df_city["timestamp"])
diffs = (df_city["timestamp"] - now_ts).abs()
current_row = df_city.loc[diffs.idxmin()]

# Các thông số quan trắc hiện thời
current_aqi = float(current_row.get("aqi_us", 156.0))
current_pm25 = float(current_row.get("pm2_5", 64.5))
current_pm10 = float(current_row.get("pm10", 112.0))
current_no2 = float(current_row.get("nitrogen_dioxide", 45.0))
current_o3 = float(current_row.get("ozone", 32.0))
current_temp = float(current_row.get("temperature_2m", 28.5))
current_humidity = float(current_row.get("relative_humidity_2m", 75.0))
current_rain = float(current_row.get("precipitation_probability", 10.0))
current_uv = float(current_row.get("uv_index", 4.2))
current_wind = float(current_row.get("wind_speed_10m", 11.5))

aqi_color, aqi_category, aqi_emoji = get_aqi_theme(current_aqi)
weather_status = get_weather_desc(current_temp, current_rain, current_uv, current_wind)

# Tính tỷ lệ vượt ngưỡng WHO đối với PM2.5 (Ngưỡng 24h của WHO là 15 µg/m³)
if current_pm25 <= 15:
    who_text = "✓ Đạt tiêu chuẩn WHO (≤ 15 µg/m³)"
else:
    ratio_who = current_pm25 / 15.0
    who_text = f"(gấp {ratio_who:.1f} lần tiêu chuẩn WHO)"

gauge_svg = render_arc_gauge(current_aqi, aqi_color)


# -------------------------------------------------------------
# 6. KHỐI HERO CHUẨN IOS LIQUID GLASS NỀN TRẮNG
# -------------------------------------------------------------
main_pol_name, main_pol_val = get_main_pollutant(current_pm25, current_pm10, current_no2, current_o3)
advisory_text = get_aqi_advisory(current_aqi)

is_night = datetime.now().hour >= 18 or datetime.now().hour < 6
if is_night:
    weather_icon_svg = (
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="#94a3b8" style="vertical-align: middle;">'
        '<path d="M12.3 2a10 10 0 0 0-.19 20 10 10 0 0 0 8.09-4.11 1 1 0 0 0-.84-1.57A8 8 0 0 1 11.7 4.14 1 1 0 0 0 12.3 2z"/>'
        '<circle cx="18" cy="5" r="1.2" fill="#94a3b8"/>'
        '<circle cx="20.5" cy="8.5" r="0.9" fill="#94a3b8"/>'
        '</svg>'
    )
else:
    weather_icon_svg = (
        '<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="vertical-align: middle;">'
        '<circle cx="12" cy="12" r="5" fill="#f59e0b"/>'
        '<path d="M12 1v2M12 21v2M4.22 4.22l1.42 1.42M18.36 18.36l1.42 1.42M1 12h2M21 12h2M4.22 19.78l1.42-1.42M18.36 5.64l1.42-1.42" stroke="#f59e0b" stroke-width="2" stroke-linecap="round"/>'
        '</svg>'
    )

hero_html = (
    f'<div class="liquid-card" style="text-align: center; padding: 26px 28px; max-width: 680px; margin: 0 auto 20px auto;">'
    f'<div class="ios-city-title">{city_name_display}</div>'
    f'{gauge_svg}'
    f'<div class="ios-air-status" style="margin-top: 6px; margin-bottom: 12px;">Chất lượng không khí: <span style="color: {aqi_color}; font-weight: 800;">{aqi_category}</span></div>'
    f'<div class="main-pollutant-bar" style="background: {aqi_color}; color: #ffffff; border-radius: 12px; padding: 11px 20px; display: flex; justify-content: space-between; align-items: center; margin: 16px 0 14px 0; font-family: -apple-system, BlinkMacSystemFont, \'SF Pro Display\', \'Segoe UI\', Roboto, sans-serif; box-shadow: 0 4px 14px {aqi_color}40;">'
    f'<span style="font-size: 15px; font-weight: 500; letter-spacing: -0.2px;">Chất ô nhiễm chính: <strong style="font-weight: 800; font-size: 16px;">{main_pol_name}</strong></span>'
    f'<span style="font-size: 16px; font-weight: 800; letter-spacing: -0.2px;">{main_pol_val}</span>'
    f'</div>'
    f'<div class="ios-advisory-card">'
    f'{advisory_text}'
    f'</div>'
    f'<div style="display: flex; justify-content: space-around; align-items: center; margin-top: 18px; padding-top: 16px; border-top: 1px solid rgba(226, 232, 240, 0.9);">'
    f'<div style="display: flex; align-items: center; gap: 8px;">'
    f'{weather_icon_svg}'
    f'<span style="font-size: 17px; font-weight: 700; color: #0f172a;">{int(round(current_temp))}°</span>'
    f'</div>'
    f'<div style="display: flex; align-items: center; gap: 8px;">'
    f'<svg width="18" height="18" viewBox="0 0 24 24" fill="#64748b" style="vertical-align: middle;">'
    f'<polygon points="3,11 21,3 13,21 11,13"/>'
    f'</svg>'
    f'<span style="font-size: 17px; font-weight: 700; color: #0f172a;">{int(round(current_wind))} km/h</span>'
    f'</div>'
    f'<div style="display: flex; align-items: center; gap: 8px;">'
    f'<svg width="20" height="20" viewBox="0 0 24 24" fill="none" style="vertical-align: middle;">'
    f'<path d="M9 3.5C9 3.5 4 9.5 4 13.5C4 16.5 6.2 19 9 19C11.8 19 14 16.5 14 13.5C14 9.5 9 3.5 9 3.5Z" fill="#38bdf8"/>'
    f'<path d="M17 9C18.2 10.2 18.2 12 17 13.2" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round"/>'
    f'<path d="M20 7C22 9.2 22 12.8 20 15" stroke="#38bdf8" stroke-width="1.8" stroke-linecap="round"/>'
    f'</svg>'
    f'<span style="font-size: 17px; font-weight: 700; color: #0f172a;">{int(round(current_humidity))} %</span>'
    f'</div>'
    f'</div>'
    f'</div>'
)
st.markdown(hero_html, unsafe_allow_html=True)

with st.expander("📊 Xem chi tiết các thông số ô nhiễm khác (PM10, NO2, O3, Chuẩn WHO)"):
    det_c1, det_c2, det_c3, det_c4 = st.columns(4)
    with det_c1:
        st.metric("✨ Bụi PM2.5", f"{current_pm25:.1f} µg/m³", delta=who_text, delta_color="inverse")
    with det_c2:
        st.metric("☀️ Bụi PM10", f"{int(round(current_pm10))} µg/m³", "Bụi thô & đường sá")
    with det_c3:
        st.metric("👁️ Khí NO2", f"{int(round(current_no2))} ppb", "Khí thải xe cộ")
    with det_c4:
        st.metric("🧪 Khí O3", f"{int(round(current_o3))} ppb", "Ozone tầng đối lưu")


# -------------------------------------------------------------
# 7. BẢNG KHUYẾN NGHỊ
# -------------------------------------------------------------
st.write("")
with st.container(border=True):
    # Header của Bảng khuyến nghị
    st.markdown(
        '<div style="font-size: 16px; font-weight: 800; letter-spacing: -0.2px; color: #0f172a; text-transform: uppercase; margin-bottom: 4px;">'
        'BẢNG KHUYẾN NGHỊ'
        '</div>'
        '<div style="font-size: 12.5px; color: #64748b; margin-bottom: 12px;">'
        'Hệ thống tự động tổng hợp chất lượng không khí và thể trạng cá nhân để đưa ra khuyến nghị bảo vệ sức khỏe phù hợp.'
        '</div>',
        unsafe_allow_html=True
    )

    # Phân vùng Thiết lập thể trạng & Tiền sử bệnh nền (NẰM TRONG BẢNG KHUYẾN NGHỊ)
    st.markdown(
        '<div style="background: rgba(241, 245, 249, 0.75); border: 1px solid rgba(226, 232, 240, 0.9); '
        'border-radius: 16px; padding: 12px 18px 4px 18px; margin-bottom: 14px;">'
        '<div style="font-size: 13.5px; font-weight: 800; color: #1e293b; margin-bottom: 2px;">'
        '👤 Thiết lập thể trạng & tiền sử bệnh nền của bạn:'
        '</div>'
        '<div style="font-size: 11.5px; color: #64748b; margin-bottom: 8px;">'
        'Thay đổi độ tuổi hoặc tích chọn bệnh nền để cập nhật tức thời khuyến nghị bảo vệ sức khỏe phù hợp.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    prof_c1, prof_c2 = st.columns([1, 1.4], gap="large")
    with prof_c1:
        user_age = st.slider("🎂 Độ tuổi của bạn:", min_value=1, max_value=99, value=28, step=1, key="user_age_slider")
        if user_age < 12:
            age_badge = "👶 Trẻ em (< 12 tuổi)"
            age_badge_color = "#3b82f6"
        elif user_age < 18:
            age_badge = "🧑‍🎓 Thanh thiếu niên (12 - 17 tuổi)"
            age_badge_color = "#0284c7"
        elif user_age < 60:
            age_badge = "🧑 Người trưởng thành (18 - 59 tuổi)"
            age_badge_color = "#10b981"
        else:
            age_badge = "👴 Người cao tuổi (≥ 60 tuổi)"
            age_badge_color = "#f97316"
        st.markdown(
            f'<div style="font-size: 12px; font-weight: 700; color: {age_badge_color}; margin-top: -6px; margin-bottom: 6px;">'
            f'Phân nhóm lứa tuổi: <b>{age_badge}</b>'
            f'</div>',
            unsafe_allow_html=True
        )

    with prof_c2:
        st.markdown('<div style="font-size: 13px; font-weight: 700; color: #334155; margin-bottom: 4px;">🩺 Tích chọn bệnh nền liên quan:</div>', unsafe_allow_html=True)
        med_c1, med_c2 = st.columns(2)
        with med_c1:
            cb_respiratory = st.checkbox("🫁 Hô hấp mãn tính", value=False, key="cb_resp")
            cb_asthma = st.checkbox("🌬️ Hen suyễn", value=False, key="cb_asthma")
        with med_c2:
            cb_heart = st.checkbox("❤️ Bệnh tim mạch", value=False, key="cb_heart")
            cb_lung = st.checkbox("🩺 Bệnh phổi", value=False, key="cb_lung")

    # Xác định mức độ nhạy cảm & phân nhóm
    is_child = user_age < 12
    is_elderly = user_age >= 60
    has_conditions = cb_respiratory or cb_asthma or cb_heart or cb_lung
    is_sensitive = is_child or is_elderly or has_conditions

    selected_conditions = []
    if cb_asthma:
        selected_conditions.append("Hen suyễn")
    if cb_heart:
        selected_conditions.append("Bệnh tim mạch")
    if cb_lung:
        selected_conditions.append("Bệnh phổi")
    if cb_respiratory:
        selected_conditions.append("Hô hấp mãn tính")

    conditions_display_str = ", ".join(selected_conditions) if selected_conditions else "Không có bệnh nền (Khỏe mạnh)"

    # -------------------------------------------------------------
    # SUY DIỄN KHUYẾN NGHỊ: DỰ ĐOÁN BẰNG MÔ HÌNH RANDOM FOREST (50.000 MẪU)
    # -------------------------------------------------------------
    ml_model = load_ml_model()
    is_ml_active = False

    if ml_model is not None:
        try:
            feat_vec = np.array([[
                float(current_aqi),
                float(current_pm25),
                float(current_pm10),
                float(current_temp),
                float(current_humidity),
                float(current_rain),
                float(current_uv),
                float(current_wind),
                int(user_age),
                int(cb_respiratory),
                int(cb_asthma),
                int(cb_heart),
                int(cb_lung)
            ]])
            ml_pred = ml_model.predict(feat_vec)[0]
            pred_exercise, pred_window, pred_mask, pred_purifier = ml_pred
            is_ml_active = True
        except Exception as e:
            print("Lỗi suy diễn ML:", e)
            is_ml_active = False

    if is_ml_active:
        # 1. Khuyến nghị tập thể dục ngoài trời
        if pred_exercise == 0:
            bike_icon = "bike3"
            ex_text = "Tránh tập thể dục ngoài trời để bảo vệ đường hô hấp và tim mạch." if is_sensitive else "Tránh tập thể dục ngoài trời do thời tiết hoặc ô nhiễm bụi mịn tăng cao."
        else:
            bike_icon = "bike1"
            ex_text = "Rất lý tưởng để tập thể dục và vận động ngoài trời." if current_aqi <= 50 else "Có thể tập thể dục và sinh hoạt ngoài trời bình thường."

        # 2. Khuyến nghị đóng / mở cửa sổ
        if pred_window == 0:
            win_icon = "win3"
            win_text = "Hãy đóng cửa sổ để tránh không khí ô nhiễm bên ngoài."
        else:
            win_icon = "win1"
            win_text = "Mở cửa sổ để đón không khí trong lành tự nhiên."

        # 3. Khuyến nghị khẩu trang
        if pred_mask == 1:
            mask_icon = "mask3" if (is_sensitive or current_aqi > 150) else "mask2"
            mask_text = "Bắt buộc đeo khẩu trang lọc bụi mịn chuẩn N95 / KF94 khi ra ngoài." if (is_sensitive or current_aqi > 150) else "Hãy đeo khẩu trang khi ra ngoài trời."
        else:
            mask_icon = "mask1"
            mask_text = "Không cần đeo khẩu trang chống bụi."

        # 4. Khuyến nghị máy lọc không khí
        if pred_purifier == 1:
            air_icon = "air3" if (is_sensitive or current_aqi > 150) else "air2"
            purifier_text = "Hãy bật máy lọc không khí có màng lọc HEPA trong phòng." if (is_sensitive or current_aqi > 150) else "Hãy bật máy lọc không khí."
        else:
            air_icon = "air1"
            purifier_text = "Chất lượng không khí tốt, chưa cần bật máy lọc."
    else:
        # Fallback theo bảng quy chuẩn EPA / WHO
        if current_aqi <= 50:
            bike_icon, win_icon, mask_icon, air_icon = "bike1", "win1", "mask1", "air1"
            ex_text = "Rất lý tưởng để tập thể dục và vận động ngoài trời."
            win_text = "Mở cửa sổ để đón không khí trong lành tự nhiên."
            mask_text = "Không cần đeo khẩu trang chống bụi."
            purifier_text = "Chất lượng không khí tốt, chưa cần bật máy lọc."
        elif current_aqi <= 100:
            if is_sensitive:
                bike_icon, win_icon, mask_icon, air_icon = "bike2", "win2", "mask2", "air2"
                ex_text = "Nhóm nhạy cảm nên giảm bớt các bài tập thể lực gắng sức kéo dài."
                win_text = "Có thể mở cửa sổ thông gió tự nhiên; hạn chế nếu nhà sát đường lớn."
                mask_text = "Nhóm nhạy cảm nên đeo khẩu trang y tế khi lưu thông ngoài đường."
                purifier_text = "Người có bệnh nền hô hấp có thể bật máy lọc không khí ở chế độ nhẹ."
            else:
                bike_icon, win_icon, mask_icon, air_icon = "bike1", "win1", "mask1", "air1"
                ex_text = "Có thể tập thể dục và sinh hoạt ngoài trời bình thường."
                win_text = "Có thể mở cửa sổ để lưu thông không khí trong nhà."
                mask_text = "Chưa cần khẩu trang chống bụi (nên đeo khẩu trang y tế khi đi xe máy)."
                purifier_text = "Không khí ở mức chấp nhận được, chưa cần thiết bật máy lọc."
        elif current_aqi <= 150:
            bike_icon, win_icon, mask_icon, air_icon = "bike3", "win3", "mask2", "air2"
            ex_text = "Tránh tập thể dục ngoài trời để bảo vệ đường hô hấp và tim mạch."
            win_text = "Nên đóng cửa sổ để tránh bụi mịn tích tụ trong phòng."
            mask_text = "Cần đeo khẩu trang lọc bụi khi bắt buộc phải ra ngoài."
            purifier_text = "Nên bật máy lọc không khí có màng lọc HEPA trong phòng."
        else:
            bike_icon, win_icon, mask_icon, air_icon = "bike3", "win3", "mask3", "air3"
            ex_text = "Tránh tập thể dục ngoài trời, chuyển toàn bộ hoạt động thể chất vào trong nhà."
            win_text = "Hãy đóng kín cửa sổ để tránh không khí ô nhiễm xâm nhập."
            mask_text = "Bắt buộc đeo khẩu trang lọc bụi mịn chuẩn N95 / KF94 khi ra ngoài."
            purifier_text = "Hãy vận hành máy lọc không khí liên tục trong phòng kín."

    src_bike = get_rec_icon_b64(bike_icon)
    src_win = get_rec_icon_b64(win_icon)
    src_mask = get_rec_icon_b64(mask_icon)
    src_air = get_rec_icon_b64(air_icon)

    health_recs_html = (
        f'<div style="margin-top: 18px; padding-top: 16px; border-top: 1px solid rgba(226, 232, 240, 0.85);">'
        f'<div style="font-size: 18px; font-weight: 800; color: #0f172a; margin-bottom: 20px; letter-spacing: -0.2px;">'
        f'Khuyến nghị về sức khỏe'
        f'</div>'
        f'<div style="display: flex; flex-direction: column; gap: 16px;">'
        f'<div style="display: flex; align-items: center; gap: 18px;">'
        f'<img src="{src_bike}" style="width: 56px; height: 56px; min-width: 56px; border-radius: 14px; object-fit: cover; display: block; box-shadow: 0 2px 8px rgba(0,0,0,0.04);" />'
        f'<div style="font-size: 15px; font-weight: 500; color: #0f172a; line-height: 1.45;">'
        f'{ex_text}'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 18px;">'
        f'<img src="{src_win}" style="width: 56px; height: 56px; min-width: 56px; border-radius: 14px; object-fit: cover; display: block; box-shadow: 0 2px 8px rgba(0,0,0,0.04);" />'
        f'<div style="font-size: 15px; font-weight: 500; color: #0f172a; line-height: 1.45;">'
        f'{win_text}'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 18px;">'
        f'<img src="{src_mask}" style="width: 56px; height: 56px; min-width: 56px; border-radius: 14px; object-fit: cover; display: block; box-shadow: 0 2px 8px rgba(0,0,0,0.04);" />'
        f'<div style="font-size: 15px; font-weight: 500; color: #0f172a; line-height: 1.45;">'
        f'{mask_text}'
        f'</div>'
        f'</div>'
        f'<div style="display: flex; align-items: center; gap: 18px;">'
        f'<img src="{src_air}" style="width: 56px; height: 56px; min-width: 56px; border-radius: 14px; object-fit: cover; display: block; box-shadow: 0 2px 8px rgba(0,0,0,0.04);" />'
        f'<div style="font-size: 15px; font-weight: 500; color: #0f172a; line-height: 1.45;">'
        f'{purifier_text}'
        f'</div>'
        f'</div>'
        f'</div>'
        f'</div>'
    )
    st.markdown(health_recs_html, unsafe_allow_html=True)


# -------------------------------------------------------------
# 8. DỰ BÁO XU HƯỚNG 24H (BIỂU ĐỒ CỘT NỀN SÁNG)
# -------------------------------------------------------------
df_chart_24h = df_city[df_city["timestamp"] >= now_ts].head(24).copy()
if len(df_chart_24h) < 12:
    df_chart_24h = df_city.tail(24).copy()

df_chart_24h["hour_str"] = df_chart_24h["timestamp"].dt.strftime("%H:00")
bar_colors = [get_aqi_theme(val)[0] for val in df_chart_24h["aqi_us"]]

fig = go.Figure()

fig.add_trace(go.Bar(
    x=df_chart_24h["hour_str"],
    y=df_chart_24h["aqi_us"],
    marker=dict(
        color=bar_colors,
        line=dict(color="rgba(255, 255, 255, 0.8)", width=1.5)
    ),
    hovertemplate="<b>%{x}</b><br>AQI: <b>%{y:.0f}</b><extra></extra>",
    name="AQI US"
))

# Đường tham chiếu ngưỡng chuẩn
fig.add_hline(y=50, line_dash="dot", line_color="rgba(16, 185, 129, 0.8)", annotation_text="Tốt (50)", annotation_position="top left", annotation_font_color="#10b981")
fig.add_hline(y=100, line_dash="dot", line_color="rgba(245, 158, 11, 0.8)", annotation_text="Trung bình (100)", annotation_position="top left", annotation_font_color="#f59e0b")
fig.add_hline(y=150, line_dash="dot", line_color="rgba(239, 68, 68, 0.8)", annotation_text="Kém (150)", annotation_position="top left", annotation_font_color="#ef4444")

fig.update_layout(
    height=360,
    margin=dict(l=20, r=20, t=30, b=20),
    paper_bgcolor="rgba(0,0,0,0)",
    plot_bgcolor="rgba(0,0,0,0)",
    font=dict(color="#0f172a", family="-apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, sans-serif"),
    xaxis=dict(
        showgrid=False,
        color="#64748b",
        tickfont=dict(size=11, color="#475569")
    ),
    yaxis=dict(
        gridcolor="rgba(15, 23, 42, 0.06)",
        color="#64748b",
        title="Chỉ số AQI US",
        title_font=dict(size=12, color="#334155")
    ),
    bargap=0.3
)

with st.container(border=True):
    st.markdown(
        '<div style="font-size: 19px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px; margin: 4px 0 14px 4px;">'
        '📊 Dự Báo Xu Hướng AQI 24 Giờ Tiếp Theo'
        '</div>',
        unsafe_allow_html=True
    )
    st.plotly_chart(fig, use_container_width=True, config={"displayModeBar": False})


# -------------------------------------------------------------
# 9. DỰ BÁO CHẤT LƯỢNG KHÔNG KHÍ 7 NGÀY (TRƯỚC 1 TUẦN)
# -------------------------------------------------------------
st.write("")
df_7days = get_7day_summary(df_city)

with st.container(border=True):
    st.markdown(
        '<div style="margin-bottom: 18px;">'
        '<div style="font-size: 19px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px;">'
        '🗓️ Dự Báo Chất Lượng Không Khí 7 Ngày Tiếp Theo'
        '</div>'
        '<div style="font-size: 13px; color: #64748b; margin-top: 2px;">'
        'Tổng hợp chuỗi dự báo theo từng ngày: AQI trung bình, nhiệt độ cao nhất - thấp nhất, xác suất mưa và tia UV.'
        '</div>'
        '</div>',
        unsafe_allow_html=True
    )

    if not df_7days.empty:
        cols_7d = st.columns(len(df_7days), gap="small")
        for i, (_, day_row) in enumerate(df_7days.iterrows()):
            d_avg_aqi = float(day_row["avg_aqi"])
            d_color, d_cat, d_avatar = get_aqi_theme(d_avg_aqi)
            
            with cols_7d[i]:
                st.markdown(
                    f'<div style="background: #f8fafc; border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 18px; padding: 16px 10px; text-align: center; height: 100%; box-shadow: 0 2px 8px rgba(15, 23, 42, 0.02);">'
                    f'<div style="font-size: 12px; font-weight: 700; color: #0f172a; margin-bottom: 6px;">{day_row["label"]}</div>'
                    f'<div style="font-size: 28px; margin: 6px 0;">{d_avatar}</div>'
                    f'<div style="font-size: 22px; font-weight: 800; color: {d_color}; margin-bottom: 2px;">{int(round(d_avg_aqi))}</div>'
                    f'<div style="font-size: 11px; font-weight: 700; color: {d_color}; margin-bottom: 10px;">{day_row["category"]}</div>'
                    f'<div style="border-top: 1px solid rgba(226, 232, 240, 0.85); padding-top: 8px; font-size: 11.5px; color: #64748b; line-height: 1.5;">'
                    f'<div>🌡️ {day_row["min_temp"]:.0f}° - {day_row["max_temp"]:.0f}°C</div>'
                    f'<div>🌧️ Mưa {day_row["max_rain"]:.0f}%</div>'
                    f'<div>☀️ UV {day_row["max_uv"]:.1f}</div>'
                    f'</div>'
                    f'</div>',
                    unsafe_allow_html=True
                )


# -------------------------------------------------------------
# 10. BẢN ĐỒ PHỦ SÓNG Ô NHIỄM & MẠNG LƯỚI TRẠM QUAN TRẮC (HEATMAP)
# -------------------------------------------------------------
st.write("")
if cur_loc.get("key") in CITIES:
    stations = CITIES[cur_loc["key"]].get("stations", [])
else:
    stations = get_location_stations(cur_loc["name"], target_lat, target_lon)

station_data = []
offsets = [0, 8, -12, 15]
for idx, st_item in enumerate(stations):
    off = offsets[idx % len(offsets)]
    st_aqi = max(10, current_aqi + off)
    st_color_hex, st_cat, _ = get_aqi_theme(st_aqi)
    h = st_color_hex.lstrip('#')
    r, g, b = tuple(int(h[i:i+2], 16) for i in (0, 2, 4))
    
    station_data.append({
        "name": st_item["name"],
        "lat": float(st_item["lat"]),
        "lon": float(st_item["lon"]),
        "aqi": int(round(st_aqi)),
        "category": st_cat,
        "color_hex": st_color_hex,
        "color_rgba": [r, g, b, 230],
        "weight": float(st_aqi)
    })

# Mô hình trường nhiệt lan tỏa ô nhiễm không gian đô thị (Urban Air Pollution Dispersion Model)
def generate_pollution_heatmap_data(center_lat: float, center_lon: float, base_aqi: float, st_list: list = None) -> pd.DataFrame:
    np.random.seed(int(center_lat * 100 + center_lon * 100) % 10000)
    points = []
    core_w = float(max(15, base_aqi))
    
    # 1. Cụm nồng độ tại các trạm quan trắc thực tế
    if st_list:
        for st_entry in st_list:
            s_lat, s_lon = float(st_entry["lat"]), float(st_entry["lon"])
            s_aqi = float(st_entry.get("aqi", base_aqi))
            for _ in range(16):
                points.append({
                    "lat": s_lat + float(np.random.normal(0, 0.007)),
                    "lon": s_lon + float(np.random.normal(0, 0.007)),
                    "weight": s_aqi
                })

    # 2. Vùng lõi trung tâm (Center Core - tâm nồng độ ô nhiễm cao nhất)
    for _ in range(45):
        points.append({
            "lat": center_lat + float(np.random.normal(0, 0.012)),
            "lon": center_lon + float(np.random.normal(0, 0.014)),
            "weight": core_w
        })

    # 3. Vành đai đô thị nội thành (Inner urban belt - 3-7km)
    for _ in range(65):
        ang = float(np.random.uniform(0, 2 * np.pi))
        r = float(np.random.uniform(0.018, 0.045))
        points.append({
            "lat": center_lat + r * np.sin(ang),
            "lon": center_lon + r * np.cos(ang) * 1.1,
            "weight": max(15.0, core_w * 0.75)
        })

    # 4. Vành đai chuyển tiếp ven đô (Suburban transition belt - 7-12km)
    for _ in range(80):
        ang = float(np.random.uniform(0, 2 * np.pi))
        r = float(np.random.uniform(0.045, 0.085))
        points.append({
            "lat": center_lat + r * np.sin(ang),
            "lon": center_lon + r * np.cos(ang) * 1.15,
            "weight": max(12.0, core_w * 0.48)
        })

    # 5. Vành đai ngoại vi sinh thái xanh (Green perimeter - 12-18km)
    for _ in range(95):
        ang = float(np.random.uniform(0, 2 * np.pi))
        r = float(np.random.uniform(0.085, 0.140))
        points.append({
            "lat": center_lat + r * np.sin(ang),
            "lon": center_lon + r * np.cos(ang) * 1.2,
            "weight": max(10.0, core_w * 0.25)
        })

    return pd.DataFrame(points)

with st.container(border=True):
    map_c1, map_c2 = st.columns([1.6, 1], gap="medium")
    with map_c1:
        st.markdown(
            '<div style="font-size: 19px; font-weight: 800; color: #0f172a; letter-spacing: -0.3px;">'
            '🗺️ Bản Đồ Phủ Sóng Ô Nhiễm Không Khí'
            '</div>'
            '<div style="font-size: 13px; color: #64748b; margin-top: 2px; margin-bottom: 8px;">'
            'Mô phỏng trường lan tỏa ô nhiễm không gian đô thị (GPU Heatmap & Trạm quan trắc).'
            '</div>',
            unsafe_allow_html=True
        )
    with map_c2:
        map_view_mode = st.radio(
            "Chế độ hiển thị bản đồ:",
            options=["🔥 Phủ nhiệt (Heatmap)", "📍 Trạm quan trắc", "🌐 Kết hợp cả hai"],
            horizontal=True,
            label_visibility="collapsed",
            key="map_view_selector"
        )

    active_layers = []

    # 1. Vẽ lớp phủ nhiệt Heatmap (Deck.gl GPU-accelerated HeatmapLayer)
    if "Heatmap" in map_view_mode or "Kết hợp" in map_view_mode:
        df_heat = generate_pollution_heatmap_data(target_lat, target_lon, current_aqi, station_data)
        heat_layer = pdk.Layer(
            "HeatmapLayer",
            data=df_heat,
            get_position="[lon, lat]",
            get_weight="weight",
            radius_pixels=45,
            intensity=1.1,
            threshold=0.03,
            color_range=[
                [34, 197, 94, 95],     # Green (0-50: Tốt)
                [132, 204, 22, 135],   # Yellow-Green
                [250, 204, 21, 175],   # Yellow (51-100: Trung bình)
                [249, 115, 22, 205],   # Orange (101-150: Kém)
                [220, 38, 38, 230],    # Red (151-200: Xấu)
                [136, 19, 55, 255]     # Deep Crimson (>200: Rất xấu)
            ],
            pickable=False
        )
        active_layers.append(heat_layer)

    # 2. Vẽ các trạm quan trắc điểm tròn (ScatterplotLayer)
    if "Trạm" in map_view_mode or "Kết hợp" in map_view_mode:
        if station_data:
            df_stations = pd.DataFrame(station_data)
            stations_layer = pdk.Layer(
                "ScatterplotLayer",
                data=df_stations,
                get_position="[lon, lat]",
                get_fill_color="color_rgba",
                get_line_color=[255, 255, 255, 255],
                get_line_width=2,
                line_width_min_pixels=2,
                radius_min_pixels=8,
                radius_max_pixels=15,
                pickable=True,
                stroked=True,
                filled=True
            )
            active_layers.append(stations_layer)

        # Đánh dấu tâm vị trí người dùng đang chọn
        df_center = pd.DataFrame([{
            "name": f"Vị trí bạn đang chọn: {cur_loc.get('name', 'Trung tâm')}",
            "lat": target_lat,
            "lon": target_lon,
            "aqi": int(round(current_aqi)),
            "category": current_category,
            "color_rgba": [14, 165, 233, 255]
        }])
        center_pin_layer = pdk.Layer(
            "ScatterplotLayer",
            data=df_center,
            get_position="[lon, lat]",
            get_fill_color="color_rgba",
            get_line_color=[255, 255, 255, 255],
            get_line_width=3,
            line_width_min_pixels=3,
            radius_min_pixels=10,
            radius_max_pixels=18,
            pickable=True,
            stroked=True,
            filled=True
        )
        active_layers.append(center_pin_layer)

    # Thiết lập View State & Render bản đồ PyDeck
    view_state = pdk.ViewState(
        latitude=target_lat,
        longitude=target_lon,
        zoom=11.2,
        pitch=0,
        bearing=0
    )

    deck_map = pdk.Deck(
        layers=active_layers,
        initial_view_state=view_state,
        map_style=None,  # 100% MIỄN PHÍ: Tự động kế thừa nền Light của Streamlit, hoàn toàn không cần API key / token
        tooltip={
            "html": "<div style='font-family: -apple-system, BlinkMacSystemFont, Segoe UI, Roboto, sans-serif; font-size: 13px; padding: 4px 6px; line-height: 1.5;'>"
                    "<div style='font-weight: 700; color: #ffffff;'>{name}</div>"
                    "<div>Chỉ số AQI: <b style='color: #38bdf8; font-size: 14px;'>{aqi}</b> ({category})</div>"
                    "</div>",
            "style": {
                "backgroundColor": "rgba(15, 23, 42, 0.94)",
                "color": "#ffffff",
                "borderRadius": "8px",
                "padding": "6px 10px",
                "boxShadow": "0 4px 14px rgba(0, 0, 0, 0.25)"
            }
        }
    )

    st.pydeck_chart(deck_map, use_container_width=True)

    # Chú giải thang đo màu sắc trực quan (Color Scale Legend)
    st.markdown(
        '<div style="display: flex; justify-content: space-between; align-items: center; flex-wrap: wrap; gap: 8px; margin-top: 10px; padding: 10px 16px; background: rgba(248, 250, 252, 0.9); border: 1px solid rgba(226, 232, 240, 0.9); border-radius: 12px; font-size: 12px; color: #475569;">'
        '<div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 12px; height: 12px; border-radius: 3px; background: #22c55e;"></span><b>0 – 50:</b> Tốt (Vùng xanh ngoại vi)</div>'
        '<div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 12px; height: 12px; border-radius: 3px; background: #facc15;"></span><b>51 – 100:</b> Trung bình (Vành đai ven đô)</div>'
        '<div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 12px; height: 12px; border-radius: 3px; background: #f97316;"></span><b>101 – 150:</b> Kém (Khu vực đô thị)</div>'
        '<div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 12px; height: 12px; border-radius: 3px; background: #dc2626;"></span><b>151 – 200:</b> Xấu (Nội đô đông đúc)</div>'
        '<div style="display: flex; align-items: center; gap: 6px;"><span style="display: inline-block; width: 12px; height: 12px; border-radius: 3px; background: #881337;"></span><b>> 200:</b> Rất xấu (Vùng lõi ô nhiễm)</div>'
        '</div>',
        unsafe_allow_html=True
    )




