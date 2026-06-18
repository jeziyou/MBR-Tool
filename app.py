"""
MBR 膜设计工具
- 侧边栏参数预设 → 确认后同步HTML + 发送邮件
- 侧边栏数值不会恢复默认值
"""
import streamlit as st
import os
import smtplib
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

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


def get_sheets_range(sheet_area):
    """根据膜面积返回每台膜片数范围（与HTML一致）"""
    if sheet_area == 6:
        return 5, 30
    return 5, 60


# ============================================================================
# 初始化 session_state（侧边栏值不会恢复默认值）
# ============================================================================
defaults = {
    "project_name": "MBR膜系统工艺计算书",
    "model_idx": 2,
    "sheets_per_rack": 42,
    "pools": 2,
    "racks_per_pool": 3,
    "flow_rate": 5000,
    "iframe_version": 0,
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# 发送邮件
# ============================================================================
def send_summary_email(project_name, flow_rate, model_name, sheet_area,
                        sheets_per_rack, pools, racks_per_pool):
    try:
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
        <tr><td style='border:1px solid #ddd;padding:8px;'>平均通量</td><td style='border:1px solid #ddd;padding:8px;'>{j_avg:.1f} LMH</td></tr>
        </table>
        <hr><p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{project_name} - 工艺计算书"
        msg["From"] = "MBR设计工具 <jeziyou@163.com>"
        msg["To"] = "jeziyou@qq.com"
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        with smtplib.SMTP_SSL("smtp.163.com", 465, timeout=30) as server:
            server.login("jeziyou@163.com", "FNR3q3BjMYLyTEah")
            server.sendmail("jeziyou@163.com", ["jeziyou@qq.com"], msg.as_string())
        return True
    except Exception:
        return False

# ============================================================================
# 侧边栏：参数预设
# ============================================================================
with st.sidebar:
    st.markdown("## ⚙️ 参数预设")
    st.markdown("---")

    # 1. 项目名称
    project_name = st.text_input(
        "项目名称",
        key="project_name"
    )

    # 2. 设计水量
    flow_rate = st.number_input(
        "设计水量 (m³/d)",
        min_value=1, step=100,
        key="flow_rate"
    )

    # 3. 膜片型号
    model_options = list(MODEL_DISPLAY.keys())
    model_idx = st.selectbox(
        "膜片型号",
        range(len(model_options)),
        format_func=lambda i: MODEL_DISPLAY[model_options[i]],
        key="model_idx"
    )
    selected_model = model_options[model_idx]
    sheet_area = MODEL_SHEET_AREA[selected_model]

    # 3. 每台膜片数（范围与HTML一致）
    sh_min, sh_max = get_sheets_range(sheet_area)
    # 确保当前值在有效范围内
    if st.session_state.sheets_per_rack < sh_min or st.session_state.sheets_per_rack > sh_max:
        st.session_state.sheets_per_rack = max(sh_min, min(sh_max, st.session_state.sheets_per_rack))

    sheets_per_rack = st.number_input(
        "每台膜片数",
        min_value=sh_min, max_value=sh_max, step=1,
        key="sheets_per_rack"
    )

    # 4. 膜池数
    pools = st.number_input(
        "膜池数",
        min_value=1, step=1,
        key="pools"
    )

    # 5. 每池台数
    racks_per_pool = st.number_input(
        "每池台数",
        min_value=1, step=1,
        key="racks_per_pool"
    )

    # 计算结果预览
    st.markdown("---")
    a_actual = pools * racks_per_pool * sheets_per_rack * sheet_area
    actual_flux = flow_rate * 1000 / (a_actual * 24) if a_actual > 0 else 0
    st.metric("总膜面积", f"{int(a_actual):,} m²")
    st.metric("平均通量", f"{actual_flux:.1f} LMH")

    st.markdown("---")

    # 确认按钮
    if st.button("✅ 确认", type="primary", use_container_width=True):
        # 发送邮件
        ok = send_summary_email(
            project_name, flow_rate, selected_model, sheet_area,
            sheets_per_rack, pools, racks_per_pool
        )
        if ok:
            st.success("✅ 邮件已发送至 jeziyou@qq.com")
        else:
            st.error("❌ 邮件发送失败")

        # 同步到HTML（使用 query_params + rerun）
        st.query_params["autoCalc"] = "1"
        st.query_params["projectName"] = project_name
        st.query_params["flowRate"] = str(flow_rate)
        st.query_params["membraneModel"] = selected_model
        st.query_params["membraneSheets"] = str(sheets_per_rack)
        st.query_params["membranePools"] = str(pools)
        st.query_params["membraneSeries"] = str(racks_per_pool)
        st.session_state.iframe_version += 1
        st.rerun()

    st.markdown("---")
    st.caption("💡 点击「确认」后HTML自动同步参数并计算并发送邮件")

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
with open(_html_path, "r", encoding="utf-8") as f:
    _html_content = f.read()
_html_content += f"\n<!-- v{st.session_state.iframe_version} -->"
st.components.v1.html(_html_content, height=12000, scrolling=True)