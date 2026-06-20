import streamlit as st
import pandas as pd
import io
from auth import check_password
from data_loader import load_excel_from_drive, fmt, MONTHS_AR

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
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("📋 كشف الحساب")

# ===== تحميل البيانات =====
@st.cache_data(ttl=300)
def load_all_data():
    # شيت الموردين (الفواتير)
    df_inv = load_excel_from_drive("clients", "الموردين", header=2)
    if not df_inv.empty:
        df_inv.columns = ["م", "رقم الفاتورة", "قيمة الفاتورة", "نسبة_المورد", "عمولة_المورد",
                          "تاريخ الفاتورة", "جهة الصدور", "العميل", "المورد"]
        df_inv = df_inv.dropna(subset=["رقم الفاتورة"])
        df_inv["قيمة الفاتورة"] = pd.to_numeric(df_inv["قيمة الفاتورة"], errors="coerce").fillna(0)
        df_inv["نسبة_المورد"]   = pd.to_numeric(df_inv["نسبة_المورد"],   errors="coerce").fillna(0)
        df_inv["عمولة_المورد"]  = pd.to_numeric(df_inv["عمولة_المورد"],  errors="coerce").fillna(0)
        df_inv["تاريخ الفاتورة"] = pd.to_datetime(df_inv["تاريخ الفاتورة"], errors="coerce")
        df_inv["الشهر"] = df_inv["تاريخ الفاتورة"].dt.month
        df_inv["السنة"] = df_inv["تاريخ الفاتورة"].dt.year

    # شيت قائمة العملاء والموردين (فيه النسب الصح)
    df_list = load_excel_from_drive("clients", "قائمة الموردين والعملاء", header=0)
    
    clients_rates = {}
    suppliers_rates = {}
    clients_names = []
    suppliers_names = []
    
    if not df_list.empty:
        # العملاء في العمود 0 و 1
        for _, row in df_list.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
                name = str(row.iloc[0]).strip()
                rate = pd.to_numeric(row.iloc[1], errors="coerce") if pd.notna(row.iloc[1]) else 0
                clients_rates[name] = rate
                clients_names.append(name)
            # الموردين في العمود 2 و 3
            if len(row) > 2 and pd.notna(row.iloc[2]) and str(row.iloc[2]).strip():
                name = str(row.iloc[2]).strip()
                rate = pd.to_numeric(row.iloc[3], errors="coerce") if pd.notna(row.iloc[3]) else 0
                suppliers_rates[name] = rate
                suppliers_names.append(name)

    # إضافة نسبة العميل الصح للفواتير
    if not df_inv.empty:
        df_inv["نسبة_العميل"] = df_inv["العميل"].map(clients_rates).fillna(0)
        df_inv["عمولة_العميل"] = df_inv["قيمة الفاتورة"] * df_inv["نسبة_العميل"]
        df_inv["نسبة_المورد_فعلية"] = df_inv["المورد"].map(suppliers_rates).fillna(df_inv["نسبة_المورد"])
        df_inv["عمولة_المورد_فعلية"] = df_inv["قيمة الفاتورة"] * df_inv["نسبة_المورد_فعلية"]

    # التحصيلات والسدادات
    try:
        df_coll = load_excel_from_drive("clients", "التحصيلات والسدادات", header=3)
        client_coll = df_coll.iloc[:, :5].copy()
        client_coll.columns = ["التاريخ", "العميل", "طريقة التحصيل", "المبلغ", "ملاحظات"]
        client_coll = client_coll.dropna(subset=["العميل"])
        client_coll = client_coll[client_coll["العميل"].astype(str).str.strip() != ""]
        client_coll["المبلغ"] = pd.to_numeric(client_coll["المبلغ"], errors="coerce").fillna(0)
        client_coll["التاريخ"] = pd.to_datetime(client_coll["التاريخ"], errors="coerce")
        client_coll["الشهر"] = client_coll["التاريخ"].dt.month
        client_coll["السنة"] = client_coll["التاريخ"].dt.year

        sup_pay = df_coll.iloc[:, 7:12].copy()
        sup_pay.columns = ["التاريخ", "المسؤول", "طريقة السداد", "المبلغ", "ملاحظات"]
        sup_pay = sup_pay.dropna(subset=["المسؤول"])
        sup_pay = sup_pay[sup_pay["المسؤول"].astype(str).str.strip() != ""]
        sup_pay["المبلغ"] = pd.to_numeric(sup_pay["المبلغ"], errors="coerce").fillna(0)
        sup_pay["التاريخ"] = pd.to_datetime(sup_pay["التاريخ"], errors="coerce")
        sup_pay["الشهر"] = sup_pay["التاريخ"].dt.month
        sup_pay["السنة"] = sup_pay["التاريخ"].dt.year
    except:
        client_coll = pd.DataFrame()
        sup_pay = pd.DataFrame()

    return df_inv, clients_rates, suppliers_rates, clients_names, suppliers_names, client_coll, sup_pay

