import streamlit as st
from auth import check_password, logout
import pandas as pd
from data_loader import load_khazina, fmt, reload_all, MONTHS_AR

st.set_page_config(page_title="حركة الخزينة", page_icon="🏦", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; }
[data-testid="metric-container"] {
    background: white; border: 1px solid #d4dce5;
    border-radius: 10px; padding: 14px 18px; border-right: 4px solid #c8953a;
}
.section-title {
    font-size: 15px; font-weight: 700; color: #0f1923;
    padding-right: 12px; border-right: 3px solid #c8953a;
    margin: 20px 0 12px; direction: rtl;
}
.styled-table { width:100%; border-collapse:collapse; font-size:13px; direction:rtl; }
.styled-table thead tr { background:#0f1923; color:white; }
.styled-table thead th { padding:10px 14px; text-align:right; font-size:12px; }
.styled-table tbody tr { border-bottom:1px solid #e8edf3; }
.styled-table tbody tr:hover { background:#f7f9fb; }
.styled-table tbody td { padding:9px 14px; color:#3a4a58; }
.num-pos { color:#1a7f74; font-weight:600; font-family:monospace; }
.num-neg { color:#c0392b; font-weight:600; font-family:monospace; }
.num { font-family:monospace; font-size:12.5px; }
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-green  { background:#e0f4f2; color:#1a7f74; }
.badge-red    { background:#fdecea; color:#c0392b; }
.badge-gold   { background:#fdf3e3; color:#c8953a; }
.badge-blue   { background:#e8f0f7; color:#1a5276; }
.badge-purple { background:#f5eef8; color:#6c3483; }
.badge-orange { background:#fef0e7; color:#d35400; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("🏦 حركة الخزينة")

df = load_khazina()

if df.empty:
    st.error("تعذّر تحميل بيانات الخزينة. تأكد من مسار الملف في data_loader.py")
    st.stop()

# ===== KPIs =====
balance   = df["الرصيد"].iloc[-1]
total_in  = df["مدين"].sum()
total_out = df["دائن"].sum()
net       = total_in - total_out

col1, col2, col3, col4, col5 = st.columns(5)
with col1: st.metric("💰 الرصيد الحالي",       f"{fmt(balance)} ج")
with col2: st.metric("📥 إجمالي الإيرادات",    f"{fmt(total_in)} ج")
with col3: st.metric("📤 إجمالي المصروفات",   f"{fmt(total_out)} ج")
with col4: st.metric("📊 صافي الفترة",         f"{fmt(net)} ج")
with col5: st.metric("🔢 عدد الحركات",         f"{len(df):,}")

# ===== الملخص الشهري =====
st.markdown("<div class='section-title'>الملخص الشهري</div>", unsafe_allow_html=True)

monthly = df.groupby(["السنة", "الشهر"]).agg(
    إيرادات=("مدين", "sum"),
    مصروفات=("دائن", "sum")
).reset_index()
monthly["الشهر_اسم"] = monthly["الشهر"].map(MONTHS_AR)
monthly["صافي"] = monthly["إيرادات"] - monthly["مصروفات"]

rows = ""
for _, r in monthly.sort_values(["السنة","الشهر"]).iterrows():
    net_class = "num-pos" if r["صافي"] >= 0 else "num-neg"
    sign = "+" if r["صافي"] >= 0 else ""
    rows += f"""<tr>
      <td>{r['الشهر_اسم']} {int(r['السنة'])}</td>
      <td class='num-pos'>{fmt(r['إيرادات'])}</td>
      <td class='num-neg'>{fmt(r['مصروفات'])}</td>
      <td class='{net_class}'>{sign}{fmt(r['صافي'])}</td>
    </tr>"""

st.markdown(f"""
<table class='styled-table'>
  <thead><tr><th>الشهر</th><th>الإيرادات</th><th>المصروفات</th><th>الصافي</th></tr></thead>
  <tbody>{rows}</tbody>
</table>""", unsafe_allow_html=True)

# ===== فلاتر =====
st.markdown("<div class='section-title'>الحركات التفصيلية</div>", unsafe_allow_html=True)

col_f1, col_f2, col_f3, col_f4 = st.columns([2, 2, 2, 2])

years  = sorted(df["السنة"].dropna().unique().astype(int).tolist())
months = ["كل الشهور"] + [MONTHS_AR[m] for m in sorted(df["الشهر"].dropna().unique().astype(int).tolist())]
types  = ["كل الأنواع"] + sorted(df["النوع"].unique().tolist())
dirs   = ["الكل", "إيرادات فقط", "مصروفات فقط"]

with col_f1:
    sel_year = st.selectbox("السنة", ["كل السنوات"] + [str(y) for y in years])
with col_f2:
    sel_month = st.selectbox("الشهر", months)
with col_f3:
    sel_type = st.selectbox("نوع الحركة", types)
with col_f4:
    sel_dir = st.selectbox("الاتجاه", dirs)

search = st.text_input("🔍 بحث في البيان")

# تطبيق الفلاتر
filtered = df.copy()

if sel_year != "كل السنوات":
    filtered = filtered[filtered["السنة"] == int(sel_year)]

if sel_month != "كل الشهور":
    month_num = {v: k for k, v in MONTHS_AR.items()}[sel_month]
    filtered = filtered[filtered["الشهر"] == month_num]

if sel_type != "كل الأنواع":
    filtered = filtered[filtered["النوع"] == sel_type]

if sel_dir == "إيرادات فقط":
    filtered = filtered[filtered["مدين"] > 0]
elif sel_dir == "مصروفات فقط":
    filtered = filtered[filtered["دائن"] > 0]

if search:
    filtered = filtered[filtered["البيان"].astype(str).str.contains(search, na=False)]

# إجماليات الفلتر
col_t1, col_t2, col_t3 = st.columns(3)
with col_t1: st.metric("إجمالي إيرادات الفلتر", f"{fmt(filtered['مدين'].sum())} ج")
with col_t2: st.metric("إجمالي مصروفات الفلتر", f"{fmt(filtered['دائن'].sum())} ج")
with col_t3:
    net_f = filtered["مدين"].sum() - filtered["دائن"].sum()
    st.metric("صافي الفلتر", f"{fmt(net_f)} ج")

# الجدول
TYPE_BADGE = {
    "عملاء فواتير": "badge-green", "تحصيل اتعاب": "badge-green",
    "ارصدة عملاء":  "badge-gold",  "مرتبات":       "badge-red",
    "سداد موردين":  "badge-red",   "عمولات":       "badge-blue",
    "جاري شركاء":   "badge-purple","انتقالات":     "badge-orange",
}

rows = ""
for _, r in filtered.iloc[::-1].iterrows():
    date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
    nوع = str(r["النوع"])
    badge_cls = TYPE_BADGE.get(nوع, "badge-blue")
    debit  = f"<span class='num-pos'>{fmt(r['مدين'])}</span>" if r["مدين"] > 0 else "—"
    credit = f"<span class='num-neg'>{fmt(r['دائن'])}</span>" if r["دائن"] > 0 else "—"
    rows += f"""<tr>
      <td class='num'>{date_str}</td>
      <td>{str(r['البيان'])[:60]}</td>
      <td><span class='badge {badge_cls}'>{nوع}</span></td>
      <td>{debit}</td><td>{credit}</td>
      <td class='num'>{fmt(r['الرصيد'])}</td>
    </tr>"""

st.markdown(f"""
<table class='styled-table'>
  <thead><tr><th>التاريخ</th><th>البيان</th><th>النوع</th><th>مدين ↑</th><th>دائن ↓</th><th>الرصيد</th></tr></thead>
  <tbody>{rows}</tbody>
</table>""", unsafe_allow_html=True)

st.caption(f"إجمالي السجلات: {len(filtered):,}")

# تصدير
if st.button("⬇ تصدير Excel"):
    import io
    buf = io.BytesIO()
    filtered.to_excel(buf, index=False, engine="openpyxl")
    st.download_button("📥 تحميل الملف", buf.getvalue(),
                       file_name="حركة_الخزينة.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
