import streamlit as st
import os
import base64
import requests

RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "MBR设计工具 <onboarding@resend.dev>"
DEFAULT_RECEIVER = "jeziyou@qq.com"

def send_email_via_resend(file_data, filename, email_to, project_name):
    try:
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
            "attachments": [
                {
                    "filename": filename,
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
            return {"success": True, "message": f"邮件已发送至 {email_to}"}
        else:
            error_detail = resp.text[:300]
            return {"success": False, "error": f"Resend API错误 ({resp.status_code}): {error_detail}"}

    except Exception as e:
        return {"success": False, "error": str(e)}

st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    layout="wide",
    initial_sidebar_state="expanded"
)

with st.sidebar:
    st.title("邮件发送配置")
    st.markdown("---")
    st.success("邮件发送服务已配置完成")
    st.caption(f"发件人: {SENDER_EMAIL}")
    st.caption(f"默认收件人: {DEFAULT_RECEIVER}")
    st.markdown("---")
    st.info("导出计算书时会自动发送邮件")

html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool .html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=8000, scrolling=True)

if 'email_file_data' in st.session_state:
    data = st.session_state.email_file_data
    result = send_email_via_resend(data['file_data'], data['filename'], data['email'], data['project_name'])
    if result['success']:
        st.success(result['message'])
    else:
        st.error(f"邮件发送失败: {result['error']}")
    del st.session_state.email_file_data