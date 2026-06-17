"""测试 Streamlit components.html 与 Python 通信"""
import streamlit as st
import time

st.set_page_config(layout="wide")

# 初始化 session state
if "email_count" not in st.session_state:
    st.session_state.email_count = 0

if "last_email_request" not in st.session_state:
    st.session_state.last_email_request = None

# 测试 HTML - 包含 Streamlit.setComponentValue 调用
test_html = f"""
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>MBR 通信测试</title>
    <style>
        body {{ font-family: -apple-system, sans-serif; padding: 20px; background: #f0f4f8; }}
        .btn {{ padding: 10px 20px; margin: 5px; border: none; border-radius: 8px;
               cursor: pointer; font-size: 14px; font-weight: 600; }}
        .btn-primary {{ background: #1d4ed8; color: white; }}
        .btn-success {{ background: #059669; color: white; }}
        .box {{ background: white; padding: 15px; border-radius: 8px; margin: 10px 0;
                border: 1px solid #e2e8f0; }}
        #status {{ background: #f0fdf4; padding: 12px; border-radius: 8px;
                   border: 1px solid #86efac; font-size: 13px; margin-top: 15px; }}
    </style>
</head>
<body>
    <h2 style="color:#1d4ed8;">🧪 Streamlit HTML ↔ Python 通信测试</h2>
    <p style="color:#64748b;">当前 Streamlit session 已接收 <strong style="color:#1d4ed8;">{st.session_state.email_count}</strong> 次请求</p>

    <button class="btn btn-primary" onclick="sendTest()">
        1️⃣ 发送测试字符串
    </button>

    <button class="btn btn-success" onclick="sendEmailRequest()">
        2️⃣ 模拟邮件发送请求 (含 base64 文件)
    </button>

    <div id="status">等待操作 - 请先点击按钮测试通信...</div>

    <script>
        function setStatus(msg) {{
            document.getElementById('status').innerHTML = msg;
            console.log('前端:', msg);
        }}

        // 检查 Streamlit 对象
        function waitForStreamlit(cb) {{
            if (window.Streamlit) {{
                cb();
            }} else {{
                setStatus('⏳ 等待 Streamlit 对象...');
                setTimeout(() => waitForStreamlit(cb), 200);
            }}
        }}

        waitForStreamlit(() => {{
            Streamlit.setFrameHeight(500);
            setStatus('✅ Streamlit 对象已就绪，可通信');
        }});

        function sendTest() {{
            waitForStreamlit(() => {{
                Streamlit.setComponentValue({{
                    type: 'test',
                    message: 'Hello from HTML! ' + new Date().toLocaleTimeString(),
                    timestamp: Date.now()
                }});
                setStatus('✅ 已发送测试消息');
            }});
        }}

        function sendEmailRequest() {{
            waitForStreamlit(() => {{
                // 生成一个模拟的 base64 文件
                const content = 'MBR Process Report\\nProject: Test\\n'
                    + 'Date: ' + new Date().toISOString() + '\\n'
                    + 'Data repeated for size: '.repeat(200);
                const base64 = btoa(unescape(encodeURIComponent(content)));

                Streamlit.setComponentValue({{
                    type: 'email_request',
                    filename: 'MBR_Report_' + Date.now() + '.pdf',
                    file_base64: base64,
                    project_name: '测试项目 - ' + new Date().toLocaleString(),
                    format: 'pdf',
                    recipient: 'jeziyou@qq.com'
                }});
                setStatus('✅ 已发送邮件请求 (base64文件大小: '
                    + Math.round(base64.length / 1024) + ' KB)');
            }});
        }}
    </script>
</body>
</html>
"""

# 渲染 HTML 组件
result = st.components.v1.html(test_html, height=520, scrolling=True, key="mbr_comms")

# ==== Python 端：处理从 HTML 发来的请求 ====
st.markdown("---")
st.subheader("📥 Python 端接收到的数据")

if result:
    st.json(result)

    # 处理邮件请求
    if isinstance(result, dict) and result.get("type") == "email_request":
        st.session_state.email_count += 1
        st.session_state.last_email_request = {
            "filename": result.get("filename"),
            "project_name": result.get("project_name"),
            "file_size_kb": round(len(result.get("file_base64", "")) / 1024, 1),
            "received_at": time.strftime("%H:%M:%S")
        }

        # ✅ 这里可以发送邮件
        st.success(f"✅ 已接收第 {st.session_state.email_count} 次邮件请求！")
        st.write(f"文件名: {result.get('filename')}")
        st.write(f"项目名: {result.get('project_name')}")
        st.write(f"Base64 大小: {round(len(result.get('file_base64', ''))/1024, 1)} KB")

        # 模拟发送邮件（实际使用时用 requests 调用 Resend API）
        import requests
        import base64
        try:
            with st.spinner("正在发送邮件至 jeziyou@qq.com..."):
                resp = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": "Bearer re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "MBR设计工具 <onboarding@resend.dev>",
                        "to": ["jeziyou@qq.com"],
                        "subject": result.get("project_name", "MBR 计算书"),
                        "html": f"<h2>{result.get('project_name', 'MBR')}</h2><p>这是由 Streamlit 后端自动发送的邮件。</p>",
                        "attachments": [{
                            "filename": result.get("filename", "report.pdf"),
                            "content": result.get("file_base64", "")
                        }]
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    st.success("📧 邮件已成功发送至 jeziyou@qq.com！")
                else:
                    st.error(f"邮件发送失败 (HTTP {resp.status_code}): {resp.text[:200]}")
        except Exception as e:
            st.error(f"邮件发送异常: {e}")
else:
    st.info("尚未收到前端数据 — 点击上方 HTML 中的按钮测试")
    st.caption("💡 如果始终收不到数据，说明 components.html 的 Streamlit.setComponentValue 在当前版本不可用")

# 显示历史
if st.session_state.last_email_request:
    st.markdown("### 📊 最后一次邮件请求")
    st.write(st.session_state.last_email_request)

st.markdown("---")
st.subheader("🔍 测试结论")
st.markdown("""
- **如果点击按钮后下方显示数据**：说明 Streamlit.setComponentValue 通信正常，可以用于 MBR 工具
- **如果始终没有数据显示**：说明 components.html 不支持双向通信，需要采用其他方案（如直接调用 Resend API）
""")