df_inv, clients_rates, suppliers_rates, clients_names, suppliers_names, client_coll, sup_pay = load_all_data()

tab1, tab2 = st.tabs(["👤 كشف حساب عميل", "🏭 كشف حساب مسؤول توريد"])

# ===== تاب 1: كشف حساب عميل =====
with tab1:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        sel_client = st.selectbox("العميل", ["اختر عميل"] + clients_names)
    with col2:
        years = sorted(df_inv["السنة"].dropna().unique().astype(int).tolist(), reverse=True) if not df_inv.empty else []
        sel_year = st.selectbox("السنة", ["كل السنوات"] + [str(y) for y in years])
    with col3:
        export_btn = st.button("⬇ تصدير Excel", key="exp_client")

    if sel_client == "اختر عميل":
        st.info("اختر عميلاً من القائمة لعرض كشف حسابه")
    else:
        # نسبة العميل
        client_rate = clients_rates.get(sel_client, 0)
        st.markdown(f"<div style='background:#fdf3e3;border-radius:8px;padding:10px 14px;margin-bottom:12px;direction:rtl'>"
                    f"<strong>نسبة عمولة العميل: {client_rate*100:.2f}%</strong></div>",
                    unsafe_allow_html=True)

        # فلترة
        inv = df_inv[df_inv["العميل"].astype(str) == sel_client].copy() if not df_inv.empty else pd.DataFrame()
        if sel_year != "كل السنوات" and not inv.empty:
            inv = inv[inv["السنة"] == int(sel_year)]

        coll = client_coll[client_coll["العميل"].astype(str) == sel_client].copy() if not client_coll.empty else pd.DataFrame()
        if sel_year != "كل السنوات" and not coll.empty:
            coll = coll[coll["السنة"] == int(sel_year)]

        total_inv  = inv["قيمة الفاتورة"].sum() if not inv.empty else 0
        total_comm = inv["عمولة_العميل"].sum() if not inv.empty else 0
        total_coll = coll["المبلغ"].sum() if not coll.empty else 0
        remaining  = total_comm - total_coll

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("💼 إجمالي الفواتير",    f"{fmt(total_inv)} ج")
        with c2: st.metric("✅ العمولة المستحقة",    f"{fmt(total_comm)} ج")
        with c3: st.metric("💰 المحصّل",             f"{fmt(total_coll)} ج")
        with c4: st.metric("⏳ المتبقي",             f"{fmt(remaining)} ج")

        # ملخص شهري
        if not inv.empty:
            st.markdown("<div class='section-title'>الملخص الشهري</div>", unsafe_allow_html=True)
            monthly = inv.groupby(["السنة", "الشهر"]).agg(
                عدد=("رقم الفاتورة","count"),
                قيمة=("قيمة الفاتورة","sum"),
                عمولة=("عمولة_العميل","sum")
            ).reset_index()

            rows = ""
            grand_coll = 0
            for _, r in monthly.sort_values(["السنة","الشهر"]).iterrows():
                month_name = MONTHS_AR.get(int(r["الشهر"]), "")
                محصل = 0
                if not coll.empty:
                    m = coll[(coll["السنة"]==r["السنة"]) & (coll["الشهر"]==r["الشهر"])]
                    محصل = m["المبلغ"].sum()
                grand_coll += محصل
                متبقي = r["عمولة"] - محصل
                rows += f"""<tr>
                  <td>{month_name} {int(r["السنة"])}</td>
                  <td class='num'>{fmt(r["عدد"])}</td>
                  <td class='num'>{fmt(r["قيمة"])}</td>
                  <td class='num'>{client_rate*100:.2f}%</td>
                  <td class='num-pos'>{fmt(r["عمولة"])}</td>
                  <td class='num-pos'>{fmt(محصل)}</td>
                  <td class='{"num-neg" if متبقي>0 else "num-pos"}'>{fmt(متبقي)}</td>
                </tr>"""

            rows += f"""<tr class='total-row'>
              <td><strong>الإجمالي</strong></td>
              <td class='num'>{fmt(len(inv))}</td>
              <td class='num'>{fmt(total_inv)}</td>
              <td class='num'>{client_rate*100:.2f}%</td>
              <td class='num-pos'>{fmt(total_comm)}</td>
              <td class='num-pos'>{fmt(total_coll)}</td>
              <td class='{"num-neg" if remaining>0 else "num-pos"}'>{fmt(remaining)}</td>
            </tr>"""

            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>الشهر</th><th>عدد الفواتير</th><th>قيمة الفواتير</th>
                <th>النسبة</th><th>العمولة المستحقة</th><th>المحصّل</th><th>المتبقي</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # تفاصيل الفواتير
        if not inv.empty:
            st.markdown("<div class='section-title'>تفاصيل الفواتير</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in inv.sort_values("تاريخ الفاتورة").iterrows():
                date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{r["رقم الفاتورة"]}</td>
                  <td class='num'>{date_str}</td>
                  <td>{r["المورد"]}</td>
                  <td class='num'>{fmt(r["قيمة الفاتورة"])}</td>
                  <td class='num'>{r["نسبة_العميل"]*100:.2f}%</td>
                  <td class='num-pos'>{fmt(r["عمولة_العميل"])}</td>
                </tr>"""
            st.markdown(f"""<div style='overflow-x:auto'><table class='styled-table'>
              <thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>المورد</th>
                <th>قيمة الفاتورة</th><th>نسبة العميل</th><th>عمولة العميل</th></tr></thead>
              <tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

        # التحصيلات
        if not coll.empty:
            st.markdown("<div class='section-title'>سجل التحصيلات</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in coll.iterrows():
                date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{date_str}</td>
                  <td>{r.get("طريقة التحصيل","—")}</td>
                  <td class='num-pos'>{fmt(r["المبلغ"])}</td>
                  <td>{r.get("ملاحظات","")}</td>
                </tr>"""
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>التاريخ</th><th>طريقة التحصيل</th><th>المبلغ</th><th>ملاحظات</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        if export_btn and not inv.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                inv[["رقم الفاتورة","تاريخ الفاتورة","العميل","المورد",
                     "قيمة الفاتورة","نسبة_العميل","عمولة_العميل"]].to_excel(
                    writer, sheet_name="الفواتير", index=False)
                if not coll.empty:
                    coll.to_excel(writer, sheet_name="التحصيلات", index=False)
            st.download_button("📥 تحميل كشف الحساب", buf.getvalue(),
                               file_name=f"كشف_حساب_{sel_client}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")

# ===== تاب 2: كشف حساب مسؤول =====
with tab2:
    col1, col2, col3 = st.columns([2, 1, 1])
    with col1:
        sel_sup = st.selectbox("مسؤول التوريد", ["اختر مسؤول"] + suppliers_names)
    with col2:
        years2 = sorted(df_inv["السنة"].dropna().unique().astype(int).tolist(), reverse=True) if not df_inv.empty else []
        sel_year2 = st.selectbox("السنة", ["كل السنوات"] + [str(y) for y in years2], key="sup_year")
    with col3:
        export_btn2 = st.button("⬇ تصدير Excel", key="exp_sup")

    if sel_sup == "اختر مسؤول":
        st.info("اختر مسؤول توريد من القائمة لعرض كشف حسابه")
    else:
        sup_rate = suppliers_rates.get(sel_sup, 0)
        st.markdown(f"<div style='background:#e0f4f2;border-radius:8px;padding:10px 14px;margin-bottom:12px;direction:rtl'>"
                    f"<strong>نسبة عمولة المسؤول: {sup_rate*100:.2f}%</strong></div>",
                    unsafe_allow_html=True)

        inv2 = df_inv[df_inv["المورد"].astype(str) == sel_sup].copy() if not df_inv.empty else pd.DataFrame()
        if sel_year2 != "كل السنوات" and not inv2.empty:
            inv2 = inv2[inv2["السنة"] == int(sel_year2)]

        pay = sup_pay[sup_pay["المسؤول"].astype(str) == sel_sup].copy() if not sup_pay.empty else pd.DataFrame()
        if sel_year2 != "كل السنوات" and not pay.empty:
            pay = pay[pay["السنة"] == int(sel_year2)]

        total_inv2  = inv2["قيمة الفاتورة"].sum() if not inv2.empty else 0
        total_comm2 = inv2["عمولة_المورد_فعلية"].sum() if not inv2.empty else 0
        total_pay2  = pay["المبلغ"].sum() if not pay.empty else 0
        remaining2  = total_comm2 - total_pay2

        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("💼 إجمالي الفواتير",    f"{fmt(total_inv2)} ج")
        with c2: st.metric("✅ العمولة المستحقة",    f"{fmt(total_comm2)} ج")
        with c3: st.metric("💰 المسدود",             f"{fmt(total_pay2)} ج")
        with c4: st.metric("⏳ المتبقي",             f"{fmt(remaining2)} ج")

        # ملخص شهري
        if not inv2.empty:
            st.markdown("<div class='section-title'>الملخص الشهري</div>", unsafe_allow_html=True)
            monthly2 = inv2.groupby(["السنة", "الشهر"]).agg(
                عدد=("رقم الفاتورة","count"),
                قيمة=("قيمة الفاتورة","sum"),
                عمولة=("عمولة_المورد_فعلية","sum")
            ).reset_index()

            rows = ""
            for _, r in monthly2.sort_values(["السنة","الشهر"]).iterrows():
                month_name = MONTHS_AR.get(int(r["الشهر"]), "")
                مسدد = 0
                if not pay.empty:
                    m = pay[(pay["السنة"]==r["السنة"]) & (pay["الشهر"]==r["الشهر"])]
                    مسدد = m["المبلغ"].sum()
                متبقي = r["عمولة"] - مسدد
                rows += f"""<tr>
                  <td>{month_name} {int(r["السنة"])}</td>
                  <td class='num'>{fmt(r["عدد"])}</td>
                  <td class='num'>{fmt(r["قيمة"])}</td>
                  <td class='num'>{sup_rate*100:.2f}%</td>
                  <td class='num-pos'>{fmt(r["عمولة"])}</td>
                  <td class='num-pos'>{fmt(مسدد)}</td>
                  <td class='{"num-neg" if متبقي>0 else "num-pos"}'>{fmt(متبقي)}</td>
                </tr>"""

            rows += f"""<tr class='total-row'>
              <td><strong>الإجمالي</strong></td>
              <td class='num'>{fmt(len(inv2))}</td>
              <td class='num'>{fmt(total_inv2)}</td>
              <td class='num'>{sup_rate*100:.2f}%</td>
              <td class='num-pos'>{fmt(total_comm2)}</td>
              <td class='num-pos'>{fmt(total_pay2)}</td>
              <td class='{"num-neg" if remaining2>0 else "num-pos"}'>{fmt(remaining2)}</td>
            </tr>"""

            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>الشهر</th><th>عدد الفواتير</th><th>قيمة الفواتير</th>
                <th>النسبة</th><th>العمولة المستحقة</th><th>المسدود</th><th>المتبقي</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        # تفاصيل الفواتير
        if not inv2.empty:
            st.markdown("<div class='section-title'>تفاصيل الفواتير</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in inv2.sort_values("تاريخ الفاتورة").iterrows():
                date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{r["رقم الفاتورة"]}</td>
                  <td class='num'>{date_str}</td>
                  <td>{r["العميل"]}</td>
                  <td class='num'>{fmt(r["قيمة الفاتورة"])}</td>
                  <td class='num'>{sup_rate*100:.2f}%</td>
                  <td class='num-pos'>{fmt(r["عمولة_المورد_فعلية"])}</td>
                </tr>"""
            st.markdown(f"""<div style='overflow-x:auto'><table class='styled-table'>
              <thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th>
                <th>قيمة الفاتورة</th><th>نسبة المسؤول</th><th>عمولة المسؤول</th></tr></thead>
              <tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

        if not pay.empty:
            st.markdown("<div class='section-title'>سجل السدادات</div>", unsafe_allow_html=True)
            rows = ""
            for _, r in pay.iterrows():
                date_str = r["التاريخ"].strftime("%d/%m/%Y") if pd.notna(r["التاريخ"]) else "—"
                rows += f"""<tr>
                  <td class='num'>{date_str}</td>
                  <td>{r.get("طريقة السداد","—")}</td>
                  <td class='num-pos'>{fmt(r["المبلغ"])}</td>
                  <td>{r.get("ملاحظات","")}</td>
                </tr>"""
            st.markdown(f"""<table class='styled-table'>
              <thead><tr><th>التاريخ</th><th>طريقة السداد</th><th>المبلغ</th><th>ملاحظات</th></tr></thead>
              <tbody>{rows}</tbody></table>""", unsafe_allow_html=True)

        if export_btn2 and not inv2.empty:
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                inv2[["رقم الفاتورة","تاريخ الفاتورة","العميل","المورد",
                      "قيمة الفاتورة","عمولة_المورد_فعلية"]].to_excel(
                    writer, sheet_name="الفواتير", index=False)
                if not pay.empty:
                    pay.to_excel(writer, sheet_name="السدادات", index=False)
            st.download_button("📥 تحميل كشف الحساب", buf.getvalue(),
                               file_name=f"كشف_حساب_{sel_sup}.xlsx",
                               mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
