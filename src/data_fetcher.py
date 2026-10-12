"""
data_fetcher.py
Module thu thập và tiền xử lý dữ liệu chất lượng không khí và thời tiết
từ Open-Meteo Air Quality API và Weather Forecast API.
"""

import os
from datetime import datetime
import pandas as pd
import requests

# Tọa độ các thành phố trọng điểm có trạm chi tiết
CITIES = {
    "Hanoi": {
        "name_vn": "Hà Nội",
        "lat": 21.0285,
        "lon": 105.8542,
        "stations": [
            {"name": "Trạm Hoàn Kiếm (Trung tâm)", "lat": 21.0300, "lon": 105.8520},
            {"name": "Trạm Cầu Giấy (Khu dân cư - Học đường)", "lat": 21.0360, "lon": 105.7900},
            {"name": "Trạm Long Biên (Công nghiệp ven đô)", "lat": 21.0450, "lon": 105.8900},
            {"name": "Trạm Hà Đông (Đô thị mới)", "lat": 20.9700, "lon": 105.7700}
        ]
    },
    "Ho Chi Minh City": {
        "name_vn": "TP. Hồ Chí Minh",
        "lat": 10.8231,
        "lon": 106.6297,
        "stations": [
            {"name": "Trạm Quận 1 (Trung tâm Bến Nghé)", "lat": 10.7769, "lon": 106.7009},
            {"name": "Trạm TP. Thủ Đức (Khu đô thị sáng tạo)", "lat": 10.8500, "lon": 106.7700},
            {"name": "Trạm Tân Bình (Gần sân bay Tân Sơn Nhất)", "lat": 10.8100, "lon": 106.6600},
            {"name": "Trạm Quận 7 (Khu Nam Sài Gòn)", "lat": 10.7300, "lon": 106.7200}
        ]
    }
}

