"""
MBR 膜设计工具
- 侧边栏：项目名称 + 发送邮件按钮
- 主界面：原 HTML 计算器
- 发送时从 HTML 读取数据 → 后台发送邮件
"""
import streamlit as st
import os
import json
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

# ============================================================================
# 初始化 session_state
# ============================================================================
defaults = {
    "project_name": "MBR膜系统工艺计算书",
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
# 侧边栏：主要项目信息
# ============================================================================
with st.sidebar:
    st.markdown("## 📋 主要项目信息")
    st.markdown("---")

    project_name = st.text_input("项目名称", key="project_name")

    st.markdown("---")

    if st.button("📤 发送项目信息至邮箱", type="primary", use_container_width=True):
        st.session_state["_send_pending"] = True
        st.rerun()

    st.markdown("---")
    st.caption("💡 在HTML中完成计算后，点击上方按钮发送项目信息至 jeziyou@qq.com")

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

# 主 HTML iframe
_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
with open(_html_path, "r", encoding="utf-8") as f:
    _html_content = f.read()
st.components.v1.html(_html_content, height=12000, scrolling=True)

# ============================================================================
# 通信组件：从主 iframe 读取数据（仅在发送请求时）
# ============================================================================
if st.session_state.get("_send_pending"):
    read_script = """
    <script>
    (function poll() {
        var iframes = parent.document.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var doc = iframes[i].contentDocument;
                if (doc && doc.getElementById('btnCalculate')) {
                    var data = {
                        projectName: doc.getElementById('projectName')?.value || '',
                        flowRate: doc.getElementById('flowRate')?.value || '',
                        membraneModel: doc.getElementById('membraneModel')?.value || '',
                        membraneSheets: doc.getElementById('membraneSheets')?.value || '',
                        membranePools: doc.getElementById('membranePools')?.value || '',
                        membraneSeries: doc.getElementById('membraneSeries')?.value || '',
                    };
                    Streamlit.setComponentValue(data);
                    return;
                }
            } catch(e) {}
        }
        setTimeout(poll, 300);
    })();
    </script>
    """
    result = st.components.v1.html(read_script, height=0)

    if result and result != 0 and isinstance(result, dict):
        st.session_state["_send_pending"] = False

        # 解析数据
        model_name = result.get("membraneModel", "")
        sheet_area = MODEL_SHEET_AREA.get(model_name, 40)

        try:
            flow_rate = int(float(result.get("flowRate", 0)))
        except (ValueError, TypeError):
            flow_rate = 0

        try:
            sheets = int(result.get("membraneSheets", 0))
        except (ValueError, TypeError):
            sheets = 0

        try:
            pools = int(result.get("membranePools", 0))
        except (ValueError, TypeError):
            pools = 0

        try:
            series = int(result.get("membraneSeries", 0))
        except (ValueError, TypeError):
            series = 0

        ok = send_summary_email(
            st.session_state.project_name, flow_rate, model_name, sheet_area,
            sheets, pools, series
        )
        if ok:
            st.success("✅ 邮件已发送至 jeziyou@qq.com")
        else:
            st.error("❌ 邮件发送失败")
        st.rerun()