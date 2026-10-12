"""
rule_engine.py
Động cơ suy diễn tập luật If-Then (Rule-Based Inference Engine)
cho Hệ thống Hỗ trợ Ra Quyết định (DSS) Cảnh báo Chất lượng Không khí.
"""

from typing import Dict, Any, List
import pandas as pd

# Bản đồ phân loại AQI theo chuẩn US EPA
AQI_LEVELS = {
    "GOOD": {
        "min": 0, "max": 50,
        "name_vn": "Tốt",
        "color": "#00E400",
        "text_color": "#000000",
        "desc": "Chất lượng không khí sạch, an toàn tuyệt đối cho mọi người."
    },
    "MODERATE": {
        "min": 51, "max": 100,
        "name_vn": "Trung bình",
        "color": "#FFFF00",
        "text_color": "#000000",
        "desc": "Chất lượng không khí ở mức chấp nhận được; nhóm rất nhạy cảm có thể bị ảnh hưởng nhẹ."
    },
    "UNHEALTHY_SENSITIVE": {
        "min": 101, "max": 150,
        "name_vn": "Kém (Nhạy cảm)",
        "color": "#FF7E00",
        "text_color": "#FFFFFF",
        "desc": "Nhóm nhạy cảm (trẻ nhỏ, người già, hen suyễn) bắt đầu gặp vấn đề về hô hấp."
    },
    "UNHEALTHY": {
        "min": 151, "max": 200,
        "name_vn": "Xấu",
        "color": "#FF0000",
        "text_color": "#FFFFFF",
        "desc": "Có hại cho sức khỏe mọi người; nhóm nhạy cảm bị ảnh hưởng nghiêm trọng."
    },
    "VERY_UNHEALTHY": {
        "min": 201, "max": 300,
        "name_vn": "Rất xấu",
        "color": "#8F3F97",
        "text_color": "#FFFFFF",
        "desc": "Cảnh báo khẩn cấp: nguy cơ kích ứng phổi và bệnh tim mạch tăng cao cho toàn cộng đồng."
    },
    "HAZARDOUS": {
        "min": 301, "max": 9999,
        "name_vn": "Nguy hại",
        "color": "#7E0023",
        "text_color": "#FFFFFF",
        "desc": "Mức độ ô nhiễm cực kỳ nguy hiểm; khuyên mọi người ở trong nhà hoàn toàn."
    }
}

PROFILES = {
    "general": "Người trưởng thành khỏe mạnh",
    "child": "Trẻ em (dưới 12 tuổi)",
    "sensitive": "Người cao tuổi / Bệnh nền hô hấp - tim mạch",
    "athlete": "Vận động viên / Người tập thể thao cường độ cao"
}

def get_aqi_info(aqi: float) -> Dict[str, Any]:
    """Lấy thông tin phân cấp mức AQI."""
    if aqi <= 50:
        key = "GOOD"
    elif aqi <= 100:
        key = "MODERATE"
    elif aqi <= 150:
        key = "UNHEALTHY_SENSITIVE"
    elif aqi <= 200:
        key = "UNHEALTHY"
    elif aqi <= 300:
        key = "VERY_UNHEALTHY"
    else:
        key = "HAZARDOUS"
    
    info = AQI_LEVELS[key].copy()
    info["level_key"] = key
    info["aqi_value"] = round(aqi, 1)
    return info

