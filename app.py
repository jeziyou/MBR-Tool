"""
MBR 膜设计工具 - Streamlit 应用
- 保留原始HTML界面用于参数输入和计算
- Streamlit 按钮触发导出和邮件发送
- Python 生成 PDF/Word 文件并发送邮件
"""
import streamlit as st
import os
import json
import base64
import requests
from datetime import datetime

st.set_page_config(
    page_title="MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 邮件发送函数
# ============================================================================
def send_email(project_info, file_bytes=None, filename=None, fmt="pdf"):
    """发送邮件（可选附件）"""
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        
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
            "subject": f"{project_info.get('project_name', 'MBR计算书')} - 工艺计算摘要 ({fmt.upper()})",
            "html": html_content
        }
        
        if file_bytes and filename:
            payload["attachments"] = [{
                "filename": filename,
                "content": base64.b64encode(file_bytes).decode("utf-8")
            }]
        
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
# 从字典重建 ProcessInput 对象
# ============================================================================
def dict_to_process_input(d):
    """将字典转换为 ProcessInput 对象"""
    from mbr_calc import ProcessInput
    return ProcessInput(
        Q=d.get('Q', 5000),
        Kz=d.get('Kz', 1.3),
        cod_in=d.get('cod_in', 400),
        bod_in=d.get('bod_in', 200),
        nh3n_in=d.get('nh3n_in', 35),
        ss_in=d.get('ss_in', 150),
        tn_in=d.get('tn_in', 50),
        tp_in=d.get('tp_in', 5),
        ph_value=d.get('ph_value', 7.2),
        T=d.get('T', 20),
        MLSS=d.get('MLSS', 8000),
        model_index=d.get('model_index', 2),
        sheets_per_rack=d.get('sheets_per_rack', 42),
        pools=d.get('pools', 2),
        racks_per_pool=d.get('racks_per_pool', 3),
        J25=d.get('J25', 18),
        fouling_factor=d.get('fouling_factor', 0.85),
        SAD=d.get('SAD', 150),
        suction_on=d.get('suction_on', 7),
        suction_off=d.get('suction_off', 1),
        pool_level=d.get('pool_level', 3.5),
        pipe_loss=d.get('pipe_loss', 0.5),
        permeate_pump_head=d.get('permeate_pump_head', 6.5),
        permeate_pump_eff=d.get('permeate_pump_eff', 0.75),
        return_ratio=d.get('return_ratio', 3),
        return_pump_head=d.get('return_pump_head', 0.5),
        return_pump_eff=d.get('return_pump_eff', 0.7),
        fan_efficiency=d.get('fan_efficiency', 0.9),
        enable_bio_blower=d.get('enable_bio_blower', False)
    )

# ============================================================================
# 处理 URL 中的计算结果
# ============================================================================
query_params = st.query_params
calc_data = query_params.get("calc", "")

# 初始化 session_state
if "project_info" not in st.session_state:
    st.session_state.project_info = None
if "calc_input_dict" not in st.session_state:
    st.session_state.calc_input_dict = None

if calc_data:
    try:
        decoded_str = unescape(decodeURIComponent(calc_data))
        data = json.loads(decoded_str)
        
        st.session_state.project_info = data.get("project_info", {})
        st.session_state.calc_input_dict = data.get("input", {})
        
        st.query_params.clear()
        
    except Exception as e:
        st.error(f"数据解析失败: {e}")

# ============================================================================
# 导出按钮区域
# ============================================================================
st.markdown("### 📄 导出计算书")

has_result = st.session_state.calc_input_dict is not None