# Danh mục 63 tỉnh thành & đô thị trọng điểm toàn quốc (Việt Nam)
VIETNAM_LOCATIONS = {
    # 5 Thành phố trực thuộc Trung ương
    "Hà Nội": {"lat": 21.0285, "lon": 105.8542, "region": "Đồng bằng sông Hồng"},
    "TP. Hồ Chí Minh": {"lat": 10.8231, "lon": 106.6297, "region": "Đông Nam Bộ"},
    "Đà Nẵng": {"lat": 16.0544, "lon": 108.2022, "region": "Duyên hải Nam Trung Bộ"},
    "Hải Phòng": {"lat": 20.8449, "lon": 106.6881, "region": "Đồng bằng sông Hồng"},
    "Cần Thơ": {"lat": 10.0452, "lon": 105.7469, "region": "Đồng bằng sông Cửu Long"},

    # Miền Bắc
    "Quảng Ninh (Hạ Long)": {"lat": 20.9500, "lon": 107.0833, "region": "Đông Bắc Bộ"},
    "Lào Cai (Sa Pa)": {"lat": 22.3364, "lon": 103.8438, "region": "Tây Bắc Bộ"},
    "Bắc Ninh": {"lat": 21.1861, "lon": 106.0763, "region": "Đồng bằng sông Hồng"},
    "Hải Dương": {"lat": 20.9373, "lon": 106.3146, "region": "Đồng bằng sông Hồng"},
    "Hưng Yên": {"lat": 20.6464, "lon": 106.0511, "region": "Đồng bằng sông Hồng"},
    "Hà Nam (Phủ Lý)": {"lat": 20.5411, "lon": 105.9139, "region": "Đồng bằng sông Hồng"},
    "Nam Định": {"lat": 20.4344, "lon": 106.1681, "region": "Đồng bằng sông Hồng"},
    "Ninh Bình": {"lat": 20.2506, "lon": 105.9744, "region": "Đồng bằng sông Hồng"},
    "Thái Bình": {"lat": 20.4464, "lon": 106.3364, "region": "Đồng bằng sông Hồng"},
    "Vĩnh Phúc (Vĩnh Yên)": {"lat": 21.3089, "lon": 105.6049, "region": "Đồng bằng sông Hồng"},
    "Phú Thọ (Việt Trì)": {"lat": 21.3228, "lon": 105.4019, "region": "Đông Bắc Bộ"},
    "Thái Nguyên": {"lat": 21.5942, "lon": 105.8481, "region": "Đông Bắc Bộ"},
    "Bắc Giang": {"lat": 21.2731, "lon": 106.1947, "region": "Đông Bắc Bộ"},
    "Lạng Sơn": {"lat": 21.8536, "lon": 106.7617, "region": "Đông Bắc Bộ"},
    "Cao Bằng": {"lat": 22.6667, "lon": 106.2500, "region": "Đông Bắc Bộ"},
    "Bắc Kạn": {"lat": 22.1472, "lon": 105.8347, "region": "Đông Bắc Bộ"},
    "Tuyên Quang": {"lat": 21.8233, "lon": 105.2144, "region": "Đông Bắc Bộ"},
    "Hà Giang": {"lat": 22.8233, "lon": 104.9839, "region": "Đông Bắc Bộ"},
    "Yên Bái": {"lat": 21.7167, "lon": 104.9000, "region": "Tây Bắc Bộ"},
    "Hòa Bình": {"lat": 20.8167, "lon": 105.3333, "region": "Tây Bắc Bộ"},
    "Sơn La": {"lat": 21.3289, "lon": 103.9147, "region": "Tây Bắc Bộ"},
    "Điện Biên": {"lat": 21.3869, "lon": 103.0222, "region": "Tây Bắc Bộ"},
    "Lai Châu": {"lat": 22.3964, "lon": 103.4589, "region": "Tây Bắc Bộ"},

    # Miền Trung & Tây Nguyên
    "Thanh Hóa": {"lat": 19.8075, "lon": 105.7764, "region": "Bắc Trung Bộ"},
    "Nghệ An (Vinh)": {"lat": 18.6733, "lon": 105.6922, "region": "Bắc Trung Bộ"},
    "Hà Tĩnh": {"lat": 18.3428, "lon": 105.9058, "region": "Bắc Trung Bộ"},
    "Quảng Bình (Đồng Hới)": {"lat": 17.4833, "lon": 106.6000, "region": "Bắc Trung Bộ"},
    "Quảng Trị (Đông Hà)": {"lat": 16.8167, "lon": 107.1000, "region": "Bắc Trung Bộ"},
    "Thừa Thiên Huế": {"lat": 16.4637, "lon": 107.5909, "region": "Bắc Trung Bộ"},
    "Quảng Nam (Hội An)": {"lat": 15.8801, "lon": 108.3380, "region": "Duyên hải Nam Trung Bộ"},
    "Quảng Ngãi": {"lat": 15.1206, "lon": 108.7922, "region": "Duyên hải Nam Trung Bộ"},
    "Bình Định (Quy Nhơn)": {"lat": 13.7830, "lon": 109.2197, "region": "Duyên hải Nam Trung Bộ"},
    "Phú Yên (Tuy Hòa)": {"lat": 13.0881, "lon": 109.3081, "region": "Duyên hải Nam Trung Bộ"},
    "Khánh Hòa (Nha Trang)": {"lat": 12.2388, "lon": 109.1967, "region": "Duyên hải Nam Trung Bộ"},
    "Ninh Thuận (Phan Rang)": {"lat": 11.5667, "lon": 108.9833, "region": "Duyên hải Nam Trung Bộ"},
    "Bình Thuận (Phan Thiết)": {"lat": 10.9333, "lon": 108.1000, "region": "Duyên hải Nam Trung Bộ"},
    "Lâm Đồng (Đà Lạt)": {"lat": 11.9404, "lon": 108.4583, "region": "Tây Nguyên"},
    "Đắk Lắk (Buôn Ma Thuột)": {"lat": 12.6667, "lon": 108.0333, "region": "Tây Nguyên"},
    "Gia Lai (Pleiku)": {"lat": 13.9833, "lon": 108.0000, "region": "Tây Nguyên"},
    "Kon Tum": {"lat": 14.3500, "lon": 108.0000, "region": "Tây Nguyên"},
    "Đắk Nông": {"lat": 12.0000, "lon": 107.6833, "region": "Tây Nguyên"},

    # Miền Nam
    "Bình Dương (Thủ Dầu Một)": {"lat": 10.9804, "lon": 106.6519, "region": "Đông Nam Bộ"},
    "Đồng Nai (Biên Hòa)": {"lat": 10.9575, "lon": 106.8427, "region": "Đông Nam Bộ"},
    "Bà Rịa - Vũng Tàu": {"lat": 10.3460, "lon": 107.0843, "region": "Đông Nam Bộ"},
    "Tây Ninh": {"lat": 11.3100, "lon": 106.0983, "region": "Đông Nam Bộ"},
    "Bình Phước (Đồng Xoài)": {"lat": 11.5333, "lon": 106.8833, "region": "Đông Nam Bộ"},
    "Long An (Tân An)": {"lat": 10.5333, "lon": 106.4000, "region": "Đồng bằng sông Cửu Long"},
    "Tiền Giang (Mỹ Tho)": {"lat": 10.3600, "lon": 106.3600, "region": "Đồng bằng sông Cửu Long"},
    "Bến Tre": {"lat": 10.2333, "lon": 106.3833, "region": "Đồng bằng sông Cửu Long"},
    "Trà Vinh": {"lat": 9.9347, "lon": 106.3453, "region": "Đồng bằng sông Cửu Long"},
    "Vĩnh Long": {"lat": 10.2500, "lon": 105.9667, "region": "Đồng bằng sông Cửu Long"},
    "Đồng Tháp (Cao Lãnh)": {"lat": 10.4589, "lon": 105.6325, "region": "Đồng bằng sông Cửu Long"},
    "An Giang (Long Xuyên)": {"lat": 10.3833, "lon": 105.4333, "region": "Đồng bằng sông Cửu Long"},
    "Kiên Giang (Rạch Giá)": {"lat": 10.0167, "lon": 105.0833, "region": "Đồng bằng sông Cửu Long"},
    "Kiên Giang (Phú Quốc)": {"lat": 10.2241, "lon": 103.9716, "region": "Đồng bằng sông Cửu Long"},
    "Hậu Giang (Vị Thanh)": {"lat": 9.7833, "lon": 105.4667, "region": "Đồng bằng sông Cửu Long"},
    "Sóc Trăng": {"lat": 9.6000, "lon": 105.9667, "region": "Đồng bằng sông Cửu Long"},
    "Bạc Liêu": {"lat": 9.2833, "lon": 105.7167, "region": "Đồng bằng sông Cửu Long"},
    "Cà Mau": {"lat": 9.1833, "lon": 105.1500, "region": "Đồng bằng sông Cửu Long"}
}

