"""
MBR 膜系统工艺设计工具 - Streamlit 主应用（最终版）
- 原始 HTML 界面通过 components.html 展示（保留所有外观和前端逻辑）
- PDF/Word 在前端 HTML 中生成（保持原有格式）
- 邮件发送通过 Python 后端调用 Resend API
- 文件下载由 Streamlit download_button 提供
"""
import streamlit as st
import os
import json
import base64
import requests

# ============================================================================
# Page 配置
# ============================================================================
st.set_page_config(
    page_title="MBR 膜设计工具 - 工艺计算书",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 读取原始 HTML 内容
# ============================================================================
@st.cache_resource(show_spinner=False)
def _load_html():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# 初始化 session_state
# ============================================================================
if "pending_email" not in st.session_state:
    st.session_state.pending_email = None

if "email_result" not in st.session_state:
    st.session_state.email_result = None

if "pdf_bytes" not in st.session_state:
    st.session_state.pdf_bytes = None

if "word_bytes" not in st.session_state:
    st.session_state.word_bytes = None

if "file_ready" not in st.session_state:
    st.session_state.file_ready = None


# ============================================================================
# 辅助函数
# ============================================================================
def _send_email_via_resend(file_b64, filename, project_name, fmt):
    """通过 Resend API 发送邮件（Python 后端调用，无 CORS 问题）"""
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        payload = {
            "from": "MBR设计工具 <onboarding@resend.dev>",
            "to": ["jeziyou@qq.com"],
            "subject": f"{project_name} - 工艺计算书 ({fmt.upper()})",
            "html": (
                f"<h2>{project_name}</h2>"
                f"<p>您好，</p>"
                f"<p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书（{fmt.upper()}格式），请查收附件。</p>"
                f"<hr><p style='color:#999;font-size:12px;'>此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>"
            ),
            "attachments": [{
                "filename": filename,
                "content": file_b64
            }]
        }
        resp = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json"
            },
            timeout=30
        )
        if resp.status_code == 200:
            return f"✅ 邮件已发送至 jeziyou@qq.com"
        return f"⚠️ 邮件发送失败 (HTTP {resp.status_code}): {resp.text[:100]}"
    except Exception as e:
        return f"⚠️ 邮件发送异常: {str(e)[:100]}"


# ============================================================================
# 主界面
# ============================================================================

st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

# 顶部状态栏
col_header1, col_header2 = st.columns([4, 1])
with col_header1:
    st.success(
        "✅ 系统就绪 — 在下方界面中调整参数、点击「计算」，"
        "然后点击「📄 导出计算书 PDF」或「📝 导出计算书 Word」，"
        "文件下载的同时邮件将自动发送至 **jeziyou@qq.com**"
    )
with col_header2:
    st.markdown("**📄 PDF / 📝 Word** 按钮在左侧面板底部")

st.markdown("---")

# 加载并渲染原始 HTML 界面
html_content = _load_html()
component_result = st.components.v1.html(html_content, height=12000, scrolling=True)

# ============================================================================
# 处理从 HTML 传来的数据
# ============================================================================
if component_result is not None:
    data = component_result

    # === 情况1: 邮件发送请求 ===
    if isinstance(data, dict) and data.get("type") == "email_request":
        file_b64 = data.get("file_base64", "")
        filename = data.get("filename", "MBR_计算书")
        project_name = data.get("project_name", "MBR膜系统工艺计算书")
        fmt = data.get("format", "pdf")
        file_bytes = base64.b64decode(file_b64) if file_b64 else None

        if file_bytes and len(file_bytes) > 100:
            # 保存到 session_state 以便下载
            if fmt.lower() == "pdf":
                st.session_state.pdf_bytes = file_bytes
            else:
                st.session_state.word_bytes = file_bytes
            st.session_state.file_ready = filename

            # 发送邮件
            email_status = _send_email_via_resend(file_b64, filename, project_name, fmt)
            st.session_state.email_result = email_status

            st.rerun()
        else:
            st.warning("文件数据无效，请重试")

    # === 情况2: 其他通信数据 ===
    else:
        st.info(f"收到数据: {str(data)[:100]}")

# ============================================================================
# 下载区域（始终显示如果有文件）
# ============================================================================
has_pdf = st.session_state.pdf_bytes is not None
has_word = st.session_state.word_bytes is not None

if has_pdf or has_word or st.session_state.email_result:
    st.markdown("---")
    st.markdown("### 📥 计算书下载")

    if st.session_state.email_result:
        st.success(st.session_state.email_result)

    dl_col1, dl_col2 = st.columns(2)
    with dl_col1:
        if has_pdf:
            project_for_dl = st.session_state.file_ready.replace(".pdf","").replace(".docx","") if st.session_state.file_ready else "MBR"
            st.download_button(
                label="📄 下载 PDF 计算书",
                data=st.session_state.pdf_bytes,
                file_name=f"{project_for_dl}.pdf",
                mime="application/pdf",
                use_container_width=True,
                type="primary"
            )
        else:
            st.button("📄 下载 PDF 计算书", disabled=True, use_container_width=True)

    with dl_col2:
        if has_word:
            project_for_dl = st.session_state.file_ready.replace(".pdf","").replace(".docx","") if st.session_state.file_ready else "MBR"
            st.download_button(
                label="📝 下载 Word 计算书",
                data=st.session_state.word_bytes,
                file_name=f"{project_for_dl}.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                type="secondary"
            )
        else:
            st.button("📝 下载 Word 计算书", disabled=True, use_container_width=True)

    # 清除按钮
    if st.button("🗑️ 清除已下载文件", use_container_width=False):
        st.session_state.pdf_bytes = None
        st.session_state.word_bytes = None
        st.session_state.email_result = None
        st.session_state.file_ready = None
        st.rerun()

# ============================================================================
# 底部说明
# ============================================================================
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;padding:1rem;'>
    💧 三菱化学 MBR 膜系统工艺设计工具 | 邮件自动发送至 jeziyou@qq.com | Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