if has_result:
    st.success(f"✅ 已获取计算结果：{st.session_state.project_info.get('project_name', 'MBR项目')}")
    
    col1, col2, col3 = st.columns([1, 1, 2])
    
    with col1:
        pdf_btn = st.button("📄 导出 PDF 计算书", type="primary", use_container_width=True)
    
    with col2:
        word_btn = st.button("📝 导出 Word 计算书", type="secondary", use_container_width=True)
    
    # PDF 导出
    if pdf_btn:
        with st.spinner("正在生成 PDF..."):
            try:
                from mbr_calc import compute_process
                from mbr_report import generate_pdf_report
                
                # 重建输入对象并重新计算
                input_obj = dict_to_process_input(st.session_state.calc_input_dict)
                result_obj = compute_process(input_obj)
                
                pdf_bytes = generate_pdf_report(
                    input_obj, result_obj,
                    project_name=st.session_state.project_info.get('project_name', 'MBR计算书'),
                    designer="工程师",
                    design_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                success, msg = send_email(
                    st.session_state.project_info,
                    pdf_bytes,
                    f"{st.session_state.project_info.get('project_name', 'MBR')}_计算书.pdf",
                    "pdf"
                )
                
                if success:
                    st.success("✅ 邮件已发送至 jeziyou@qq.com")
                else:
                    st.warning(f"⚠️ 邮件发送失败: {msg}")
                
                st.download_button(
                    label="⬇️ 下载 PDF 文件",
                    data=pdf_bytes,
                    file_name=f"{st.session_state.project_info.get('project_name', 'MBR')}_计算书.pdf",
                    mime="application/pdf",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"PDF 生成失败: {e}")
    
    # Word 导出
    if word_btn:
        with st.spinner("正在生成 Word..."):
            try:
                from mbr_calc import compute_process
                from mbr_report import generate_word_report
                
                input_obj = dict_to_process_input(st.session_state.calc_input_dict)
                result_obj = compute_process(input_obj)
                
                word_bytes = generate_word_report(
                    input_obj, result_obj,
                    project_name=st.session_state.project_info.get('project_name', 'MBR计算书'),
                    designer="工程师",
                    design_date=datetime.now().strftime("%Y-%m-%d")
                )
                
                success, msg = send_email(
                    st.session_state.project_info,
                    word_bytes,
                    f"{st.session_state.project_info.get('project_name', 'MBR')}_计算书.docx",
                    "word"
                )
                
                if success:
                    st.success("✅ 邮件已发送至 jeziyou@qq.com")
                else:
                    st.warning(f"⚠️ 邮件发送失败: {msg}")
                
                st.download_button(
                    label="⬇️ 下载 Word 文件",
                    data=word_bytes,
                    file_name=f"{st.session_state.project_info.get('project_name', 'MBR')}_计算书.docx",
                    mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                    use_container_width=True
                )
                
            except Exception as e:
                st.error(f"Word 生成失败: {e}")

else:
    st.info("👈 请在下方 HTML 界面中输入参数并点击「计算」，然后点击「📤 发送结果到导出区」按钮")

st.markdown("---")

# ============================================================================
# 读取并显示原始 HTML
# ============================================================================
@st.cache_resource
def _load_html():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

html_content = _load_html()

# 注入脚本：在 HTML 中添加「发送结果到导出区」按钮
inject_script = """
<script>
(function() {
    setTimeout(function() {
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
        
        if (calcBtn && !document.getElementById('sendToExportBtn')) {
            var sendBtn = document.createElement('button');
            sendBtn.id = 'sendToExportBtn';
            sendBtn.textContent = '📤 发送结果到导出区';
            sendBtn.style.cssText = 'margin-left:10px;padding:10px 20px;background:#1e40af;color:white;border:none;border-radius:6px;cursor:pointer;font-size:14px;font-weight:bold;';
            sendBtn.onclick = function() {
                if (!APP.lastResult || !APP.lastInput) {
                    alert('请先点击「计算」按钮完成计算');
                    return;
                }
                
                var data = {
                    project_info: {
                        project_name: safeStr('projectName') || 'MBR膜系统工艺计算书',
                        flow_rate: APP.lastInput.Q || 0,
                        model_name: APP.lastResult.model_name || '-',
                        sheets: APP.lastInput.sheets_per_rack || 0,
                        pools: APP.lastInput.pools || 0,
                        racks_per_pool: APP.lastInput.racks_per_pool || 0,
                        total_area: Math.round(APP.lastResult.a_actual) || 0,
                        flux_avg: (APP.lastResult.j_avg || 0).toFixed(1),
                        flux_peak: (APP.lastResult.j_peak || 0).toFixed(1),
                        total_power: (APP.lastResult.total_power || 0).toFixed(1),
                        unit_energy: (APP.lastResult.unit_energy || 0).toFixed(3)
                    },
                    input: APP.lastInput
                };
                
                var encoded = encodeURIComponent(JSON.stringify(data));
                var url = new URL(window.location.href);
                url.searchParams.set('calc', encoded);
                window.location.href = url.toString();
            };
            
            calcBtn.parentNode.insertBefore(sendBtn, calcBtn.nextSibling);
        }
    }, 1000);
})();
</script>
"""

html_content += inject_script

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
