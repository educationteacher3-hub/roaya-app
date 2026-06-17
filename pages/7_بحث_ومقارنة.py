import streamlit as st
import pandas as pd
import io
from auth import check_password
from data_loader import load_khazina, load_suppliers, load_itqan, fmt, MONTHS_AR

st.set_page_config(page_title="بحث ومقارنة", page_icon="🔍", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
[data-testid="metric-container"] { background:white; border:1px solid #d4dce5; border-radius:10px; padding:12px 14px; border-right:4px solid #c8953a; }
[data-testid="stMetricValue"] { font-size:16px !important; font-weight:800 !important; }
.section-title { font-size:14px; font-weight:700; color:#0f1923; padding-right:10px; border-right:3px solid #c8953a; margin:16px 0 10px; direction:rtl; }
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
.result-source { display:inline-block; padding:2px 8px; border-radius:10px; font-size:10px; font-weight:600; margin-left:6px; }
.src-khazina { background:#e0f4f2; color:#1a7f74; }
.src-invoices { background:#e8f0f7; color:#1a5276; }
.src-itqan { background:#f5eef8; color:#6c3483; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("🔍 البحث والمقارنة")

tab1, tab2 = st.tabs(["🔍 البحث العالمي", "📅 مقارنة الفترات"])

# ===== تحميل البيانات =====
df_khazina  = load_khazina()
df_invoices = load_suppliers()
df_itqan    = load_itqan()

# ===== تاب 1: البحث العالمي =====
with tab1:
    st.markdown("<div class='section-title'>ابحث في كل البيانات مرة واحدة</div>", unsafe_allow_html=True)

    search_query = st.text_input("🔍 اكتب اسم عميل أو مورد أو رقم فاتورة أو أي كلمة",
                                  placeholder="مثال: رشوان، باسم، 441، تحصيل...")

    if search_query and len(search_query) >= 2:
        results_count = 0

        # بحث في الخزينة
        if not df_khazina.empty:
            mask = df_khazina["البيان"].astype(str).str.contains(search_query, case=False, na=False)
            kh_results = df_khazina[mask]
            if not kh_results.empty:
                st.markdown(f"<div class='section-title'>🏦 نتائج الخزينة ({len(kh_results)} نتيجة)</div>", unsafe_allow_html=True)
                rows = ""
                for _, r in kh_results.tail(50).iterrows():
                    date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                    debit  = f"<span class='num-pos'>{fmt(r['مدين'])}</span>" if r["مدين"] > 0 else "—"
                    credit = f"<span class='num-neg'>{fmt(r['دائن'])}</span>" if r["دائن"] > 0 else "—"
                    rows += f"""<tr>
                      <td class='num'>{date_str}</td>
                      <td>{r['البيان']}</td>
                      <td><span class='result-source src-khazina'>خزينة</span></td>
                      <td>{debit}</td><td>{credit}</td>
                      <td class='num'>{fmt(r['الرصيد'])}</td>
                    </tr>"""
                st.markdown(f"""<table class='styled-table'>
                  <thead><tr><th>التاريخ</th><th>البيان</th><th>المصدر</th><th>مدين</th><th>دائن</th><th>الرصيد</th></tr></thead>
                  <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
                results_count += len(kh_results)

        # بحث في الفواتير
        if not df_invoices.empty:
            mask = (
                df_invoices["العميل"].astype(str).str.contains(search_query, case=False, na=False) |
                df_invoices["المورد"].astype(str).str.contains(search_query, case=False, na=False) |
                df_invoices["رقم الفاتورة"].astype(str).str.contains(search_query, case=False, na=False)
            )
            inv_results = df_invoices[mask]
            if not inv_results.empty:
                st.markdown(f"<div class='section-title'>📋 نتائج الفواتير ({len(inv_results)} نتيجة)</div>", unsafe_allow_html=True)
                rows = ""
                for _, r in inv_results.head(100).iterrows():
                    date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
                    rows += f"""<tr>
                      <td class='num'>{r['رقم الفاتورة']}</td>
                      <td class='num'>{date_str}</td>
                      <td>{r['العميل']}</td>
                      <td>{r['المورد']}</td>
                      <td class='num'>{fmt(r['قيمة الفاتورة'])}</td>
                      <td class='num-pos'>{fmt(r['القيمة'])}</td>
                    </tr>"""
                st.markdown(f"""<table class='styled-table'>
                  <thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th><th>المورد</th><th>قيمة الفاتورة</th><th>العمولة</th></tr></thead>
                  <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
                results_count += len(inv_results)

        # بحث في اتقان
        if not df_itqan.empty:
            mask = df_itqan["البيان"].astype(str).str.contains(search_query, case=False, na=False)
            itqan_results = df_itqan[mask]
            if not itqan_results.empty:
                st.markdown(f"<div class='section-title'>🇦🇪 نتائج اتقان ({len(itqan_results)} نتيجة)</div>", unsafe_allow_html=True)
                rows = ""
                for _, r in itqan_results.iterrows():
                    date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                    debit  = f"<span class='num-pos'>{fmt(r['مدين AED'],2)}</span>" if r["مدين AED"] > 0 else "—"
                    credit = f"<span class='num-neg'>{fmt(r['دائن AED'],2)}</span>" if r["دائن AED"] > 0 else "—"
                    rows += f"""<tr>
                      <td class='num'>{date_str}</td>
                      <td>{r['البيان']}</td>
                      <td><span class='result-source src-itqan'>اتقان</span></td>
                      <td>{debit}</td><td>{credit}</td>
                    </tr>"""
                st.markdown(f"""<table class='styled-table'>
                  <thead><tr><th>التاريخ</th><th>البيان</th><th>المصدر</th><th>مدين AED</th><th>دائن AED</th></tr></thead>
                  <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
                results_count += len(itqan_results)

        if results_count == 0:
            st.warning(f"لا توجد نتائج لـ '{search_query}'")
        else:
            st.success(f"إجمالي النتائج: {results_count}")

    elif search_query:
        st.info("اكتب على الأقل حرفين للبحث")

# ===== تاب 2: مقارنة الفترات =====
with tab2:
    st.markdown("<div class='section-title'>قارن بين فترتين أو سنتين</div>", unsafe_allow_html=True)

    if not df_khazina.empty:
        years = sorted(df_khazina["السنة"].dropna().unique().astype(int).tolist())

        col1, col2 = st.columns(2)
        with col1:
            st.markdown("**📅 الفترة الأولى**")
            y1 = st.selectbox("السنة", years, key="y1")
            months_ar_list = [MONTHS_AR[m] for m in range(1, 13)]
            m1_from = st.selectbox("من شهر", months_ar_list, key="m1f")
            m1_to   = st.selectbox("إلى شهر", months_ar_list, index=11, key="m1t")

        with col2:
            st.markdown("**📅 الفترة الثانية**")
            y2 = st.selectbox("السنة", years, index=len(years)-1 if len(years)>1 else 0, key="y2")
            m2_from = st.selectbox("من شهر", months_ar_list, key="m2f")
            m2_to   = st.selectbox("إلى شهر", months_ar_list, index=11, key="m2t")

        rev_map = {v: k for k, v in MONTHS_AR.items()}
        m1f_n, m1t_n = rev_map[m1_from], rev_map[m1_to]
        m2f_n, m2t_n = rev_map[m2_from], rev_map[m2t]

        p1 = df_khazina[(df_khazina["السنة"]==y1) & (df_khazina["الشهر"].between(m1f_n, m1t_n))]
        p2 = df_khazina[(df_khazina["السنة"]==y2) & (df_khazina["الشهر"].between(m2f_n, m2t_n))]

        p1_rev = p1["مدين"].sum()
        p1_exp = p1["دائن"].sum()
        p1_net = p1_rev - p1_exp

        p2_rev = p2["مدين"].sum()
        p2_exp = p2["دائن"].sum()
        p2_net = p2_rev - p2_exp

        st.markdown("<div class='section-title'>نتيجة المقارنة</div>", unsafe_allow_html=True)

        def diff_pct(a, b):
            if b == 0: return "—"
            pct = (a - b) / b * 100
            sign = "+" if pct > 0 else ""
            color = "#1a7f74" if pct > 0 else "#c0392b"
            return f"<span style='color:{color};font-weight:700'>{sign}{pct:.1f}%</span>"

        rows = f"""
        <tr>
          <td><strong>الإيرادات</strong></td>
          <td class='num-pos'>{fmt(p1_rev)}</td>
          <td class='num-pos'>{fmt(p2_rev)}</td>
          <td>{diff_pct(p2_rev, p1_rev)}</td>
        </tr>
        <tr>
          <td><strong>المصروفات</strong></td>
          <td class='num-neg'>{fmt(p1_exp)}</td>
          <td class='num-neg'>{fmt(p2_exp)}</td>
          <td>{diff_pct(p2_exp, p1_exp)}</td>
        </tr>
        <tr class='total-row'>
          <td><strong>الصافي</strong></td>
          <td class='{"num-pos" if p1_net>=0 else "num-neg"}'>{fmt(p1_net)}</td>
          <td class='{"num-pos" if p2_net>=0 else "num-neg"}'>{fmt(p2_net)}</td>
          <td>{diff_pct(p2_net, p1_net)}</td>
        </tr>"""

        st.markdown(f"""<table class='styled-table'>
          <thead><tr>
            <th>البند</th>
            <th>الفترة الأولى ({m1_from}→{m1_to} {y1})</th>
            <th>الفترة الثانية ({m2_from}→{m2_to} {y2})</th>
            <th>التغيير</th>
          </tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # مقارنة شهرية
        st.markdown("<div class='section-title'>المقارنة الشهرية التفصيلية</div>", unsafe_allow_html=True)

        monthly1 = p1.groupby("الشهر").agg(إيرادات=("مدين","sum"), مصروفات=("دائن","sum")).reset_index()
        monthly2 = p2.groupby("الشهر").agg(إيرادات=("مدين","sum"), مصروفات=("دائن","sum")).reset_index()

        rows = ""
        for m in range(1, 13):
            r1 = monthly1[monthly1["الشهر"]==m]
            r2 = monthly2[monthly2["الشهر"]==m]
            if r1.empty and r2.empty: continue
            rev1 = r1["إيرادات"].iloc[0] if not r1.empty else 0
            rev2 = r2["إيرادات"].iloc[0] if not r2.empty else 0
            rows += f"""<tr>
              <td><strong>{MONTHS_AR[m]}</strong></td>
              <td class='num-pos'>{fmt(rev1) if rev1>0 else "—"}</td>
              <td class='num-pos'>{fmt(rev2) if rev2>0 else "—"}</td>
              <td>{diff_pct(rev2, rev1)}</td>
            </tr>"""

        if rows:
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>الشهر</th><th>إيرادات {y1}</th><th>إيرادات {y2}</th><th>التغيير</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
