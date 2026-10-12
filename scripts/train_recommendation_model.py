"""
scripts/train_recommendation_model.py
Huấn luyện mô hình Machine Learning (Random Forest Multi-Output)
trên tập dữ liệu tổng hợp 50.000 bản ghi cho bài toán khuyến nghị sức khỏe:
- Tập thể dục ngoài trời (Tránh / Được phép)
- Đóng / mở cửa sổ
- Đeo khẩu trang khi ra ngoài
- Bật máy lọc không khí trong nhà
"""

import os
import json
import numpy as np
import pandas as pd
from sklearn.model_selection import train_test_split
from sklearn.ensemble import RandomForestClassifier
from sklearn.metrics import classification_report, accuracy_score
import joblib

def generate_health_dataset(num_samples: int = 50000, seed: int = 42) -> pd.DataFrame:
    """
    Sinh tập dữ liệu 50.000 bản ghi mô phỏng đa dạng điều kiện môi trường thực tế tại Việt Nam
    kết hợp hồ sơ thể trạng và bệnh lý cá nhân.
    """
    np.random.seed(seed)
    
    # 1. Các biến môi trường & khí tượng
    # AQI mô phỏng theo phân phối Weibull/Beta thực tế của các đô thị Việt Nam (dao động 15 - 320)
    aqi_raw = np.random.gamma(shape=3.5, scale=24, size=num_samples)
    aqi_us = np.clip(aqi_raw, 10, 350).round(1)
    
    # PM2.5 có tương quan chặt chẽ với AQI (r ~ 0.85 - 0.95)
    pm2_5 = np.clip(aqi_us * 0.42 + np.random.normal(0, 4.5, num_samples), 3, 280).round(1)
    pm10 = np.clip(pm2_5 * 1.55 + np.random.normal(0, 8, num_samples), 5, 400).round(1)
    
    # Thời tiết nhiệt đới gió mùa Việt Nam
    temperature = np.random.normal(27.5, 5.5, num_samples).clip(10, 42).round(1)
    humidity = np.random.normal(76, 12, num_samples).clip(30, 100).round(1)
    rain_prob = np.random.beta(a=0.8, b=2.2, size=num_samples) * 100
    rain_prob = np.clip(rain_prob, 0, 100).round(1)
    uv_index = np.random.exponential(scale=3.8, size=num_samples).clip(0, 12).round(1)
    wind_speed = np.random.gamma(shape=2.2, scale=4.0, size=num_samples).clip(1, 45).round(1)
    
    # 2. Hồ sơ thể trạng người dùng
    age = np.random.randint(1, 95, size=num_samples)
    
    # Xác suất bệnh nền thực tế theo độ tuổi
    # Người cao tuổi và trẻ em có nguy cơ cao hơn
    prob_resp = np.where(age > 50, 0.28, np.where(age < 12, 0.18, 0.08))
    prob_asthma = np.where(age < 18, 0.16, np.where(age > 55, 0.14, 0.06))
    prob_heart = np.where(age > 50, 0.32, 0.03)
    prob_copd = np.where(age > 45, 0.22, 0.02)
    
    has_respiratory = (np.random.rand(num_samples) < prob_resp).astype(int)
    has_asthma = (np.random.rand(num_samples) < prob_asthma).astype(int)
    has_heart = (np.random.rand(num_samples) < prob_heart).astype(int)
    has_copd = (np.random.rand(num_samples) < prob_copd).astype(int)
    
    # 3. Gán nhãn chuẩn theo quy chuẩn y tế (Ground Truth Labels theo WHO / US EPA / IQAir)
    is_sensitive = (age < 12) | (age >= 60) | (has_respiratory == 1) | (has_asthma == 1) | (has_heart == 1) | (has_copd == 1)
    
    # Nhãn 1: rec_exercise (0 = Tránh tập thể dục ngoài trời, 1 = Có thể tập ngoài trời)
    # Tránh khi: Ô nhiễm cao HOẶC (nhạy cảm và AQI > 50) HOẶC mưa bão (rain >= 60) HOẶC nắng gắt (T >= 36 & UV >= 8)
    avoid_exercise = (
        (aqi_us > 100) |
        (is_sensitive & (aqi_us > 50)) |
        (rain_prob >= 60) |
        ((temperature >= 36) & (uv_index >= 8)) |
        ((has_heart == 1) & (aqi_us > 70)) |
        ((has_asthma == 1) & (aqi_us > 60))
    )
    rec_exercise = np.where(avoid_exercise, 0, 1)
    
    # Nhãn 2: rec_window (0 = Đóng cửa sổ, 1 = Mở cửa thông gió trong lành)
    # Đóng khi ô nhiễm ngoài trời vượt ngưỡng hoặc người nhạy cảm ở mức trung bình trở lên
    close_window = (
        (aqi_us > 100) |
        (is_sensitive & (aqi_us > 50)) |
        (pm2_5 > 35) |
        (rain_prob >= 75)
    )
    rec_window = np.where(close_window, 0, 1)
    
    # Nhãn 3: rec_mask (0 = Không cần đeo, 1 = Cần đeo khẩu trang khi ra ngoài)
    # Đeo khi AQI > 50 hoặc nhóm nhạy cảm
    need_mask = (
        (aqi_us > 50) |
        (is_sensitive & (aqi_us > 40)) |
        (pm2_5 > 25)
    )
    rec_mask = np.where(need_mask, 1, 0)
    
    # Nhãn 4: rec_purifier (0 = Chưa cần bật, 1 = Bật máy lọc không khí)
    need_purifier = (
        (aqi_us > 80) |
        (is_sensitive & (aqi_us > 50)) |
        (pm2_5 > 30) |
        (has_asthma == 1) |
        (has_copd == 1)
    )
    rec_purifier = np.where(need_purifier, 1, 0)
    
    df = pd.DataFrame({
        "aqi_us": aqi_us,
        "pm2_5": pm2_5,
        "pm10": pm10,
        "temperature": temperature,
        "humidity": humidity,
        "precipitation_prob": rain_prob,
        "uv_index": uv_index,
        "wind_speed": wind_speed,
        "age": age,
        "has_respiratory": has_respiratory,
        "has_asthma": has_asthma,
        "has_heart": has_heart,
        "has_copd": has_copd,
        "rec_exercise": rec_exercise,
        "rec_window": rec_window,
        "rec_mask": rec_mask,
        "rec_purifier": rec_purifier
    })
    
    return df

