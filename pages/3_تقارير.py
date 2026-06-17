import streamlit as st
import pandas as pd
from auth import check_password, logout
from data_loader import load_khazina, load_excel_from_drive, fmt, MONTHS_AR

st.set_page_config(page_title="التقارير المالية", page_icon="📈", layout="wide")

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

st.title("📈 التقارير المالية")

df = load_khazina()
if df.empty:
    st.error("تعذّر تحميل البيانات.")
    st.stop()

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 قائمة الدخل",
    "📅 مقارنة الأشهر",
    "💸 تحليل المصروفات",
    "📈 تحليل مصروفات شهري",
    "📋 بيان الإيرادات"
])

# ===== تاب 1: قائمة الدخل =====
with tab1:
    years = sorted(df["السنة"].dropna().unique().astype(int).tolist())
    months_available = sorted(df["الشهر"].dropna().unique().astype(int).tolist())

    col_y, col_m = st.columns([1, 2])
    with col_y:
        sel_year = st.selectbox("السنة", years, index=len(years)-1)
    with col_m:
        month_names = [MONTHS_AR[m] for m in months_available]
        sel_month_name = st.selectbox("الشهر", month_names, index=len(month_names)-1)
        sel_month = {v: k for k, v in MONTHS_AR.items()}[sel_month_name]

    mask = (df["السنة"] == sel_year) & (df["الشهر"] == sel_month)
    df_month = df[mask]

    if df_month.empty:
        st.warning("لا توجد بيانات للشهر المختار.")
    else:
        revenue_types = df_month[df_month["مدين"] > 0].groupby("النوع")["مدين"].sum().sort_values(ascending=False)
        expense_types = df_month[df_month["دائن"] > 0].groupby("النوع")["دائن"].sum().sort_values(ascending=False)

        total_rev = revenue_types.sum()
        total_exp = expense_types.sum()
        net = total_rev - total_exp

        c1, c2, c3 = st.columns(3)
        with c1: st.metric("📥 إجمالي الإيرادات", f"{fmt(total_rev)} ج")
        with c2: st.metric("📤 إجمالي المصروفات", f"{fmt(total_exp)} ج")
        with c3: st.metric("📊 صافي الشهر", f"{fmt(net)} ج", delta=f"{fmt(net)} ج")

        col_rev, col_exp = st.columns(2)

        with col_rev:
            st.markdown("<div class='section-title'>📥 الإيرادات</div>", unsafe_allow_html=True)
            rows = ""
            for nوع, val in revenue_types.items():
                pct = (val / total_rev * 100) if total_rev > 0 else 0
                rows += f"<tr><td>{nوع}</td><td class='num'>{pct:.1f}%</td><td class='num-pos'>{fmt(val)}</td></tr>"
            rows += f"<tr class='total-row'><td><strong>الإجمالي</strong></td><td></td><td class='num-pos'><strong>{fmt(total_rev)}</strong></td></tr>"
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>البند</th><th>النسبة</th><th>القيمة</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        with col_exp:
            st.markdown("<div class='section-title'>📤 المصروفات</div>", unsafe_allow_html=True)
            rows = ""
            for nوع, val in expense_types.items():
                pct = (val / total_exp * 100) if total_exp > 0 else 0
                rows += f"<tr><td>{nوع}</td><td class='num'>{pct:.1f}%</td><td class='num-neg'>{fmt(val)}</td></tr>"
            rows += f"<tr class='total-row'><td><strong>الإجمالي</strong></td><td></td><td class='num-neg'><strong>{fmt(total_exp)}</strong></td></tr>"
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>البند</th><th>النسبة</th><th>القيمة</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        net_color = "#1a7f74" if net >= 0 else "#c0392b"
        net_label = "فائض ✅" if net >= 0 else "عجز ❌"
        sign = "+" if net >= 0 else ""
        st.markdown(f"""<div style="background:white;border:2px solid {net_color};border-radius:10px;
            padding:16px 20px;display:flex;justify-content:space-between;align-items:center;margin:16px 0">
            <span style="font-size:15px;font-weight:700">صافي {sel_month_name} {sel_year} — {net_label}</span>
            <span style="font-family:monospace;font-size:22px;font-weight:900;color:{net_color}">{sign}{fmt(net)} ج</span>
        </div>""", unsafe_allow_html=True)

