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
.report-header { background:linear-gradient(135deg,#0f1923 0%,#1a3a52 100%); color:white; border-radius:12px; padding:18px 24px; margin-bottom:20px; }
.report-header h2 { font-size:17px; font-weight:800; margin-bottom:3px; }
.report-header p { font-size:12px; opacity:0.6; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("📊 التقرير الأسبوعي")

col1, col2, col3 = st.columns([2, 2, 1])
with col1:
    date_from = st.date_input("من تاريخ", value=datetime.today() - timedelta(days=7))
with col2:
    date_to = st.date_input("إلى تاريخ", value=datetime.today())
with col3:
    st.markdown("<br>", unsafe_allow_html=True)
    gen_btn = st.button("📊 توليد", use_container_width=True)

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
        df_inv["قيمة الفاتورة"]  = pd.to_numeric(df_inv["قيمة الفاتورة"],  errors="coerce").fillna(0)
        df_inv["تاريخ الفاتورة"] = pd.to_datetime(df_inv["تاريخ الفاتورة"], errors="coerce")
        df_inv["نسبة_العميل"]    = df_inv["العميل"].map(clients_rates).fillna(0)
        df_inv["عمولة_العميل"]   = df_inv["قيمة الفاتورة"] * df_inv["نسبة_العميل"]
        df_inv["نسبة_المورد_ف"]  = df_inv["المورد"].map(suppliers_rates).fillna(0)
        df_inv["عمولة_المورد_ف"] = df_inv["قيمة الفاتورة"] * df_inv["نسبة_المورد_ف"]
    try:
        df_coll_raw = load_excel_from_drive("clients", "التحصيلات والسدادات", header=3)
        c_coll = df_coll_raw.iloc[:,:5].copy()
        c_coll.columns = ["التاريخ","العميل","طريقة التحصيل","المبلغ","ملاحظات"]
        c_coll = c_coll.dropna(subset=["العميل"])
        c_coll["المبلغ"]  = pd.to_numeric(c_coll["المبلغ"],  errors="coerce").fillna(0)
        c_coll["التاريخ"] = pd.to_datetime(c_coll["التاريخ"], errors="coerce")
        s_pay = df_coll_raw.iloc[:,7:12].copy()
        s_pay.columns = ["التاريخ","المسؤول","طريقة السداد","المبلغ","ملاحظات"]
        s_pay = s_pay.dropna(subset=["المسؤول"])
        s_pay["المبلغ"]  = pd.to_numeric(s_pay["المبلغ"],  errors="coerce").fillna(0)
        s_pay["التاريخ"] = pd.to_datetime(s_pay["التاريخ"], errors="coerce")
    except:
        c_coll = pd.DataFrame()
        s_pay  = pd.DataFrame()
    return df_inv, c_coll, s_pay

df_inv, df_coll, df_sup_pay = load_invoices_with_rates()

# ===== فلترة الفترة =====
kh       = df_khazina[(df_khazina["التاريخ"]>=from_ts)&(df_khazina["التاريخ"]<=to_ts)] if not df_khazina.empty else pd.DataFrame()
inv_f    = df_inv[(df_inv["تاريخ الفاتورة"]>=from_ts)&(df_inv["تاريخ الفاتورة"]<=to_ts)] if not df_inv.empty else pd.DataFrame()
coll_f   = df_coll[(df_coll["التاريخ"]>=from_ts)&(df_coll["التاريخ"]<=to_ts)] if not df_coll.empty else pd.DataFrame()
pay_f    = df_sup_pay[(df_sup_pay["التاريخ"]>=from_ts)&(df_sup_pay["التاريخ"]<=to_ts)] if not df_sup_pay.empty else pd.DataFrame()
itqan_f  = df_itqan[(df_itqan["التاريخ"]>=from_ts)&(df_itqan["التاريخ"]<=to_ts)] if not df_itqan.empty else pd.DataFrame()

# ===== هيدر =====
st.markdown(f"""
<div class='report-header'>
    <h2>📊 التقرير الأسبوعي — مكتب رؤية</h2>
    <p>من {date_from.strftime('%d/%m/%Y')} إلى {date_to.strftime('%d/%m/%Y')}</p>
</div>""", unsafe_allow_html=True)

# ===== 1. الملخص الإجمالي =====
st.markdown("<div class='section-title'>📋 الملخص الإجمالي</div>", unsafe_allow_html=True)
c1,c2,c3 = st.columns(3)
with c1: st.metric("📋 عدد الفواتير",          f"{len(inv_f):,}")
with c2: st.metric("💼 إجمالي قيمة الفواتير",  f"{fmt(inv_f['قيمة الفاتورة'].sum() if not inv_f.empty else 0)} ج")
with c3: st.metric("✅ عمولات العملاء",         f"{fmt(inv_f['عمولة_العميل'].sum() if not inv_f.empty else 0)} ج")

c4,c5,c6 = st.columns(3)
with c4: st.metric("🏭 عمولات مسؤولي التوريد", f"{fmt(inv_f['عمولة_المورد_ف'].sum() if not inv_f.empty else 0)} ج")
with c5: st.metric("💰 إجمالي التحصيلات",      f"{fmt(coll_f['المبلغ'].sum() if not coll_f.empty else 0)} ج")
with c6: st.metric("💸 سدادات المسؤولين",      f"{fmt(pay_f['المبلغ'].sum() if not pay_f.empty else 0)} ج")

# ===== 2. ملخص الخزينة =====
st.markdown("<div class='section-title'>🏦 ملخص الخزينة</div>", unsafe_allow_html=True)
if not kh.empty:
    total_in  = kh["مدين"].sum()
    total_out = kh["دائن"].sum()
    net       = total_in - total_out
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("📥 الإيرادات",   f"{fmt(total_in)} ج")
    with c2: st.metric("📤 المصروفات",   f"{fmt(total_out)} ج")
    with c3: st.metric("📊 الصافي",      f"{fmt(net)} ج")
    with c4: st.metric("🔢 عدد الحركات", f"{len(kh):,}")

    col_r, col_e = st.columns(2)
    with col_r:
        st.markdown("<div class='section-title'>📥 الإيرادات حسب النوع</div>", unsafe_allow_html=True)
        rev = kh[kh["مدين"]>0].groupby("النوع")["مدين"].sum().sort_values(ascending=False)
        rows = ""
        for t, v in rev.items():
            pct = v/total_in*100 if total_in>0 else 0
            rows += f"<tr><td>{t}</td><td class='num-pos'>{fmt(v)}</td><td class='num'>{pct:.1f}%</td></tr>"
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-pos'>{fmt(total_in)}</td><td>100%</td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

    with col_e:
        st.markdown("<div class='section-title'>📤 المصروفات حسب النوع</div>", unsafe_allow_html=True)
        exp = kh[kh["دائن"]>0].groupby("النوع")["دائن"].sum().sort_values(ascending=False)
        rows = ""
        for t, v in exp.items():
            pct = v/total_out*100 if total_out>0 else 0
            rows += f"<tr><td>{t}</td><td class='num-neg'>{fmt(v)}</td><td class='num'>{pct:.1f}%</td></tr>"
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-neg'>{fmt(total_out)}</td><td>100%</td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)
else:
    st.info("لا توجد حركات خزينة في هذه الفترة")

# ===== 3. ملخص اتقان =====
st.markdown("<div class='section-title'>🇦🇪 ملخص اتقان</div>", unsafe_allow_html=True)
if not itqan_f.empty:
    c1,c2,c3,c4 = st.columns(4)
    with c1: st.metric("📥 إيداعات (AED)",  f"{fmt(itqan_f['مدين AED'].sum(),2)}")
    with c2: st.metric("📤 مصروفات (AED)", f"{fmt(itqan_f['دائن AED'].sum(),2)}")
    with c3: st.metric("📊 الصافي (AED)",   f"{fmt(itqan_f['مدين AED'].sum()-itqan_f['دائن AED'].sum(),2)}")
    with c4: st.metric("🔢 عدد الحركات",   f"{len(itqan_f):,}")
else:
    st.info("لا توجد حركات اتقان في هذه الفترة")

# ===== 4. ملخص الفواتير حسب العميل =====
if not inv_f.empty:
    st.markdown("<div class='section-title'>📋 ملخص الفواتير حسب العميل</div>", unsafe_allow_html=True)
    by_client = inv_f.groupby("العميل").agg(
        عدد=("رقم الفاتورة","count"),
        قيمة=("قيمة الفاتورة","sum"),
        عمولة_عميل=("عمولة_العميل","sum"),
        عمولة_مورد=("عمولة_المورد_ف","sum")
    ).reset_index().sort_values("قيمة", ascending=False)
    rows = ""
    for _, r in by_client.iterrows():
        rows += f"<tr><td>{r['العميل']}</td><td class='num'>{fmt(r['عدد'])}</td><td class='num'>{fmt(r['قيمة'])}</td><td class='num-pos'>{fmt(r['عمولة_عميل'])}</td><td class='num-pos'>{fmt(r['عمولة_مورد'])}</td></tr>"
    rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num'>{fmt(len(inv_f))}</td><td class='num'>{fmt(inv_f['قيمة الفاتورة'].sum())}</td><td class='num-pos'>{fmt(inv_f['عمولة_العميل'].sum())}</td><td class='num-pos'>{fmt(inv_f['عمولة_المورد_ف'].sum())}</td></tr>"
    st.markdown(f"<table class='styled-table'><thead><tr><th>العميل</th><th>عدد الفواتير</th><th>قيمة الفواتير</th><th>عمولة العميل</th><th>عمولة المورد</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

# ===== 5. التحصيلات والسدادات ملخص =====
col_c, col_p = st.columns(2)
with col_c:
    st.markdown("<div class='section-title'>💰 ملخص التحصيلات</div>", unsafe_allow_html=True)
    if not coll_f.empty:
        by_c = coll_f.groupby("العميل")["المبلغ"].sum().reset_index().sort_values("المبلغ", ascending=False)
        rows = ""
        for _, r in by_c.iterrows():
            rows += f"<tr><td>{r['العميل']}</td><td class='num-pos'>{fmt(r['المبلغ'])}</td></tr>"
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-pos'>{fmt(coll_f['المبلغ'].sum())}</td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>العميل</th><th>المبلغ</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)
    else:
        st.info("لا توجد تحصيلات في هذه الفترة")

with col_p:
    st.markdown("<div class='section-title'>💸 ملخص سدادات المسؤولين</div>", unsafe_allow_html=True)
    if not pay_f.empty:
        by_s = pay_f.groupby("المسؤول")["المبلغ"].sum().reset_index().sort_values("المبلغ", ascending=False)
        rows = ""
        for _, r in by_s.iterrows():
            rows += f"<tr><td>{r['المسؤول']}</td><td class='num-pos'>{fmt(r['المبلغ'])}</td></tr>"
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-pos'>{fmt(pay_f['المبلغ'].sum())}</td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>المسؤول</th><th>المبلغ</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)
    else:
        st.info("لا توجد سدادات في هذه الفترة")

# ===== تصدير =====
st.markdown("---")
col_e1, col_e2 = st.columns(2)
with col_e1:
    if st.button("📥 تصدير Excel", use_container_width=True):
        buf = io.BytesIO()
        with pd.ExcelWriter(buf, engine="openpyxl") as writer:
            if not kh.empty:
                kh.to_excel(writer, sheet_name="حركة الخزينة", index=False)
            if not inv_f.empty:
                inv_f.to_excel(writer, sheet_name="الفواتير", index=False)
            if not coll_f.empty:
                coll_f.to_excel(writer, sheet_name="التحصيلات", index=False)
            if not pay_f.empty:
                pay_f.to_excel(writer, sheet_name="سدادات المسؤولين", index=False)
        st.download_button("📥 تحميل", buf.getvalue(),
                           file_name=f"تقرير_{date_from}_{date_to}.xlsx",
                           mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
with col_e2:
    if st.button("🖨️ طباعة PDF", use_container_width=True):
        st.info("اضغط Ctrl+P في المتصفح واختار 'حفظ كـ PDF'")
