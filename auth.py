import streamlit as st
import hmac

def check_password():
    """
    شاشة الدخول — ترجع True لو المستخدم سجل دخول صح
    """

    def login_form():
        st.markdown("""
        <style>
        @import url('https://fonts.googleapis.com/css2?family=Cairo:wght@400;600;700;900&display=swap');
        * { font-family: 'Cairo', sans-serif !important; }
        html, body, [class*="css"] { direction: rtl; }

        .login-wrapper {
            display: flex; justify-content: center; align-items: center;
            min-height: 80vh;
        }
        .login-box {
            background: white; border-radius: 16px;
            border: 1px solid #d4dce5;
            padding: 40px; width: 100%; max-width: 400px;
            box-shadow: 0 8px 32px rgba(15,25,35,0.12);
            text-align: center;
        }
        .login-logo {
            width: 60px; height: 60px; background: #c8953a;
            border-radius: 14px; display: flex;
            align-items: center; justify-content: center;
            font-size: 28px; font-weight: 900; color: #0f1923;
            margin: 0 auto 16px;
        }
        .login-title { font-size: 22px; font-weight: 800; color: #0f1923; margin-bottom: 4px; }
        .login-sub { font-size: 13px; color: #7a8e9e; margin-bottom: 28px; }
        </style>

        <div class='login-wrapper'>
          <div class='login-box'>
            <div class='login-logo'>ر</div>
            <div class='login-title'>مكتب رؤية</div>
            <div class='login-sub'>النظام المالي — تسجيل الدخول</div>
          </div>
        </div>
        """, unsafe_allow_html=True)

        with st.form("login_form"):
            username = st.text_input("👤 اسم المستخدم", placeholder="أدخل اسم المستخدم")
            password = st.text_input("🔒 كلمة المرور", type="password", placeholder="أدخل كلمة المرور")
            submitted = st.form_submit_button("دخول ←", use_container_width=True)

            if submitted:
                users = st.secrets.get("users", {})
                if username in users:
                    stored = users[username].get("password", "")
                    if hmac.compare_digest(password, stored):
                        st.session_state["logged_in"]  = True
                        st.session_state["username"]   = username
                        st.session_state["user_name"]  = users[username].get("name", username)
                        st.rerun()
                    else:
                        st.error("كلمة المرور غلط")
                else:
                    st.error("اسم المستخدم غير موجود")

    # لو مسجل دخول → رجّع True
    if st.session_state.get("logged_in"):
        return True

    # لو لأ → وريه فورم الدخول
    login_form()
    return False


def logout():
    """زر تسجيل الخروج"""
    st.session_state["logged_in"] = False
    st.session_state["username"]  = ""
    st.session_state["user_name"] = ""
    st.rerun()
