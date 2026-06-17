"""
MBR 膜设计工具
- 保留原始HTML界面
- 接收文件数据 → 显示下载和发邮件按钮
"""
import streamlit as st
import os
import json
import base64
import requests

st.set_page_config(
    page_title="MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 发送邮件
# ============================================================================
def send_email(project_info):
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        
        html_content = f"""
        <h2>{project_info.get('project_name', 'MBR膜系统工艺计算书')}</h2>
        <table style='border-collapse:collapse;border:1px solid #ddd;'>
        <tr><th style='border:1px solid #ddd;padding:8px;'>参数</th><th style='border:1px solid #ddd;padding:8px;'>值</th></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计流量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flow_rate', '-')} m³/d</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片型号</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('model_name', '-')}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总膜面积</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('total_area', '-')} m²</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>平均通量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flux_avg', '-')} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>单位电耗</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('unit_energy', '-')} kWh/m³</td></tr>
        </table>
        <p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """
        
        resp = requests.post(
            "https://api.resend.com/emails",
            json={
                "from": "MBR设计工具 <onboarding@resend.dev>",
                "to": ["jeziyou@qq.com"],
                "subject": f"{project_info.get('project_name', 'MBR')} - 工艺计算摘要",
                "html": html_content
            },
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        return resp.status_code == 200
    except:
        return False

# ============================================================================
# 初始化
# ============================================================================
for key in ["cached_pdf", "cached_word", "cached_info", "pdf_sent", "word_sent"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ============================================================================
# 处理URL参数
# ============================================================================
query_params = st.query_params
file_data = query_params.get("f", "")

if file_data:
    try:
        decoded = json.loads(unescape(decodeURIComponent(file_data)))
        
        file_bytes = base64.b64decode(decoded.get("file_base64", ""))
        file_type = decoded.get("type", "pdf")
        project_info = decoded.get("project_info", {})
        
        if file_type == "pdf":
            st.session_state.cached_pdf = file_bytes
        else:
            st.session_state.cached_word = file_bytes
        st.session_state.cached_info = project_info
        
        st.query_params.clear()
        
    except Exception as e:
        st.error(f"接收数据失败: {e}")

# ============================================================================
# 界面
# ============================================================================
st.markdown("## 💧 MBR 膜设计工具")

# PDF缓存
if st.session_state.cached_pdf:
    st.success("📄 PDF 文件已准备好")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 下载 PDF",
            data=st.session_state.cached_pdf,
            file_name="MBR_计算书.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col2:
        if st.button("📧 发送邮件到 jeziyou@qq.com", use_container_width=True):
            if send_email(st.session_state.cached_info or {}):
                st.session_state.pdf_sent = True
                st.success("✅ 邮件已发送至 jeziyou@qq.com")
            else:
                st.error("❌ 邮件发送失败")

# Word缓存
if st.session_state.cached_word:
    st.success("📝 Word 文件已准备好")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 下载 Word",
            data=st.session_state.cached_word,
            file_name="MBR_计算书.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )
    with col2:
        if st.button("📧 发送邮件到 jeziyou@qq.com", use_container_width=True):
            if send_email(st.session_state.cached_info or {}):
                st.session_state.word_sent = True
                st.success("✅ 邮件已发送至 jeziyou@qq.com")
            else:
                st.error("❌ 邮件发送失败")

# 无缓存时
if not st.session_state.cached_pdf and not st.session_state.cached_word:
    st.info("👇 在下方HTML界面中输入参数并计算，然后点击「导出计算书」")

st.markdown("---")

# 显示HTML
@st.cache_resource
def _load_html():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html"), "r", encoding="utf-8") as f:
        return f.read()

st.components.v1.html(_load_html(), height=12000, scrolling=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;'>
    💧 三菱化学 MBR 膜设计工具
    </div>
    """,
    unsafe_allow_html=True
)
