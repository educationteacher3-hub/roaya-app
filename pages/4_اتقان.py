import streamlit as st
from auth import check_password, logout
import pandas as pd
from data_loader import load_itqan, load_itqan_summary, fmt

st.set_page_config(page_title="اتقان — الإمارات", page_icon="🇦🇪", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; }
[data-testid="metric-container"] {
    background: white; border: 1px solid #d4dce5;
    border-radius: 10px; padding: 14px 18px; border-right: 4px solid #1a5276;
}
.section-title {
    font-size: 15px; font-weight: 700; color: #0f1923;
    padding-right: 12px; border-right: 3px solid #1a5276;
    margin: 20px 0 12px; direction: rtl;
}
.styled-table { width:100%; border-collapse:collapse; font-size:13px; direction:rtl; }
.styled-table thead tr { background:#1a5276; color:white; }
.styled-table thead th { padding:10px 14px; text-align:right; font-size:12px; white-space:nowrap; }
.styled-table tbody tr { border-bottom:1px solid #e8edf3; }
.styled-table tbody tr:hover { background:#f7f9fb; }
.styled-table tbody td { padding:9px 14px; color:#3a4a58; }
.num-pos { color:#1a7f74; font-weight:600; font-family:monospace; }
.num-neg { color:#c0392b; font-weight:600; font-family:monospace; }
.num { font-family:monospace; font-size:12px; }
.badge { display:inline-block; padding:2px 9px; border-radius:20px; font-size:11px; font-weight:600; }
.badge-green { background:#e0f4f2; color:#1a7f74; }
.badge-red   { background:#fdecea; color:#c0392b; }
.itqan-banner {
    background: linear-gradient(135deg, #1a5276 0%, #0d3b5c 100%);
    color: white; border-radius: 12px; padding: 22px 28px;
    margin-bottom: 20px; display:flex; justify-content:space-between; align-items:center;
}
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("🇦🇪 اتقان — كشف الحساب")

df  = load_itqan()
summary = load_itqan_summary()

if df.empty:
    st.error("تعذّر تحميل بيانات اتقان. تأكد من اسم الشيت في ملف اتقان.")
    st.stop()

# ===== البانر =====
رصيد_aed = summary.get("رصيد_aed", 0)
رصيد_egp = summary.get("رصيد_egp", 0)
rcolor    = "#ff6b6b" if رصيد_aed < 0 else "#7dcea0"

st.markdown(f"""
<div class='itqan-banner'>
  <div>
    <div style='font-size:18px;font-weight:800;'>🇦🇪 شركة اتقان — حساب حورس</div>
    <div style='font-size:13px;opacity:0.6;margin-top:4px'>كشف حساب بالدرهم الإماراتي والجنيه المصري</div>
  </div>
  <div style='text-align:left'>
    <div style='font-size:11px;opacity:0.5;margin-bottom:3px'>الرصيد الحالي</div>
    <div style='font-family:monospace;font-size:26px;font-weight:900;color:{rcolor}'>{fmt(رصيد_aed,2)} AED</div>
    <div style='font-family:monospace;font-size:14px;color:rgba(255,255,255,0.5);margin-top:3px'>{fmt(رصيد_egp,2)} EGP</div>
  </div>
</div>""", unsafe_allow_html=True)

# ===== KPIs =====
مدين_aed = summary.get("مدين_aed", df["مدين AED"].sum())
دائن_aed = summary.get("دائن_aed", df["دائن AED"].sum())
avg_rate  = df[df["سعر الصرف"] > 0]["سعر الصرف"].mean()

c1, c2, c3, c4 = st.columns(4)
with c1: st.metric("📥 إجمالي الإيداعات (AED)",   f"{fmt(مدين_aed, 2)}")
with c2: st.metric("📤 إجمالي المصروفات (AED)",   f"{fmt(دائن_aed, 2)}")
with c3: st.metric("🔢 عدد الحركات",               f"{len(df):,}")
with c4: st.metric("💱 متوسط سعر الصرف",           f"{avg_rate:.2f} ج/د.إ")

# ===== فلاتر =====
st.markdown("<div class='section-title'>كشف الحساب التفصيلي</div>", unsafe_allow_html=True)

col_f1, col_f2, col_f3 = st.columns(3)
with col_f1:
    sel_dir = st.selectbox("نوع الحركة", ["الكل", "إيداعات فقط", "مصروفات فقط"])
with col_f2:
    search  = st.text_input("🔍 بحث في البيان")
with col_f3:
    sel_sort = st.selectbox("ترتيب", ["الأحدث أولاً", "الأقدم أولاً", "الأعلى قيمة"])

# تطبيق
filtered = df.copy()
if sel_dir == "إيداعات فقط":
    filtered = filtered[filtered["مدين AED"] > 0]
elif sel_dir == "مصروفات فقط":
    filtered = filtered[filtered["دائن AED"] > 0]

if search:
    filtered = filtered[filtered["البيان"].astype(str).str.contains(search, na=False)]

if sel_sort == "الأحدث أولاً":
    filtered = filtered.sort_values("التاريخ", ascending=False)
elif sel_sort == "الأقدم أولاً":
    filtered = filtered.sort_values("التاريخ", ascending=True)
elif sel_sort == "الأعلى قيمة":
    filtered["_max"] = filtered[["مدين AED", "دائن AED"]].max(axis=1)
    filtered = filtered.sort_values("_max", ascending=False)

# إجماليات الفلتر
ct1, ct2, ct3 = st.columns(3)
with ct1: st.metric("إيداعات الفلتر (AED)", f"{fmt(filtered['مدين AED'].sum(), 2)}")
with ct2: st.metric("مصروفات الفلتر (AED)", f"{fmt(filtered['دائن AED'].sum(), 2)}")
with ct3:
    net_f = filtered["مدين AED"].sum() - filtered["دائن AED"].sum()
    st.metric("صافي الفلتر (AED)", f"{fmt(net_f, 2)}")

# ===== الجدول =====
rows = ""
for _, r in filtered.iterrows():
    date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
    is_in  = r["مدين AED"] > 0
    badge  = "<span class='badge badge-green'>إيداع</span>" if is_in else "<span class='badge badge-red'>صرف</span>"
    debit_aed  = f"<span class='num-pos'>{fmt(r['مدين AED'],2)}</span>" if r["مدين AED"] > 0 else "—"
    credit_aed = f"<span class='num-neg'>{fmt(r['دائن AED'],2)}</span>" if r["دائن AED"] > 0 else "—"
    debit_egp  = f"<span class='num-pos'>{fmt(r['مدين EGP'],2)}</span>" if r["مدين EGP"] > 0 else "—"
    credit_egp = f"<span class='num-neg'>{fmt(r['دائن EGP'],2)}</span>" if r["دائن EGP"] > 0 else "—"
    bal_cls = "num-neg" if r["الرصيد AED"] < 0 else "num-pos"
    rate    = f"{r['سعر الصرف']:.2f}" if r["سعر الصرف"] > 0 else "—"

    rows += f"""<tr>
      <td class='num'>{date_str}</td>
      <td>{str(r['البيان'])[:55]}</td>
      <td>{badge}</td>
      <td class='num'>{rate}</td>
      <td>{debit_aed}</td>
      <td>{credit_aed}</td>
      <td>{debit_egp}</td>
      <td>{credit_egp}</td>
      <td class='{bal_cls}'>{fmt(r['الرصيد AED'],2)}</td>
    </tr>"""

st.markdown(f"""
<div style='overflow-x:auto'>
<table class='styled-table'>
  <thead><tr>
    <th>التاريخ</th><th>البيان</th><th>النوع</th><th>سعر الصرف</th>
    <th>مدين AED</th><th>دائن AED</th>
    <th>مدين EGP</th><th>دائن EGP</th>
    <th>الرصيد AED</th>
  </tr></thead>
  <tbody>{rows}</tbody>
</table>
</div>""", unsafe_allow_html=True)

st.caption(f"إجمالي السجلات: {len(filtered):,}")

# ===== توزيع المصروفات =====
st.markdown("<div class='section-title'>توزيع المصروفات حسب النوع</div>", unsafe_allow_html=True)

if "نوع الحركة" in df.columns:
    exp_df = df[df["دائن AED"] > 0].copy()
    if not exp_df.empty:
        by_type = exp_df.groupby("نوع الحركة")["دائن AED"].sum().sort_values(ascending=False)
        total_e = by_type.sum()
        rows_t  = ""
        for t, v in by_type.items():
            pct = v / total_e * 100 if total_e > 0 else 0
            rows_t += f"""<tr>
              <td><strong>{t}</strong></td>
              <td class='num-neg'>{fmt(v,2)} AED</td>
              <td class='num'>{pct:.1f}%</td>
              <td><div style='background:#e8edf3;border-radius:4px;height:7px;width:120px;overflow:hidden'>
                  <div style='height:100%;width:{int(pct)}%;background:#c0392b;border-radius:4px'></div>
              </div></td>
            </tr>"""
        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr><th>النوع</th><th>القيمة (AED)</th><th>النسبة</th><th>التمثيل</th></tr></thead>
          <tbody>{rows_t}</tbody>
        </table>""", unsafe_allow_html=True)

# تصدير
if st.button("⬇ تصدير Excel"):
    import io
    buf = io.BytesIO()
    filtered.drop(columns=["_max"], errors="ignore").to_excel(buf, index=False, engine="openpyxl")
    st.download_button("📥 تحميل", buf.getvalue(),
                       file_name="اتقان_كشف_الحساب.xlsx",
                       mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
