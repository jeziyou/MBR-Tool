"""
MBR 膜设计工具
- 保留原始HTML界面
- 添加邮件发送区域：输入邮件地址，发送项目概要
- 同时发送给输入的邮件地址和 jeziyou@qq.com
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
# 发送邮件（同时发给用户输入的地址和 jeziyou@qq.com）
# ============================================================================
def send_email(project_info, user_email=None, fmt="PDF"):
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        
        # 构建收件人列表
        to_emails = ["jeziyou@qq.com"]
        if user_email and user_email.strip():
            to_emails.append(user_email.strip())
        
        html_content = f"""
        <h2>{project_info.get('project_name', 'MBR膜系统工艺计算书')}</h2>
        <table style='border-collapse:collapse;border:1px solid #ddd;width:100%;'>
        <tr><th style='border:1px solid #ddd;padding:8px;text-align:left;background:#f5f5f5;'>参数</th><th style='border:1px solid #ddd;padding:8px;text-align:left;'>值</th></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>项目名称</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('project_name', '-')}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计流量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flow_rate', '-')} m³/d</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片型号</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('model_name', '-')}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总膜面积</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('total_area', '-')} m²</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>平均通量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flux_avg', '-')} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>峰值通量</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('flux_peak', '-')} LMH</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总功率</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('total_power', '-')} kW</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>单位电耗</td><td style='border:1px solid #ddd;padding:8px;'>{project_info.get('unit_energy', '-')} kWh/m³</td></tr>
        </table>
        <hr>
        <p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """
        
        resp = requests.post(
            "https://api.resend.com/emails",
            json={
                "from": "MBR设计工具 <onboarding@resend.dev>",
                "to": to_emails,
                "subject": f"{project_info.get('project_name', 'MBR')} - 工艺计算摘要 ({fmt})",
                "html": html_content
            },
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        return resp.status_code == 200, f"已发送至: {', '.join(to_emails)}"
    except Exception as e:
        return False, str(e)

# ============================================================================
# 初始化
# ============================================================================
for key in ["cached_info", "pdf_data", "word_data", "data_sent"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ============================================================================
# 处理URL参数
# ============================================================================
query_params = st.query_params
info_data = query_params.get("info", "")

if info_data:
    try:
        decoded = json.loads(unescape(decodeURIComponent(info_data)))
        
        st.session_state.cached_info = decoded
        st.session_state.data_sent = True
        
        from mbr_calc import ProcessInput, compute_process
        from mbr_report import generate_pdf_report, generate_word_report
        
        inp_data = decoded.get("input", {})
        input_obj = ProcessInput(
            Q=inp_data.get('Q', 5000), Kz=inp_data.get('Kz', 1.3),
            cod_in=inp_data.get('cod_in', 400), bod_in=inp_data.get('bod_in', 200),
            nh3n_in=inp_data.get('nh3n_in', 35), ss_in=inp_data.get('ss_in', 150),
            tn_in=inp_data.get('tn_in', 50), tp_in=inp_data.get('tp_in', 5),
            ph_value=inp_data.get('ph_value', 7.2), T=inp_data.get('T', 20),
            MLSS=inp_data.get('MLSS', 8000), model_index=inp_data.get('model_index', 2),
            sheets_per_rack=inp_data.get('sheets_per_rack', 42),
            pools=inp_data.get('pools', 2), racks_per_pool=inp_data.get('racks_per_pool', 3),
            J25=inp_data.get('J25', 18), fouling_factor=inp_data.get('fouling_factor', 0.85),
            SAD=inp_data.get('SAD', 150), suction_on=inp_data.get('suction_on', 7),
            suction_off=inp_data.get('suction_off', 1), pool_level=inp_data.get('pool_level', 3.5),
            pipe_loss=inp_data.get('pipe_loss', 0.5),
            permeate_pump_head=inp_data.get('permeate_pump_head', 6.5),
            permeate_pump_eff=inp_data.get('permeate_pump_eff', 0.75),
            return_ratio=inp_data.get('return_ratio', 3),
            return_pump_head=inp_data.get('return_pump_head', 0.5),
            return_pump_eff=inp_data.get('return_pump_eff', 0.7),
            fan_efficiency=inp_data.get('fan_efficiency', 0.9),
            enable_bio_blower=False
        )
        
        result_obj = compute_process(input_obj)
        project_name = decoded.get("project_info", {}).get("project_name", "MBR计算书")
        
        st.session_state.pdf_data = generate_pdf_report(
            input_obj, result_obj, project_name=project_name,
            designer="工程师", design_date=datetime.now().strftime("%Y-%m-%d")
        )
        st.session_state.word_data = generate_word_report(
            input_obj, result_obj, project_name=project_name,
            designer="工程师", design_date=datetime.now().strftime("%Y-%m-%d")
        )
        
        st.query_params.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"处理数据失败: {e}")

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 MBR 膜设计工具")

# 显示下载按钮
if st.session_state.pdf_data:
    info = st.session_state.cached_info.get("project_info", {}) if st.session_state.cached_info else {}
    st.success(f"📄 PDF 已准备好：{info.get('project_name', 'MBR项目')}")
    
    col1, col2 = st.columns(2)
    with col1:
        st.download_button(
            label="📥 下载 PDF",
            data=st.session_state.pdf_data,
            file_name=f"{info.get('project_name', 'MBR')}_计算书.pdf",
            mime="application/pdf",
            use_container_width=True
        )
    with col2:
        st.download_button(
            label="📥 下载 Word",
            data=st.session_state.word_data,
            file_name=f"{info.get('project_name', 'MBR')}_计算书.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
            use_container_width=True
        )

# 邮件发送区域
st.markdown("---")
st.markdown("### 📧 发送项目概要邮件")

# 创建邮件发送区域
with st.container():
    st.markdown(
        """
        <div style='background:#f8fafc;border-radius:12px;padding:1rem;border:1px solid #e2e8f0;'>
        <p style='color:#64748b;font-size:14px;margin-bottom:0.5rem;'>输入邮箱地址，发送项目概要到您的邮箱（同时发送到 jeziyou@qq.com）</p>
        </div>
        """,
        unsafe_allow_html=True
    )
    
    col_email, col_send = st.columns([2, 1])
    
    with col_email:
        user_email = st.text_input(
            "收件人邮箱",
            placeholder="请输入您的邮箱地址",
            label_visibility="collapsed"
        )
    
    with col_send:
        if st.button("发送邮件", type="primary", use_container_width=True):
            if st.session_state.cached_info:
                info = st.session_state.cached_info.get("project_info", {})
                success, msg = send_email(info, user_email)
                
                if success:
                    st.success(f"✅ 邮件发送成功！{msg}")
                else:
                    st.error(f"❌ 邮件发送失败: {msg}")
            else:
                st.warning("⚠️ 请先点击下方HTML界面中的「📤 发送项目信息」按钮")

if not st.session_state.data_sent:
    st.info("💡 在下方HTML界面中计算后，点击「📤 发送项目信息」按钮")

st.markdown("---")

# 显示HTML
@st.cache_resource
def _load_html():
    with open(os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html"), "r", encoding="utf-8") as f:
        return f.read()

html_content = _load_html()

# 注入脚本：添加"发送项目信息"按钮
inject_script = """
<script>
(function() {
    function addSendButton() {
        var calcBtn = document.getElementById('btnCompute');
        if (!calcBtn) {
            var buttons = document.querySelectorAll('button');
            for (var i = 0; i < buttons.length; i++) {
                if (buttons[i].textContent.includes('计算')) {
                    calcBtn = buttons[i];
                    break;
                }
            }
        }
        
        if (document.getElementById('sendInfoBtn')) return;
        
        if (calcBtn) {
            var btn = document.createElement('button');
            btn.id = 'sendInfoBtn';
            btn.textContent = '📤 发送项目信息';
            btn.style.cssText = 'margin-left:10px;padding:10px 20px;background:#10b981;color:white;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:bold;';
            btn.onclick = function() {
                if (!APP.lastResult || !APP.lastInput) {
                    alert('请先点击「计算」按钮完成计算');
                    return;
                }
                
                var info = {
                    project_info: {
                        project_name: window.safeStr('projectName') || 'MBR膜系统工艺计算书',
                        flow_rate: APP.lastInput.Q || 0,
                        model_name: APP.lastResult.model_name || '-',
                        sheets: APP.lastInput.sheets_per_rack || 0,
                        pools: APP.lastInput.pools || 0,
                        racks_per_pool: APP.lastInput.racks_per_pool || 0,
                        total_area: Math.round(APP.lastResult.a_actual) || 0,
                        flux_avg: parseFloat((APP.lastResult.j_avg || 0).toFixed(1)),
                        flux_peak: parseFloat((APP.lastResult.j_peak || 0).toFixed(1)),
                        total_power: parseFloat((APP.lastResult.total_power || 0).toFixed(1)),
                        unit_energy: parseFloat((APP.lastResult.unit_energy || 0).toFixed(3))
                    },
                    input: APP.lastInput
                };
                
                var encoded = encodeURIComponent(JSON.stringify(info));
                var url = new URL(window.location.href);
                url.searchParams.set('info', encoded);
                window.location.href = url.toString();
            };
            
            calcBtn.parentNode.insertBefore(btn, calcBtn.nextSibling);
        }
    }
    
    setTimeout(addSendButton, 1500);
})();
</script>
"""

html_content += inject_script

st.components.v1.html(html_content, height=12000, scrolling=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;'>
    💧 三菱化学 MBR 膜设计工具
    </div>
    """,
    unsafe_allow_html=True
)
