import streamlit as st
import os
import base64
import requests
import json
from flask import Flask, request, jsonify
from flask_cors import CORS
import threading

st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    layout="wide",
    initial_sidebar_state="expanded"
)

# ============================================================
# Email Sending Configuration
# ============================================================
RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "MBR设计工具 <onboarding@resend.dev>"

# ============================================================
# Flask app for email endpoint
# ============================================================
flask_app = Flask(__name__)
CORS(flask_app)

@flask_app.route("/api/send-email", methods=["POST"])
def send_email():
    try:
        email_to = request.form.get("email", "").strip()
        project_name = request.form.get("project_name", "MBR膜系统工艺计算书")
        file_type = request.form.get("file_type", "pdf")

        if not email_to:
            return jsonify({"success": False, "error": "邮箱地址不能为空"}), 400

        if "file" not in request.files:
            return jsonify({"success": False, "error": "未找到附件文件"}), 400

        file = request.files["file"]
        file_data = file.read()
        file_name = file.filename or f"{project_name}.{file_type}"

        if not RESEND_API_KEY:
            return jsonify({
                "success": False,
                "error": "Resend API Key 未配置"
            }), 400

        payload = {
            "from": SENDER_EMAIL,
            "to": [email_to],
            "subject": f"{project_name} - 计算书",
            "html": f"""
            <h2>{project_name}</h2>
            <p>您好，</p>
            <p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书，请查收附件。</p>
            <p>文件格式：{file_type.upper()}</p>
            <hr>
            <p style="color:#999;font-size:12px;">此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>
            """,
            "attachments": [
                {
                    "filename": file_name,
                    "content": base64.b64encode(file_data).decode("utf-8"),
                }
            ],
        }

        resp = requests.post(
            RESEND_API_URL,
            json=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )

        if resp.status_code == 200:
            return jsonify({"success": True, "message": f"邮件已发送至 {email_to}"})
        else:
            error_detail = resp.text[:300]
            return jsonify({"success": False, "error": f"Resend API错误 ({resp.status_code}): {error_detail}"}), 500

    except Exception as e:
        return jsonify({"success": False, "error": str(e)}), 500

@flask_app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})

@flask_app.route("/api/config", methods=["GET", "POST"])
def config():
    if request.method == "POST":
        return jsonify({"success": True, "configured": True, "sender": SENDER_EMAIL})
    return jsonify({"configured": True, "sender": SENDER_EMAIL})

def start_flask():
    flask_app.run(host="0.0.0.0", port=8502, debug=False, use_reloader=False)

# Start Flask in background thread
flask_thread = threading.Thread(target=start_flask, daemon=True)
flask_thread.start()

# Wait a bit for Flask to start
import time
time.sleep(2)

# ============================================================
# Sidebar: Configuration
# ============================================================
with st.sidebar:
    st.title("邮件发送配置")
    st.markdown("---")
    st.success("邮件发送服务已配置完成")
    st.caption(f"发件人: {SENDER_EMAIL}")
    st.markdown("---")
    st.info("邮件将自动发送至 jeziyou@qq.com")

# ============================================================
# Main content: Embed HTML
# ============================================================
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool .html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=8000, scrolling=True)