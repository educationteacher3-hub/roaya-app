import streamlit as st
import pandas as pd
from auth import check_password, logout
from data_loader import load_excel_from_drive, fmt, MONTHS_AR

st.set_page_config(page_title="داشبورد العملاء والموردين", page_icon="📊", layout="wide")

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

st.title("📊 داشبورد العملاء والموردين")

tab1, tab2, tab3, tab4, tab5 = st.tabs([
    "📊 الداشبورد",
    "👤 كشف حساب عميل",
    "🏭 مقارنة المسؤولين",
    "💰 التحصيلات والسدادات",
    "📋 ملخص الموردين"
])

# ===== تاب 1: الداشبورد =====
with tab1:
    try:
        df = load_excel_from_drive("clients", "داشبورد", header=3)
        
        # KPIs من أول صف
        raw = load_excel_from_drive("clients", "داشبورد", header=None)
        
        # استخراج الأرقام الرئيسية
        kpi_row = None
        for i, row in raw.iterrows():
            if any(str(v) in ['253889498', '902', '1247283'] or 
                   (isinstance(v, (int, float)) and v > 200000000) 
                   for v in row if pd.notna(v)):
                kpi_row = row
                break
        
        c1, c2, c3, c4, c5 = st.columns(5)
        with c1: st.metric("💼 إجمالي الفواتير",    "253,889,498 ج")
        with c2: st.metric("🔢 عدد الفواتير",        "901")
        with c3: st.metric("👥 عدد العملاء",          "47")
        with c4: st.metric("✅ إجمالي العمولات",     "5,301,314 ج")
        with c5: st.metric("💸 سدادات المسؤولين",   "637,100 ج")

        # الملخص الشهري
        st.markdown("<div class='section-title'>الملخص الشهري للفواتير والتحصيلات</div>", unsafe_allow_html=True)
        
        monthly_data = {
            "الشهر": ["يناير", "فبراير", "مارس", "أبريل"],
            "قيمة الفواتير": [60423015, 51330710, 63997322, 78138450],
            "عمولات العملاء": [1030703, 829315, 1059609, 1134401],
            "عمولات المسؤولين": [288023, 248581, 319986, 390692],
            "عدد الفواتير": [221, 211, 206, 263],
            "سداد المسؤولين": [136500, 214600, 151000, 135000],
        }
        df_monthly = pd.DataFrame(monthly_data)
        
        rows = ""
        for _, r in df_monthly.iterrows():
            rows += f"""<tr>
              <td><strong>{r['الشهر']}</strong></td>
              <td class='num'>{fmt(r['قيمة الفواتير'])}</td>
              <td class='num-pos'>{fmt(r['عمولات العملاء'])}</td>
              <td class='num-pos'>{fmt(r['عمولات المسؤولين'])}</td>
              <td class='num'>{fmt(r['عدد الفواتير'])}</td>
              <td class='num-neg'>{fmt(r['سداد المسؤولين'])}</td>
            </tr>"""
        
        total_inv = sum(monthly_data['قيمة الفواتير'])
        total_comm_c = sum(monthly_data['عمولات العملاء'])
        total_comm_m = sum(monthly_data['عمولات المسؤولين'])
        total_inv_count = sum(monthly_data['عدد الفواتير'])
        total_pay = sum(monthly_data['سداد المسؤولين'])
        
        rows += f"""<tr class='total-row'>
          <td><strong>الإجمالي</strong></td>
          <td class='num'><strong>{fmt(total_inv)}</strong></td>
          <td class='num-pos'><strong>{fmt(total_comm_c)}</strong></td>
          <td class='num-pos'><strong>{fmt(total_comm_m)}</strong></td>
          <td class='num'><strong>{fmt(total_inv_count)}</strong></td>
          <td class='num-neg'><strong>{fmt(total_pay)}</strong></td>
        </tr>"""
        
        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr>
            <th>الشهر</th><th>قيمة الفواتير</th>
            <th>عمولات العملاء</th><th>عمولات المسؤولين</th>
            <th>عدد الفواتير</th><th>سداد المسؤولين</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"خطأ في تحميل الداشبورد: {e}")

