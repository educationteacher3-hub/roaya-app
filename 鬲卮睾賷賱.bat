@echo off
chcp 65001 > nul
title مكتب رؤية — النظام المالي

echo.
echo ===============================================
echo    مكتب رؤية — النظام المالي
echo ===============================================
echo.

:: التحقق من وجود Python
python --version > nul 2>&1
if errorlevel 1 (
    echo [خطأ] Python غير مثبت على جهازك.
    echo يرجى تثبيت Python من: https://www.python.org/downloads/
    echo تأكد من تفعيل خيار "Add Python to PATH" أثناء التثبيت
    pause
    exit /b 1
)

echo [1/3] جاري التحقق من المكتبات...
pip show streamlit > nul 2>&1
if errorlevel 1 (
    echo [2/3] جاري تثبيت المكتبات المطلوبة...
    pip install -r requirements.txt
    if errorlevel 1 (
        echo [خطأ] فشل تثبيت المكتبات
        pause
        exit /b 1
    )
) else (
    echo [2/3] المكتبات موجودة بالفعل
)

echo [3/3] جاري تشغيل التطبيق...
echo.
echo افتح المتصفح على: http://localhost:8501
echo لإيقاف التطبيق: اضغط Ctrl+C في هذه النافذة
echo.

streamlit run app.py --server.port 8501 --server.headless false --browser.gatherUsageStats false

pause
