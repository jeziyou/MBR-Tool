import streamlit as st
import os
import requests
from flask import Flask, request, jsonify
from werkzeug.middleware.dispatcher import DispatcherMiddleware

RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "MBR设计工具 <onboarding@resend.dev>"
DEFAULT_RECEIVER = "jeziyou@qq.com"

flask_app = Flask(__name__)

@flask_app.route("/api/send-email", methods=["POST", "OPTIONS"])
def api_send_email():
    if request.method == "OPTIONS":
        resp = flask_app.make_response("")
        resp.headers["Access-Control-Allow-Origin"] = "*"
        resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
        resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
        return resp
    try:
        data = request.get_json() or {}
        file_content = data.get("file_content", "")
        filename = data.get("filename", "计算书.pdf")
        email_to = data.get("email_to", DEFAULT_RECEIVER)
        project_name = data.get("project_name", "MBR膜系统工艺计算书")
        if not email_to:
            return jsonify({"success": False, "error": "收件人邮箱为空"}), 400
        payload = {
            "from": SENDER_EMAIL, "to": [email_to],
            "subject": f"{project_name} - 计算书",
            "html": f"<h2>{project_name}</h2><p>附件为工艺计算书。</p>",
        }
        if file_content:
            payload["attachments"] = [{"filename": filename, "content": file_content}]
        resp = requests.post(RESEND_API_URL, json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30)
        if resp.status_code == 200:
            return jsonify({"success": True, "message": f"邮件已发送至 {email_to}"})
        else:
            return jsonify({"success": False, "error": f"API错误 ({resp.status_code})"}), resp.status_code
    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route("/api/health", methods=["GET"])
def api_health():
    return jsonify({"status": "ok"})

st.set_page_config(page_title="MBR", layout="wide", initial_sidebar_state="collapsed")

# ============ 详细调试注入 ============
injection_log = []

def try_inject():
    try:
        runtime = st.runtime.get_instance()
        injection_log.append(f"runtime type: {type(runtime)}")
        injection_log.append(f"runtime attrs: {[a for a in dir(runtime) if not a.startswith('__')]}")
        if hasattr(runtime, '_server'):
            srv = runtime._server
            injection_log.append(f"server type: {type(srv)}")
            injection_log.append(f"server attrs: {[a for a in dir(srv) if not a.startswith('__')]}")
            if hasattr(srv, '_wsgi_app'):
                injection_log.append(f"_wsgi_app type: {type(srv._wsgi_app)}")
            if hasattr(srv, 'uvicorn'):
                injection_log.append(f"uvicorn attr exists: {type(srv.uvicorn)}")
            # Try to find uvicorn server
            for attr_name in dir(srv):
                attr = getattr(srv, attr_name, None)
                if attr and 'uvicorn' in str(type(attr)).lower():
                    injection_log.append(f"Found uvicorn at {attr_name}: {type(attr)}")
                    if hasattr(attr, 'mount'):
                        injection_log.append(f"  has mount: yes")
                    if hasattr(attr, 'app'):
                        app = attr.app
                        injection_log.append(f"  app type: {type(app)}")
    except Exception as e:
        injection_log.append(f"ERROR: {type(e).__name__}: {e}")

try_inject()

if injection_log:
    st.sidebar.markdown("### 调试信息")
    for line in injection_log:
        st.sidebar.code(line)

# ============ 主页面 ============
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool .html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()
st.components.v1.html(html_content, height=9000, scrolling=True)