# ===== تاب 2: مقارنة الأشهر =====
with tab2:
    years = sorted(df["السنة"].dropna().unique().astype(int).tolist())
    sel_year2 = st.selectbox("السنة", years, index=len(years)-1, key="year2")
    df_year = df[df["السنة"] == sel_year2]

    monthly = df_year.groupby("الشهر").agg(
        إيرادات=("مدين", "sum"),
        مصروفات=("دائن", "sum")
    ).reset_index()
    monthly["الشهر_اسم"] = monthly["الشهر"].map(MONTHS_AR)
    monthly["صافي"] = monthly["إيرادات"] - monthly["مصروفات"]
    monthly = monthly.sort_values("الشهر")

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("إجمالي إيرادات السنة",  f"{fmt(monthly['إيرادات'].sum())} ج")
    with c2: st.metric("إجمالي مصروفات السنة", f"{fmt(monthly['مصروفات'].sum())} ج")
    with c3: st.metric("صافي السنة",             f"{fmt(monthly['صافي'].sum())} ج")
    with c4:
        if len(monthly) > 0:
            best = monthly.loc[monthly["صافي"].idxmax(), "الشهر_اسم"]
            st.metric("أفضل شهر", best)

    st.markdown("<div class='section-title'>مقارنة شهرية</div>", unsafe_allow_html=True)

    rows = ""
    for _, r in monthly.iterrows():
        net_cls = "net-pos" if r["صافي"] >= 0 else "net-neg"
        nc = "num-pos" if r["صافي"] >= 0 else "num-neg"
        sign = "+" if r["صافي"] >= 0 else ""
        pct = abs(r["صافي"]/r["إيرادات"]*100) if r["إيرادات"] > 0 else 0
        rows += f"""<tr class='{net_cls}'>
          <td><strong>{r['الشهر_اسم']}</strong></td>
          <td class='num-pos'>{fmt(r['إيرادات'])}</td>
          <td class='num-neg'>{fmt(r['مصروفات'])}</td>
          <td class='{nc}'>{sign}{fmt(r['صافي'])}</td>
          <td class='num'>{pct:.1f}%</td>
        </tr>"""

    tot_rev = monthly["إيرادات"].sum()
    tot_exp = monthly["مصروفات"].sum()
    tot_net = monthly["صافي"].sum()
    nc_tot = "num-pos" if tot_net >= 0 else "num-neg"
    rows += f"""<tr class='total-row'>
      <td>الإجمالي</td>
      <td class='num-pos'>{fmt(tot_rev)}</td>
      <td class='num-neg'>{fmt(tot_exp)}</td>
      <td class='{nc_tot}'>{"+" if tot_net>=0 else ""}{fmt(tot_net)}</td>
      <td class='num'>—</td>
    </tr>"""

    st.markdown(f"""<table class='styled-table'>
      <thead><tr><th>الشهر</th><th>الإيرادات</th><th>المصروفات</th><th>الصافي</th><th>نسبة الصافي</th></tr></thead>
      <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

# ===== تاب 3: تحليل المصروفات =====
with tab3:
    col_y3, col_m3 = st.columns([1, 2])
    years = sorted(df["السنة"].dropna().unique().astype(int).tolist())
    months_available = sorted(df["الشهر"].dropna().unique().astype(int).tolist())
    with col_y3:
        sel_year3 = st.selectbox("السنة", ["كل السنوات"] + [str(y) for y in years], key="year3")
    with col_m3:
        sel_month3 = st.selectbox("الشهر", ["كل الشهور"] + [MONTHS_AR[m] for m in months_available], key="month3")

    df_exp = df[df["دائن"] > 0].copy()
    if sel_year3 != "كل السنوات":
        df_exp = df_exp[df_exp["السنة"] == int(sel_year3)]
    if sel_month3 != "كل الشهور":
        m3 = {v: k for k, v in MONTHS_AR.items()}[sel_month3]
        df_exp = df_exp[df_exp["الشهر"] == m3]

    exp_by_type = df_exp.groupby("النوع")["دائن"].sum().sort_values(ascending=False)
    total_exp3 = exp_by_type.sum()

    st.metric("إجمالي المصروفات", f"{fmt(total_exp3)} ج")

    rows = ""
    for nوع, val in exp_by_type.items():
        pct = (val / total_exp3 * 100) if total_exp3 > 0 else 0
        bar_w = int(pct)
        rows += f"""<tr>
          <td><strong>{nوع}</strong></td>
          <td class='num-neg'>{fmt(val)}</td>
          <td class='num'>{pct:.1f}%</td>
          <td><div style='background:#e8edf3;border-radius:4px;height:8px;width:150px;overflow:hidden'>
              <div style='height:100%;width:{bar_w}%;background:#c0392b;border-radius:4px'></div>
          </div></td>
        </tr>"""

    rows += f"""<tr class='total-row'>
      <td><strong>الإجمالي</strong></td>
      <td class='num-neg'><strong>{fmt(total_exp3)}</strong></td>
      <td class='num'>100%</td><td>—</td>
    </tr>"""

    st.markdown(f"""<table class='styled-table'>
      <thead><tr><th>نوع المصروف</th><th>القيمة</th><th>النسبة</th><th>التمثيل</th></tr></thead>
      <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

# ===== تاب 4: تحليل مصروفات شهري =====
with tab4:
    years = sorted(df["السنة"].dropna().unique().astype(int).tolist())
    sel_year4 = st.selectbox("السنة", ["كل السنوات"] + [str(y) for y in years], key="year4")

    df_pivot = df[df["دائن"] > 0].copy()
    if sel_year4 != "كل السنوات":
        df_pivot = df_pivot[df_pivot["السنة"] == int(sel_year4)]

    pivot = df_pivot.pivot_table(
        index="النوع", columns="الشهر", values="دائن", aggfunc="sum", fill_value=0
    )
    pivot.columns = [MONTHS_AR.get(int(c), c) for c in pivot.columns]
    pivot["الإجمالي"] = pivot.sum(axis=1)
    pivot = pivot.sort_values("الإجمالي", ascending=False)

    header_cols = "<th>النوع</th>" + "".join(f"<th>{c}</th>" for c in pivot.columns)
    rows_p = ""
    for nوع, r in pivot.iterrows():
        cells = f"<td><strong>{nوع}</strong></td>"
        for c in pivot.columns:
            val = r[c]
            cls = "num-neg" if c == "الإجمالي" else "num"
            cells += f"<td class='{cls}'>{fmt(val) if val>0 else '—'}</td>"
        rows_p += f"<tr>{cells}</tr>"

    st.markdown(f"""<div style='overflow-x:auto'>
    <table class='styled-table'>
      <thead><tr>{header_cols}</tr></thead>
      <tbody>{rows_p}</tbody>
    </table></div>""", unsafe_allow_html=True)

    if st.button("⬇ تصدير Excel"):
        import io
        buf = io.BytesIO()
        pivot.to_excel(buf, engine="openpyxl")
        st.download_button("📥 تحميل", buf.getvalue(),
                           file_name="تحليل_المصروفات.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ===== تاب 5: بيان الإيرادات =====
with tab5:
    try:
        df_bayan = load_excel_from_drive("roaya_cash", "بيان", header=0)
        if not df_bayan.empty:
            st.markdown("<div class='section-title'>بيان الإيرادات والمصروفات</div>", unsafe_allow_html=True)
            df_bayan = df_bayan.dropna(how='all')
            st.dataframe(df_bayan, use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد بيانات في شيت البيان")
    except Exception as e:
        st.error(f"خطأ في تحميل البيان: {e}")
