import streamlit as st
import pandas as pd
import io
from auth import check_password
from data_loader import load_excel_from_drive, load_suppliers, load_clients_list, fmt, MONTHS_AR

st.set_page_config(page_title="كشف الحساب", page_icon="📋", layout="wide")

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
.summary-box { background:white; border:1px solid #d4dce5; border-radius:10px; padding:16px; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("📋 كشف الحساب")

tab1, tab2 = st.tabs(["👤 كشف حساب عميل", "🏭 كشف حساب مسؤول توريد"])

# ===== تحميل البيانات =====
@st.cache_data(ttl=300)
def load_collections():
    try:
        df = load_excel_from_drive("clients", "التحصيلات والسدادات", header=3)
        # العمود الأول: تاريخ، الثاني: عميل، الثالث: طريقة، الرابع: مبلغ
        # العمود الثامن: تاريخ، التاسع: مسؤول، العاشر: طريقة، الحادي عشر: مبلغ
        clients_collections = df.iloc[:, :6].copy()
        clients_collections.columns = ["التاريخ", "العميل", "طريقة التحصيل", "المبلغ", "ملاحظات", "مرجعي"]
        clients_collections = clients_collections.dropna(subset=["العميل"])
        clients_collections["المبلغ"] = pd.to_numeric(clients_collections["المبلغ"], errors="coerce").fillna(0)
        clients_collections["التاريخ"] = pd.to_datetime(clients_collections["التاريخ"], errors="coerce")
        clients_collections["الشهر"] = clients_collections["التاريخ"].dt.month
        clients_collections["السنة"] = clients_collections["التاريخ"].dt.year

        suppliers_payments = df.iloc[:, 7:12].copy()
        suppliers_payments.columns = ["التاريخ", "المسؤول", "طريقة السداد", "المبلغ", "ملاحظات"]
        suppliers_payments = suppliers_payments.dropna(subset=["المسؤول"])
        suppliers_payments["المبلغ"] = pd.to_numeric(suppliers_payments["المبلغ"], errors="coerce").fillna(0)
        suppliers_payments["التاريخ"] = pd.to_datetime(suppliers_payments["التاريخ"], errors="coerce")
        suppliers_payments["الشهر"] = suppliers_payments["التاريخ"].dt.month
        suppliers_payments["السنة"] = suppliers_payments["التاريخ"].dt.year

        return clients_collections, suppliers_payments
    except Exception as e:
        st.error(f"خطأ في تحميل التحصيلات: {e}")
        return pd.DataFrame(), pd.DataFrame()

df_invoices = load_suppliers()
clients_list, suppliers_list = load_clients_list()
df_client_coll, df_sup_pay = load_collections()

# ===== تاب 1: كشف حساب عميل =====
with tab1:
    clients_names = ["اختر عميل"] + (clients_list["العميل"].tolist() if not clients_list.empty else [])

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        sel_client = st.selectbox("العميل", clients_names)
    with col2:
        year_options = ["كل السنوات"] + sorted(df_invoices["تاريخ الفاتورة"].dt.year.dropna().unique().astype(int).tolist(), reverse=True) if not df_invoices.empty else ["كل السنوات"]
        sel_year = st.selectbox("السنة", year_options)
    with col3:
        export_btn = st.button("⬇ تصدير Excel", key="exp_client")

    if sel_client == "اختر عميل":
        st.info("اختر عميلاً من القائمة لعرض كشف حسابه")
    else:
        # فلترة الفواتير
        inv = df_invoices[df_invoices["العميل"].astype(str) == sel_client].copy() if not df_invoices.empty else pd.DataFrame()
        if sel_year != "كل السنوات" and not inv.empty:
            inv = inv[inv["تاريخ الفاتورة"].dt.year == int(sel_year)]

        # فلترة التحصيلات
        coll = df_client_coll[df_client_coll["العميل"].astype(str) == sel_client].copy() if not df_client_coll.empty else pd.DataFrame()
        if sel_year != "كل السنوات" and not coll.empty:
            coll = coll[coll["السنة"] == int(sel_year)]

        # KPIs
        total_inv   = inv["قيمة الفاتورة"].sum() if not inv.empty else 0
        total_comm  = inv["القيمة"].sum() if not inv.empty else 0
        total_coll  = coll["المبلغ"].sum() if not coll.empty else 0
        remaining   = total_comm - total_coll

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("💼 إجمالي الفواتير", f"{fmt(total_inv)} ج")
        with c2: st.metric("✅ العمولة المستحقة", f"{fmt(total_comm)} ج")
        with c3: st.metric("💰 المحصّل", f"{fmt(total_coll)} ج")
        with c4: st.metric("⏳ المتبقي", f"{fmt(remaining)} ج",
                           delta=f"-{fmt(remaining)} ج" if remaining > 0 else "✅ مسدد")

        # ملخص شهري
        st.markdown("<div class='section-title'>الملخص الشهري</div>", unsafe_allow_html=True)

        if not inv.empty:
            inv["الشهر"] = inv["تاريخ الفاتورة"].dt.month
            inv["السنة"] = inv["تاريخ الفاتورة"].dt.year
            monthly_inv = inv.groupby(["السنة", "الشهر"]).agg(
                عدد_الفواتير=("رقم الفاتورة", "count"),
                قيمة_الفواتير=("قيمة الفاتورة", "sum"),
                العمولة=("القيمة", "sum")
            ).reset_index()

            monthly_coll = pd.DataFrame()
            if not coll.empty:
                monthly_coll = coll.groupby(["السنة", "الشهر"])["المبلغ"].sum().reset_index()
                monthly_coll.columns = ["السنة", "الشهر", "المحصل"]

            rows = ""
            for _, r in monthly_inv.iterrows():
                month_name = MONTHS_AR.get(int(r["الشهر"]), str(r["الشهر"]))
                محصل = 0
                if not monthly_coll.empty:
                    m = monthly_coll[(monthly_coll["السنة"]==r["السنة"]) & (monthly_coll["الشهر"]==r["الشهر"])]
                    if not m.empty:
                        محصل = m["المحصل"].iloc[0]
                متبقي = r["العمولة"] - محصل
                rows += f"""<tr>
                  <td>{month_name} {int(r['السنة'])}</td>
                  <td class='num'>{fmt(r['عدد_الفواتير'])}</td>
                  <td class='num'>{fmt(r['قيمة_الفواتير'])}</td>
                  <td class='num-pos'>{fmt(r['العمولة'])}</td>
                  <td class='num-pos'>{fmt(محصل)}</td>
                  <td class='{"num-neg" if متبقي > 0 else "num-pos"}'>{fmt(متبقي)}</td>
                </tr>"""

            rows += f"""<tr class='total-row'>
              <td><strong>الإجمالي</strong></td>
              <td class='num'><strong>{fmt(len(inv))}</strong></td>
              <td class='num'><strong>{fmt(total_inv)}</strong></td>
              <td class='num-pos'><strong>{fmt(total_comm)}</strong></td>
              <td class='num-pos'><strong>{fmt(total_coll)}</strong></td>
              <td class='{"num-neg" if remaining > 0 else "num-pos"}'><strong>{fmt(remaining)}</strong></td>
            </tr>"""

            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>الشهر</th><th>عدد الفواتير</th><th>قيمة الفواتير</th>
                         <th>العمولة المستحقة</th><th>المحصّل</th><th>المتبقي</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # تفاصيل الفواتير
        st.markdown("<div class='section-title'>تفاصيل الفواتير</div>", unsafe_allow_html=True)
        if not inv.empty:
            rows = ""
            for _, r in inv.iterrows():
                date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{r['رقم الفاتورة']}</td>
                  <td class='num'>{date_str}</td>
                  <td>{r['المورد']}</td>
                  <td class='num'>{fmt(r['قيمة الفاتورة'])}</td>
                  <td class='num'>{r['النسبة']*100:.1f}%</td>
                  <td class='num-pos'>{fmt(r['القيمة'])}</td>
                </tr>"""
            st.markdown(f"""<div style='overflow-x:auto'><table class='styled-table'>
              <thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>المورد</th>
                         <th>قيمة الفاتورة</th><th>النسبة</th><th>العمولة</th></tr></thead>
              <tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

        # التحصيلات
        if not coll.empty:
            st.markdown("<div class='section-title'>سجل التحصيلات</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in coll.iterrows():
                date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{date_str}</td>
                  <td>{r.get('طريقة التحصيل','—')}</td>
                  <td class='num-pos'>{fmt(r['المبلغ'])}</td>
                  <td>{r.get('ملاحظات','')}</td>
                </tr>"""
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>التاريخ</th><th>طريقة التحصيل</th><th>المبلغ</th><th>ملاحظات</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # تصدير
        if export_btn and not inv.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                inv.to_excel(writer, sheet_name="الفواتير", index=False)
                if not coll.empty:
                    coll.to_excel(writer, sheet_name="التحصيلات", index=False)
            st.download_button("📥 تحميل كشف الحساب", buf.getvalue(),
                               file_name=f"كشف_حساب_{sel_client}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ===== تاب 2: كشف حساب مسؤول =====
with tab2:
    sup_names = ["اختر مسؤول"] + (suppliers_list["المورد"].tolist() if not suppliers_list.empty else [])

    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        sel_sup = st.selectbox("مسؤول التوريد", sup_names)
    with col2:
        year_options2 = ["كل السنوات"] + sorted(df_invoices["تاريخ الفاتورة"].dt.year.dropna().unique().astype(int).tolist(), reverse=True) if not df_invoices.empty else ["كل السنوات"]
        sel_year2 = st.selectbox("السنة", year_options2, key="sup_year")
    with col3:
        export_btn2 = st.button("⬇ تصدير Excel", key="exp_sup")

    if sel_sup == "اختر مسؤول":
        st.info("اختر مسؤول توريد من القائمة لعرض كشف حسابه")
    else:
        # فلترة الفواتير
        inv2 = df_invoices[df_invoices["المورد"].astype(str) == sel_sup].copy() if not df_invoices.empty else pd.DataFrame()
        if sel_year2 != "كل السنوات" and not inv2.empty:
            inv2 = inv2[inv2["تاريخ الفاتورة"].dt.year == int(sel_year2)]

        # فلترة السدادات
        pay = df_sup_pay[df_sup_pay["المسؤول"].astype(str) == sel_sup].copy() if not df_sup_pay.empty else pd.DataFrame()
        if sel_year2 != "كل السنوات" and not pay.empty:
            pay = pay[pay["السنة"] == int(sel_year2)]

        # KPIs
        total_inv2  = inv2["قيمة الفاتورة"].sum() if not inv2.empty else 0
        total_comm2 = inv2["القيمة"].sum() if not inv2.empty else 0
        total_pay2  = pay["المبلغ"].sum() if not pay.empty else 0
        remaining2  = total_comm2 - total_pay2

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("💼 إجمالي الفواتير", f"{fmt(total_inv2)} ج")
        with c2: st.metric("✅ العمولة المستحقة", f"{fmt(total_comm2)} ج")
        with c3: st.metric("💰 المسدود", f"{fmt(total_pay2)} ج")
        with c4: st.metric("⏳ المتبقي", f"{fmt(remaining2)} ج",
                           delta=f"-{fmt(remaining2)} ج" if remaining2 > 0 else "✅ مسدد")

        # ملخص شهري
        st.markdown("<div class='section-title'>الملخص الشهري</div>", unsafe_allow_html=True)

        if not inv2.empty:
            inv2["الشهر"] = inv2["تاريخ الفاتورة"].dt.month
            inv2["السنة_f"] = inv2["تاريخ الفاتورة"].dt.year
            monthly_inv2 = inv2.groupby(["السنة_f", "الشهر"]).agg(
                عدد_الفواتير=("رقم الفاتورة", "count"),
                قيمة_الفواتير=("قيمة الفاتورة", "sum"),
                العمولة=("القيمة", "sum")
            ).reset_index()

            monthly_pay = pd.DataFrame()
            if not pay.empty:
                monthly_pay = pay.groupby(["السنة", "الشهر"])["المبلغ"].sum().reset_index()
                monthly_pay.columns = ["السنة", "الشهر", "المسدد"]

            rows = ""
            for _, r in monthly_inv2.iterrows():
                month_name = MONTHS_AR.get(int(r["الشهر"]), str(r["الشهر"]))
                مسدد = 0
                if not monthly_pay.empty:
                    m = monthly_pay[(monthly_pay["السنة"]==r["السنة_f"]) & (monthly_pay["الشهر"]==r["الشهر"])]
                    if not m.empty:
                        مسدد = m["المسدد"].iloc[0]
                متبقي = r["العمولة"] - مسدد
                rows += f"""<tr>
                  <td>{month_name} {int(r['السنة_f'])}</td>
                  <td class='num'>{fmt(r['عدد_الفواتير'])}</td>
                  <td class='num'>{fmt(r['قيمة_الفواتير'])}</td>
                  <td class='num-pos'>{fmt(r['العمولة'])}</td>
                  <td class='num-pos'>{fmt(مسدد)}</td>
                  <td class='{"num-neg" if متبقي > 0 else "num-pos"}'>{fmt(متبقي)}</td>
                </tr>"""

            rows += f"""<tr class='total-row'>
              <td><strong>الإجمالي</strong></td>
              <td class='num'><strong>{fmt(len(inv2))}</strong></td>
              <td class='num'><strong>{fmt(total_inv2)}</strong></td>
              <td class='num-pos'><strong>{fmt(total_comm2)}</strong></td>
              <td class='num-pos'><strong>{fmt(total_pay2)}</strong></td>
              <td class='{"num-neg" if remaining2 > 0 else "num-pos"}'><strong>{fmt(remaining2)}</strong></td>
            </tr>"""

            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>الشهر</th><th>عدد الفواتير</th><th>قيمة الفواتير</th>
                         <th>العمولة المستحقة</th><th>المسدود</th><th>المتبقي</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # سجل السدادات
        if not pay.empty:
            st.markdown("<div class='section-title'>سجل السدادات</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in pay.iterrows():
                date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{date_str}</td>
                  <td>{r.get('طريقة السداد','—')}</td>
                  <td class='num-pos'>{fmt(r['المبلغ'])}</td>
                  <td>{r.get('ملاحظات','')}</td>
                </tr>"""
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>التاريخ</th><th>طريقة السداد</th><th>المبلغ</th><th>ملاحظات</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        if export_btn2 and not inv2.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                inv2.to_excel(writer, sheet_name="الفواتير", index=False)
                if not pay.empty:
                    pay.to_excel(writer, sheet_name="السدادات", index=False)
            st.download_button("📥 تحميل كشف الحساب", buf.getvalue(),
                               file_name=f"كشف_حساب_{sel_sup}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