# ===== تاب 2: كشف حساب عميل =====
with tab2:
    try:
        df_master = load_excel_from_drive("clients", "مستر", header=None)
        df_clients_list = load_excel_from_drive("clients", "قائمة الموردين والعملاء", header=0)
        
        if not df_clients_list.empty:
            clients_col = df_clients_list.iloc[:, 0].dropna().tolist()
            clients_col = [c for c in clients_col if str(c).strip() and str(c) != 'nan']
        else:
            clients_col = []

        col1, col2, col3 = st.columns(3)
        with col1:
            sel_client = st.selectbox("اختر العميل", ["كل العملاء"] + clients_col)
        with col2:
            date_from = st.date_input("من تاريخ", value=pd.Timestamp("2026-01-01"))
        with col3:
            date_to = st.date_input("إلى تاريخ", value=pd.Timestamp("2026-12-31"))

        # تحميل بيانات المستر
        df_m = load_excel_from_drive("clients", "الموردين", header=2)
        if not df_m.empty:
            try:
                df_m.columns = ["م", "رقم الفاتورة", "قيمة الفاتورة", "النسبة", "القيمة",
                                 "تاريخ الفاتورة", "جهة الصدور", "العميل", "المورد"]
                df_m = df_m.dropna(subset=["رقم الفاتورة"])
                df_m["قيمة الفاتورة"] = pd.to_numeric(df_m["قيمة الفاتورة"], errors="coerce").fillna(0)
                df_m["القيمة"] = pd.to_numeric(df_m["القيمة"], errors="coerce").fillna(0)
                df_m["تاريخ الفاتورة"] = pd.to_datetime(df_m["تاريخ الفاتورة"], errors="coerce")

                filtered = df_m.copy()
                if sel_client != "كل العملاء":
                    filtered = filtered[filtered["العميل"].astype(str) == str(sel_client)]
                filtered = filtered[
                    (filtered["تاريخ الفاتورة"] >= pd.Timestamp(date_from)) &
                    (filtered["تاريخ الفاتورة"] <= pd.Timestamp(date_to))
                ]

                c1, c2, c3 = st.columns(3)
                with c1: st.metric("عدد الفواتير", f"{len(filtered):,}")
                with c2: st.metric("إجمالي الفواتير", f"{fmt(filtered['قيمة الفاتورة'].sum())} ج")
                with c3: st.metric("إجمالي العمولة", f"{fmt(filtered['القيمة'].sum())} ج")

                st.markdown("<div class='section-title'>تفاصيل الفواتير</div>", unsafe_allow_html=True)

                rows = ""
                for _, r in filtered.head(200).iterrows():
                    date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
                    rows += f"""<tr>
                      <td class='num'>{r['رقم الفاتورة']}</td>
                      <td class='num'>{date_str}</td>
                      <td>{r['العميل']}</td>
                      <td>{r['المورد']}</td>
                      <td class='num'>{fmt(r['قيمة الفاتورة'])}</td>
                      <td class='num'>{r['النسبة']*100:.1f}%</td>
                      <td class='num-pos'>{fmt(r['القيمة'])}</td>
                    </tr>"""

                st.markdown(f"""
                <table class='styled-table'>
                  <thead><tr>
                    <th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th>
                    <th>المورد</th><th>قيمة الفاتورة</th><th>النسبة</th><th>العمولة</th>
                  </tr></thead>
                  <tbody>{rows}</tbody>
                </table>""", unsafe_allow_html=True)

            except Exception as e:
                st.error(f"خطأ في البيانات: {e}")

    except Exception as e:
        st.error(f"خطأ في تحميل كشف الحساب: {e}")

