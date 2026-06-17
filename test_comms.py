"""测试 st.components.v1.html 中的 Streamlit JS 对象"""
import streamlit as st

st.set_page_config(layout="wide")

# 测试 HTML 中是否可以通过 Streamlit 对象与 Python 通信
test_html = """
<!DOCTYPE html>
<html>
<head>
    <meta charset="UTF-8">
    <title>测试</title>
    <script src="https://cdn.tailwindcss.com"></script>
</head>
<body class="p-6">
    <h1 class="text-2xl font-bold text-blue-600 mb-4">🧪 Streamlit 组件通信测试</h1>
    <p class="mb-4 text-gray-600">点击下方按钮，尝试通过 Streamlit.setComponentValue() 与 Python 通信</p>

    <div class="space-y-3">
        <button id="btn1" class="bg-blue-500 hover:bg-blue-600 text-white px-4 py-2 rounded">
            发送字符串
        </button>
        <button id="btn2" class="bg-green-500 hover:bg-green-600 text-white px-4 py-2 rounded">
            发送 JSON 对象
        </button>
        <button id="btn3" class="bg-purple-500 hover:bg-purple-600 text-white px-4 py-2 rounded">
            发送大文件 (base64)
        </button>
    </div>

    <div id="status" class="mt-4 p-3 bg-gray-100 rounded text-sm text-gray-700">
        等待操作...
    </div>

    <script>
        const statusEl = document.getElementById('status');
        const setStatus = (msg) => { statusEl.textContent = msg; console.log(msg); };

        // 检查 Streamlit 对象是否可用
        if (window.Streamlit) {
            setStatus('✅ Streamlit 对象可用');
            // 设置组件初始高度
            Streamlit.setFrameHeight(400);
        } else {
            setStatus('⚠️ Streamlit 对象不可用，等待 1 秒再检查...');
            setTimeout(() => {
                if (window.Streamlit) {
                    setStatus('✅ Streamlit 对象已就绪');
                    Streamlit.setFrameHeight(400);
                } else {
                    setStatus('❌ Streamlit 对象仍然不可用');
                }
            }, 1000);
        }

        document.getElementById('btn1').addEventListener('click', () => {
            if (window.Streamlit) {
                Streamlit.setComponentValue({ action: 'test', message: '来自前端的问候！' });
                setStatus('✅ 已发送字符串');
            } else {
                setStatus('❌ 无法发送 - Streamlit 对象不可用');
            }
        });

        document.getElementById('btn2').addEventListener('click', () => {
            if (window.Streamlit) {
                Streamlit.setComponentValue({
                    action: 'email',
                    filename: 'test.pdf',
                    project_name: '测试项目',
                    format: 'pdf',
                    timestamp: Date.now()
                });
                setStatus('✅ 已发送 JSON 对象');
            } else {
                setStatus('❌ 无法发送');
            }
        });

        document.getElementById('btn3').addEventListener('click', () => {
            if (window.Streamlit) {
                // 生成一个简单的 base64 "文件"
                const base64Data = btoa('This is a test file content for email sending test. '
                    + 'Repeated to simulate larger size: '.repeat(50));
                Streamlit.setComponentValue({
                    action: 'email',
                    filename: 'test_document.pdf',
                    file_base64: base64Data,
                    project_name: '测试文档',
                    format: 'pdf'
                });
                setStatus('✅ 已发送 base64 文件 (大小: ' + Math.round(base64Data.length/1024) + ' KB)');
            } else {
                setStatus('❌ 无法发送');
            }
        });
    </script>
</body>
</html>
"""

result = st.components.v1.html(test_html, height=450, scrolling=True, key="comms_test")

st.markdown("---")
st.subheader("📥 Python 端接收到的数据")

if result:
    st.write("类型:", type(result))
    st.json(result)
else:
    st.info("尚未收到数据 — 点击上方 HTML 中的按钮测试通信")
    st.caption("如果始终收不到数据，说明 Streamlit components.html 不支持与 Python 通信")

# 检查是否有 email 请求
if result and result.get("action") == "email":
    st.success("📧 收到邮件发送请求！")
    st.write(f"文件名: {result.get('filename')}")
    st.write(f"项目名: {result.get('project_name')}")
    st.write(f"文件大小: {len(result.get('file_base64', ''))} 字符")