def train_and_evaluate_model():
    print("=" * 60)
    print("BƯỚC 1: Sinh tập dữ liệu 50.000 bản ghi huấn luyện...")
    df = generate_health_dataset(num_samples=50000)
    
    os.makedirs("data", exist_ok=True)
    os.makedirs("models", exist_ok=True)
    
    csv_path = os.path.join("data", "health_recommendations_50k.csv")
    df.to_csv(csv_path, index=False, encoding="utf-8-sig")
    print(f"-> Đã lưu dữ liệu vào {csv_path} ({len(df):,} dòng, {len(df.columns)} cột)")
    
    feature_cols = [
        "aqi_us", "pm2_5", "pm10", "temperature", "humidity",
        "precipitation_prob", "uv_index", "wind_speed",
        "age", "has_respiratory", "has_asthma", "has_heart", "has_copd"
    ]
    target_cols = ["rec_exercise", "rec_window", "rec_mask", "rec_purifier"]
    
    X = df[feature_cols]
    y = df[target_cols]
    
    print("\nBƯỚC 2: Phân chia tập dữ liệu (80% Train - 20% Test)...")
    X_train, X_test, y_train, y_test = train_test_split(X, y, test_size=0.2, random_state=42)
    print(f"-> Kích thước tập Train: {len(X_train):,} mẫu")
    print(f"-> Kích thước tập Test:  {len(X_test):,} mẫu")
    
    print("\nBƯỚC 3: Huấn luyện mô hình Random Forest Classifier (n_estimators=100)...")
    model = RandomForestClassifier(
        n_estimators=100,
        max_depth=16,
        min_samples_split=4,
        random_state=42,
        n_jobs=-1
    )
    model.fit(X_train, y_train)
    
    print("\nBƯỚC 4: Đánh giá mô hình trên tập Test (10.000 mẫu)...")
    y_pred = model.predict(X_test)
    y_pred_df = pd.DataFrame(y_pred, columns=target_cols, index=y_test.index)
    
    metrics = {}
    for col in target_cols:
        acc = accuracy_score(y_test[col], y_pred_df[col])
        metrics[col] = {
            "accuracy": round(float(acc) * 100, 2),
            "report": classification_report(y_test[col], y_pred_df[col], output_dict=True)
        }
        print(f"-> Độ chính xác nhãn '{col}': {acc * 100:.2f}%")
        
    overall_exact_match = (y_pred == y_test.values).all(axis=1).mean() * 100
    print(f"\n=> Tỷ lệ dự đoán ĐÚNG ĐỒNG THỜI CẢ 4 NHÃN (Exact Match Ratio): {overall_exact_match:.2f}%")
    
    # Feature Importance
    importances = model.feature_importances_
    feat_imp = sorted(zip(feature_cols, [round(float(x) * 100, 2) for x in importances]), key=lambda x: x[1], reverse=True)
    print("\nTẦM QUAN TRỌNG CỦA CÁC ĐẶC TRƯNG (FEATURE IMPORTANCE):")
    for name, imp in feat_imp:
        print(f"  • {name:20s}: {imp:5.2f}%")
        
    # Lưu mô hình & thông số
    model_path = os.path.join("models", "health_rec_model.joblib")
    joblib.dump(model, model_path, compress=3)
    print(f"\n-> Đã lưu mô hình huấn luyện vào: {model_path}")
    
    metadata = {
        "model_type": "RandomForestClassifier",
        "n_samples": len(df),
        "train_samples": len(X_train),
        "test_samples": len(X_test),
        "feature_cols": feature_cols,
        "target_cols": target_cols,
        "exact_match_ratio": round(overall_exact_match, 2),
        "metrics": metrics,
        "feature_importance": dict(feat_imp)
    }
    
    meta_path = os.path.join("models", "model_metrics.json")
    with open(meta_path, "w", encoding="utf-8") as f:
        json.dump(metadata, f, ensure_ascii=False, indent=2)
    print(f"-> Đã lưu báo cáo đánh giá vào: {meta_path}")
    print("=" * 60)

if __name__ == "__main__":
    train_and_evaluate_model()
