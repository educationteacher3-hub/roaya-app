import pandas as pd
import streamlit as st
import io
import json
from google.oauth2 import service_account
from googleapiclient.discovery import build
from googleapiclient.http import MediaIoBaseDownload

# ===== IDs ملفات Google Drive =====
DRIVE_FILES = {
    "roaya_cash": "1ALVnrsaypbI-0lZ8EW3mfLWGhTPZ5EQP",
    "clients":    "1SV9TVYSWTt1-V8m1sGtdRJcgjszfCvmV",
    "itqan":      "1muSQN0yLi2nVD80Ou7MaVFdoDKaKhYXX",
}

def get_drive_service():
    """إنشاء اتصال بـ Google Drive API"""
    creds_dict = dict(st.secrets["gcp_service_account"])
    creds = service_account.Credentials.from_service_account_info(
        creds_dict,
        scopes=["https://www.googleapis.com/auth/drive.readonly"]
    )
    return build("drive", "v3", credentials=creds)

@st.cache_data(ttl=300)
def download_excel(file_key):
    """تحميل ملف Excel من Google Drive عبر API"""
    try:
        service = get_drive_service()
        file_id = DRIVE_FILES[file_key]
        request = service.files().export_media(
            fileId=file_id,
            mimeType="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
        )
        buf = io.BytesIO()
        downloader = MediaIoBaseDownload(buf, request)
        done = False
        while not done:
            _, done = downloader.next_chunk()
        buf.seek(0)
        return buf
    except Exception as e:
        # لو مش Google Sheets جرب تحميل مباشر
        try:
            service = get_drive_service()
            file_id = DRIVE_FILES[file_key]
            request = service.files().get_media(fileId=file_id)
            buf = io.BytesIO()
            downloader = MediaIoBaseDownload(buf, request)
            done = False
            while not done:
                _, done = downloader.next_chunk()
            buf.seek(0)
            return buf
        except Exception as e2:
            st.error(f"خطأ في تحميل الملف ({file_key}): {e2}")
            return None

