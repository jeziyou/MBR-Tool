import streamlit as st
import os
import base64
import requests
import threading
from flask import Flask, request, jsonify
from flask_cors import CORS

# ============================================================
# 邮件发送配置
# ============================================================
RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "MBR设计工具 <onboarding@resend.dev>"
DEFAULT_RECEIVER = "jeziyou@qq.com"

# ============================================================
# Flask 后端（与 Streamlit 同端口，通过 /api/ 路径区分）
# ============================================================
def create_flask_app():
    app = Flask(__name__)
    # CORS 允许同源请求
    CORS(app, resources={r"/api/*": {"origins": "*"}})

    @app.route("/api/send-email", methods=["POST", "OPTIONS"])
    def api_send_email():
        # 处理 OPTIONS 预检请求
        if request.method == "OPTIONS":
            resp = app.make_response("")
            resp.headers["Access-Control-Allow-Origin"] = "*"
            resp.headers["Access-Control-Allow-Methods"] = "POST, OPTIONS"
            resp.headers["Access-Control-Allow-Headers"] = "Content-Type"
            return resp

        try:
            data = request.get_json()
            file_content = data.get("file_content", "")  # base64 编码的文件内容
            filename = data.get("filename", "计算书.pdf")
            email_to = data.get("email_to", DEFAULT_RECEIVER)
            project_name = data.get("project_name", "MBR膜系统工艺计算书")
            file_size = data.get("file_size", 0)

            if not email_to:
                return jsonify({"success": False, "error": "收件人邮箱为空"}), 400

            # 调用 Resend API
            payload = {
                "from": SENDER_EMAIL,
                "to": [email_to],
                "subject": f"{project_name} - 计算书",
                "html": f"""
                <h2>{project_name}</h2>
                <p>您好，</p>
                <p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书，请查收附件。</p>
                <hr>
                <p style="color:#999;font-size:12px;">此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>
                """,
            }

            # 如果有附件内容，添加附件
            if file_content:
                payload["attachments"] = [
                    {"filename": filename, "content": file_content}
                ]

            resp = requests.post(
                RESEND_API_URL,
                json=payload,
                headers={
                    "Authorization": f"Bearer {RESEND_API_KEY}",
                    "Content-Type": "application/json",
                },
                timeout=60,
            )

            if resp.status_code == 200:
                return jsonify({
                    "success": True,
                    "message": f"邮件已发送至 {email_to}",
                    "file_size_kb": round(file_size / 1024, 1) if file_size else None,
                })
            else:
                return jsonify({
                    "success": False,
                    "error": f"Resend API 错误 ({resp.status_code}): {resp.text[:300]}",
                }), resp.status_code

        except Exception as e:
            return jsonify({"success": False, "error": str(e)}), 500

    @app.route("/api/health", methods=["GET"])
    def api_health():
        return jsonify({"status": "ok"})

    return app


def run_flask_in_thread():
    """在后台线程中运行 Flask 服务"""
    app = create_flask_app()
    # 在 8502 端口运行（Streamlit 通常用 8501）
    app.run(host="127.0.0.1", port=8502, debug=False, threaded=True, use_reloader=False)


# ============================================================
# Streamlit 页面配置
# ============================================================
st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    layout="wide",
    initial_sidebar_state="expanded",
)

# 启动时在后台线程中运行 Flask 邮件服务
if "flask_started" not in st.session_state:
    t = threading.Thread(target=run_flask_in_thread, daemon=True)
    t.start()
    st.session_state.flask_started = True

# ============================================================
# 侧边栏配置
# ============================================================
with st.sidebar:
    st.title("📧 邮件发送配置")
    st.markdown("---")
    st.success("✅ 邮件服务已就绪（后台运行）")
    st.caption(f"默认收件人：{DEFAULT_RECEIVER}")
    st.caption(f"发件人：{SENDER_EMAIL}")
    st.markdown("---")
    st.info(
        "💡 **使用说明**\n\n"
        "1. 在右侧页面输入参数，点击「计算」\n"
        "2. 点击「导出计算书 PDF/Word」按钮\n"
        "3. 邮件将在**后台自动发送**至默认邮箱\n"
        "4. 无需手动操作，发送状态会显示在按钮下方"
    )

# ============================================================
# 主页面：嵌入 HTML 计算工具
# ============================================================
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool .html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

st.iframe(html_content, height=9000, scrolling=True)
