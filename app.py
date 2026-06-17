"""
MBR 膜设计工具 - Streamlit 应用
- 保留原始HTML界面
- 点击导出 → 生成文件并缓存 → 显示下载按钮 → 点击下载时发送邮件
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
# 发送邮件（无附件，只发摘要）
# ============================================================================
def send_summary_email(project_info, fmt):
    """发送项目摘要邮件"""
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
                "subject": f"{project_info.get('project_name', 'MBR')} - 工艺计算摘要 ({fmt})",
                "html": html_content
            },
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        return resp.status_code == 200
    except:
        return False

# ============================================================================
# 初始化 session_state
# ============================================================================
for key in ["cached_pdf", "cached_word", "cached_project_info", "email_sent_pdf", "email_sent_word"]:
    if key not in st.session_state:
        st.session_state[key] = None

# ============================================================================
# 处理 URL 参数（接收HTML传递的文件数据）
# ============================================================================
query_params = st.query_params
file_data = query_params.get("f", "")

if file_data:
    try:
        decoded_str = unescape(decodeURIComponent(file_data))
        data = json.loads(decoded_str)
        
        file_bytes = base64.b64decode(data.get("file_base64", ""))
        file_type = data.get("type", "pdf")  # pdf or word
        filename = data.get("filename", "MBR_计算书")
        project_info = data.get("project_info", {})
        
        if file_type == "pdf":
            st.session_state.cached_pdf = file_bytes
            st.session_state.cached_project_info = project_info
        else:
            st.session_state.cached_word = file_bytes
            st.session_state.cached_project_info = project_info
        
        st.query_params.clear()
        st.rerun()
        
    except Exception as e:
        st.error(f"接收文件失败: {e}")

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 MBR 膜设计工具")

# 状态显示
if st.session_state.cached_pdf:
    st.success("✅ PDF 文件已生成，请点击下方按钮下载")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 下载 PDF 计算书", type="primary", use_container_width=True):
            # 发送邮件
            if st.session_state.cached_project_info:
                send_summary_email(st.session_state.cached_project_info, "PDF")
                st.session_state.email_sent_pdf = True
            st.download_button(
                label="✅ PDF 已下载（邮件已发送）",
                data=st.session_state.cached_pdf,
                file_name="MBR_计算书.pdf",
                mime="application/pdf",
                use_container_width=True,
                disabled=True
            )
    with col2:
        st.button("🗑️ 清除缓存", on_click=lambda: setattr(st.session_state, 'cached_pdf', None), use_container_width=True)

elif st.session_state.cached_word:
    st.success("✅ Word 文件已生成，请点击下方按钮下载")
    col1, col2 = st.columns([1, 1])
    with col1:
        if st.button("📥 下载 Word 计算书", type="primary", use_container_width=True):
            if st.session_state.cached_project_info:
                send_summary_email(st.session_state.cached_project_info, "Word")
                st.session_state.email_sent_word = True
            st.download_button(
                label="✅ Word 已下载（邮件已发送）",
                data=st.session_state.cached_word,
                file_name="MBR_计算书.docx",
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True,
                disabled=True
            )
    with col2:
        st.button("🗑️ 清除缓存", on_click=lambda: setattr(st.session_state, 'cached_word', None), use_container_width=True)

else:
    st.info("👇 在下方HTML界面中输入参数并计算，然后点击「导出计算书」按钮")

# 显示邮件发送状态
if st.session_state.email_sent_pdf or st.session_state.email_sent_word:
    fmt = "PDF" if st.session_state.email_sent_pdf else "Word"
    st.success(f"✅ {fmt}下载完成，邮件已发送至 jeziyou@qq.com")

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

# 注入脚本：修改 sendReportByEmail，传递文件数据到 Streamlit
inject_script = """
<script>
// 修改导出函数，生成文件后通过URL传递数据给Streamlit
(function() {
    var _original = window.sendReportByEmail;
    window.sendReportByEmail = async function(format, existingBlob, existingFilename) {
        // 执行原始导出（下载文件）
        if (_original) {
            await _original.call(this, format, existingBlob, existingFilename);
        }
        
        // 重新生成文件（因为原始函数可能已经释放了blob）
        try {
            var blob, filename;
            if (existingBlob) {
                blob = existingBlob;
                filename = existingFilename;
            } else {
                if (format === 'pdf') {
                    blob = await window.exportCalcPDF({ returnBlob: true });
                    filename = (window.safeStr('projectName') || 'MBR') + '_计算书.pdf';
                } else {
                    blob = await window.exportCalcDOCX({ returnBlob: true });
                    filename = (window.safeStr('projectName') || 'MBR') + '_计算书.docx';
                }
            }
            
            if (!blob) return;
            
            // 转换为base64
            var base64Data = await new Promise(function(resolve, reject) {
                var reader = new FileReader();
                reader.onload = function(e) { resolve(e.target.result.split(',')[1]); };
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
            
            // 收集项目信息
            var projectInfo = {
                project_name: window.safeStr('projectName') || 'MBR膜系统工艺计算书',
                flow_rate: (APP.lastInput && APP.lastInput.Q) ? APP.lastInput.Q : '-',
                model_name: (APP.lastResult && APP.lastResult.model_name) ? APP.lastResult.model_name : '-',
                total_area: (APP.lastResult && APP.lastResult.a_actual) ? Math.round(APP.lastResult.a_actual) : '-',
                flux_avg: (APP.lastResult && APP.lastResult.j_avg) ? APP.lastResult.j_avg.toFixed(1) : '-',
                unit_energy: (APP.lastResult && APP.lastResult.unit_energy) ? APP.lastResult.unit_energy.toFixed(3) : '-'
            };
            
            // 构造数据
            var data = {
                type: format,
                filename: filename,
                file_base64: base64Data,
                project_info: projectInfo
            };
            
            // 通过URL参数传递给Streamlit
            var encoded = encodeURIComponent(JSON.stringify(data));
            var url = new URL(window.location.href);
            url.searchParams.set('f', encoded);
            window.location.href = url.toString();
            
        } catch(e) {
            console.error('Export error:', e);
        }
    };
})();
</script>
"""

html_content += inject_script

st.components.v1.html(html_content, height=12000, scrolling=True)

st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;'>
    💧 三菱化学 MBR 膜设计工具 | 邮件发送至 jeziyou@qq.com
    </div>
    """,
    unsafe_allow_html=True
)
