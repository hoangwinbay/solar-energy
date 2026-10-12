@echo off
title He Thong Ho Tro Ra Quyet Dinh Chat Luong Khong Khi (DSS)
echo =========================================================================
echo    HE HO TRO RA QUYET DINH CHAT LUONG KHONG KHI ^& KHUYEN NGHI SUC KHOE (DSS)
echo =========================================================================
echo Dang khoi dong Web Dashboard tren trinh duyet...
cd /d "%~dp0"
streamlit run app.py
pause
