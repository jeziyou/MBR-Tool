"""
MBR 膜设计工具 - Streamlit 应用
- 保留原始HTML界面和交互
- 导出时发送项目摘要邮件（名称、水量、膜型号、面积等）
- 文件下载由浏览器原生触发
"""
import streamlit as st
import os
import json
import requests

st.set_page_config(
    page_title="MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 发送邮件（仅发送文本信息，无附件）
# ============================================================================
def send_email(project_info):
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        
        # 邮件内容模板
        html_content = f"""
        <h2>{project_info.get('project_name', 'MBR膜系统工艺计算书')}</h2>
        <table style='border-collapse:collapse;border:1px solid #ddd;width:100%;'>
        <tr><th style='border:1px solid #ddd;padding:8px;text-align:left;background:#f5f5f5;'>参数</th><th style='border:1px solid #ddd;padding:8px;text-align:left;'>值</th></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>项目名称</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('project_name', '-')}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计流量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flow_rate', '-')} m³/d</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片型号</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('model_name', '-')}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片数量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('sheets', '-')} 片</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜池数量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('pools', '-')} 池</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>每池台数</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('racks_per_pool', '-')} 台</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总膜面积</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('total_area', '-')} m²</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>平均通量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flux_avg', '-')} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>峰值通量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flux_peak', '-')} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总功率</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('total_power', '-')} kW</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>单位电耗</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('unit_energy', '-')} kWh/m³</td></tr>
        </table>
        <hr>
        <p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """
        
        payload = {
            "from": "MBR设计工具 <onboarding@resend.dev>",
            "to": ["jeziyou@qq.com"],
            "subject": f"{project_info.get('project_name', 'MBR计算书')} - 工艺计算摘要",
            "html": html_content
        }
        
        resp = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        
        return resp.status_code == 200, resp.status_code
    except Exception as e:
        return False, str(e)

# ============================================================================
# 处理 URL 中的邮件请求
# ============================================================================
query_params = st.query_params
email_data = query_params.get("e", "")

if email_data:
    try:
        decoded_str = unescape(decodeURIComponent(email_data))
        project_info = json.loads(decoded_str)
        
        success, result = send_email(project_info)
        
        if success:
            st.success(f"✅ 邮件已发送至 jeziyou@qq.com")
            st.info("📄 文件已下载，请查看浏览器下载")
        else:
            st.error(f"⚠️ 邮件发送失败: {result}")
        
        st.query_params.clear()
        
    except Exception as e:
        st.error(f"处理失败: {e}")
        st.query_params.clear()

# ============================================================================
# 读取并显示原始 HTML
# ============================================================================
@st.cache_resource
def _load_html():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

html_content = _load_html()

# 显示界面
st.success("✅ 系统就绪 - 点击「导出计算书」将发送项目摘要邮件至 jeziyou@qq.com")
st.markdown("---")
st.components.v1.html(html_content, height=12000, scrolling=True)
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;padding:1rem;'>
    💧 三菱化学 MBR 膜系统工艺设计工具 | 邮件发送至 jeziyou@qq.com
    </div>
    """,
    unsafe_allow_html=True
)
