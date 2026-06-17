"""验证: components.html 中 Streamlit.setComponentValue 是否工作"""
import streamlit as st
import time

st.set_page_config(layout="wide")

st.title("🔑 Streamlit.setComponentValue 通信测试")

if "counter" not in st.session_state:
    st.session_state.counter = 0

# HTML 中通过 Streamlit.setComponentValue 发送值
html_code = """
<div style="padding:20px;background:#f0f4f8;border-radius:12px;">
    <h3>HTML 端</h3>
    <p>点击按钮测试 Streamlit.setComponentValue() 是否能将值传回 Python</p>

    <button id="btn1" style="padding:10px 20px;background:#1d4ed8;color:white;
            border:none;border-radius:8px;cursor:pointer;margin:5px;">
        发送字符串 "hello-python"
    </button>

    <button id="btn2" style="padding:10px 20px;background:#059669;color:white;
            border:none;border-radius:8px;cursor:pointer;margin:5px;">
        发送 JSON 对象
    </button>

    <button id="btn3" style="padding:10px 20px;background:#f59e0b;color:white;
            border:none;border-radius:8px;cursor:pointer;margin:5px;">
        发送大 base64 数据 (50KB)
    </button>

    <div id="status" style="margin-top:15px;padding:12px;background:white;
         border-radius:8px;font-size:13px;font-family:monospace;">
        Streamlit 对象: <span id="stStatus">检测中...</span>
    </div>

    <div id="lastValue" style="margin-top:10px;padding:10px;background:#e0f2fe;
         border-radius:8px;font-size:12px;font-family:monospace;
         white-space:pre-wrap;word-break:break-all;">
        上次发送的值: <b>无</b>
    </div>
</div>

<script>
// 检测 Streamlit 对象
if (window.Streamlit) {
    document.getElementById('stStatus').innerHTML =
        '<span style="color:#059669;font-weight:bold;">✅ 可用</span>';
} else {
    setTimeout(function() {
        if (window.Streamlit) {
            document.getElementById('stStatus').innerHTML =
                '<span style="color:#059669;font-weight:bold;">✅ 可用 (延迟检测)</span>';
        } else {
            document.getElementById('stStatus').innerHTML =
                '<span style="color:#dc2626;font-weight:bold;">❌ 不可用</span>';
        }
    }, 2000);
}

// 设置组件初始高度
if (window.Streamlit && Streamlit.setFrameHeight) {
    Streamlit.setFrameHeight(350);
}

document.getElementById('btn1').addEventListener('click', function() {
    var value = 'hello-python-' + Date.now();
    document.getElementById('lastValue').innerHTML =
        '上次发送的值: <b>' + value + '</b>';
    if (window.Streamlit) {
        Streamlit.setComponentValue(value);
    }
});

document.getElementById('btn2').addEventListener('click', function() {
    var value = {
        type: 'email_request',
        filename: 'test_' + Date.now() + '.pdf',
        file_base64: btoa('test content'),
        project_name: '测试项目',
        timestamp: Date.now()
    };
    document.getElementById('lastValue').innerHTML =
        '上次发送的值: <b>' + JSON.stringify(value) + '</b>';
    if (window.Streamlit) {
        Streamlit.setComponentValue(value);
    }
});

document.getElementById('btn3').addEventListener('click', function() {
    // 生成约 50KB 的 base64 数据
    var content = '';
    for (var i = 0; i < 500; i++) {
        content += 'This is test data for email sending. ';
    }
    // 转 base64
    var base64 = btoa(unescape(encodeURIComponent(content)));
    var value = {
        type: 'large_data_test',
        size_kb: Math.round(base64.length / 1024),
        filename: 'large_test.pdf',
        file_base64: base64
    };
    document.getElementById('lastValue').innerHTML =
        '上次发送的值: <b>大数据包 (' + value.size_kb + ' KB)</b>';
    if (window.Streamlit) {
        Streamlit.setComponentValue(value);
    }
});
</script>
"""

# 关键: 使用 components.html 渲染，
# 并将返回值保存到变量
component_value = st.components.v1.html(html_code, height=350, scrolling=True)

# ============================================================
# Python 端: 显示从 HTML 传回的值
# ============================================================
st.markdown("---")
st.subheader("📥 Python 端接收到的值")

if component_value:
    st.success(f"✅ 收到值! 类型: {type(component_value).__name__}")
    st.write("值内容:")
    st.json(component_value)

    # 如果是邮件请求，发送邮件
    if isinstance(component_value, dict) and component_value.get("type") == "email_request":
        st.session_state.counter += 1
        st.info(f"📧 检测到邮件请求 #{st.session_state.counter}! "
                f"文件: {component_value.get('filename')}")

        # 实际发送邮件
        import requests
        with st.spinner("正在通过 Resend API 发送邮件..."):
            try:
                resp = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": "Bearer re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "MBR设计工具 <onboarding@resend.dev>",
                        "to": ["jeziyou@qq.com"],
                        "subject": f"Streamlit 测试邮件 #{st.session_state.counter}",
                        "html": f"<h2>Streamlit HTML 通信测试</h2><p>这是通过 HTML→Python 传值后由后端发送的邮件。</p>",
                        "attachments": [{
                            "filename": component_value.get("filename", "test.pdf"),
                            "content": component_value.get("file_base64", "")
                        }]
                    },
                    timeout=30
                )
                if resp.status_code == 200:
                    st.success(f"✅ 邮件 #{st.session_state.counter} 已发送至 jeziyou@qq.com!")
                else:
                    st.error(f"邮件发送失败: HTTP {resp.status_code} - {resp.text[:200]}")
            except Exception as e:
                st.error(f"邮件发送异常: {e}")
else:
    st.warning("⚠️ 尚未收到值 - 请点击上方 HTML 中的按钮测试")
    st.info("💡 如果点击按钮后这里始终没有显示值，说明 components.html 不支持双向通信")

st.markdown("---")
st.subheader("📊 统计")
st.write(f"已处理邮件请求次数: {st.session_state.counter}")
