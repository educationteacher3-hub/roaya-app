import streamlit as st
import pandas as pd
import io
from auth import check_password
from data_loader import load_excel_from_drive, fmt

st.set_page_config(page_title="الفواتير المكررة والتصدير", page_icon="🔍", layout="wide")

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
.styled-table tbody tr.dup-row { background:#fdecea; }
.styled-table tbody tr.total-row { background:#f0f4f8; font-weight:700; }
.styled-table tbody td { padding:7px 10px; color:#3a4a58; }
.num-pos { color:#1a7f74; font-weight:600; font-family:monospace; }
.num-neg { color:#c0392b; font-weight:600; font-family:monospace; }
.num { font-family:monospace; font-size:11.5px; }
.alert-box { background:#fdecea; border:1px solid #f5b7b1; border-radius:10px; padding:14px 18px; margin-bottom:16px; }
.alert-box h4 { color:#c0392b; font-size:14px; font-weight:700; margin-bottom:4px; }
.info-box { background:#e8f0f7; border:1px solid #aed6f1; border-radius:10px; padding:14px 18px; margin-bottom:16px; }
</style>
""", unsafe_allow_html=True)

if not check_password():
    st.stop()

st.title("🔍 الفواتير المكررة والتصدير")

# ===== تحميل الفواتير =====
@st.cache_data(ttl=300)
def load_all_invoices():
    df = load_excel_from_drive("clients", "الموردين", header=2)
    df_list = load_excel_from_drive("clients", "قائمة الموردين والعملاء", header=0)
    
    clients_rates = {}
    suppliers_rates = {}
    if not df_list.empty:
        for _, row in df_list.iterrows():
            if pd.notna(row.iloc[0]) and str(row.iloc[0]).strip():
                clients_rates[str(row.iloc[0]).strip()] = pd.to_numeric(row.iloc[1], errors="coerce") or 0
            if len(row) > 2 and pd.notna(row.iloc[2]) and str(row.iloc[2]).strip():
                suppliers_rates[str(row.iloc[2]).strip()] = pd.to_numeric(row.iloc[3], errors="coerce") or 0

    if not df.empty:
        df.columns = ["م","رقم الفاتورة","قيمة الفاتورة","نسبة_المورد","عمولة_المورد",
                      "تاريخ الفاتورة","جهة الصدور","العميل","المورد"]
        df = df.dropna(subset=["رقم الفاتورة"])
        df["قيمة الفاتورة"]  = pd.to_numeric(df["قيمة الفاتورة"],  errors="coerce").fillna(0)
        df["نسبة_المورد"]    = pd.to_numeric(df["نسبة_المورد"],    errors="coerce").fillna(0)
        df["عمولة_المورد"]   = pd.to_numeric(df["عمولة_المورد"],   errors="coerce").fillna(0)
        df["تاريخ الفاتورة"] = pd.to_datetime(df["تاريخ الفاتورة"], errors="coerce")
        df["رقم الفاتورة"]   = df["رقم الفاتورة"].astype(str).str.strip()
        df["نسبة_العميل"]    = df["العميل"].map(clients_rates).fillna(0)
        df["عمولة_العميل"]   = df["قيمة الفاتورة"] * df["نسبة_العميل"]
        df["نسبة_المورد_ف"]  = df["المورد"].map(suppliers_rates).fillna(df["نسبة_المورد"])
        df["عمولة_المورد_ف"] = df["قيمة الفاتورة"] * df["نسبة_المورد_ف"]
    
    return df, clients_rates, suppliers_rates

df, clients_rates, suppliers_rates = load_all_invoices()

tab1, tab2 = st.tabs(["🔴 الفواتير المكررة", "⬇ تصدير البيانات"])

# ===== تاب 1: الفواتير المكررة =====
with tab1:
    if df.empty:
        st.error("تعذّر تحميل الفواتير")
    else:
        # كشف التكرار
        col_f1, col_f2 = st.columns(2)
        with col_f1:
            dup_type = st.selectbox("نوع الكشف", [
                "رقم الفاتورة + قيمة الفاتورة (الأدق)",
                "رقم الفاتورة + قيمة الفاتورة + المورد",
                "رقم الفاتورة + قيمة الفاتورة + العميل + المورد",
                "رقم الفاتورة فقط (أوسع نطاقاً)"
            ])
        with col_f2:
            min_dup = st.number_input("الحد الأدنى للتكرار", min_value=2, value=2)

        # تطبيق منطق الكشف
        if dup_type == "رقم الفاتورة + قيمة الفاتورة (الأدق)":
            dup_keys = ["رقم الفاتورة", "قيمة الفاتورة"]
        elif dup_type == "رقم الفاتورة + قيمة الفاتورة + المورد":
            dup_keys = ["رقم الفاتورة", "قيمة الفاتورة", "المورد"]
        elif dup_type == "رقم الفاتورة + قيمة الفاتورة + العميل + المورد":
            dup_keys = ["رقم الفاتورة", "قيمة الفاتورة", "العميل", "المورد"]
        else:
            dup_keys = ["رقم الفاتورة"]

        # حساب التكرار
        df_count = df.groupby(dup_keys).size().reset_index(name="عدد_التكرار")
        df_count = df_count[df_count["عدد_التكرار"] >= min_dup]
        df_dups  = df.merge(df_count, on=dup_keys)
        df_dups  = df_dups.sort_values(["عدد_التكرار"] + dup_keys, ascending=[False] + [True]*len(dup_keys))

        # KPIs
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("🔴 مجموعات مكررة",        f"{len(df_count):,}")
        with c2: st.metric("📋 إجمالي سجلات مكررة",   f"{len(df_dups):,}")
        with c3: st.metric("💰 قيمة الفواتير المكررة", f"{fmt(df_dups['قيمة الفاتورة'].sum())} ج")
        with c4: st.metric("✅ عمولات مكررة محتملة",   f"{fmt(df_dups['عمولة_العميل'].sum())} ج")

        if len(df_dups) > 0:
            st.markdown(f"""
            <div class='alert-box'>
                <h4>⚠️ تحذير: تم اكتشاف {len(df_count):,} مجموعة فواتير مكررة</h4>
                <p style='color:#c0392b;font-size:13px'>يرجى مراجعة الفواتير المميزة باللون الأحمر أدناه والتحقق منها</p>
            </div>""", unsafe_allow_html=True)

            # فلتر إضافي
            all_clients = ["كل العملاء"] + sorted(df_dups["العميل"].dropna().unique().tolist())
            sel_c = st.selectbox("فلتر حسب العميل", all_clients)
            if sel_c != "كل العملاء":
                df_dups = df_dups[df_dups["العميل"] == sel_c]

            # الجدول
            st.markdown("<div class='section-title'>📋 تفاصيل الفواتير المكررة</div>", unsafe_allow_html=True)
            rows = ""
            prev_key = None
            for _, r in df_dups.iterrows():
                curr_key = tuple(r[k] for k in dup_keys)
                date_str = r["تاريخ الفاتورة"].strftime("%d/%m/%Y") if pd.notna(r["تاريخ الفاتورة"]) else "—"
                sep = "border-top:2px solid #c0392b;" if curr_key != prev_key and prev_key is not None else ""
                rows += f"""<tr class='dup-row' style='{sep}'>
                  <td class='num' style='color:#c0392b;font-weight:700'>{r["رقم الفاتورة"]}</td>
                  <td class='num'>{date_str}</td>
                  <td>{r["العميل"]}</td>
                  <td>{r["المورد"]}</td>
                  <td class='num'>{fmt(r["قيمة الفاتورة"])}</td>
                  <td class='num-pos'>{fmt(r["عمولة_العميل"])}</td>
                  <td class='num' style='color:#c0392b;font-weight:700;text-align:center'>{int(r["عدد_التكرار"])} مرات</td>
                </tr>"""
                prev_key = curr_key

            st.markdown(f"""<div style='overflow-x:auto'><table class='styled-table'>
              <thead><tr><th>رقم الفاتورة</th><th>التاريخ</th><th>العميل</th><th>المورد</th>
                <th>القيمة</th><th>عمولة العميل</th><th>عدد التكرار</th></tr></thead>
              <tbody>{rows}</tbody></table></div>""", unsafe_allow_html=True)

            # تصدير المكررة
            if st.button("⬇ تصدير الفواتير المكررة Excel"):
                buf = io.BytesIO()
                df_dups.to_excel(buf, index=False, engine="openpyxl")
                st.download_button("📥 تحميل", buf.getvalue(),
                                   file_name="فواتير_مكررة.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet")
        else:
            st.success("✅ لا توجد فواتير مكررة بهذا النوع من الكشف")

# ===== تاب 2: تصدير البيانات =====
with tab2:
    st.markdown("<div class='section-title'>⬇ خيارات التصدير</div>", unsafe_allow_html=True)

    if df.empty:
        st.error("تعذّر تحميل البيانات")
    else:
        # فلاتر التصدير
        col1, col2, col3 = st.columns(3)
        with col1:
            all_clients = ["كل العملاء"] + sorted(df["العميل"].dropna().unique().tolist())
            exp_client = st.selectbox("العميل", all_clients, key="exp_c")
        with col2:
            all_suppliers = ["كل الموردين"] + sorted(df["المورد"].dropna().unique().tolist())
            exp_supplier = st.selectbox("المورد", all_suppliers, key="exp_s")
        with col3:
            years = sorted(df["تاريخ الفاتورة"].dt.year.dropna().unique().astype(int).tolist(), reverse=True)
            exp_year = st.selectbox("السنة", ["كل السنوات"] + [str(y) for y in years], key="exp_y")

        col4, col5 = st.columns(2)
        with col4:
            exp_from = st.date_input("من تاريخ", value=df["تاريخ الفاتورة"].min(), key="exp_from")
        with col5:
            exp_to = st.date_input("إلى تاريخ", value=df["تاريخ الفاتورة"].max(), key="exp_to")

        # تطبيق الفلاتر
        filtered = df.copy()
        if exp_client != "كل العملاء":
            filtered = filtered[filtered["العميل"] == exp_client]
        if exp_supplier != "كل الموردين":
            filtered = filtered[filtered["المورد"] == exp_supplier]
        if exp_year != "كل السنوات":
            filtered = filtered[filtered["تاريخ الفاتورة"].dt.year == int(exp_year)]
        filtered = filtered[
            (filtered["تاريخ الفاتورة"] >= pd.Timestamp(exp_from)) &
            (filtered["تاريخ الفاتورة"] <= pd.Timestamp(exp_to))
        ]

        # إجماليات
        c1, c2, c3, c4 = st.columns(4)
        with c1: st.metric("عدد الفواتير",         f"{len(filtered):,}")
        with c2: st.metric("إجمالي قيمة الفواتير", f"{fmt(filtered['قيمة الفاتورة'].sum())} ج")
        with c3: st.metric("عمولات العملاء",        f"{fmt(filtered['عمولة_العميل'].sum())} ج")
        with c4: st.metric("عمولات المسؤولين",      f"{fmt(filtered['عمولة_المورد_ف'].sum())} ج")

        st.markdown("<div class='section-title'>اختار شكل التصدير</div>", unsafe_allow_html=True)

        col_e1, col_e2, col_e3 = st.columns(3)

        # تصدير 1: كل الفواتير
        with col_e1:
            st.markdown("**📋 كل الفواتير**")
            st.caption(f"{len(filtered):,} فاتورة")
            if st.button("⬇ تصدير Excel", key="exp1", use_container_width=True):
                buf = io.BytesIO()
                export_df = filtered[[
                    "رقم الفاتورة","تاريخ الفاتورة","العميل","المورد",
                    "قيمة الفاتورة","نسبة_العميل","عمولة_العميل",
                    "نسبة_المورد_ف","عمولة_المورد_ف"
                ]].copy()
                export_df.columns = [
                    "رقم الفاتورة","التاريخ","العميل","المورد",
                    "قيمة الفاتورة","نسبة العميل","عمولة العميل",
                    "نسبة المورد","عمولة المورد"
                ]
                export_df.to_excel(buf, index=False, engine="openpyxl")
                st.download_button("📥 تحميل", buf.getvalue(),
                                   file_name="الفواتير_الكاملة.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl1")

        # تصدير 2: ملخص حسب العميل
        with col_e2:
            st.markdown("**👥 ملخص حسب العميل**")
            by_c = filtered.groupby("العميل").agg(
                عدد_الفواتير=("رقم الفاتورة","count"),
                قيمة_الفواتير=("قيمة الفاتورة","sum"),
                عمولة_العميل=("عمولة_العميل","sum"),
                عمولة_المورد=("عمولة_المورد_ف","sum")
            ).reset_index()
            st.caption(f"{len(by_c):,} عميل")
            if st.button("⬇ تصدير Excel", key="exp2", use_container_width=True):
                buf = io.BytesIO()
                by_c.to_excel(buf, index=False, engine="openpyxl")
                st.download_button("📥 تحميل", buf.getvalue(),
                                   file_name="ملخص_العملاء.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl2")

        # تصدير 3: ملخص حسب المورد
        with col_e3:
            st.markdown("**🏭 ملخص حسب المورد**")
            by_s = filtered.groupby("المورد").agg(
                عدد_الفواتير=("رقم الفاتورة","count"),
                قيمة_الفواتير=("قيمة الفاتورة","sum"),
                عمولة_المورد=("عمولة_المورد_ف","sum")
            ).reset_index()
            st.caption(f"{len(by_s):,} مورد")
            if st.button("⬇ تصدير Excel", key="exp3", use_container_width=True):
                buf = io.BytesIO()
                by_s.to_excel(buf, index=False, engine="openpyxl")
                st.download_button("📥 تحميل", buf.getvalue(),
                                   file_name="ملخص_الموردين.xlsx",
                                   mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                                   key="dl3")

        # تصدير 4: ملف شامل بكل الشيتات
        st.markdown("<div class='section-title'>📦 تصدير شامل (ملف واحد بكل الشيتات)</div>", unsafe_allow_html=True)
        if st.button("⬇ تصدير ملف شامل Excel", use_container_width=True):
            buf = io.BytesIO()
            with pd.ExcelWriter(buf, engine="openpyxl") as writer:
                # كل الفواتير
                filtered.to_excel(writer, sheet_name="كل الفواتير", index=False)
                # ملخص عملاء
                by_c.to_excel(writer, sheet_name="ملخص العملاء", index=False)
                # ملخص موردين
                by_s.to_excel(writer, sheet_name="ملخص الموردين", index=False)
                # ملخص شهري
                monthly = filtered.copy()
                monthly["الشهر"] = monthly["تاريخ الفاتورة"].dt.month
                monthly["السنة"] = monthly["تاريخ الفاتورة"].dt.year
                monthly_sum = monthly.groupby(["السنة","الشهر"]).agg(
                    عدد_الفواتير=("رقم الفاتورة","count"),
                    قيمة_الفواتير=("قيمة الفاتورة","sum"),
                    عمولات_العملاء=("عمولة_العميل","sum"),
                    عمولات_الموردين=("عمولة_المورد_ف","sum")
                ).reset_index()
                monthly_sum.to_excel(writer, sheet_name="الملخص الشهري", index=False)
                # الفواتير المكررة
                dup_check = filtered[filtered.duplicated(subset=["رقم الفاتورة","قيمة الفاتورة"], keep=False)]
                if not dup_check.empty:
                    dup_check.to_excel(writer, sheet_name="فواتير مكررة", index=False)
            st.download_button(
                "📥 تحميل الملف الشامل",
                buf.getvalue(),
                file_name="تقرير_شامل.xlsx",
                mime="application/vnd.openxmlformats-officedocument.spreadsheetml.sheet",
                key="dl_full"
            )
        
        # معاينة البيانات
        with st.expander("👁️ معاينة البيانات"):
            st.dataframe(
                filtered[["رقم الفاتورة","تاريخ الفاتورة","العميل","المورد",
                          "قيمة الفاتورة","نسبة_العميل","عمولة_العميل"]].head(100),
                use_container_width=True, hide_index=True
            )
