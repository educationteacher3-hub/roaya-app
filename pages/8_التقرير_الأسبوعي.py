import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from auth import check_password
from data_loader import load_khazina, load_suppliers, load_clients_list, fmt, MONTHS_AR

st.set_page_config(page_title="التقرير الأسبوعي", page_icon="📊", layout="wide")

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
.styled-table tbody td { padding:7px 10px; color:#3a4a58; }
.num-pos { color:#1a7f74; font-weight:600; font-family:monospace; }
.num-neg { color:#c0392b; font-weight:600; font-family:monospace; }
.num { font-family:monospace; font-size:11.5px; }
.report-header {
    background: linear-gradient(135deg, #0f1923 0%, #1a3a52 100%);
    color: white; border-radius: 12px; padding: 20px 24px; margin-bottom: 20px;
}
.report-header h2 { font-size: 18px; font-weight: 800; margin-bottom: 4px; }
.report-header p { font-size: 13px; opacity: 0.6; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("📊 التقرير الأسبوعي")

# ===== تحميل البيانات =====
df_khazina  = load_khazina()
df_invoices = load_suppliers()

# ===== اختيار الفترة =====
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    date_from = st.date_input("من تاريخ",
                               value=datetime.today() - timedelta(days=7))
with col2:
    date_to = st.date_input("إلى تاريخ",
                             value=datetime.today())
with col3:
    gen_btn = st.button("📊 توليد التقرير", use_container_width=True)

if gen_btn or True:  # يعرض دايماً
    from_ts = pd.Timestamp(date_from)
    to_ts   = pd.Timestamp(date_to)

    # ===== هيدر التقرير =====
    st.markdown(f"""
    <div class='report-header'>
        <h2>📊 التقرير المالي الأسبوعي — مكتب رؤية</h2>
        <p>الفترة من {date_from.strftime('%d/%m/%Y')} إلى {date_to.strftime('%d/%m/%Y')}</p>
    </div>""", unsafe_allow_html=True)

    # ===== خزينة الفترة =====
    if not df_khazina.empty:
        kh = df_khazina[
            (df_khazina["التاريخ"] >= from_ts) &
            (df_khazina["التاريخ"] <= to_ts)
        ]

        total_in  = kh["مدين"].sum()
        total_out = kh["دائن"].sum()
        net       = total_in - total_out

        st.markdown("<div class='section-title'>🏦 ملخص الخزينة</div>", unsafe_allow_html=True)

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("📥 الإيرادات",    f"{fmt(total_in)} ج")
        with c2: st.metric("📤 المصروفات",    f"{fmt(total_out)} ج")
        with c3: st.metric("📊 الصافي",       f"{fmt(net)} ج")
        with c4: st.metric("🔢 عدد الحركات", f"{len(kh):,}")

        if not kh.empty:
            # إيرادات حسب النوع
            rev_by_type = kh[kh["مدين"]>0].groupby("النوع")["مدين"].sum().sort_values(ascending=False)
            exp_by_type = kh[kh["دائن"]>0].groupby("النوع")["دائن"].sum().sort_values(ascending=False)

            col_r, col_e = st.columns(2)

            with col_r:
                st.markdown("<div class='section-title'>📥 الإيرادات حسب النوع</div>", unsafe_allow_html=True)
                rows = ""
                for t, v in rev_by_type.items():
                    pct = v/total_in*100 if total_in > 0 else 0
                    rows += f"<tr><td>{t}</td><td class='num-pos'>{fmt(v)}</td><td class='num'>{pct:.1f}%</td></tr>"
                st.markdown(f"""<table class='styled-table'>
                  <thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th></tr></thead>
                  <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

            with col_e:
                st.markdown("<div class='section-title'>📤 المصروفات حسب النوع</div>", unsafe_allow_html=True)
                rows = ""
                for t, v in exp_by_type.items():
                    pct = v/total_out*100 if total_out > 0 else 0
                    rows += f"<tr><td>{t}</td><td class='num-neg'>{fmt(v)}</td><td class='num'>{pct:.1f}%</td></tr>"
                st.markdown(f"""<table class='styled-table'>
                  <thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th></tr></thead>
                  <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

            # تفاصيل الحركات
            st.markdown("<div class='section-title'>📋 تفاصيل حركات الخزينة</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in kh.iloc[::-1].iterrows():
                date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                debit  = f"<span class='num-pos'>{fmt(r['مدين'])}</span>" if r["مدين"] > 0 else "—"
                credit = f"<span class='num-neg'>{fmt(r['دائن'])}</span>" if r["دائن"] > 0 else "—"
                rows += f"""<tr>
                  <td class='num'>{date_str}</td>
                  <td>{str(r['البيان'])[:50]}</td>
                  <td>{r['النوع']}</td>
                  <td>{debit}</td>
                  <td>{credit}</td>
                  <td class='num'>{fmt(r['الرصيد'])}</td>
                </tr>"""
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>التاريخ</th><th>البيان</th><th>النوع</th><th>مدين</th><th>دائن</th><th>الرصيد</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

    # ===== فواتير الفترة =====
    if not df_invoices.empty:
        inv = df_invoices[
            (df_invoices["تاريخ الفاتورة"] >= from_ts) &
            (df_invoices["تاريخ الفاتورة"] <= to_ts)
        ]

        if not inv.empty:
            st.markdown("<div class='section-title'>📋 فواتير الفترة</div>", unsafe_allow_html=True)

            c1, c2, c3 = st.columns(3)
            with c1: st.metric("عدد الفواتير",       f"{len(inv):,}")
            with c2: st.metric("إجمالي قيمة الفواتير", f"{fmt(inv['قيمة الفاتورة'].sum())} ج")
            with c3: st.metric("إجمالي العمولات",     f"{fmt(inv['القيمة'].sum())} ج")

            # ملخص حسب العميل
            by_client = inv.groupby("العميل").agg(
                عدد_الفواتير=("رقم الفاتورة","count"),
                قيمة_الفواتير=("قيمة الفاتورة","sum"),
                العمولة=("القيمة","sum")
            ).reset_index().sort_values("قيمة_الفواتير", ascending=False)

            rows = ""
            for _, r in by_client.iterrows():
                rows += f"""<tr>
                  <td>{r['العميل']}</td>
                  <td class='num'>{fmt(r['عدد_الفواتير'])}</td>
                  <td class='num'>{fmt(r['قيمة_الفواتير'])}</td>
                  <td class='num-pos'>{fmt(r['العمولة'])}</td>
                </tr>"""
            rows += f"""<tr class='total-row'>
              <td><strong>الإجمالي</strong></td>
              <td class='num'><strong>{fmt(len(inv))}</strong></td>
              <td class='num'><strong>{fmt(inv['قيمة الفاتورة'].sum())}</strong></td>
              <td class='num-pos'><strong>{fmt(inv['القيمة'].sum())}</strong></td>
            </tr>"""

            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>العميل</th><th>عدد الفواتير</th><th>قيمة الفواتير</th><th>العمولة</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

    # ===== تصدير التقرير =====
    st.markdown("---")
    st.markdown("<div class='section-title'>⬇ تصدير التقرير</div>", unsafe_allow_html=True)

    col_e1, col_e2 = st.columns(2)

    with col_e1:
        if st.button("📥 تصدير Excel", use_container_width=True):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                if not df_khazina.empty and not kh.empty:
                    kh.to_excel(writer, sheet_name="حركة الخزينة", index=False)
                if not df_invoices.empty and not inv.empty:
                    inv.to_excel(writer, sheet_name="الفواتير", index=False)
            st.download_button(
                "📥 تحميل Excel",
                buf.getvalue(),
                file_name=f"تقرير_أسبوعي_{date_from}_{date_to}.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet"
            )

    with col_e2:
        if st.button("🖨️ طباعة / حفظ PDF", use_container_width=True):
            st.info("افتح قائمة الطباعة في المتصفح (Ctrl+P) واختار 'حفظ كـ PDF'")