def get_location_stations(name_vn: str, lat: float, lon: float) -> list:
    """Tạo mạng lưới trạm cảm biến môi trường đô thị cho bất kỳ địa điểm nào."""
    return [
        {"name": f"Trạm {name_vn} (Trung tâm đô thị)", "lat": round(lat + 0.002, 4), "lon": round(lon - 0.002, 4)},
        {"name": f"Trạm {name_vn} (Khu dân cư - Học đường)", "lat": round(lat + 0.008, 4), "lon": round(lon - 0.012, 4)},
        {"name": f"Trạm {name_vn} (Cửa ngõ giao thông)", "lat": round(lat + 0.012, 4), "lon": round(lon + 0.015, 4)},
        {"name": f"Trạm {name_vn} (Khu sinh thái - Ven đô)", "lat": round(lat - 0.012, 4), "lon": round(lon - 0.008, 4)}
    ]

import unicodedata

def _normalize_str(text: str) -> str:
    """Chuẩn hóa chuỗi bỏ dấu tiếng Việt để tìm kiếm không dấu."""
    s = unicodedata.normalize('NFD', text.lower())
    s = ''.join(c for c in s if unicodedata.category(c) != 'Mn')
    return s.replace('đ', 'd')

def search_vietnam_locations(query: str, max_results: int = 8) -> list:
    """Tìm kiếm địa điểm tại Việt Nam: kết hợp 63 tỉnh thành nội bộ và Open-Meteo Geocoding API."""
    if not query or len(query.strip()) < 2:
        return []
    
    q_raw = query.strip()
    q_norm = _normalize_str(q_raw)
    results = []
    seen = set()

    # 1. Quét nhanh 63 tỉnh thành trong nước (tức thì, hỗ trợ gõ không dấu)
    for prov_name, prov_info in VIETNAM_LOCATIONS.items():
        prov_norm = _normalize_str(prov_name)
        if q_norm in prov_norm or prov_norm in q_norm:
            loc_key = (round(prov_info["lat"], 2), round(prov_info["lon"], 2))
            if loc_key not in seen:
                seen.add(loc_key)
                region = prov_info.get("region", "Việt Nam")
                results.append({
                    "label": f"{prov_name} ({region})",
                    "name": prov_name,
                    "lat": prov_info["lat"],
                    "lon": prov_info["lon"],
                    "admin1": region
                })

    # 2. Truy vấn Open-Meteo Geocoding API (cho các huyện, thị xã, đảo, điểm du lịch: Sa Pa, Phú Quốc, Tam Đảo, Ba Đình...)
    try:
        url = f"https://geocoding-api.open-meteo.com/v1/search?name={requests.utils.quote(q_raw)}&count={max_results}&language=vi&format=json"
        res = requests.get(url, timeout=4)
        if res.status_code == 200:
            data = res.json()
            for item in data.get("results", []):
                if item.get("country_code") == "VN" or item.get("country") == "Việt Nam":
                    lat_f = float(item["latitude"])
                    lon_f = float(item["longitude"])
                    loc_key = (round(lat_f, 2), round(lon_f, 2))
                    if loc_key in seen:
                        continue
                    seen.add(loc_key)
                    name = item.get("name", q_raw)
                    admin1 = item.get("admin1", "")
                    admin2 = item.get("admin2", "")
                    parts = [name]
                    if admin2 and admin2 != name:
                        parts.append(admin2)
                    if admin1 and admin1 != name:
                        parts.append(admin1)
                    label = ", ".join(parts)
                    results.append({
                        "label": label,
                        "name": name,
                        "lat": lat_f,
                        "lon": lon_f,
                        "admin1": admin1
                    })
    except Exception as e:
        print(f"Lỗi tìm kiếm geocoding: {e}")
        
    return results[:max_results]