def evaluate_dss(
    aqi: float,
    temperature: float = 28.0,
    humidity: float = 75.0,
    precipitation_prob: float = 0.0,
    uv_index: float = 3.0,
    wind_speed: float = 10.0,
    profile: str = "general"
) -> Dict[str, Any]:
    """
    Động cơ suy diễn tập luật If-Then đa tiêu chí:
    Kết hợp AQI, Nhiệt độ, Mưa, UV và Hồ sơ đối tượng để đưa ra 4 nhóm quyết định.
    """
    aqi_info = get_aqi_info(aqi)
    is_sensitive = profile in ["child", "sensitive"]
    is_athlete = profile == "athlete"

    # Kiểm tra các yếu tố khí tượng cực đoan
    is_rainy = precipitation_prob >= 60.0
    is_heat_extreme = temperature >= 36.0
    is_cold_extreme = temperature <= 12.0
    is_uv_extreme = uv_index >= 8.0
    is_uv_high = uv_index >= 6.0

    # -------------------------------------------------------------
    # 1. QUYẾT ĐỊNH CHẠY BỘ / THỂ DỤC NGOÀI TRỜI (RUNNING / OUTDOOR SPORT)
    # -------------------------------------------------------------
    running = {}
    if aqi <= 50:
        if is_rainy:
            running = {
                "status": "Tạm dừng ngoài trời",
                "badge": "warning",
                "color": "#FFC107",
                "advice": "Không khí trong lành tuyệt vời, tuy nhiên trời có mưa lớn (xác suất {:.0f}%). Nên chuyển vào chạy máy chạy bộ trong nhà hoặc phòng gym.".format(precipitation_prob)
            }
        elif is_heat_extreme:
            running = {
                "status": "Chỉ tập sáng sớm / chiều mát",
                "badge": "warning",
                "color": "#FFC107",
                "advice": "Không khí rất sạch nhưng nhiệt độ cao ({:.1f}°C) dễ gây kiệt sức và sốc nhiệt. Chỉ nên chạy trước 7h sáng hoặc sau 17h30 chiều.".format(temperature)
            }
        else:
            running = {
                "status": "Rất lý tưởng để chạy bộ",
                "badge": "success",
                "color": "#28A745",
                "advice": "Thời tiết và chất lượng không khí hoàn hảo. Bạn có thể tự do tập luyện, chạy cự ly dài và hít thở sâu mà không lo ngại rủi ro sức khỏe."
            }
    elif aqi <= 100:
        if is_sensitive:
            running = {
                "status": "Giảm cường độ tập",
                "badge": "warning",
                "color": "#FFC107",
                "advice": "Không khí ở mức trung bình. Nhóm nhạy cảm chỉ nên đi bộ nhẹ nhàng trong công viên có nhiều bóng cây, tránh chạy gắng sức."
            }
        elif is_rainy:
            running = {
                "status": "Nên tập trong nhà",
                "badge": "warning",
                "color": "#FFC107",
                "advice": "Xác suất mưa cao kết hợp không khí trung bình. Nên tập trong nhà hoặc phòng tập thể dục."
            }
        else:
            running = {
                "status": "Được phép chạy bộ",
                "badge": "success",
                "color": "#28A745",
                "advice": "Chất lượng không khí chấp nhận được cho người bình thường. Có thể chạy bộ và đạp xe ngoài trời bình thường."
            }
    elif aqi <= 150:
        if is_sensitive:
            running = {
                "status": "Không nên tập ngoài trời",
                "badge": "danger",
                "color": "#DC3545",
                "advice": "Không khí kém. Trẻ em, người già và người có bệnh hô hấp tuyệt đối KHÔNG chạy nhảy gắng sức ngoài trời để tránh khởi phát cơn hen suyễn."
            }
        elif is_athlete:
            running = {
                "status": "Hạn chế bài tập nặng",
                "badge": "warning",
                "color": "#FD7E14",
                "advice": "Vận động viên cần giảm khối lượng bài tập hoặc chuyển sang bài tập bổ trợ trong nhà để giảm thể tích thông khí nạp bụi mịn PM2.5."
            }
        else:
            running = {
                "status": "Chỉ tập nhẹ, dưới 30 phút",
                "badge": "warning",
                "color": "#FD7E14",
                "advice": "Người bình thường chỉ nên đi bộ nhanh hoặc chạy cự ly ngắn dưới 30 phút. Tránh các tuyến đường có mật độ xe cộ đông đúc."
            }
    elif aqi <= 200:
        running = {
            "status": "Cấm vận động mạnh ngoài trời",
            "badge": "danger",
            "color": "#DC3545",
            "advice": "Không khí ở mức XẤU. Hít thở sâu khi chạy bộ sẽ đưa lượng lớn bụi mịn PM2.5 đi thẳng vào phế nang phổi. Chuyển toàn bộ hoạt động thể thao vào phòng kín."
        }
    else:
        running = {
            "status": "Tuyệt đối không chạy ngoài trời",
            "badge": "danger",
            "color": "#7E0023",
            "advice": "Mức ô nhiễm RẤT XẤU / NGUY HẠI. Hoạt động gắng sức ngoài trời có nguy cơ gây ngộ độc đường thở cấp tính và biến cố tim mạch."
        }

    # -------------------------------------------------------------
    # 2. QUYẾT ĐỊNH ĐEO KHẨU TRANG (MASK RECOMMENDATION)
    # -------------------------------------------------------------
    mask = {}
    if aqi <= 50:
        mask = {
            "type": "Không cần khẩu trang chống bụi",
            "badge": "success",
            "color": "#28A745",
            "advice": "Không khí sạch, có thể thoải mái hít thở không khí tự nhiên khi đi bộ hoặc chạy bộ ở nơi thoáng đãng."
        }
    elif aqi <= 100:
        if is_sensitive:
            mask = {
                "type": "Nên đeo khẩu trang y tế",
                "badge": "warning",
                "color": "#FFC107",
                "advice": "Nhóm nhạy cảm nên đeo khẩu trang y tế thông thường khi lưu thông trên đường lộ để ngăn ngừa bụi đường và khói xe."
            }
        else:
            mask = {
                "type": "Khẩu trang y tế (khi ra đường lớn)",
                "badge": "info",
                "color": "#17A2B8",
                "advice": "Có thể không cần đeo trong công viên, nhưng nên đeo khẩu trang thông thường khi đi xe máy trên các trục đường lớn."
            }
    elif aqi <= 150:
        mask = {
            "type": "Khẩu trang y tế hoặc KN90",
            "badge": "warning",
            "color": "#FD7E14",
            "advice": "Bắt buộc đeo khẩu trang y tế dày hoặc khẩu trang lọc bụi KN90 khi ra đường. Nhóm nhạy cảm nên ưu tiên dùng khẩu trang N95."
        }
    elif aqi <= 200:
        mask = {
            "type": "Bắt buộc khẩu trang N95 / KF94",
            "badge": "danger",
            "color": "#DC3545",
            "advice": "Khẩu trang vải hay y tế thông thường không ngăn được PM2.5 ở mức này. Bắt buộc dùng khẩu trang chuyên dụng N95 hoặc KF94 và đeo khít mép mặt."
        }
    else:
        mask = {
            "type": "Bắt buộc N95 & Hạn chế ra đường",
            "badge": "danger",
            "color": "#7E0023",
            "advice": "Ô nhiễm nghiêm trọng! Chỉ ra ngoài khi thực sự cấp bách và bắt buộc trang bị khẩu trang N95 đạt chuẩn có van hoặc phin lọc tốt."
        }

    # -------------------------------------------------------------
    # 3. QUYẾT ĐỊNH TRẺ EM & NHÓM NHẠY CẢM (CHILDREN & SENSITIVE GROUP)
    # -------------------------------------------------------------
    sensitive_dec = {}
    if aqi <= 50:
        if is_rainy or is_heat_extreme:
            sensitive_dec = {
                "status": "Chơi trong nhà mát",
                "badge": "warning",
                "color": "#FFC107",
                "advice": "Không khí tốt nhưng thời tiết bất lợi (mưa hoặc nắng nóng). Tránh để trẻ em ra ngoài bị ướt hoặc sốc nhiệt."
            }
        else:
            sensitive_dec = {
                "status": "Khuyến khích ra ngoài vui chơi",
                "badge": "success",
                "color": "#28A745",
                "advice": "Rất tốt để trẻ em vui chơi vận động ngoài trời, tắm nắng và người cao tuổi đi dạo dưỡng sinh."
            }
    elif aqi <= 100:
        sensitive_dec = {
            "status": "Được phép ra ngoài (Cần theo dõi)",
            "badge": "info",
            "color": "#17A2B8",
            "advice": "Trẻ em có thể tham gia các hoạt động ngoại khóa. Cần uống đủ nước và hạn chế vui chơi vào giờ cao điểm kẹt xe."
        }
    elif aqi <= 150:
        sensitive_dec = {
            "status": "Hạn chế tối đa ra ngoài",
            "badge": "warning",
            "color": "#FD7E14",
            "advice": "Nhà trường nên hạn chế các tiết thể dục ngoài trời cho học sinh tiểu học/mầm non. Người có bệnh hen suyễn cần mang theo bình xịt dự phòng."
        }
    elif aqi <= 200:
        sensitive_dec = {
            "status": "Nghiêm cấm hoạt động ngoài trời",
            "badge": "danger",
            "color": "#DC3545",
            "advice": "Giữ trẻ nhỏ và người cao tuổi trong nhà. Đóng kín cửa sổ phòng ngủ và thường xuyên nhỏ mắt, súc họng bằng nước muối sinh lý."
        }
    else:
        sensitive_dec = {
            "status": "Ở trong nhà tuyệt đối",
            "badge": "danger",
            "color": "#7E0023",
            "advice": "Nguy cơ kích phát cơn hen cấp tính rất cao. Duy trì phòng kín và theo dõi sát sao sức khỏe của người già và trẻ nhỏ."
        }

    # -------------------------------------------------------------
    # 4. QUYẾT ĐỊNH KHÔNG GIAN SỐNG & HÀNH ĐỘNG BỔ TRỢ (HOME & WELLNESS)
    # -------------------------------------------------------------
    home_actions = []
    if aqi <= 50:
        home_actions.append("🪟 Mở cửa sổ thông gió tự nhiên để lưu thông khí tươi trong phòng.")
    elif aqi <= 100:
        home_actions.append("🪟 Có thể mở cửa sổ thông gió vào buổi trưa/đầu giờ chiều (khi bụi lắng).")
    else:
        home_actions.append("🚪 Đóng kín các cửa sổ hướng ra mặt đường để ngăn bụi mịn xâm nhập.")
        home_actions.append("💨 Bật máy lọc không khí (Air Purifier) chế độ tự động hoặc tăng cường.")
    
    if is_uv_extreme:
        home_actions.append("☀️ Tia cực tím UV cực đại ({:.1f})! Cần thoa kem chống nắng SPF 50+, mang kính râm và mũ rộng vành khi ra ngoài.".format(uv_index))
    elif is_uv_high:
        home_actions.append("☀️ Chỉ số UV khá cao ({:.1f}). Nên che chắn da khi ra ngoài trong khoảng 10h - 15h.".format(uv_index))

    if aqi >= 101:
        home_actions.append("💧 Vệ sinh mũi họng bằng nước muối sinh lý NaCl 0.9% sau khi từ bên ngoài về.")

    return {
        "aqi_info": aqi_info,
        "profile": profile,
        "profile_vn": PROFILES.get(profile, profile),
        "weather_summary": {
            "temperature": temperature,
            "humidity": humidity,
            "precipitation_prob": precipitation_prob,
            "uv_index": uv_index,
            "wind_speed": wind_speed,
            "is_rainy": is_rainy,
            "is_heat_extreme": is_heat_extreme,
            "is_uv_high": is_uv_high
        },
        "running": running,
        "mask": mask,
        "sensitive": sensitive_dec,
        "home_actions": home_actions
    }

