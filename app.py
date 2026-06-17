import streamlit as st
import os
import base64
import requests

# ============================================================
# 邮件发送配置
# ============================================================
RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
RESEND_API_URL = "https://api.resend.com/emails"
SENDER_EMAIL = "MBR设计工具 <onboarding@resend.dev>"
DEFAULT_RECEIVER = "jeziyou@qq.com"
PROJECT_NAME_DEFAULT = "MBR膜系统工艺计算书"


def send_email_via_resend(file_data, filename, email_to, project_name):
    """由 Python 后端调用 Resend API 发送邮件，避开浏览器 CORS 限制"""
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
            timeout=60,
        )

        if resp.status_code == 200:
            return {"success": True, "message": f"邮件已发送至 {email_to}"}
        else:
            error_detail = resp.text[:500]
            return {
                "success": False,
                "error": f"Resend API 错误 ({resp.status_code}): {error_detail}",
            }

    except Exception as e:
        return {"success": False, "error": f"发送异常: {str(e)}"}


# ============================================================
# Streamlit 页面配置
# ============================================================
st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    layout="wide",
    initial_sidebar_state="expanded",
)

# ============================================================
# 侧边栏：邮件发送功能（由 Python 后端驱动，避开 CORS）
# ============================================================
with st.sidebar:
    st.title("📤 发送计算书至邮箱")
    st.markdown("---")

    email_to = st.text_input(
        "收件人邮箱",
        value=DEFAULT_RECEIVER,
        help="默认发送至 jeziyou@qq.com，可按需修改",
    )

    project_name = st.text_input(
        "项目名称（用于邮件标题）",
        value=PROJECT_NAME_DEFAULT,
    )

    uploaded_file = st.file_uploader(
        "📎 上传计算书文件（PDF / Word）",
        type=["pdf", "docx"],
        help="先在右侧页面中点击'下载计算书 PDF/Word'按钮，把下载好的文件上传到这里，再点击下方'发送邮件'按钮。",
    )

    st.markdown("---")

    if st.button("🚀 发送邮件", type="primary", use_container_width=True):
        if not email_to:
            st.error("请填写收件人邮箱")
        elif not uploaded_file:
            st.error("请先上传计算书文件（PDF 或 Word）")
        else:
            with st.spinner("正在发送邮件..."):
                file_bytes = uploaded_file.getvalue()
                filename = uploaded_file.name

                result = send_email_via_resend(
                    file_bytes, filename, email_to, project_name
                )

                if result["success"]:
                    st.success(f"✅ {result['message']}")
                    st.caption(f"文件：{filename}（{len(file_bytes)/1024:.1f} KB）")
                else:
                    st.error(f"❌ {result['error']}")
                    st.caption("提示：请检查 Resend API Key 是否有效，或稍后重试。")

    st.markdown("---")
    st.info(
        "💡 **使用流程**\n\n"
        "1. 在右侧页面输入参数并点击「计算」\n"
        "2. 点击「下载计算书 PDF/Word」保存文件到本地\n"
        "3. 回到左侧，上传该文件并点击「发送邮件」\n"
        "4. 邮件将由后端 Resend API 发出，不经过浏览器 CORS 限制"
    )
    st.markdown("---")
    st.caption(f"发件人：{SENDER_EMAIL}")
    st.caption(f"默认收件人：{DEFAULT_RECEIVER}")


# ============================================================
# 主页面：嵌入 HTML 计算工具
# ============================================================
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool .html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

st.components.v1.html(html_content, height=9000, scrolling=True)
