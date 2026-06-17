"""
MBR 膜设计工具
- 侧边栏参数与HTML实时同步（无需点击确认）
- 点击「发送邮件」按钮发送项目概要至 jeziyou@qq.com
"""
import streamlit as st
import os
import urllib.parse
import requests
import math

st.set_page_config(
    page_title="MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 膜型号→膜面积映射
# ============================================================================
MODEL_SHEET_AREA = {
    "56E0040SA": 40, "63E0040SA": 40, "62E0040SA": 40,
    "60E0025SA": 25, "55E0025SA": 25, "50E0025SA": 25,
    "55E0015SA": 15, "60E0015SA": 15, "50E0015SA": 15,
    "50E0006SA": 6,
}

MODEL_DISPLAY = {
    "56E0040SA": "56E0040SA - UF 0.05μm 40m²",
    "63E0040SA": "63E0040SA - UF 0.1μm 40m²",
    "62E0040SA": "62E0040SA - UF 0.2μm 40m²",
    "60E0025SA": "60E0025SA - MF 0.4μm 25m²",
    "55E0025SA": "55E0025SA - UF 0.05μm 25m²",
    "50E0025SA": "50E0025SA - MF 0.4μm 25m²",
    "55E0015SA": "55E0015SA - UF 0.05μm 15m²",
    "60E0015SA": "60E0015SA - MF 0.4μm 15m²",
    "50E0015SA": "50E0015SA - MF 0.4μm 15m²",
    "50E0006SA": "50E0006SA - MF 0.4μm 6m²",
}

# ============================================================================
# 初始化 session_state
# ============================================================================
defaults = {
    "project_name": "MBR膜系统工艺计算书",
    "flow_rate": 5000,
    "model_idx": 2,
    "pools": 2,
    "flux": 18.0,
    "param_hash": "",
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# 发送邮件
# ============================================================================
def send_summary_email(project_name, flow_rate, model_name, sheet_area,
                        sheets_per_rack, pools, racks_per_pool, flux):
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"

        a_actual = pools * racks_per_pool * sheets_per_rack * sheet_area
        j_avg = flow_rate * 1000 / (a_actual * 24) if a_actual > 0 else 0

        html_content = f"""
        <h2>{project_name}</h2>
        <table style='border-collapse:collapse;border:1px solid #ddd;width:100%;'>
        <tr><th style='border:1px solid #ddd;padding:8px;text-align:left;background:#f5f5f5;'>参数</th><th style='border:1px solid #ddd;padding:8px;text-align:left;'>值</th></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>项目名称</td><td style='border:1px solid #ddd;padding:8px;'>{project_name}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计流量</td><td style='border:1px solid #ddd;padding:8px;'>{flow_rate} m³/d</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片型号</td><td style='border:1px solid #ddd;padding:8px;'>{model_name}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>每台膜片数</td><td style='border:1px solid #ddd;padding:8px;'>{sheets_per_rack} 片</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜池数</td><td style='border:1px solid #ddd;padding:8px;'>{pools} 池</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>每池台数</td><td style='border:1px solid #ddd;padding:8px;'>{racks_per_pool} 台</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总膜面积</td><td style='border:1px solid #ddd;padding:8px;'>{int(a_actual):,} m²</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计通量</td><td style='border:1px solid #ddd;padding:8px;'>{flux:.1f} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>实际通量</td><td style='border:1px solid #ddd;padding:8px;'>{j_avg:.1f} LMH</td></tr>
        </table>
        <hr><p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """

        resp = requests.post(
            "https://api.resend.com/emails",
            json={
                "from": "MBR设计工具 <onboarding@resend.dev>",
                "to": ["jeziyou@qq.com"],
                "subject": f"{project_name} - 工艺计算书",
                "html": html_content
            },
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        return resp.status_code == 200
    except Exception:
        return False

# ============================================================================
# 侧边栏：参数预设
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ 参数预设")
    st.caption("修改参数后HTML自动同步")
    st.markdown("---")

    project_name = st.text_input(
        "项目名称",
        value=st.session_state.project_name,
        key="project_name"
    )

    flow_rate = st.number_input(
        "设计水量 (m³/d)",
        value=st.session_state.flow_rate,
        min_value=1, step=100,
        key="flow_rate"
    )

    model_options = list(MODEL_DISPLAY.keys())
    model_idx = st.selectbox(
        "膜片型号",
        range(len(model_options)),
        format_func=lambda i: MODEL_DISPLAY[model_options[i]],
        index=st.session_state.model_idx,
        key="model_idx"
    )
    selected_model = model_options[model_idx]

    pools = st.number_input(
        "膜池数",
        value=st.session_state.pools,
        min_value=1, step=1,
        key="pools"
    )

    flux = st.number_input(
        "设计通量 (LMH)",
        value=st.session_state.flux,
        min_value=5.0, max_value=40.0, step=0.5,
        key="flux"
    )

    # 计算每台膜片数和每池台数
    sheet_area = MODEL_SHEET_AREA[selected_model]
    sheets_per_rack = 42
    a_req = flow_rate * 1000 / (flux * 24) if flux > 0 else 0
    racks_per_pool = max(1, round(a_req / (pools * sheets_per_rack * sheet_area))) if pools > 0 and sheet_area > 0 else 1

    # 显示计算结果
    st.markdown("---")
    st.caption(f"自动计算：每台 {sheets_per_rack} 片，每池 {racks_per_pool} 台")
    a_actual = pools * racks_per_pool * sheets_per_rack * sheet_area
    actual_flux = flow_rate * 1000 / (a_actual * 24) if a_actual > 0 else 0
    st.caption(f"总膜面积：{int(a_actual):,} m²，实际通量：{actual_flux:.1f} LMH")

    st.markdown("---")

    # 发送邮件按钮
    if st.button("📧 发送邮件", type="primary", use_container_width=True):
        ok = send_summary_email(
            project_name, flow_rate, selected_model, sheet_area,
            sheets_per_rack, pools, racks_per_pool, flux
        )
        if ok:
            st.success("✅ 邮件已发送至 jeziyou@qq.com")
        else:
            st.error("❌ 邮件发送失败")

    st.markdown("---")
    st.caption("💡 参数修改后右侧HTML自动同步并计算")

# ============================================================================
# 实时同步：更新URL参数
# ============================================================================
param_hash = f"{project_name}|{flow_rate}|{selected_model}|{pools}|{flux}"

if param_hash != st.session_state.param_hash:
    st.session_state.param_hash = param_hash

    params = {
        "autoCalc": "1",
        "projectName": project_name,
        "flowRate": str(flow_rate),
        "membraneModel": selected_model,
        "membraneSheets": str(sheets_per_rack),
        "membranePools": str(pools),
        "membraneSeries": str(racks_per_pool),
    }

    # 使用 st.query_params 更新（会触发一次rerun，但下次hash相同不会重复）
    try:
        st.query_params.update(params)
    except Exception:
        pass

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

@st.cache_resource
def _load_html():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html"), "r", encoding="utf-8") as f:
        return f.read()

st.components.v1.html(_load_html(), height=12000, scrolling=True)