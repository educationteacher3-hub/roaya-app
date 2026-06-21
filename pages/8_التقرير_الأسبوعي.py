import streamlit as st
import pandas as pd
import io
from datetime import datetime, timedelta
from auth import check_password
from data_loader import load_khazina, load_itqan, load_excel_from_drive, fmt, MONTHS_AR

st.set_page_config(page_title="التقرير الأسبوعي", page_icon="📊", layout="wide")

st.markdown("""
<style>
@import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
* { font-family: 'Cairo', sans-serif !important; }
html, body, [class*="css"] { direction: rtl; }
#MainMenu { visibility: hidden; } footer { visibility: hidden; } header { visibility: hidden; }
[data-testid="metric-container"] { background:white; border:1px solid #d4dce5; border-radius:10px; padding:12px 14px; border-right:4px solid #c8953a; }
[data-testid="stMetricValue"] { font-size:15px !important; font-weight:800 !important; }
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
.report-header { background:linear-gradient(135deg,#0f1923 0%,#1a3a52 100%); color:white; border-radius:12px; padding:20px 24px; margin-bottom:20px; }
.report-header h2 { font-size:18px; font-weight:800; margin-bottom:4px; }
.report-header p { font-size:13px; opacity:0.6; }
.kpi-section { background:white; border:1px solid #d4dce5; border-radius:10px; padding:16px; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("📊 التقرير الأسبوعي")

# ===== اختيار الفترة =====
col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    date_from = st.date_input("من تاريخ", value=datetime.today() - timedelta(days=7))
with col2:
    date_to = st.date_input("إلى تاريخ", value=datetime.today())
with col3:
    gen_btn = st.button("📊 توليد التقرير", use_container_width=True)

from_ts = pd.Timestamp(date_from)
to_ts   = pd.Timestamp(date_to)

# ===== تحميل البيانات =====
df_khazina = load_khazina()
df_itqan   = load_itqan()

@st.cache_data(ttl=300)
def load_invoices_with_rates():
    df_inv = load_excel_from_drive("clients", "الموردين", header=2)
    df_list = load_excel_from_drive("clients", "قائمة الموردين والعملاء", header=0)
    
    clients_rates = {}
    suppliers_rates = {}
    if not df_list.empty:
        for _, row in df_list.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
                clients_rates[str(row.iloc[0]).strip()] = pd.to_numeric(row.iloc[1], errors="coerce") or 0
            if len(row) > 2 and pd.notna(row.iloc[2]) and str(row.iloc[2]).strip():
                suppliers_rates[str(row.iloc[2]).strip()] = pd.to_numeric(row.iloc[3], errors="coerce") or 0

    if not df_inv.empty:
        df_inv.columns = ["م","رقم الفاتورة","قيمة الفاتورة","نسبة_المورد","عمولة_المورد",
                          "تاريخ الفاتورة","جهة الصدور","العميل","المورد"]
        df_inv = df_inv.dropna(subset=["رقم الفاتورة"])
        df_inv["قيمة الفاتورة"] = pd.to_numeric(df_inv["قيمة الفاتورة"], errors="coerce").fillna(0)
        df_inv["تاريخ الفاتورة"] = pd.to_datetime(df_inv["تاريخ الفاتورة"], errors="coerce")
        df_inv["نسبة_العميل"]    = df_inv["العميل"].map(clients_rates).fillna(0)
        df_inv["عمولة_العميل"]   = df_inv["قيمة الفاتورة"] * df_inv["نسبة_العميل"]
        df_inv["نسبة_المورد_ف"]  = df_inv["المورد"].map(suppliers_rates).fillna(df_inv["نسبة_المورد"])
        df_inv["عمولة_المورد_ف"] = df_inv["قيمة الفاتورة"] * df_inv["نسبة_المورد_ف"]

    try:
        df_coll = load_excel_from_drive("clients", "التحصيلات والسدادات", header=3)
        c_coll = df_coll.iloc[:,:5].copy()
        c_coll.columns = ["التاريخ","العميل","طريقة التحصيل","المبلغ","ملاحظات"]
        c_coll = c_coll.dropna(subset=["العميل"])
        c_coll["المبلغ"] = pd.to_numeric(c_coll["المبلغ"], errors="coerce").fillna(0)
        c_coll["التاريخ"] = pd.to_datetime(c_coll["التاريخ"], errors="coerce")
        
        s_pay = df_coll.iloc[:,7:12].copy()
        s_pay.columns = ["التاريخ","المسؤول","طريقة السداد","المبلغ","ملاحظات"]
        s_pay = s_pay.dropna(subset=["المسؤول"])
        s_pay["المبلغ"] = pd.to_numeric(s_pay["المبلغ"], errors="coerce").fillna(0)
        s_pay["التاريخ"] = pd.to_datetime(s_pay["التاريخ"], errors="coerce")
    except:
        c_coll = pd.DataFrame()
        s_pay  = pd.DataFrame()

    return df_inv, c_coll, s_pay

df_inv, df_coll, df_sup_pay = load_invoices_with_rates()

# ===== هيدر التقرير =====
st.markdown(f"""
<div class='report-header'>
    <h2>📊 التقرير المالي الأسبوعي — مكتب رؤية</h2>
    <p>الفترة من {date_from.strftime('%d/%m/%Y')} إلى {date_to.strftime('%d/%m/%Y')}</p>
</div>""", unsafe_allow_html=True)

# ===== 1. ملخص إجمالي الأسبوع =====
st.markdown("<div class='section-title'>📋 الملخص الإجمالي للأسبوع</div>", unsafe_allow_html=True)

# فواتير الأسبوع
inv_week = pd.DataFrame()
if not df_inv.empty:
    inv_week = df_inv[
        (df_inv["تاريخ الفاتورة"] >= from_ts) &
        (df_inv["تاريخ الفاتورة"] <= to_ts)
    ]

# تحصيلات الأسبوع
coll_week = pd.DataFrame()
if not df_coll.empty:
    coll_week = df_coll[
        (df_coll["التاريخ"] >= from_ts) &
        (df_coll["التاريخ"] <= to_ts)
    ]

# سدادات المسؤولين الأسبوع
pay_week = pd.DataFrame()
if not df_sup_pay.empty:
    pay_week = df_sup_pay[
        (df_sup_pay["التاريخ"] >= from_ts) &
        (df_sup_pay["التاريخ"] <= to_ts)
    ]

# خزينة الأسبوع
kh_week = pd.DataFrame()
if not df_khazina.empty:
    kh_week = df_khazina[
        (df_khazina["التاريخ"] >= from_ts) &
        (df_khazina["التاريخ"] <= to_ts)
    ]

c1, c2, c3 = st.columns(3)
with c1: st.metric("📋 عدد الفواتير",             f"{len(inv_week):,}")
with c2: st.metric("💼 إجمالي قيمة الفواتير",     f"{fmt(inv_week['قيمة الفاتورة'].sum() if not inv_week.empty else 0)} ج")
with c3: st.metric("✅ عمولات العملاء",            f"{fmt(inv_week['عمولة_العميل'].sum() if not inv_week.empty else 0)} ج")

c4, c5, c6 = st.columns(3)
with c4: st.metric("🏭 عمولات مسؤولي التوريد",    f"{fmt(inv_week['عمولة_المورد_ف'].sum() if not inv_week.empty else 0)} ج")
with c5: st.metric("💰 إجمالي تحصيل الأسبوع",    f"{fmt(coll_week['المبلغ'].sum() if not coll_week.empty else 0)} ج")
with c6: st.metric("💸 سدادات مسؤولي التوريد",   f"{fmt(pay_week['المبلغ'].sum() if not pay_week.empty else 0)} ج")

# ===== 2. تحليل الخزينة =====
st.markdown("<div class='section-title'>🏦 تحليل إيرادات ومصروفات الخزينة</div>", unsafe_allow_html=True)

if not kh_week.empty:
    total_in  = kh_week["مدين"].sum()
    total_out = kh_week["دائن"].sum()
    net       = total_in - total_out

    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("📥 إجمالي الإيرادات",  f"{fmt(total_in)} ج")
    with c2: st.metric("📤 إجمالي المصروفات", f"{fmt(total_out)} ج")
    with c3: st.metric("📊 الصافي",            f"{fmt(net)} ج")
    with c4: st.metric("🔢 عدد الحركات",       f"{len(kh_week):,}")

    col_r, col_e = st.columns(2)

    with col_r:
        st.markdown("<div class='section-title'>📥 الإيرادات حسب النوع</div>", unsafe_allow_html=True)
        rev = kh_week[kh_week["مدين"]>0].groupby("النوع")["مدين"].sum().sort_values(ascending=False)
        rows = ""
        for t, v in rev.items():
            pct = v/total_in*100 if total_in>0 else 0
            bar = int(pct)
            rows += f"""<tr>
              <td>{t}</td>
              <td class='num-pos'>{fmt(v)}</td>
              <td class='num'>{pct:.1f}%</td>
              <td><div style='background:#e8edf3;border-radius:3px;height:6px;width:100px;overflow:hidden'>
                <div style='height:100%;width:{bar}%;background:#1a7f74;border-radius:3px'></div>
              </div></td>
            </tr>"""
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-pos'>{fmt(total_in)}</td><td>100%</td><td></td></tr>"
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th><th></th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

    with col_e:
        st.markdown("<div class='section-title'>📤 المصروفات حسب النوع</div>", unsafe_allow_html=True)
        exp = kh_week[kh_week["دائن"]>0].groupby("النوع")["دائن"].sum().sort_values(ascending=False)
        rows = ""
        for t, v in exp.items():
            pct = v/total_out*100 if total_out>0 else 0
            bar = int(pct)
            rows += f"""<tr>
              <td>{t}</td>
              <td class='num-neg'>{fmt(v)}</td>
              <td class='num'>{pct:.1f}%</td>
              <td><div style='background:#e8edf3;border-radius:3px;height:6px;width:100px;overflow:hidden'>
                <div style='height:100%;width:{bar}%;background:#c0392b;border-radius:3px'></div>
              </div></td>
            </tr>"""
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-neg'>{fmt(total_out)}</td><td>100%</td><td></td></tr>"
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th><th></th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

    # تفاصيل حركات الخزينة
    st.markdown("<div class='section-title'>📋 تفاصيل حركات الخزينة</div>", unsafe_allow_html=True)
    rows = ""
    for _, r in kh_week.iloc[::-1].iterrows():
        date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
        debit  = f"<span class='num-pos'>{fmt(r['مدين'])}</span>" if r["مدين"]>0 else "—"
        credit = f"<span class='num-neg'>{fmt(r['دائن'])}</span>" if r["دائن"]>0 else "—"
        rows += f"""<tr>
          <td class='num'>{date_str}</td>
          <td>{str(r['البيان'])[:50]}</td>
          <td>{r['النوع']}</td>
          <td>{debit}</td><td>{credit}</td>
          <td class='num'>{fmt(r['الرصيد'])}</td>
        </tr>"""
    st.markdown(f"""<table class='styled-table'>
      <thead><tr><th>التاريخ</th><th>البيان</th><th>النوع</th><th>مدين</th><th>دائن</th><th>الرصيد</th></tr></thead>
      <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
else:
    st.info("لا توجد حركات خزينة في هذه الفترة")

# ===== 3. ملخص اتقان =====
st.markdown("<div class='section-title'>🇦🇪 ملخص حركات اتقان</div>", unsafe_allow_html=True)

if not df_itqan.empty:
    itqan_week = df_itqan[
        (df_itqan["التاريخ"] >= from_ts) &
        (df_itqan["التاريخ"] <= to_ts)
    ]

    if not itqan_week.empty:
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("📥 إيداعات (AED)",    f"{fmt(itqan_week['مدين AED'].sum(), 2)}")
        with c2: st.metric("📤 مصروفات (AED)",   f"{fmt(itqan_week['دائن AED'].sum(), 2)}")
        with c3: st.metric("📊 الصافي (AED)",     f"{fmt(itqan_week['مدين AED'].sum() - itqan_week['دائن AED'].sum(), 2)}")
        with c4: st.metric("🔢 عدد الحركات",      f"{len(itqan_week):,}")

        rows = ""
        for _, r in itqan_week.iloc[::-1].iterrows():
            date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
            is_in = r["مدين AED"] > 0
            badge = "<span style='background:#e0f4f2;color:#1a7f74;padding:2px 7px;border-radius:10px;font-size:10px'>إيداع</span>" if is_in else "<span style='background:#fdecea;color:#c0392b;padding:2px 7px;border-radius:10px;font-size:10px'>صرف</span>"
            debit  = f"<span class='num-pos'>{fmt(r['مدين AED'],2)}</span>" if r["مدين AED"]>0 else "—"
            credit = f"<span class='num-neg'>{fmt(r['دائن AED'],2)}</span>" if r["دائن AED"]>0 else "—"
            rows += f"""<tr>
              <td class='num'>{date_str}</td>
              <td>{str(r['البيان'])[:45]}</td>
              <td>{badge}</td>
              <td>{debit}</td><td>{credit}</td>
              <td class='{"num-neg" if r["الرصيد AED"]<0 else "num-pos"}'>{fmt(r['الرصيد AED'],2)}</td>
            </tr>"""
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>التاريخ</th><th>البيان</th><th>النوع</th><th>مدين AED</th><th>دائن AED</th><th>الرصيد AED</th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    else:
        st.info("لا توجد حركات اتقان في هذه الفترة")

# ===== 4. فواتير الأسبوع =====
if not inv_week.empty:
    st.markdown("<div class='section-title'>📋 فواتير الأسبوع حسب العميل</div>", unsafe_allow_html=True)

    by_client = inv_week.groupby("العميل").agg(
        عدد=("رقم الفاتورة","count"),
        قيمة=("قيمة الفاتورة","sum"),
        عمولة_عميل=("عمولة_العميل","sum"),
        عمولة_مورد=("عمولة_المورد_ف","sum")
    ).reset_index().sort_values("قيمة", ascending=False)

    rows = ""
    for _, r in by_client.iterrows():
        rows += f"""<tr>
          <td>{r['العميل']}</td>
          <td class='num'>{fmt(r['عدد'])}</td>
          <td class='num'>{fmt(r['قيمة'])}</td>
          <td class='num-pos'>{fmt(r['عمولة_عميل'])}</td>
          <td class='num-pos'>{fmt(r['عمولة_مورد'])}</td>
        </tr>"""
    rows += f"""<tr class='total-row'>
      <td><strong>الإجمالي</strong></td>
      <td class='num'>{fmt(len(inv_week))}</td>
      <td class='num'>{fmt(inv_week['قيمة الفاتورة'].sum())}</td>
      <td class='num-pos'>{fmt(inv_week['عمولة_العميل'].sum())}</td>
      <td class='num-pos'>{fmt(inv_week['عمولة_المورد_ف'].sum())}</td>
    </tr>"""
    st.markdown(f"""<table class='styled-table'>
      <thead><tr><th>العميل</th><th>عدد الفواتير</th><th>قيمة الفواتير</th><th>عمولة العميل</th><th>عمولة المورد</th></tr></thead>
      <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

# ===== 5. التحصيلات والسدادات =====
col_c, col_p = st.columns(2)

with col_c:
    st.markdown("<div class='section-title'>💰 تحصيلات الأسبوع</div>", unsafe_allow_html=True)
    if not coll_week.empty:
        rows = ""
        for _, r in coll_week.iterrows():
            date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
            rows += f"<tr><td class='num'>{date_str}</td><td>{r['العميل']}</td><td class='num-pos'>{fmt(r['المبلغ'])}</td></tr>"
        rows += f"<tr class='total-row'><td colspan='2'><strong>الإجمالي</strong></td><td class='num-pos'><strong>{fmt(coll_week['المبلغ'].sum())}</strong></td></tr>"
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>التاريخ</th><th>العميل</th><th>المبلغ</th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    else:
        st.info("لا توجد تحصيلات في هذه الفترة")

with col_p:
    st.markdown("<div class='section-title'>💸 سدادات مسؤولي التوريد</div>", unsafe_allow_html=True)
    if not pay_week.empty:
        rows = ""
        for _, r in pay_week.iterrows():
            date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
            rows += f"<tr><td class='num'>{date_str}</td><td>{r['المسؤول']}</td><td class='num-pos'>{fmt(r['المبلغ'])}</td></tr>"
        rows += f"<tr class='total-row'><td colspan='2'><strong>الإجمالي</strong></td><td class='num-pos'><strong>{fmt(pay_week['المبلغ'].sum())}</strong></td></tr>"
        st.markdown(f"""<table class='styled-table'>
          <thead><tr><th>التاريخ</th><th>المسؤول</th><th>المبلغ</th></tr></thead>
          <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)
    else:
        st.info("لا توجد سدادات في هذه الفترة")

# ===== تصدير =====
st.markdown("---")
col_e1, col_e2 = st.columns(2)

with col_e1:
    if st.button("📥 تصدير Excel", use_container_width=True):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            if not kh_week.empty:
                kh_week.to_excel(writer, sheet_name="حركة الخزينة", index=False)
            if not inv_week.empty:
                inv_week.to_excel(writer, sheet_name="الفواتير", index=False)
            if not itqan_week.empty if not df_itqan.empty else True:
                pass
            if not coll_week.empty:
                coll_week.to_excel(writer, sheet_name="التحصيلات", index=False)
            if not pay_week.empty:
                pay_week.to_excel(writer, sheet_name="سدادات المسؤولين", index=False)
        st.download_button("📥 تحميل Excel", buf.getvalue(),
                           file_name=f"تقرير_{date_from}_{date_to}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

with col_e2:
    if st.button("🖨️ طباعة / حفظ PDF", use_container_width=True):
        st.info("افتح قائمة الطباعة في المتصفح (Ctrl+P) واختار 'حفظ كـ PDF'")