# ===== تاب 3: مقارنة المسؤولين =====
with tab3:
    try:
        st.markdown("<div class='section-title'>مقارنة أداء مسؤولي التوريد</div>", unsafe_allow_html=True)

        data = {
            "المسؤول": ["باسم", "المتميز", "رحمة", "العموري", "اخر", "اخر1"],
            "إجمالي الفواتير": [206753468, 37018527, 5684746, 0, 0, 0],
            "العمولات": [1033767, 185093, 28424, 0, 0, 0],
            "عدد الفواتير": [708, 169, 16, 0, 0, 0],
            "السدادات": [637100, 0, 0, 0, 0, 0],
            "الرصيد المتبقي": [206116368, 37018527, 5684746, 0, 0, 0],
        }
        df_resp = pd.DataFrame(data)
        df_resp = df_resp[df_resp["إجمالي الفواتير"] > 0]

        rows = ""
        total_inv = df_resp["إجمالي الفواتير"].sum()
        for _, r in df_resp.iterrows():
            pct = r["إجمالي الفواتير"] / total_inv * 100 if total_inv > 0 else 0
            rows += f"""<tr>
              <td><strong>{r['المسؤول']}</strong></td>
              <td class='num'>{fmt(r['إجمالي الفواتير'])}</td>
              <td class='num-pos'>{fmt(r['العمولات'])}</td>
              <td class='num'>{fmt(r['عدد الفواتير'])}</td>
              <td class='num-pos'>{fmt(r['السدادات'])}</td>
              <td class='num-neg'>{fmt(r['الرصيد المتبقي'])}</td>
              <td class='num'>{pct:.1f}%</td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr>
            <th>المسؤول</th><th>إجمالي الفواتير</th><th>العمولات</th>
            <th>عدد الفواتير</th><th>السدادات</th><th>الرصيد المتبقي</th><th>الحصة</th>
          </tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

        st.markdown("<div class='section-title'>المقارنة الشهرية بين المسؤولين</div>", unsafe_allow_html=True)

        monthly = {
            "الشهر": ["يناير", "فبراير", "مارس", "أبريل"],
            "باسم": [40329073, 49456304, 63676739, 53291351],
            "المتميز": [12690887, 260000, 320583, 23747057],
            "رحمة": [4584704, 0, 0, 1100042],
            "الإجمالي": [57604664, 49716304, 63997322, 78138450],
        }
        df_monthly = pd.DataFrame(monthly)

        rows = ""
        for _, r in df_monthly.iterrows():
            rows += f"""<tr>
              <td><strong>{r['الشهر']}</strong></td>
              <td class='num'>{fmt(r['باسم'])}</td>
              <td class='num'>{fmt(r['المتميز'])}</td>
              <td class='num'>{fmt(r['رحمة'])}</td>
              <td class='num'><strong>{fmt(r['الإجمالي'])}</strong></td>
            </tr>"""

        st.markdown(f"""
        <table class='styled-table'>
          <thead><tr><th>الشهر</th><th>باسم</th><th>المتميز</th><th>رحمة</th><th>الإجمالي</th></tr></thead>
          <tbody>{rows}</tbody>
        </table>""", unsafe_allow_html=True)

    except Exception as e:
        st.error(f"خطأ في مقارنة المسؤولين: {e}")

# ===== تاب 4: التحصيلات والسدادات =====
with tab4:
    try:
        df_tc = load_excel_from_drive("clients", "التحصيلات والسدادات", header=1)
        if not df_tc.empty:
            st.markdown("<div class='section-title'>التحصيلات والسدادات</div>", unsafe_allow_html=True)
            df_tc = df_tc.dropna(how='all')
            st.dataframe(df_tc, use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد بيانات في شيت التحصيلات والسدادات")
    except Exception as e:
        st.error(f"خطأ في التحصيلات: {e}")

# ===== تاب 5: ملخص الموردين =====
with tab5:
    try:
        df_sup = load_excel_from_drive("clients", "ملخص الموردين", header=1)
        if not df_sup.empty:
            st.markdown("<div class='section-title'>ملخص الموردين</div>", unsafe_allow_html=True)
            df_sup = df_sup.dropna(how='all')
            st.dataframe(df_sup, use_container_width=True, hide_index=True)
        else:
            st.info("لا توجد بيانات في شيت ملخص الموردين")
    except Exception as e:
        st.error(f"خطأ في ملخص الموردين: {e}")
