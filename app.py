import streamlit as st
import os
import subprocess
import threading
import time
import requests
import atexit

st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Backend Server Management
# ============================================================
def start_backend():
    """启动Flask后端服务"""
    backend_path = os.path.join(os.path.dirname(__file__), "backend.py")
    proc = subprocess.Popen(
        ["python", backend_path],
        stdout=subprocess.DEVNULL,
        stderr=subprocess.DEVNULL,
    )
    # Wait for backend to start
    for _ in range(10):
        try:
            resp = requests.get("http://localhost:8502/health", timeout=1)
            if resp.status_code == 200:
                return proc
        except Exception:
            time.sleep(0.5)
    return proc


def stop_backend():
    """停止后端服务"""
    if "backend_proc" in st.session_state:
        st.session_state.backend_proc.terminate()
        st.session_state.backend_proc = None


# Initialize backend
if "backend_proc" not in st.session_state:
    st.session_state.backend_proc = start_backend()
    atexit.register(stop_backend)

# ============================================================
# Sidebar: SMTP configuration
# ============================================================
with st.sidebar:
    st.title("邮件发送配置")
    st.markdown("---")
    st.caption("配置SMTP服务器以使用邮件发送功能")

    smtp_host = st.text_input("SMTP服务器", value="smtp.qq.com", key="smtp_host")
    smtp_port = st.number_input("端口", value=587, min_value=1, max_value=65535, key="smtp_port")
    smtp_user = st.text_input("发件邮箱", value="", placeholder="your@email.com", key="smtp_user")
    smtp_password = st.text_input("邮箱密码/授权码", value="", type="password", key="smtp_pass")
    smtp_tls = st.checkbox("使用TLS", value=True, key="smtp_tls")

    if st.button("保存配置"):
        try:
            resp = requests.post(
                "http://localhost:8502/api/config",
                json={
                    "host": smtp_host,
                    "port": int(smtp_port),
                    "user": smtp_user,
                    "password": smtp_password,
                    "use_tls": smtp_tls,
                },
                timeout=5,
            )
            if resp.status_code == 200:
                st.success("SMTP配置已保存")
            else:
                st.error("保存失败")
        except Exception as e:
            st.error(f"无法连接后端服务: {e}")

    # Show current config status
    try:
        resp = requests.get("http://localhost:8502/api/config", timeout=3)
        if resp.status_code == 200:
            config = resp.json()
            if config.get("configured"):
                st.success(f"已配置: {config['host']}:{config['port']}")
            else:
                st.warning("SMTP尚未配置，邮件发送功能不可用")
    except Exception:
        st.warning("后端服务未就绪")

    st.markdown("---")
    st.caption("提示: QQ邮箱请使用授权码而非密码")

# ============================================================
# Main content: Embed HTML
# ============================================================
# Read HTML file
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool .html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# Embed the HTML content
st.components.v1.html(html_content, height=8000, scrolling=True)