def generate_decision_rules_df() -> pd.DataFrame:
    """Tạo DataFrame bảng tập luật If-Then chuẩn mực để xuất ra CSV."""
    rules_data = [
        {
            "rule_id": "R01",
            "aqi_min": 0, "aqi_max": 50, "aqi_category": "Tốt",
            "weather_condition": "Thời tiết đẹp (Mưa < 50%, T < 35°C)",
            "target_group": "Tất cả mọi người",
            "running_decision": "Rất lý tưởng để chạy bộ tự do",
            "mask_decision": "Không cần khẩu trang",
            "sensitive_group_decision": "Khuyến khích ra ngoài vui chơi",
            "home_action": "Mở cửa thông gió nhà cửa"
        },
        {
            "rule_id": "R02",
            "aqi_min": 0, "aqi_max": 50, "aqi_category": "Tốt",
            "weather_condition": "Mưa lớn (>= 60%) hoặc Nắng gắt (>= 36°C)",
            "target_group": "Tất cả mọi người",
            "running_decision": "Tạm dừng chạy ngoài trời (do thời tiết)",
            "mask_decision": "Không cần khẩu trang bụi",
            "sensitive_group_decision": "Hạn chế ra ngoài tránh sốc nhiệt/cảm lạnh",
            "home_action": "Tập luyện thể thao trong nhà"
        },
        {
            "rule_id": "R03",
            "aqi_min": 51, "aqi_max": 100, "aqi_category": "Trung bình",
            "weather_condition": "Thời tiết bình thường",
            "target_group": "Người khỏe mạnh",
            "running_decision": "Được phép chạy bộ bình thường",
            "mask_decision": "Khẩu trang y tế khi đi đường lớn",
            "sensitive_group_decision": "Được phép ra ngoài",
            "home_action": "Thông gió vào đầu giờ chiều"
        },
        {
            "rule_id": "R04",
            "aqi_min": 51, "aqi_max": 100, "aqi_category": "Trung bình",
            "weather_condition": "Thời tiết bình thường",
            "target_group": "Trẻ em & Nhóm nhạy cảm",
            "running_decision": "Giảm cường độ, chỉ đi bộ nhẹ",
            "mask_decision": "Nên đeo khẩu trang y tế",
            "sensitive_group_decision": "Theo dõi phản ứng hô hấp",
            "home_action": "Uống nhiều nước"
        },
        {
            "rule_id": "R05",
            "aqi_min": 101, "aqi_max": 150, "aqi_category": "Kém (Nhạy cảm)",
            "weather_condition": "Bất kỳ",
            "target_group": "Người khỏe mạnh / Vận động viên",
            "running_decision": "Tập nhẹ < 30 phút, tránh giờ cao điểm",
            "mask_decision": "Nên đeo khẩu trang y tế hoặc KN90",
            "sensitive_group_decision": "Hạn chế hoạt động sân trường",
            "home_action": "Đóng cửa sổ giờ cao điểm, lọc khí"
        },
        {
            "rule_id": "R06",
            "aqi_min": 101, "aqi_max": 150, "aqi_category": "Kém (Nhạy cảm)",
            "weather_condition": "Bất kỳ",
            "target_group": "Trẻ em & Nhóm nhạy cảm",
            "running_decision": "Không tập thể dục ngoài trời",
            "mask_decision": "Nên đeo khẩu trang N95",
            "sensitive_group_decision": "Hạn chế tối đa ra ngoài",
            "home_action": "Mang theo bình xịt hen suyễn dự phòng"
        },
        {
            "rule_id": "R07",
            "aqi_min": 151, "aqi_max": 200, "aqi_category": "Xấu",
            "weather_condition": "Bất kỳ",
            "target_group": "Tất cả mọi người",
            "running_decision": "Cấm vận động mạnh ngoài trời",
            "mask_decision": "Bắt buộc khẩu trang N95 / KF94 ôm khít",
            "sensitive_group_decision": "Nghiêm cấm ra ngoài",
            "home_action": "Đóng kín cửa, bật máy lọc không khí"
        },
        {
            "rule_id": "R08",
            "aqi_min": 201, "aqi_max": 300, "aqi_category": "Rất xấu",
            "weather_condition": "Bất kỳ",
            "target_group": "Tất cả mọi người",
            "running_decision": "Cấm tuyệt đối mọi hoạt động ngoài trời",
            "mask_decision": "Bắt buộc N95, chỉ ra ngoài khi cấp bách",
            "sensitive_group_decision": "Ở trong phòng kín tuyệt đối",
            "home_action": "Bật máy lọc khí tối đa, súc họng mũi"
        },
        {
            "rule_id": "R09",
            "aqi_min": 301, "aqi_max": 500, "aqi_category": "Nguy hại",
            "weather_condition": "Bất kỳ",
            "target_group": "Tất cả mọi người",
            "running_decision": "Cảnh báo khẩn cấp: Ngừng mọi hoạt động",
            "mask_decision": "Đồ bảo hộ hô hấp chuyên dụng",
            "sensitive_group_decision": "Cấm rời khỏi phòng kín",
            "home_action": "Dùng máy lọc khí tuần hoàn khép kín"
        }
    ]
    return pd.DataFrame(rules_data)

