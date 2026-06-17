"""
MBR 膜设计工具
- 保留原始HTML界面（components.html，纯展示和交互）
- Streamlit 侧边栏：输入邮箱地址，发送项目概要邮件
- 同时发送给输入的邮箱和 jeziyou@qq.com
"""
import streamlit as st
import os
import json
import requests
from datetime import datetime

st.set_page_config(
    page_title="MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 发送邮件
# ============================================================================
def send_summary_email(user_email=None):
    """发送项目概要邮件，同时发给 jeziyou@qq.com 和用户输入的邮箱"""
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"

        to_emails = ["jeziyou@qq.com"]
        if user_email and user_email.strip():
            to_emails.append(user_email.strip())

        # 使用默认参数计算项目信息
        from mbr_calc import ProcessInput, compute_process

        inp = ProcessInput(
            Q=5000, Kz=1.3, cod_in=400, bod_in=200, nh3n_in=35,
            ss_in=150, tn_in=50, tp_in=5, ph_value=7.2, T=20, MLSS=8000,
            model_index=2, sheets_per_rack=42, pools=2, racks_per_pool=3,
            J25=18, fouling_factor=0.85, SAD=150,
            suction_on=7, suction_off=1, pool_level=3.5, pipe_loss=0.5,
            permeate_pump_head=6.5, permeate_pump_eff=0.75,
            return_ratio=3, return_pump_head=0.5, return_pump_eff=0.7,
            fan_efficiency=0.9, enable_bio_blower=False
        )
        result = compute_process(inp)

        html_content = f"""
        <h2>MBR膜系统工艺计算书</h2>
        <table style='border-collapse:collapse;border:1px solid #ddd;width:100%;'>
        <tr><th style='border:1px solid #ddd;padding:8px;text-align:left;background:#f5f5f5;'>参数</th><th style='border:1px solid #ddd;padding:8px;text-align:left;'>值</th></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>项目名称</td><td style='border:1px solid #ddd;padding:8px;'>MBR膜系统工艺计算书</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片型号</td><td style='border:1px solid #ddd;padding:8px;'>{result.model_name}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计流量</td><td style='border:1px solid #ddd;padding:8px;'>5000 m³/d</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总膜面积</td><td style='border:1px solid #ddd;padding:8px;'>{int(result.a_actual):,} m²</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>组件台数</td><td style='border:1px solid #ddd;padding:8px;'>{result.n_racks} 台</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>平均通量</td><td style='border:1px solid #ddd;padding:8px;'>{result.j_avg:.1f} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>峰值通量</td><td style='border:1px solid #ddd;padding:8px;'>{result.j_peak:.1f} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总功率</td><td style='border:1px solid #ddd;padding:8px;'>{result.total_power:.1f} kW</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>单位电耗</td><td style='border:1px solid #ddd;padding:8px;'>{result.unit_energy:.3f} kWh/m³</td></tr>
        </table>
        <hr>
        <p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """

        resp = requests.post(
            "https://api.resend.com/emails",
            json={
                "from": "MBR设计工具 <onboarding@resend.dev>",
                "to": to_emails,
                "subject": "MBR膜系统工艺计算书 - 项目概要",
                "html": html_content
            },
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        return resp.status_code == 200, f"已发送至: {', '.join(to_emails)}"
    except Exception as e:
        return False, str(e)

# ============================================================================
# 侧边栏：邮件发送
# ============================================================================
with st.sidebar:
    st.markdown("## 📧 发送项目概要")

    st.markdown("---")

    user_email = st.text_input(
        "收件人邮箱",
        placeholder="请输入邮箱地址",
        key="sidebar_email"
    )

    st.caption("邮件将同时发送至 jeziyou@qq.com")

    if st.button("📧 发送邮件", type="primary", use_container_width=True):
        with st.spinner("正在发送..."):
            success, msg = send_summary_email(user_email)
            if success:
                st.success(f"✅ {msg}")
            else:
                st.error(f"❌ 发送失败: {msg}")

    st.markdown("---")
    st.markdown("""
    **📤 邮件内容包含：**
    - 项目名称
    - 膜片型号
    - 设计流量
    - 总膜面积
    - 组件台数
    - 平均通量 / 峰值通量
    - 总功率 / 单位电耗
    """)

    st.markdown("---")
    st.caption("💡 在右侧HTML界面中计算并导出PDF/Word文件")

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

# 读取并显示HTML
@st.cache_resource
def _load_html():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html"), "r", encoding="utf-8") as f:
        return f.read()

st.components.v1.html(_load_html(), height=12000, scrolling=True)