def get_aqi_category(aqi_val: float) -> str:
    """Xác định mức độ chất lượng không khí theo tiêu chuẩn US EPA."""
    if pd.isna(aqi_val):
        return "Không xác định"
    aqi = float(aqi_val)
    if aqi <= 50:
        return "Tốt"
    elif aqi <= 100:
        return "Trung bình"
    elif aqi <= 150:
        return "Kém (Nhạy cảm)"
    elif aqi <= 200:
        return "Xấu"
    elif aqi <= 300:
        return "Rất xấu"
    else:
        return "Nguy hại"

def fetch_city_data(
    city_key: str = "Hanoi", 
    lat: float = None, 
    lon: float = None, 
    city_name_vn: str = None, 
    past_days: int = 14, 
    forecast_days: int = 7
) -> pd.DataFrame:
    """
    Thu thập dữ liệu chất lượng không khí và thời tiết từ Open-Meteo cho bất kỳ địa điểm nào tại Việt Nam.
    Trả về DataFrame kết hợp đã được làm sạch và chuẩn hóa (bao gồm 7 ngày dự báo).
    """
    if lat is not None and lon is not None:
        target_lat = float(lat)
        target_lon = float(lon)
        name_vn = city_name_vn or city_key
    elif city_key in CITIES:
        city_info = CITIES[city_key]
        target_lat = city_info["lat"]
        target_lon = city_info["lon"]
        name_vn = city_info["name_vn"]
    elif city_key in VIETNAM_LOCATIONS:
        loc_info = VIETNAM_LOCATIONS[city_key]
        target_lat = loc_info["lat"]
        target_lon = loc_info["lon"]
        name_vn = city_key
    else:
        # Mặc định Hà Nội
        target_lat = 21.0285
        target_lon = 105.8542
        name_vn = "Hà Nội"

    # 1. Gọi Open-Meteo Air Quality API
    air_url = (
        f"https://air-quality-api.open-meteo.com/v1/air-quality"
        f"?latitude={target_lat}&longitude={target_lon}"
        f"&hourly=pm10,pm2_5,carbon_monoxide,nitrogen_dioxide,ozone,us_aqi"
        f"&past_days={past_days}&forecast_days={forecast_days}&timezone=Asia%2FBangkok"
    )
    
    # 2. Gọi Open-Meteo Weather Forecast API
    weather_url = (
        f"https://api.open-meteo.com/v1/forecast"
        f"?latitude={target_lat}&longitude={target_lon}"
        f"&hourly=temperature_2m,relative_humidity_2m,precipitation_probability,precipitation,uv_index,wind_speed_10m"
        f"&past_days={past_days}&forecast_days={forecast_days}&timezone=Asia%2FBangkok"
    )

    try:
        r_air = requests.get(air_url, timeout=12)
        r_air.raise_for_status()
        air_json = r_air.json()
        df_air = pd.DataFrame(air_json["hourly"])
    except Exception as e:
        print(f"Lỗi khi gọi API Air Quality: {e}")
        df_air = pd.DataFrame()

    try:
        r_weather = requests.get(weather_url, timeout=12)
        r_weather.raise_for_status()
        weather_json = r_weather.json()
        df_weather = pd.DataFrame(weather_json["hourly"])
    except Exception as e:
        print(f"Lỗi khi gọi API Weather: {e}")
        df_weather = pd.DataFrame()

    # Trộn dữ liệu nếu cả 2 API thành công
    if not df_air.empty and not df_weather.empty:
        df = pd.merge(df_air, df_weather, on="time", how="inner")
    elif not df_air.empty:
        df = df_air
    else:
        df = df_weather

    if df.empty:
        raise RuntimeError("Không thể lấy dữ liệu từ Open-Meteo API.")

    # Đổi tên cột cho chuẩn mực và rõ ràng
    df.rename(columns={
        "time": "timestamp",
        "us_aqi": "aqi_us",
        "pm2_5": "pm2_5",
        "pm10": "pm10",
        "nitrogen_dioxide": "nitrogen_dioxide",
        "carbon_monoxide": "carbon_monoxide",
        "ozone": "ozone",
        "temperature_2m": "temperature_2m",
        "relative_humidity_2m": "relative_humidity_2m",
        "precipitation_probability": "precipitation_probability",
        "precipitation": "precipitation",
        "uv_index": "uv_index",
        "wind_speed_10m": "wind_speed_10m"
    }, inplace=True)

    # Thêm thông tin thành phố
    df["city"] = city_key
    df["city_name_vn"] = name_vn
    df["station_name"] = f"Trạm Trung tâm {name_vn}"
    df["latitude"] = target_lat
    df["longitude"] = target_lon

    # Tiền xử lý: Điền khuyết dữ liệu bằng nội suy thời gian
    numeric_cols = df.select_dtypes(include=["number"]).columns
    df[numeric_cols] = df[numeric_cols].interpolate(method="linear").bfill().ffill()

    # Phân loại mức AQI
    if "aqi_us" in df.columns:
        df["aqi_category"] = df["aqi_us"].apply(get_aqi_category)

    return df