def find_best_outdoor_hours(df_hourly: pd.DataFrame, top_k: int = 3) -> pd.DataFrame:
    """
    Tìm khung giờ thích hợp nhất để chạy bộ / hoạt động ngoài trời
    dựa trên chỉ số tổng hợp điểm rủi ro: Risk Score = 0.6 * AQI + 0.2 * Rain_Prob + 0.2 * UV
    """
    if df_hourly.empty or "aqi_us" not in df_hourly.columns:
        return pd.DataFrame()

    df = df_hourly.copy()
    # Chỉ xét trong 24 giờ tiếp theo
    df_24h = df.head(24).copy()

    # Tính điểm rủi ro (Risk score càng thấp càng tốt)
    rain = df_24h["precipitation_probability"] if "precipitation_probability" in df_24h.columns else 0
    uv = df_24h["uv_index"] if "uv_index" in df_24h.columns else 0
    df_24h["risk_score"] = (
        0.6 * df_24h["aqi_us"] +
        0.2 * rain +
        0.2 * (uv * 10)
    )

    best_hours = df_24h.sort_values(by="risk_score", ascending=True).head(top_k)
    return best_hours

def get_active_rule(aqi: float, precipitation_prob: float = 0.0, temperature: float = 28.0, profile: str = "general") -> Dict[str, str]:
    """Xác định mã luật If-Then kích hoạt trong cơ sở tri thức 9 luật chuẩn."""
    is_sensitive = profile in ["child", "sensitive"]
    is_extreme_weather = precipitation_prob >= 60.0 or temperature >= 36.0 or temperature <= 12.0
    
    if aqi <= 50:
        if is_extreme_weather:
            return {
                "rule_id": "R02",
                "condition": "AQI ≤ 50 & (Mưa ≥ 60% HOẶC Nhiệt độ cực đoan)",
                "action": "Tạm dừng chạy ngoài trời do thời tiết, Không cần khẩu trang lọc bụi, Tập luyện trong nhà"
            }
        else:
            return {
                "rule_id": "R01",
                "condition": "AQI ≤ 50 & Thời tiết thuận lợi",
                "action": "Rất lý tưởng để chạy bộ, Không cần khẩu trang, Khuyến khích ra ngoài vui chơi, Mở cửa thông gió"
            }
    elif aqi <= 100:
        if is_sensitive:
            return {
                "rule_id": "R04",
                "condition": "51 ≤ AQI ≤ 100 & Nhóm nhạy cảm / Trẻ em",
                "action": "Giảm cường độ tập, Đeo khẩu trang y tế khi ra đường, Theo dõi phản ứng hô hấp"
            }
        else:
            return {
                "rule_id": "R03",
                "condition": "51 ≤ AQI ≤ 100 & Người khỏe mạnh",
                "action": "Được phép chạy bộ bình thường, Khẩu trang y tế khi đi đường lớn, Mở cửa thông gió đầu giờ chiều"
            }
    elif aqi <= 150:
        if is_sensitive:
            return {
                "rule_id": "R06",
                "condition": "101 ≤ AQI ≤ 150 & Nhóm nhạy cảm / Trẻ em",
                "action": "Không tập thể dục ngoài trời, Bắt buộc khẩu trang N95, Hạn chế tối đa ra ngoài"
            }
        else:
            return {
                "rule_id": "R05",
                "condition": "101 ≤ AQI ≤ 150 & Người khỏe mạnh / Vận động viên",
                "action": "Tập nhẹ < 30 phút, Khẩu trang y tế / KN90, Hạn chế hoạt động gắng sức"
            }
    elif aqi <= 200:
        return {
            "rule_id": "R07",
            "condition": "151 ≤ AQI ≤ 200 (Xấu) & Mọi đối tượng",
            "action": "Cấm vận động mạnh ngoài trời, Bắt buộc N95/KF94 ôm khít, Nghiêm cấm trẻ em ra ngoài, Đóng kín cửa bật lọc khí"
        }
    elif aqi <= 300:
        return {
            "rule_id": "R08",
            "condition": "201 ≤ AQI ≤ 300 (Rất xấu) & Mọi đối tượng",
            "action": "Cấm tuyệt đối mọi hoạt động ngoài trời, Bắt buộc N95 khi cấp bách, Ở phòng kín tuyệt đối, Lọc khí tối đa"
        }
    else:
        return {
            "rule_id": "R09",
            "condition": "AQI > 300 (Nguy hại) & Mọi đối tượng",
            "action": "Cảnh báo khẩn cấp: Ngừng mọi hoạt động, Đồ bảo hộ chuyên dụng, Dùng máy lọc khí tuần hoàn khép kín"
        }

