import streamlit as st
import pandas as pd
from data_loader import (
    load_khazina, load_itqan_summary, load_clients_list,
    load_itqan, fmt, reload_all, MONTHS_AR
)
from auth import check_password, logout

st.set_page_config(
    page_title="مكتب رؤية — النظام المالي",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

if not check_password():
    st.stop()

# ===== CSS =====
st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');

* { font-family: 'Cairo', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; }

/* Metric cards */
[data-testid="metric-container"] {
    background: white;
    border: 1px solid #d4dce5;
    border-radius: 10px;
    padding: 14px 18px;
    border-right: 4px solid #c8953a;
}
[data-testid="stMetricLabel"] { font-size: 12px !important; color: #7a8e9e !important; }
[data-testid="stMetricValue"] { font-size: 22px !important; font-weight: 800 !important; }

/* Sidebar */
[data-testid="stSidebar"] {
    background: #0f1923 !important;
}
[data-testid="stSidebar"] * { color: rgba(255,255,255,0.75) !important; }
[data-testid="stSidebar"] .stButton button {
    background: rgba(255,255,255,0.05) !important;
    border: none !important; width: 100% !important;
    text-align: right !important; color: rgba(255,255,255,0.7) !important;
    font-size: 13px !important; padding: 8px 12px !important;
    border-radius: 7px !important; margin-bottom: 3px !important;
}
[data-testid="stSidebar"] .stButton button:hover {
    background: rgba(200,149,58,0.2) !important;
    color: white !important;
}

/* Section headers */
.section-title {
    font-size: 15px; font-weight: 700; color: #0f1923;
    padding-right: 12px; border-right: 3px solid #c8953a;
    margin: 20px 0 12px; direction: rtl;
}

/* KPI banner */
.kpi-banner {
    background: linear-gradient(135deg, #0f1923 0%, #1a3a52 100%);
    color: white; border-radius: 12px; padding: 20px 24px;
    margin-bottom: 20px; display: flex;
    justify-content: space-between; align-items: center;
}

/* Table styling */
.styled-table {
    width: 100%; border-collapse: collapse;
    font-size: 13px; direction: rtl;
}
.styled-table thead tr { background: #0f1923; color: white; }
.styled-table thead th { padding: 10px 14px; text-align: right; font-size: 12px; }
.styled-table tbody tr { border-bottom: 1px solid #e8edf3; }
.styled-table tbody tr:hover { background: #f7f9fb; }
.styled-table tbody td { padding: 9px 14px; color: #3a4a58; }

.num-pos { color: #1a7f74; font-weight: 600; font-family: monospace; }
.num-neg { color: #c0392b; font-weight: 600; font-family: monospace; }
.num     { font-family: monospace; font-size: 12.5px; }

.badge { display: inline-block; padding: 2px 9px; border-radius: 20px; font-size: 11px; font-weight: 600; }
.badge-green  { background: #e0f4f2; color: #1a7f74; }
.badge-red    { background: #fdecea; color: #c0392b; }
.badge-gold   { background: #fdf3e3; color: #c8953a; }
.badge-blue   { background: #e8f0f7; color: #1a5276; }
.badge-purple { background: #f5eef8; color: #6c3483; }
</style>
""", unsafe_allow_html=True)

# ===== SIDEBAR =====
with st.sidebar:
    st.markdown("""
    <div style='padding:16px 0 20px; border-bottom:1px solid rgba(255,255,255,0.08); margin-bottom:10px;'>
        <div style='display:flex; align-items:center; gap:10px;'>
            <div style='width:38px;height:38px;background:#c8953a;border-radius:8px;
                        display:flex;align-items:center;justify-content:center;
                        font-size:18px;font-weight:900;color:#0f1923;'>ر</div>
            <div>
                <div style='font-size:15px;font-weight:700;color:white;'>مكتب رؤية</div>
                <div style='font-size:11px;color:rgba(255,255,255,0.4);'>النظام المالي</div>
            </div>
        </div>
    </div>
    """, unsafe_allow_html=True)

    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.3);padding:4px 8px;margin-bottom:4px;'>الرئيسية</div>", unsafe_allow_html=True)
    st.page_link("app.py",                      label="📊 لوحة التحكم")

    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.3);padding:8px 8px 4px;margin-bottom:4px;'>رؤية — مصر</div>", unsafe_allow_html=True)
    st.page_link("pages/1_خزينة.py",            label="🏦 حركة الخزينة")
    st.page_link("pages/2_عملاء_وموردين.py",    label="👥 العملاء والموردين")
    st.page_link("pages/3_تقارير.py",           label="📈 التقارير المالية")

    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.3);padding:8px 8px 4px;margin-bottom:4px;'>اتقان — الإمارات</div>", unsafe_allow_html=True)
    st.page_link("pages/4_اتقان.py",            label="🇦🇪 كشف الحساب")

    st.divider()
    if st.button("↻ تحديث البيانات", use_container_width=True):
        reload_all()
        st.success("تم التحديث!")

    st.markdown("<div style='font-size:11px;color:rgba(255,255,255,0.2);padding-top:10px;'>ROAYA__CASH.xlsx<br>حسابات_العملاء.xlsx<br>اتقان.xlsx</div>", unsafe_allow_html=True)

    st.divider()
    user_name = st.session_state.get('user_name', '')
    st.markdown(f"<div style='font-size:12px;color:rgba(255,255,255,0.5);padding:4px 8px;'>👤 {user_name}</div>", unsafe_allow_html=True)
    if st.button('🚪 تسجيل الخروج', use_container_width=True):
        logout()

# ===== MAIN CONTENT =====
st.title("📊 لوحة التحكم")

# تحميل البيانات
df_khazina = load_khazina()
itqan_summary = load_itqan_summary()
clients_list, suppliers_list = load_clients_list()

# ===== KPIs =====
col1, col2, col3, col4 = st.columns(4)

if not df_khazina.empty:
    total_in  = df_khazina["مدين"].sum()
    total_out = df_khazina["دائن"].sum()
    balance   = df_khazina["الرصيد"].iloc[-1] if len(df_khazina) > 0 else 0

    with col1:
        st.metric("💰 رصيد الخزينة", f"{fmt(balance)} ج")
    with col2:
        st.metric("📥 إجمالي الإيرادات", f"{fmt(total_in)} ج")
    with col3:
        st.metric("📤 إجمالي المصروفات", f"{fmt(total_out)} ج")
    with col4:
        rصيد_aed = itqan_summary.get("رصيد_aed", 0)
        color = "normal" if rصيد_aed >= 0 else "inverse"
        st.metric("🇦🇪 رصيد اتقان (AED)", f"{fmt(rصيد_aed, 2)} د.إ")

# ===== الملخص الشهري =====
st.markdown("<div class='section-title'>الملخص الشهري — إيرادات ومصروفات</div>", unsafe_allow_html=True)

if not df_khazina.empty:
    monthly = df_khazina.groupby(["السنة", "الشهر"]).agg(
        إيرادات=("مدين", "sum"),
        مصروفات=("دائن", "sum")
    ).reset_index()
    monthly["الشهر_اسم"] = monthly["الشهر"].map(MONTHS_AR)
    monthly["صافي"] = monthly["إيرادات"] - monthly["مصروفات"]
    monthly = monthly.sort_values(["السنة", "الشهر"]).tail(12)

    # عرض جدول شهري
    rows = ""
    for _, r in monthly.iterrows():
        net_class = "num-pos" if r["صافي"] >= 0 else "num-neg"
        net_sign  = "+" if r["صافي"] >= 0 else ""
        rows += f"""
        <tr>
          <td>{r['الشهر_اسم']} {int(r['السنة'])}</td>
          <td class='num-pos'>{fmt(r['إيرادات'])}</td>
          <td class='num-neg'>{fmt(r['مصروفات'])}</td>
          <td class='{net_class}'>{net_sign}{fmt(r['صافي'])}</td>
        </tr>"""

    st.markdown(f"""
    <table class='styled-table'>
      <thead><tr><th>الشهر</th><th>الإيرادات</th><th>المصروفات</th><th>الصافي</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

# ===== آخر حركات الخزينة =====
st.markdown("<div class='section-title'>آخر 10 حركات في الخزينة</div>", unsafe_allow_html=True)

if not df_khazina.empty:
    last10 = df_khazina.tail(10).iloc[::-1]

    TYPE_BADGE = {
        "عملاء فواتير":   "badge-green",
        "تحصيل اتعاب":    "badge-green",
        "ارصدة عملاء":    "badge-gold",
        "مرتبات":         "badge-red",
        "سداد موردين":    "badge-red",
        "عمولات":         "badge-blue",
        "جاري شركاء":     "badge-purple",
        "انتقالات":        "badge-red",
    }

    rows = ""
    for _, r in last10.iterrows():
        date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
        nوع = str(r["النوع"])
        badge_cls = TYPE_BADGE.get(nوع, "badge-blue")
        debit  = f"<span class='num-pos'>{fmt(r['مدين'])}</span>" if r["مدين"] > 0 else "—"
        credit = f"<span class='num-neg'>{fmt(r['دائن'])}</span>" if r["دائن"] > 0 else "—"
        rows += f"""
        <tr>
          <td class='num'>{date_str}</td>
          <td>{r['البيان']}</td>
          <td><span class='badge {badge_cls}'>{nوع}</span></td>
          <td>{debit}</td>
          <td>{credit}</td>
          <td class='num'>{fmt(r['الرصيد'])}</td>
        </tr>"""

    st.markdown(f"""
    <table class='styled-table'>
      <thead><tr><th>التاريخ</th><th>البيان</th><th>النوع</th><th>مدين</th><th>دائن</th><th>الرصيد</th></tr></thead>
      <tbody>{rows}</tbody>
    </table>""", unsafe_allow_html=True)

# ===== العملاء والموردين =====
col_c, col_s = st.columns(2)

with col_c:
    st.markdown("<div class='section-title'>قائمة العملاء</div>", unsafe_allow_html=True)
    if not clients_list.empty:
        clients_list["النسبة %"] = (clients_list["النسبة"] * 100).round(2).astype(str) + "%"
        st.dataframe(
            clients_list[["العميل", "النسبة %"]],
            use_container_width=True, hide_index=True
        )

with col_s:
    st.markdown("<div class='section-title'>قائمة الموردين</div>", unsafe_allow_html=True)
    if not suppliers_list.empty:
        suppliers_list["النسبة %"] = (suppliers_list["النسبة"] * 100).round(2).astype(str) + "%"
        st.dataframe(
            suppliers_list[["المورد", "النسبة %"]],
            use_container_width=True, hide_index=True
        )
