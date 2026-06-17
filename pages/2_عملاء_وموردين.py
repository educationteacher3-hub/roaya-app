import streamlit as st
from auth import check_password, logout
import pandas as pd
from data_loader import load_clients_list, load_suppliers, fmt, reload_all

st.set_page_config(page_title="العملاء والموردين", page_icon="👥", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; }
#MainMenu { visibility: hidden; }
footer { visibility: hidden; }
header { visibility: hidden; }
[data-testid="stMetricValue"] { font-size: 16px !important; font-weight: 800 !important; white-space: nowrap; overflow: hidden; text-overflow: ellipsis; }
[data-testid="metric-container"] { background: white; border: 1px solid #d4dce5; border-radius: 10px; padding: 12px 14px; border-right: 4px solid #c8953a; }
.section-title { font-size: 14px; font-weight: 700; color: #0f1923; padding-right: 10px; border-right: 3px solid #c8953a; margin: 16px 0 10px; direction: rtl; }
.styled-table { width:100%; border-collapse:collapse; font-size:12px; direction:rtl; }
.styled-table thead tr { background:#0f1923; color:white; }
.styled-table thead th { padding:8px 10px; text-align:right; font-size:11px; white-space:nowrap; }
.styled-table tbody tr { border-bottom:1px solid #e8edf3; }
.styled-table tbody tr:hover { background:#f7f9fb; }
.styled-table tbody tr.total-row { background:#f0f4f8; font-weight:700; }
.styled-table tbody tr.net-pos { background:#e0f4f2; }
.styled-table tbody tr.net-neg { background:#fdecea; }
.styled-table tbody td { padding:7px 10px; color:#3a4a58; }
.num-pos { color:#1a7f74; font-weight:600; font-family:monospace; }
.num-neg { color:#c0392b; font-weight:600; font-family:monospace; }
.num { font-family:monospace; font-size:11.5px; }
.badge { display:inline-block; padding:2px 8px; border-radius:20px; font-size:10px; font-weight:600; }
.badge-green { background:#e0f4f2; color:#1a7f74; }
.badge-red { background:#fdecea; color:#c0392b; }
.badge-gold { background:#fdf3e3; color:#c8953a; }
.badge-blue { background:#e8f0f7; color:#1a5276; }
.badge-purple { background:#f5eef8; color:#6c3483; }
.badge-orange { background:#fef0e7; color:#d35400; }
@media (max-width: 768px) {
    [data-testid="stMetricValue"] { font-size: 12px !important; }
    .styled-table { font-size: 10px; }
    .styled-table thead th { padding: 5px; font-size: 9px; }
    .styled-table tbody td { padding: 4px 5px; }
}
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("👥 العملاء والموردين")

clients_list, suppliers_list = load_clients_list()
df_sup = load_suppliers()

# ===== تبويبات =====
tab1, tab2, tab3 = st.tabs(["👥 العملاء", "🏭 الموردين", "📋 تفاصيل الفواتير"])

# ===== تاب العملاء =====
with tab1:
    if not clients_list.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("عدد العملاء", f"{len(clients_list)}")
        with col2:
            avg_rate = (clients_list["النسبة"].mean() * 100).round(2)
            st.metric("متوسط نسبة العمولة", f"{avg_rate}%")

        st.markdown("<div class='section-title'>قائمة العملاء ونسب العمولة</div>", unsafe_allow_html=True)

        search_c = st.text_input("🔍 بحث باسم العميل", key="search_client")
        cl = clients_list.copy()
        if search_c:
            cl = cl[cl["العميل"].astype(str).str.contains(search_c, na=False)]

        rows = ""
        for i, r in cl.reset_index(drop=True).iterrows():
            pct = f"{r['النسبة']*100:.1f}%"
            rows += f"""<tr>
              <td class='num' style='color:#7a8e9e'>{i+1}</td>
              <td><strong>{r['العميل']}</strong></td>
              <td class='num'>{pct}</td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr><th>#</th><th>اسم العميل</th><th>نسبة العمولة</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

# ===== تاب الموردين =====
with tab2:
    if not suppliers_list.empty:
        col1, col2 = st.columns([1, 1])
        with col1:
            st.metric("عدد الموردين", f"{len(suppliers_list)}")

        st.markdown("<div class='section-title'>قائمة الموردين ونسب العمولة</div>", unsafe_allow_html=True)

        rows = ""
        for i, r in suppliers_list.reset_index(drop=True).iterrows():
            pct = f"{r['النسبة']*100:.1f}%"
            rows += f"""<tr>
              <td class='num' style='color:#7a8e9e'>{i+1}</td>
              <td><strong>{r['المورد']}</strong></td>
              <td class='num'>{pct}</td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr><th>#</th><th>اسم المورد</th><th>نسبة العمولة</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

    # ملخص الموردين من الفواتير
    if not df_sup.empty:
        st.markdown("<div class='section-title'>ملخص الفواتير حسب المورد</div>", unsafe_allow_html=True)

        sup_summary = df_sup.groupby("المورد").agg(
            عدد_الفواتير=("رقم الفاتورة", "count"),
            إجمالي_الفواتير=("قيمة الفاتورة", "sum"),
            إجمالي_العمولة=("القيمة", "sum")
        ).reset_index().sort_values("إجمالي_الفواتير", ascending=False)

        rows = ""
        for _, r in sup_summary.iterrows():
            rows += f"""<tr>
              <td><strong>{r['المورد']}</strong></td>
              <td class='num'>{fmt(r['عدد_الفواتير'])}</td>
              <td class='num'>{fmt(r['إجمالي_الفواتير'])}</td>
              <td class='num-pos'>{fmt(r['إجمالي_العمولة'])}</td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr><th>المورد</th><th>عدد الفواتير</th><th>إجمالي الفواتير</th><th>إجمالي العمولة</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

# ===== تاب الفواتير =====
with tab3:
    if not df_sup.empty:
        st.markdown("<div class='section-title'>تفاصيل الفواتير</div>", unsafe_allow_html=True)

        col_f1, col_f2, col_f3 = st.columns(3)

        all_clients   = ["كل العملاء"]   + sorted(df_sup["العميل"].dropna().unique().tolist())
        all_suppliers = ["كل الموردين"] + sorted(df_sup["المورد"].dropna().unique().tolist())

        with col_f1:
            sel_client = st.selectbox("العميل", all_clients)
        with col_f2:
            sel_sup    = st.selectbox("المورد", all_suppliers)
        with col_f3:
            search_inv = st.text_input("🔍 بحث في البيان")

        filtered = df_sup.copy()
        if sel_client != "كل العملاء":
            filtered = filtered[filtered["العميل"] == sel_client]
        if sel_sup != "كل الموردين":
            filtered = filtered[filtered["المورد"] == sel_sup]
        if search_inv:
            filtered = filtered[filtered["العميل"].astype(str).str.contains(search_inv, na=False)]

        # إجماليات
        col_t1, col_t2, col_t3 = st.columns(3)
        with col_t1: st.metric("عدد الفواتير",       f"{len(filtered):,}")
        with col_t2: st.metric("إجمالي قيمة الفواتير", f"{fmt(filtered['قيمة الفاتورة'].sum())} ج")
        with col_t3: st.metric("إجمالي العمولة",      f"{fmt(filtered['القيمة'].sum())} ج")

        rows = ""
        for _, r in filtered.head(200).iterrows():
            date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
            sup = str(r["المورد"])
            badge = "badge-blue" if sup == "باسم" else ("badge-gold" if sup == "المتميز" else "badge-green")
            rows += f"""<tr>
              <td class='num'>{r['رقم الفاتورة']}</td>
              <td class='num'>{date_str}</td>
              <td>{r['العميل']}</td>
              <td><span class='badge {badge}'>{sup}</span></td>
              <td class='num'>{fmt(r['قيمة الفاتورة'])}</td>
              <td class='num'>{r['النسبة']*100:.1f}%</td>
              <td class='num-pos'>{fmt(r['القيمة'])}</td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th><th>المورد</th>
                     <th>قيمة الفاتورة</th><th>النسبة</th><th>العمولة</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

        if len(filtered) > 200:
            st.caption(f"تعرض أول 200 سجل من أصل {len(filtered):,}")

        if st.button("⬇ تصدير Excel", key="exp_inv"):
            import io
            buf = io.BytesIO()
            filtered.to_excel(buf, index=False, engine="openpyxl")
            st.download_button("📥 تحميل", buf.getvalue(),
                               file_name="الفواتير.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