def calculate_composite_risk_score(aqi: float, rain_prob: float = 0.0, uv: float = 3.0, temp: float = 28.0) -> Dict[str, Any]:
    """Tính chỉ số rủi ro tổng hợp đa tiêu chí DSS (0 - 100)."""
    norm_aqi = min(100.0, (aqi / 300.0) * 100.0)
    norm_rain = min(100.0, float(rain_prob))
    norm_uv = min(100.0, (uv / 11.0) * 100.0)
    norm_temp = 0.0
    if temp >= 35.0:
        norm_temp = min(100.0, (temp - 35.0) * 15.0)
    elif temp <= 15.0:
        norm_temp = min(100.0, (15.0 - temp) * 10.0)
    
    score = 0.55 * norm_aqi + 0.20 * norm_rain + 0.15 * norm_uv + 0.10 * norm_temp
    score = round(min(100.0, max(0.0, score)), 1)
    
    if score < 30:
        level = "Rủi ro Thấp (An toàn)"
        color = "#10b981"
    elif score < 55:
        level = "Rủi ro Trung bình"
        color = "#f59e0b"
    elif score < 75:
        level = "Rủi ro Cao (Cần cảnh giác)"
        color = "#f97316"
    else:
        level = "Rủi ro Rất cao (Nguy hiểm)"
        color = "#ef4444"
        
    return {
        "score": score,
        "level": level,
        "color": color,
        "breakdown": {
            "aqi_impact": round(0.55 * norm_aqi, 1),
            "rain_impact": round(0.20 * norm_rain, 1),
            "uv_impact": round(0.15 * norm_uv, 1),
            "temp_impact": round(0.10 * norm_temp, 1)
        }
    }

