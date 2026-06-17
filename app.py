"""
MBR 膜设计工具
- 保留原始HTML界面
- 侧边栏：参数预设 + 确认按钮 → 自动填充HTML并计算 + 发送邮件至 jeziyou@qq.com
"""
import streamlit as st
import os
import urllib.parse
import requests

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
# 发送邮件
# ============================================================================
def send_summary_email(project_name, flow_rate, model_name, sheet_area,
                        sheets_per_rack, pools, racks_per_pool, flux):
    """发送项目概要邮件到 jeziyou@qq.com"""
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"

        # 计算
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
        <hr>
        <p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
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
    st.markdown("---")

    project_name = st.text_input("项目名称", value="MBR膜系统工艺计算书")

    flow_rate = st.number_input("设计水量 (m³/d)", value=5000, min_value=1, step=100)

    model_options = list(MODEL_DISPLAY.keys())
    model_idx = st.selectbox(
        "膜片型号",
        range(len(model_options)),
        format_func=lambda i: MODEL_DISPLAY[model_options[i]],
        index=2  # default: 62E0040SA
    )
    selected_model = model_options[model_idx]

    pools = st.number_input("膜池数", value=2, min_value=1, step=1)

    flux = st.number_input("设计通量 (LMH)", value=18.0, min_value=5.0, max_value=40.0, step=0.5)

    st.markdown("---")

    if st.button("✅ 确认", type="primary", use_container_width=True):
        # 1. 计算每台膜片数和每池台数
        sheet_area = MODEL_SHEET_AREA[selected_model]
        sheets_per_rack = 42  # 默认值

        # a_req = Q * 1000 / (J * 24)
        a_req = flow_rate * 1000 / (flux * 24)
        # racks_per_pool = a_req / (pools * sheets_per_rack * sheet_area)
        racks_per_pool = max(1, round(a_req / (pools * sheets_per_rack * sheet_area)))

        # 2. 发送邮件
        email_ok = send_summary_email(
            project_name, flow_rate, selected_model, sheet_area,
            sheets_per_rack, pools, racks_per_pool, flux
        )

        if email_ok:
            st.success("✅ 邮件已发送至 jeziyou@qq.com")
        else:
            st.warning("⚠️ 邮件发送失败，但参数已设置")

        # 3. 构建URL参数，跳转到HTML页面自动填充
        params = {
            "autoCalc": "1",
            "projectName": project_name,
            "flowRate": str(flow_rate),
            "membraneModel": selected_model,
            "membraneSheets": str(sheets_per_rack),
            "membranePools": str(pools),
            "membraneSeries": str(racks_per_pool),
        }
        query_string = urllib.parse.urlencode(params)
        st.markdown(
            f'<meta http-equiv="refresh" content="0;url=?{query_string}">',
            unsafe_allow_html=True
        )
        st.stop()

    st.markdown("---")
    st.markdown("""
    **📤 确认后自动：**
    1. 发送邮件至 jeziyou@qq.com
    2. 自动填充HTML参数
    3. 自动触发计算
    """)

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

@st.cache_resource
def _load_html():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html"), "r", encoding="utf-8") as f:
        return f.read()

st.components.v1.html(_load_html(), height=12000, scrolling=True)