import streamlit as st
import pandas as pd
from auth import check_password, logout
from data_loader import (
    load_khazina, load_itqan, load_excel_from_drive,
    fmt, reload_all, MONTHS_AR
)

st.set_page_config(
    page_title="مكتب رؤية — النظام المالي",
    page_icon="💼",
    layout="wide",
    initial_sidebar_state="expanded"
)

if not check_password():
    st.stop()

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
.badge { display:inline-block; padding:2px 8px; border-radius:20px; font-size:10px; font-weight:600; }
.badge-green { background:#e0f4f2; color:#1a7f74; }
.badge-red { background:#fdecea; color:#c0392b; }
.badge-gold { background:#fdf3e3; color:#c8953a; }
.badge-blue { background:#e8f0f7; color:#1a5276; }
.badge-purple { background:#f5eef8; color:#6c3483; }
.badge-orange { background:#fef0e7; color:#d35400; }
.report-banner { background:linear-gradient(135deg,#0f1923 0%,#1a3a52 100%); color:white; border-radius:12px; padding:18px 24px; margin-bottom:20px; }
.report-banner h2 { font-size:17px; font-weight:800; margin-bottom:3px; }
.report-banner p { font-size:12px; opacity:0.6; }
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
    st.page_link("app.py",                           label="📊 لوحة التحكم")

    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.3);padding:8px 8px 4px;'>رؤية — مصر</div>", unsafe_allow_html=True)
    st.page_link("pages/1_خزينة.py",                label="🏦 حركة الخزينة")
    st.page_link("pages/2_عملاء_وموردين.py",        label="👥 العملاء والموردين")
    st.page_link("pages/3_تقارير.py",               label="📈 التقارير المالية")

    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.3);padding:8px 8px 4px;'>اتقان — الإمارات</div>", unsafe_allow_html=True)
    st.page_link("pages/4_اتقان.py",                label="🇦🇪 كشف الحساب")

    st.markdown("<div style='font-size:10px;color:rgba(255,255,255,0.3);padding:8px 8px 4px;'>تقارير متقدمة</div>", unsafe_allow_html=True)
    st.page_link("pages/5_داشبورد_العملاء.py",      label="📊 داشبورد العملاء")
    st.page_link("pages/6_كشف_حساب.py",             label="📋 كشف الحساب")
    st.page_link("pages/7_بحث_ومقارنة.py",          label="🔍 بحث ومقارنة")
    st.page_link("pages/8_التقرير_الأسبوعي.py",     label="📊 التقرير الأسبوعي")

    st.divider()
    if st.button("↻ تحديث البيانات", use_container_width=True):
        reload_all()
        st.success("تم التحديث!")

    user_name = st.session_state.get("user_name", "")
    st.markdown(f"<div style='font-size:12px;color:rgba(255,255,255,0.5);padding:4px 8px;'>👤 {user_name}</div>", unsafe_allow_html=True)
    if st.button("🚪 تسجيل الخروج", use_container_width=True):
        logout()

# ===== تحميل البيانات =====
@st.cache_data(ttl=300)
def load_invoices_data():
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
        df_inv["نسبة_المورد_ف"]  = df_inv["المورد"].map(suppliers_rates).fillna(0)
        df_inv["عمولة_المورد_ف"] = df_inv["قيمة الفاتورة"] * df_inv["نسبة_المورد_ف"]
    try:
        df_coll_raw = load_excel_from_drive("clients", "التحصيلات والسدادات", header=3)
        c_coll = df_coll_raw.iloc[:,:5].copy()
        c_coll.columns = ["التاريخ","العميل","طريقة التحصيل","المبلغ","ملاحظات"]
        c_coll = c_coll.dropna(subset=["العميل"])
        c_coll["المبلغ"] = pd.to_numeric(c_coll["المبلغ"], errors="coerce").fillna(0)
        c_coll["التاريخ"] = pd.to_datetime(c_coll["التاريخ"], errors="coerce")
        s_pay = df_coll_raw.iloc[:,7:12].copy()
        s_pay.columns = ["التاريخ","المسؤول","طريقة السداد","المبلغ","ملاحظات"]
        s_pay = s_pay.dropna(subset=["المسؤول"])
        s_pay["المبلغ"] = pd.to_numeric(s_pay["المبلغ"], errors="coerce").fillna(0)
        s_pay["التاريخ"] = pd.to_datetime(s_pay["التاريخ"], errors="coerce")
    except:
        c_coll = pd.DataFrame()
        s_pay  = pd.DataFrame()
    return df_inv, c_coll, s_pay

df_khazina  = load_khazina()
df_itqan    = load_itqan()
df_inv, df_coll, df_sup_pay = load_invoices_data()

# ===== فلاتر الفترة =====
st.title("📊 لوحة التحكم الرئيسية")

col_f1, col_f2, col_f3 = st.columns([2, 2, 2])

years = sorted(df_khazina["السنة"].dropna().unique().astype(int).tolist()) if not df_khazina.empty else [2026]
months_list = ["كل الشهور"] + [MONTHS_AR[m] for m in range(1,13)]

with col_f1:
    sel_year = st.selectbox("السنة", [str(y) for y in years], index=len(years)-1)
with col_f2:
    month_from = st.selectbox("من شهر", months_list)
with col_f3:
    month_to = st.selectbox("إلى شهر", months_list, index=len(months_list)-1)

rev_map = {v: k for k, v in MONTHS_AR.items()}

# تحديد الفترة
sel_year_int = int(sel_year)
if month_from == "كل الشهور":
    from_ts = pd.Timestamp(f"{sel_year_int}-01-01")
else:
    from_ts = pd.Timestamp(f"{sel_year_int}-{rev_map[month_from]:02d}-01")

if month_to == "كل الشهور":
    to_ts = pd.Timestamp(f"{sel_year_int}-12-31")
else:
    m_to = rev_map[month_to]
    # آخر يوم في الشهر
    next_m = m_to + 1 if m_to < 12 else 1
    next_y = sel_year_int if m_to < 12 else sel_year_int + 1
    to_ts = pd.Timestamp(f"{next_y}-{next_m:02d}-01") - pd.Timedelta(days=1)

st.markdown(f"""
<div class='report-banner'>
    <h2>📊 تقرير مكتب رؤية — {sel_year}</h2>
    <p>الفترة من {from_ts.strftime('%d/%m/%Y')} إلى {to_ts.strftime('%d/%m/%Y')}</p>
</div>""", unsafe_allow_html=True)

# ===== فلترة البيانات =====
kh = df_khazina[(df_khazina["التاريخ"]>=from_ts)&(df_khazina["التاريخ"]<=to_ts)] if not df_khazina.empty else pd.DataFrame()
inv_f = df_inv[(df_inv["تاريخ الفاتورة"]>=from_ts)&(df_inv["تاريخ الفاتورة"]<=to_ts)] if not df_inv.empty else pd.DataFrame()
coll_f = df_coll[(df_coll["التاريخ"]>=from_ts)&(df_coll["التاريخ"]<=to_ts)] if not df_coll.empty else pd.DataFrame()
pay_f = df_sup_pay[(df_sup_pay["التاريخ"]>=from_ts)&(df_sup_pay["التاريخ"]<=to_ts)] if not df_sup_pay.empty else pd.DataFrame()
itqan_f = df_itqan[(df_itqan["التاريخ"]>=from_ts)&(df_itqan["التاريخ"]<=to_ts)] if not df_itqan.empty else pd.DataFrame()

# ===== 1. الملخص الإجمالي =====
st.markdown("<div class='section-title'>📋 الملخص الإجمالي للفترة</div>", unsafe_allow_html=True)

c1, c2, c3 = st.columns(3)
with c1: st.metric("📋 عدد الفواتير",          f"{len(inv_f):,}")
with c2: st.metric("💼 إجمالي قيمة الفواتير",  f"{fmt(inv_f['قيمة الفاتورة'].sum() if not inv_f.empty else 0)} ج")
with c3: st.metric("✅ عمولات العملاء",         f"{fmt(inv_f['عمولة_العميل'].sum() if not inv_f.empty else 0)} ج")

c4, c5, c6 = st.columns(3)
with c4: st.metric("🏭 عمولات مسؤولي التوريد", f"{fmt(inv_f['عمولة_المورد_ف'].sum() if not inv_f.empty else 0)} ج")
with c5: st.metric("💰 إجمالي التحصيلات",      f"{fmt(coll_f['المبلغ'].sum() if not coll_f.empty else 0)} ج")
with c6: st.metric("💸 سدادات المسؤولين",      f"{fmt(pay_f['المبلغ'].sum() if not pay_f.empty else 0)} ج")

# ===== 2. تحليل الخزينة =====
st.markdown("<div class='section-title'>🏦 تحليل إيرادات ومصروفات الخزينة</div>", unsafe_allow_html=True)

if not kh.empty:
    total_in  = kh["مدين"].sum()
    total_out = kh["دائن"].sum()
    net       = total_in - total_out

    c1, c2, c3, c4 = st.columns(4)
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
            rows += f"<tr><td>{t}</td><td class='num-pos'>{fmt(v)}</td><td class='num'>{pct:.1f}%</td><td><div style='background:#e8edf3;border-radius:3px;height:6px;width:80px;overflow:hidden'><div style='height:100%;width:{int(pct)}%;background:#1a7f74;border-radius:3px'></div></div></td></tr>"
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-pos'>{fmt(total_in)}</td><td>100%</td><td></td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th><th></th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

    with col_e:
        st.markdown("<div class='section-title'>📤 المصروفات حسب النوع</div>", unsafe_allow_html=True)
        exp = kh[kh["دائن"]>0].groupby("النوع")["دائن"].sum().sort_values(ascending=False)
        rows = ""
        for t, v in exp.items():
            pct = v/total_out*100 if total_out>0 else 0
            rows += f"<tr><td>{t}</td><td class='num-neg'>{fmt(v)}</td><td class='num'>{pct:.1f}%</td><td><div style='background:#e8edf3;border-radius:3px;height:6px;width:80px;overflow:hidden'><div style='height:100%;width:{int(pct)}%;background:#c0392b;border-radius:3px'></div></div></td></tr>"
        rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-neg'>{fmt(total_out)}</td><td>100%</td><td></td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>النوع</th><th>المبلغ</th><th>النسبة</th><th></th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

    # الملخص الشهري للخزينة
    st.markdown("<div class='section-title'>📅 الملخص الشهري للخزينة</div>", unsafe_allow_html=True)
    monthly = kh.groupby("الشهر").agg(إيرادات=("مدين","sum"), مصروفات=("دائن","sum")).reset_index()
    monthly["صافي"] = monthly["إيرادات"] - monthly["مصروفات"]
    rows = ""
    for _, r in monthly.sort_values("الشهر").iterrows():
        nc = "num-pos" if r["صافي"]>=0 else "num-neg"
        sign = "+" if r["صافي"]>=0 else ""
        rows += f"<tr><td><strong>{MONTHS_AR.get(int(r['الشهر']),'')}</strong></td><td class='num-pos'>{fmt(r['إيرادات'])}</td><td class='num-neg'>{fmt(r['مصروفات'])}</td><td class='{nc}'>{sign}{fmt(r['صافي'])}</td></tr>"
    rows += f"<tr class='total-row'><td>الإجمالي</td><td class='num-pos'>{fmt(total_in)}</td><td class='num-neg'>{fmt(total_out)}</td><td class='{"num-pos" if net>=0 else "num-neg"}'>{'+ ' if net>=0 else ''}{fmt(net)}</td></tr>"
    st.markdown(f"<table class='styled-table'><thead><tr><th>الشهر</th><th>الإيرادات</th><th>المصروفات</th><th>الصافي</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)

# ===== 3. ملخص اتقان =====
st.markdown("<div class='section-title'>🇦🇪 ملخص حركات اتقان للفترة</div>", unsafe_allow_html=True)

if not itqan_f.empty:
    c1, c2, c3, c4 = st.columns(4)
    with c1: st.metric("📥 إيداعات (AED)",  f"{fmt(itqan_f['مدين AED'].sum(),2)}")
    with c2: st.metric("📤 مصروفات (AED)", f"{fmt(itqan_f['دائن AED'].sum(),2)}")
    with c3: st.metric("📊 الصافي (AED)",   f"{fmt(itqan_f['مدين AED'].sum()-itqan_f['دائن AED'].sum(),2)}")
    with c4: st.metric("🔢 عدد الحركات",   f"{len(itqan_f):,}")

    rows = ""
    for _, r in itqan_f.iloc[::-1].head(50).iterrows():
        date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
        is_in = r["مدين AED"]>0
        badge = "<span style='background:#e0f4f2;color:#1a7f74;padding:1px 6px;border-radius:8px;font-size:10px'>إيداع</span>" if is_in else "<span style='background:#fdecea;color:#c0392b;padding:1px 6px;border-radius:8px;font-size:10px'>صرف</span>"
        debit  = f"<span class='num-pos'>{fmt(r['مدين AED'],2)}</span>" if r["مدين AED"]>0 else "—"
        credit = f"<span class='num-neg'>{fmt(r['دائن AED'],2)}</span>" if r["دائن AED"]>0 else "—"
        rows += f"<tr><td class='num'>{date_str}</td><td>{str(r['البيان'])[:40]}</td><td>{badge}</td><td>{debit}</td><td>{credit}</td><td class='{"num-neg" if r["الرصيد AED"]<0 else "num-pos"}'>{fmt(r['الرصيد AED'],2)}</td></tr>"
    st.markdown(f"<div style='overflow-x:auto'><table class='styled-table'><thead><tr><th>التاريخ</th><th>البيان</th><th>النوع</th><th>مدين AED</th><th>دائن AED</th><th>الرصيد AED</th></tr></thead><tbody>{rows}</tbody></table></div>", unsafe_allow_html=True)
else:
    st.info("لا توجد حركات اتقان في هذه الفترة")

# ===== 4. فواتير الفترة =====
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

# ===== 5. التحصيلات والسدادات =====
col_c, col_p = st.columns(2)

with col_c:
    st.markdown("<div class='section-title'>💰 التحصيلات</div>", unsafe_allow_html=True)
    if not coll_f.empty:
        rows = ""
        for _, r in coll_f.iterrows():
            date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
            rows += f"<tr><td class='num'>{date_str}</td><td>{r['العميل']}</td><td class='num-pos'>{fmt(r['المبلغ'])}</td></tr>"
        rows += f"<tr class='total-row'><td colspan='2'>الإجمالي</td><td class='num-pos'>{fmt(coll_f['المبلغ'].sum())}</td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>التاريخ</th><th>العميل</th><th>المبلغ</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)
    else:
        st.info("لا توجد تحصيلات في هذه الفترة")

with col_p:
    st.markdown("<div class='section-title'>💸 سدادات مسؤولي التوريد</div>", unsafe_allow_html=True)
    if not pay_f.empty:
        rows = ""
        for _, r in pay_f.iterrows():
            date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
            rows += f"<tr><td class='num'>{date_str}</td><td>{r['المسؤول']}</td><td class='num-pos'>{fmt(r['المبلغ'])}</td></tr>"
        rows += f"<tr class='total-row'><td colspan='2'>الإجمالي</td><td class='num-pos'>{fmt(pay_f['المبلغ'].sum())}</td></tr>"
        st.markdown(f"<table class='styled-table'><thead><tr><th>التاريخ</th><th>المسؤول</th><th>المبلغ</th></tr></thead><tbody>{rows}</tbody></table>", unsafe_allow_html=True)
    else:
        st.info("لا توجد سدادات في هذه الفترة")