def get_activity_suitability(aqi: float, rain_prob: float = 0.0, uv: float = 3.0, temp: float = 28.0, profile: str = "general") -> List[Dict[str, Any]]:
    """Đánh giá mức độ phù hợp cho 6 hoạt động sinh hoạt & thể thao ngoài trời phổ biến."""
    is_sensitive = profile in ["child", "sensitive"]
    
    # 1. Chạy bộ đường dài (> 5km)
    if aqi > 150 or rain_prob > 70 or temp > 36:
        act_run = {"name": "Chạy bộ cự ly dài (> 5km)", "icon": "🏃", "verdict": "KHÔNG NÊN", "color": "#ef4444", "reason": "Hít thở sâu thể tích khí lớn làm tích tụ hạt bụi PM2.5 sâu trong phế nang."}
    elif aqi > 100 or is_sensitive:
        act_run = {"name": "Chạy bộ cự ly dài (> 5km)", "icon": "🏃", "verdict": "HẠN CHẾ", "color": "#f97316", "reason": "Giảm xuống cự ly ngắn < 3km hoặc chuyển vào chạy máy trong phòng tập."}
    else:
        act_run = {"name": "Chạy bộ cự ly dài (> 5km)", "icon": "🏃", "verdict": "PHÙ HỢP", "color": "#10b981", "reason": "Điều kiện không khí và thời tiết an toàn cho tập luyện gắng sức."}
        
    # 2. Đi bộ nhẹ dưỡng sinh công viên
    if aqi > 200:
        act_walk = {"name": "Đi bộ dưỡng sinh / Dạo mát", "icon": "🚶", "verdict": "KHÔNG NÊN", "color": "#ef4444", "reason": "Ô nhiễm mức cao gây kích ứng niêm mạc mắt và đường hô hấp trên."}
    elif aqi > 100:
        act_walk = {"name": "Đi bộ dưỡng sinh / Dạo mát", "icon": "🚶", "verdict": "CÂN NHẮC", "color": "#f59e0b", "reason": "Đi bộ dưới 30 phút trong công viên nhiều cây xanh, bắt buộc đeo khẩu trang."}
    else:
        act_walk = {"name": "Đi bộ dưỡng sinh / Dạo mát", "icon": "🚶", "verdict": "RẤT TỐT", "color": "#10b981", "reason": "Rất có lợi cho tim mạch và thư giãn tinh thần."}

    # 3. Trẻ em vui chơi sân trường / ngoại khóa
    if aqi > 100 or is_sensitive or rain_prob > 60:
        act_child = {"name": "Trẻ em vui chơi / Thể dục trường học", "icon": "⚽", "verdict": "HỦY BỎ", "color": "#ef4444", "reason": "Phổi trẻ chưa phát triển hoàn thiện; chuyển toàn bộ tiết học vào nhà đa năng."}
    elif aqi > 50:
        act_child = {"name": "Trẻ em vui chơi / Thể dục trường học", "icon": "⚽", "verdict": "THEO DÕI", "color": "#f59e0b", "reason": "Chỉ hoạt động nhẹ dưới bóng râm, uống đủ nước."}
    else:
        act_child = {"name": "Trẻ em vui chơi / Thể dục trường học", "icon": "⚽", "verdict": "AN TOÀN", "color": "#10b981", "reason": "Khuyến khích trẻ vận động giải phóng năng lượng ngoài trời."}

    # 4. Đạp xe ngoài trời / Đi xe máy lộ trình dài
    if aqi > 150:
        act_bike = {"name": "Đạp xe / Di chuyển bằng xe máy", "icon": "🚴", "verdict": "BẮT BUỘC N95", "color": "#ef4444", "reason": "Tiếp xúc trực tiếp với khói xả giao thông và bụi mịn lơ lửng mặt đường."}
    elif aqi > 100:
        act_bike = {"name": "Đạp xe / Di chuyển bằng xe máy", "icon": "🚴", "verdict": "CẦN BẢO VỆ", "color": "#f97316", "reason": "Đeo khẩu trang y tế hoặc KN90, mang kính chắn gió."}
    else:
        act_bike = {"name": "Đạp xe / Di chuyển bằng xe máy", "icon": "🚴", "verdict": "THOẢI MÁI", "color": "#10b981", "reason": "Lưu thông bình thường, thời tiết thuận lợi."}

    # 5. Mở cửa sổ thông gió đón gió tự nhiên
    if aqi > 100:
        act_vent = {"name": "Mở cửa thông gió phòng", "icon": "🪟", "verdict": "ĐÓNG KÍN", "color": "#ef4444", "reason": "Không khí bên ngoài ô nhiễm hơn trong nhà. Đóng cửa và bật máy lọc khí HEPA."}
    else:
        act_vent = {"name": "Mở cửa thông gió phòng", "icon": "🪟", "verdict": "NÊN MỞ", "color": "#10b981", "reason": "Lưu thông không khí tươi, giảm nồng độ CO2 và ẩm mốc trong phòng."}

    # 6. Phơi quần áo ngoài ban công / sân thượng
    if aqi > 150 or rain_prob > 50:
        act_dry = {"name": "Phơi đồ ban công / Ngoài trời", "icon": "🧺", "verdict": "PHƠI TRONG NHÀ", "color": "#f97316", "reason": "Bụi mịn và khí thải bám dính vào sợi vải gây kích ứng da và dị ứng."}
    else:
        act_dry = {"name": "Phơi đồ ban công / Ngoài trời", "icon": "🧺", "verdict": "PHƠI NGOÀI TRỜI", "color": "#10b981", "reason": "Nắng và gió tự nhiên giúp diệt khuẩn sợi vải hiệu quả."}

    return [act_run, act_walk, act_child, act_bike, act_vent, act_dry]

