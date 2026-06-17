"""
方案E：隐藏输入框通信桥（最可靠）
- HTML 通过 JS 操作隐藏输入框传递数据
- Streamlit 监听输入变化触发邮件发送
- 完全保留原始 HTML 界面和交互
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
    """发送邮件（Python 后端直接调用）"""
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        payload = {
            "from": "MBR设计工具 <onboarding@resend.dev>",
            "to": ["jeziyou@qq.com"],
            "subject": f"{project_name} - 工艺计算书 ({fmt.upper()})",
            "html": f"<h2>{project_name}</h2><p>这是由 MBR 设计工具自动生成的计算书，请查收附件。</p>",
            "attachments": [{"filename": filename, "content": file_b64}]
        }
        resp = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
            timeout=30
        )
        return resp.status_code == 200, "邮件已发送" if resp.status_code == 200 else f"HTTP {resp.status_code}"
    except Exception as e:
        return False, str(e)

# ============================================================================
# 读取原始 HTML 并注入通信脚本
# ============================================================================
@st.cache_resource
def _load_html():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()

# 注入通信脚本到 HTML
def _inject_communication_script(html_content):
    """在 HTML 末尾注入与 Streamlit 通信的 JavaScript"""
    script = """
<script>
// Streamlit 通信桥 - 通过隐藏输入框传递数据
function sendToStreamlit(data) {
    // 查找 Streamlit 的文本输入框（通过特定 ID）
    var inputEl = window.parent.document.getElementById('email_data_input');
    if (inputEl) {
        // 将数据序列化为 JSON 并编码
        var jsonStr = JSON.stringify(data);
        // 使用 base64 编码避免特殊字符问题
        var encoded = btoa(unescape(encodeURIComponent(jsonStr)));
        // 设置输入框值并触发事件
        inputEl.value = encoded;
        inputEl.dispatchEvent(new Event('input'));
        inputEl.dispatchEvent(new Event('change'));
        console.log('数据已发送到 Streamlit');
        return true;
    } else {
        console.warn('未找到通信输入框');
        return false;
    }
}

// 修改 sendReportByEmail 使用新的通信方式
var originalSendReportByEmail = sendReportByEmail;
sendReportByEmail = async function(format, existingBlob, existingFilename) {
    if (_emailSending) return;
    if (!APP.lastResult || !APP.lastInput) {
        showEmailStatus('请先执行计算，再导出计算书');
        return;
    }

    _emailSending = true;
    showEmailStatus('正在生成文件...');

    try {
        var blob, filename;
        if (existingBlob) {
            blob = existingBlob;
            filename = existingFilename;
        } else {
            if (format === 'pdf') {
                blob = await exportCalcPDF({ returnBlob: true });
                filename = (safeStr('projectName') || 'MBR') + '_计算书.pdf';
            } else {
                blob = await exportCalcDOCX({ returnBlob: true });
                filename = (safeStr('projectName') || 'MBR') + '_计算书.docx';
            }
        }

        if (!blob) {
            showEmailStatus('文件生成失败');
            _emailSending = false;
            return;
        }

        // 触发浏览器下载
        var url = URL.createObjectURL(blob);
        var a = document.createElement('a');
        a.href = url;
        a.download = filename;
        document.body.appendChild(a);
        a.click();
        document.body.removeChild(a);
        URL.revokeObjectURL(url);

        showEmailStatus('正在后台发送邮件...');

        // 转换为 base64 并发送到 Streamlit
        var base64Data = await new Promise(function(resolve, reject) {
            var reader = new FileReader();
            reader.onload = function(e) { resolve(e.target.result.split(',')[1]); };
            reader.onerror = reject;
            reader.readAsDataURL(blob);
        });

        var projectName = safeStr('projectName') || 'MBR膜系统工艺计算书';

        // 通过通信桥发送数据
        var success = sendToStreamlit({
            type: 'email_request',
            filename: filename,
            file_base64: base64Data,
            project_name: projectName,
            format: format
        });

        if (success) {
            showEmailStatus('✅ 正在处理邮件发送...');
            showToast('文件已下载，邮件发送中...', 'success');
        } else {
            // 备用方案：直接调用 API
            showEmailStatus('⏳ 使用备用方式发送...');
            var response = await fetch('/api/send-email', {
                method: 'POST',
                headers: { 'Content-Type': 'application/json' },
                body: JSON.stringify({
                    filename: filename,
                    file_base64: base64Data,
                    project_name: projectName,
                    format: format
                })
            });
            if (response.ok) {
                showEmailStatus('✅ 邮件已发送至 jeziyou@qq.com');
                showToast('邮件已发送', 'success');
            } else {
                showEmailStatus('⚠️ 邮件发送失败');
                showToast('邮件发送失败', 'warning');
            }
        }

    } catch(e) {
        console.error('Email error:', e);
        showEmailStatus('发送失败: ' + (e.message || '未知错误'));
        showToast('邮件发送失败', 'warning');
    } finally {
        _emailSending = false;
    }
};
</script>
"""
    return html_content + script

html_content = _inject_communication_script(_load_html())

# ============================================================================
# 隐藏输入框作为通信桥
# ============================================================================
# 这个输入框是 HTML 和 Streamlit 之间的通信桥梁
email_data_input = st.text_input(
    "Email Data",
    key="email_data_input",
    label_visibility="hidden",
    disabled=False
)

# ============================================================================
# 处理从 HTML 传来的数据
# ============================================================================
if email_data_input and email_data_input != st.session_state.get("last_email_data"):
    try:
        # 解码数据
        decoded = json.loads(unescape(decodeURIComponent(atob(email_data_input))))
        
        if decoded.get("type") == "email_request":
            file_b64 = decoded.get("file_base64")
            filename = decoded.get("filename")
            project_name = decoded.get("project_name")
            fmt = decoded.get("format")

            # 发送邮件
            success, msg = send_email(file_b64, filename, project_name, fmt)
            
            if success:
                st.success(f"✅ 邮件已发送至 jeziyou@qq.com ({filename})")
            else:
                st.warning(f"⚠️ 邮件发送失败: {msg}")

            # 记录已处理
            st.session_state.last_email_data = email_data_input
            
    except Exception as e:
        st.error(f"数据解码失败: {e}")

# ============================================================================
# 显示原始 HTML 界面
# ============================================================================
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