def get_7day_summary(df: pd.DataFrame) -> pd.DataFrame:
    """
    Tổng hợp dữ liệu dự báo theo từng ngày cho 7 ngày tới (1 tuần).
    """
    if df.empty or "timestamp" not in df.columns:
        return pd.DataFrame()

    df_copy = df.copy()
    if not pd.api.types.is_datetime64_any_dtype(df_copy["timestamp"]):
        df_copy["timestamp"] = pd.to_datetime(df_copy["timestamp"])

    now_date = pd.Timestamp.now().normalize()
    df_future = df_copy[df_copy["timestamp"] >= now_date].copy()
    if len(df_future) < 24:
        df_future = df_copy.tail(168).copy()

    df_future["date"] = df_future["timestamp"].dt.date
    daily_records = []
    days_vi = ["Thứ Hai", "Thứ Ba", "Thứ Tư", "Thứ Năm", "Thứ Sáu", "Thứ Bảy", "Chủ Nhật"]

    for date_val, group in df_future.groupby("date"):
        dt = pd.to_datetime(date_val)
        day_name = days_vi[dt.weekday()]
        date_str = dt.strftime("%d/%m")
        label = f"{day_name}, {date_str}"

        avg_aqi = group["aqi_us"].mean() if "aqi_us" in group.columns else 50
        max_aqi = group["aqi_us"].max() if "aqi_us" in group.columns else 50
        avg_pm25 = group["pm2_5"].mean() if "pm2_5" in group.columns else 15
        max_temp = group["temperature_2m"].max() if "temperature_2m" in group.columns else 30
        min_temp = group["temperature_2m"].min() if "temperature_2m" in group.columns else 22
        max_rain = group["precipitation_probability"].max() if "precipitation_probability" in group.columns else 0
        max_uv = group["uv_index"].max() if "uv_index" in group.columns else 3

        category = get_aqi_category(avg_aqi)

        daily_records.append({
            "date": dt,
            "label": label,
            "avg_aqi": round(avg_aqi, 0),
            "max_aqi": round(max_aqi, 0),
            "category": category,
            "avg_pm25": round(avg_pm25, 1),
            "max_temp": round(max_temp, 1),
            "min_temp": round(min_temp, 1),
            "max_rain": round(max_rain, 0),
            "max_uv": round(max_uv, 1)
        })

        if len(daily_records) >= 7:
            break

    return pd.DataFrame(daily_records)


