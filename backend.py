import os
import json
import base64
import logging
import requests
from flask import Flask, request, jsonify
from flask_cors import CORS

logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

app = Flask(__name__)
CORS(app)

# Resend API 配置
RESEND_API_KEY = os.environ.get("RESEND_API_KEY", "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv")
RESEND_API_URL = "https://api.resend.com/emails"

# 发件人配置（Resend免费版可用 onboarding@resend.dev）
SENDER_EMAIL = os.environ.get("SENDER_EMAIL", "MBR设计工具 <onboarding@resend.dev>")

# 兼容旧配置格式
CONFIGURED = False


@app.route("/health", methods=["GET"])
def health():
    return jsonify({"status": "ok"})


@app.route("/api/send-email", methods=["POST"])
def send_email():
    """接收文件并通过Resend API发送邮件"""
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

        result = _send_via_resend(
            to_email=email_to,
            subject=f"{project_name} - 计算书",
            body=f"""
            <h2>{project_name}</h2>
            <p>您好，</p>
            <p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书，请查收附件。</p>
            <p>文件格式：{file_type.upper()}</p>
            <hr>
            <p style="color:#999;font-size:12px;">此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>
            """,
            attachment_data=file_data,
            attachment_name=file_name,
        )

        if result["success"]:
            logger.info(f"Email sent successfully to {email_to}")
            return jsonify({"success": True, "message": f"邮件已发送至 {email_to}"})
        else:
            logger.error(f"Failed to send email: {result['error']}")
            return jsonify({"success": False, "error": result["error"]}), 500

    except Exception as e:
        logger.exception("Email send error")
        return jsonify({"success": False, "error": str(e)}), 500


def _send_via_resend(to_email, subject, body, attachment_data, attachment_name):
    """通过Resend HTTP API发送邮件"""
    try:
        payload = {
            "from": SENDER_EMAIL,
            "to": [to_email],
            "subject": subject,
            "html": body,
            "attachments": [
                {
                    "filename": attachment_name,
                    "content": base64.b64encode(attachment_data).decode("utf-8"),
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
            return {"success": True}
        else:
            error_detail = resp.text[:300]
            logger.error(f"Resend API error: {resp.status_code} - {error_detail}")
            return {"success": False, "error": f"Resend API返回错误 ({resp.status_code}): {error_detail}"}

    except requests.exceptions.Timeout:
        return {"success": False, "error": "Resend API 请求超时"}
    except Exception as e:
        return {"success": False, "error": str(e)}


@app.route("/api/config", methods=["GET", "POST"])
def smtp_config():
    """获取或更新配置（兼容旧接口）"""
    global RESEND_API_KEY, SENDER_EMAIL, CONFIGURED
    if request.method == "POST":
        data = request.get_json() or {}
        if "api_key" in data:
            RESEND_API_KEY = data["api_key"]
        if "sender" in data:
            SENDER_EMAIL = data["sender"]
        if "host" in data and "user" in data:
            CONFIGURED = True
        return jsonify({
            "success": True,
            "configured": bool(RESEND_API_KEY),
            "sender": SENDER_EMAIL,
        })
    return jsonify({
        "configured": bool(RESEND_API_KEY),
        "sender": SENDER_EMAIL,
    })


if __name__ == "__main__":
    app.run(host="0.0.0.0", port=8502, debug=False)