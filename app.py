"""
简化版：原始HTML界面 + Python直接发送邮件
- 保留原始HTML界面和交互
- 导出时自动调用Python Resend API发送邮件
- 使用页面刷新机制触发Python处理
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
# 邮件发送函数
# ============================================================================
def send_email(file_b64, filename, project_name, fmt):
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        payload = {
            "from": "MBR设计工具 <onboarding@resend.dev>",
            "to": ["jeziyou@qq.com"],
            "subject": f"{project_name} - 工艺计算书 ({fmt.upper()})",
            "html": (
                f"<h2>{project_name}</h2>"
                f"<p>您好，</p>"
                f"<p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书（{fmt.upper()}格式），请查收附件。</p>"
                f"<hr><p style='color:#999;font-size:12px;'>此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>"
            ),
            "attachments": [{"filename": filename, "content": file_b64}]
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
# 读取原始 HTML
# ============================================================================
@st.cache_resource
def _load_html():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# ============================================================================
# 处理 URL 中的邮件请求（通过页面刷新传递数据）
# ============================================================================
query_params = st.query_params
email_data = query_params.get("e", "")

if email_data:
    try:
        decoded_str = unescape(decodeURIComponent(atob(email_data)))
        data = json.loads(decoded_str)
        
        if data.get("type") == "email_request":
            success, result = send_email(
                data.get("file_base64", ""),
                data.get("filename", "MBR_计算书"),
                data.get("project_name", "MBR膜系统工艺计算书"),
                data.get("format", "pdf")
            )
            
            if success:
                st.success(f"✅ 邮件已发送至 jeziyou@qq.com ({data.get('filename', '')})")
            else:
                st.error(f"⚠️ 邮件发送失败: {result}")
            
            # 清理 URL 参数
            st.query_params.clear()
            
    except Exception as e:
        st.error(f"处理失败: {e}")
        st.query_params.clear()

# ============================================================================
# 注入通信脚本
# ============================================================================
html_content = _load_html()

# 在HTML末尾添加脚本
comm_script = """
<script>
// 拦截 sendReportByEmail，在下载后通过 URL 参数触发邮件发送
(function() {
    var _original = window.sendReportByEmail;
    window.sendReportByEmail = async function(format, existingBlob, existingFilename) {
        // 先执行原始函数
        if (_original) {
            await _original.call(this, format, existingBlob, existingFilename);
        }
        
        // 然后准备邮件数据
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
            
            window.showEmailStatus('正在准备发送邮件...');
            
            // 转换为 base64
            var base64Data = await new Promise(function(resolve, reject) {
                var reader = new FileReader();
                reader.onload = function(e) { resolve(e.target.result.split(',')[1]); };
                reader.onerror = reject;
                reader.readAsDataURL(blob);
            });
            
            var projectName = window.safeStr('projectName') || 'MBR膜系统工艺计算书';
            
            // 编码并通过 URL 参数传递到 Python
            var data = JSON.stringify({
                type: 'email_request',
                filename: filename,
                file_base64: base64Data,
                project_name: projectName,
                format: format
            });
            
            var encoded = btoa(unescape(encodeURIComponent(data)));
            window.showEmailStatus('正在刷新页面发送邮件...');
            
            // 通过 URL 参数刷新页面，让 Python 处理
            var url = new URL(window.location.href);
            url.searchParams.set('e', encoded);
            window.location.href = url.toString();
            
        } catch(e) {
            console.error('Email prep error:', e);
            window.showEmailStatus('邮件准备失败');
        }
    };
})();
</script>
"""

html_content += comm_script

# ============================================================================
# 显示界面
# ============================================================================
st.success("✅ 系统就绪 - 点击「导出计算书」将自动发送邮件至 jeziyou@qq.com")
st.markdown("---")
st.components.v1.html(html_content, height=12000, scrolling=True)
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;padding:1rem;'>
    💧 三菱化学 MBR 膜系统工艺设计工具 | 邮件自动发送至 jeziyou@qq.com
    </div>
    """,
    unsafe_allow_html=True
)