def generate_and_save_all_datasets(output_dir: str = "data") -> None:
    """
    Thu thập và xuất 3 file dataset CSV chuẩn vào thư mục output_dir.
    """
    os.makedirs(output_dir, exist_ok=True)

    print("Đang thu thập dữ liệu Hà Nội...")
    df_hanoi = fetch_city_data("Hanoi", past_days=30, forecast_days=7)
    hanoi_path = os.path.join(output_dir, "air_quality_hanoi.csv")
    df_hanoi.to_csv(hanoi_path, index=False, encoding="utf-8-sig")
    print(f"-> Đã lưu {len(df_hanoi)} dòng vào {hanoi_path}")

    print("Đang thu thập dữ liệu TP. Hồ Chí Minh...")
    df_hcm = fetch_city_data("Ho Chi Minh City", past_days=30, forecast_days=7)
    hcm_path = os.path.join(output_dir, "air_quality_hcm.csv")
    df_hcm.to_csv(hcm_path, index=False, encoding="utf-8-sig")
    print(f"-> Đã lưu {len(df_hcm)} dòng vào {hcm_path}")

    # Xuất file dự báo thời tiết tổng hợp
    print("Đang tổng hợp dữ liệu dự báo thời tiết...")
    cols_weather = ["timestamp", "city", "city_name_vn", "temperature_2m", "relative_humidity_2m", 
                    "precipitation_probability", "precipitation", "uv_index", "wind_speed_10m"]
    df_weather = pd.concat([df_hanoi[cols_weather], df_hcm[cols_weather]], ignore_index=True)
    weather_path = os.path.join(output_dir, "weather_forecast.csv")
    df_weather.to_csv(weather_path, index=False, encoding="utf-8-sig")
    print(f"-> Đã lưu {len(df_weather)} dòng vào {weather_path}")

if __name__ == "__main__":
    generate_and_save_all_datasets()