@st.cache_data(ttl=300)
def load_excel_from_drive(file_key, sheet_name, header=0, nrows=None):
    try:
        buf = download_excel(file_key)
        if buf is None:
            return pd.DataFrame()
        df = pd.read_excel(buf, sheet_name=sheet_name, header=header,
                           nrows=nrows, engine="openpyxl")
        return df
    except Exception as e:
        st.error(f"خطأ في قراءة الشيت ({file_key} - {sheet_name}): {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_khazina():
    try:
        df = load_excel_from_drive("roaya_cash", "حركة الخزينة", header=1)
        if df.empty: return df
        df.columns = ["التاريخ", "البيان", "مدين", "دائن", "الرصيد", "النوع"]
        df = df.dropna(subset=["البيان"])
        df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce", origin="1899-12-30", unit="D")
        df["مدين"]   = pd.to_numeric(df["مدين"],   errors="coerce").fillna(0)
        df["دائن"]   = pd.to_numeric(df["دائن"],   errors="coerce").fillna(0)
        df["الرصيد"] = pd.to_numeric(df["الرصيد"], errors="coerce").fillna(0)
        df["النوع"]  = df["النوع"].fillna("أخرى").astype(str).str.strip()
        df = df[df["البيان"].astype(str).str.strip() != ""]
        df["الشهر"] = df["التاريخ"].dt.month
        df["السنة"] = df["التاريخ"].dt.year
        return df
    except Exception as e:
        st.error(f"خطأ في تحميل الخزينة: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_income_statement():
    try:
        return load_excel_from_drive("roaya_cash", "قائمة الدخل", header=1)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_expense_analysis():
    try:
        return load_excel_from_drive("roaya_cash", "تحليل مصروفات شهري", header=None)
    except:
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_suppliers():
    try:
        df = load_excel_from_drive("clients", "الموردين", header=2)
        if df.empty: return df
        df.columns = ["م", "رقم الفاتورة", "قيمة الفاتورة", "النسبة", "القيمة",
                      "تاريخ الفاتورة", "جهة الصدور", "العميل", "المورد"]
        df = df.dropna(subset=["رقم الفاتورة"])
        df["قيمة الفاتورة"] = pd.to_numeric(df["قيمة الفاتورة"], errors="coerce").fillna(0)
        df["القيمة"]        = pd.to_numeric(df["القيمة"],        errors="coerce").fillna(0)
        df["النسبة"]        = pd.to_numeric(df["النسبة"],        errors="coerce").fillna(0)
        df["تاريخ الفاتورة"] = pd.to_datetime(df["تاريخ الفاتورة"], errors="coerce",
                                               origin="1899-12-30", unit="D")
        return df
    except Exception as e:
        st.error(f"خطأ في الموردين: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_clients_list():
    try:
        df = load_excel_from_drive("clients", "قائمة الموردين والعملاء", header=0)
        if df.empty: return pd.DataFrame(), pd.DataFrame()
        clients   = df.iloc[:, :2].dropna(subset=[df.columns[0]])
        clients.columns = ["العميل", "النسبة"]
        suppliers = df.iloc[:, 2:4].dropna(subset=[df.columns[2]])
        suppliers.columns = ["المورد", "النسبة"]
        return clients, suppliers
    except Exception as e:
        st.error(f"خطأ في القوائم: {e}")
        return pd.DataFrame(), pd.DataFrame()

@st.cache_data(ttl=300)
def load_itqan():
    try:
        df = load_excel_from_drive("itqan", "كشف الحساب", header=4)
        if df.empty: return df
        df.columns = ["التاريخ", "البيان", "نوع الحركة", "سعر الصرف",
                      "مدين EGP", "دائن EGP", "مدين AED", "دائن AED", "الرصيد AED"]
        df = df.dropna(subset=["البيان"])
        df["التاريخ"] = pd.to_datetime(df["التاريخ"], errors="coerce",
                                        origin="1899-12-30", unit="D")
        for col in ["مدين EGP", "دائن EGP", "مدين AED", "دائن AED", "الرصيد AED"]:
            df[col] = pd.to_numeric(df[col], errors="coerce").fillna(0)
        df["سعر الصرف"] = pd.to_numeric(df["سعر الصرف"], errors="coerce").fillna(0)
        df = df[df["البيان"].astype(str).str.strip() != ""]
        return df
    except Exception as e:
        st.error(f"خطأ في اتقان: {e}")
        return pd.DataFrame()

@st.cache_data(ttl=300)
def load_itqan_summary():
    try:
        df = load_excel_from_drive("itqan", "كشف الحساب", header=0, nrows=3)
        summary = {}
        summary["مدين_egp"] = pd.to_numeric(df.iloc[0, 1], errors="coerce")
        summary["دائن_egp"] = pd.to_numeric(df.iloc[1, 1], errors="coerce")
        summary["رصيد_egp"] = pd.to_numeric(df.iloc[2, 1], errors="coerce")
        summary["مدين_aed"] = pd.to_numeric(df.iloc[0, 2], errors="coerce")
        summary["دائن_aed"] = pd.to_numeric(df.iloc[1, 2], errors="coerce")
        summary["رصيد_aed"] = pd.to_numeric(df.iloc[2, 2], errors="coerce")
        return summary
    except:
        return {}

MONTHS_AR = {
    1:"يناير", 2:"فبراير", 3:"مارس", 4:"أبريل",
    5:"مايو",  6:"يونيو",  7:"يوليو", 8:"أغسطس",
    9:"سبتمبر",10:"أكتوبر",11:"نوفمبر",12:"ديسمبر"
}

def fmt(n, decimals=0):
    if pd.isna(n): return "—"
    try:
        if decimals == 0:
            return f"{int(n):,}"
        return f"{n:,.{decimals}f}"
    except:
        return str(n)

def reload_all():
    st.cache_data.clear()
