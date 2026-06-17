"""测试：向 Streamlit 的 Starlette 应用动态注册路由"""
import streamlit as st
import time
import json

st.set_page_config(layout="wide")

st.title("🧪 Starlette 路由注册测试")

# ============================================================
# 方法1: Monkey patch create_streamlit_routes
# ============================================================
st.subheader("方法1: Monkey patching")

try:
    from streamlit.web.server.starlette import starlette_app as sa

    original_func = sa.create_streamlit_routes

    def patched_create_routes(runtime):
        from starlette.routing import Route
        from starlette.responses import JSONResponse

        routes = original_func(runtime)

        async def custom_endpoint(request):
            try:
                body = await request.json()
            except:
                body = {}
            return JSONResponse({
                "status": "success",
                "message": "✅ 自定义路由工作正常！",
                "received_data": str(body)[:200],
                "timestamp": time.strftime("%H:%M:%S")
            })

        routes.append(Route('/api/test-route', custom_endpoint, methods=['POST', 'GET']))
        return routes

    sa.create_streamlit_routes = patched_create_routes
    st.success("✅ Monkey patch 已应用（注意：如果服务器已启动，路由可能已创建，需要重启）")

except Exception as e:
    st.error(f"方法1失败: {e}")

# ============================================================
# 方法2: 运行时查找 Starlette 应用并添加路由
# ============================================================
st.subheader("方法2: 运行时查找并添加路由")

try:
    from streamlit.runtime import Runtime
    runtime = Runtime.instance()
    st.write(f"Runtime: {type(runtime).__name__}")

    # 查找 Starlette 应用
    starlette_app = None
    search_paths = [
        ("_server",),
        ("_server", "_app"),
        ("_server", "_starlette_app"),
    ]

    for path in search_paths:
        obj = runtime
        for attr in path:
            obj = getattr(obj, attr, None)
            if obj is None:
                break
        if obj is not None and hasattr(obj, "routes"):
            starlette_app = obj
            st.success(f"✅ 通过路径 {'->'.join(path)} 找到 Starlette app！")
            st.write(f"   类型: {type(obj).__name__}")
            st.write(f"   当前路由数: {len(obj.routes)}")
            break

    if starlette_app is None:
        # 更广泛地搜索
        st.info("深度搜索 runtime 属性...")
        for attr in dir(runtime):
            if not attr.startswith('_') or attr in ['_server']:
                val = getattr(runtime, attr, None)
                if val is not None and hasattr(val, "routes"):
                    starlette_app = val
                    st.success(f"✅ 通过 .{attr} 找到 Starlette app！")
                    break

    if starlette_app is not None:
        # 添加路由
        from starlette.routing import Route
        from starlette.responses import JSONResponse

        async def test_email_endpoint(request):
            try:
                body = await request.json()
            except:
                body = {}
            return JSONResponse({
                "status": "success",
                "message": "邮件路由工作正常！",
                "data": str(body)[:200]
            })

        starlette_app.routes.append(
            Route('/api/send-email', test_email_endpoint, methods=['POST'])
        )
        st.success(f"✅ 已添加 /api/send-email 路由！总路由数: {len(starlette_app.routes)}")
    else:
        st.warning("⚠️ 未能找到 Starlette 应用 - 尝试其他方法")

except Exception as e:
    st.warning(f"方法2异常: {e}")

# ============================================================
# 测试：HTML 中 fetch 路由
# ============================================================
st.markdown("---")
st.subheader("📡 HTML 端测试: fetch 到 /api/send-email")

test_html = """
<div style="padding:20px;background:#f0f4f8;border-radius:12px;">
    <button id="testBtn" style="padding:12px 24px;background:#1d4ed8;color:white;
            border:none;border-radius:8px;cursor:pointer;font-size:14px;font-weight:600;">
        🔍 测试 /api/send-email 路由
    </button>
    <div id="result" style="margin-top:15px;padding:12px;background:white;
         border-radius:8px;font-size:13px;font-family:monospace;">
        点击按钮测试...
    </div>
</div>

<script>
document.getElementById('testBtn').addEventListener('click', async () => {
    const resultEl = document.getElementById('result');
    resultEl.innerHTML = '⏳ 正在发送请求...';
    try {
        const resp = await fetch('/api/send-email', {
            method: 'POST',
            headers: {'Content-Type': 'application/json'},
            body: JSON.stringify({test: 'hello', value: 123})
        });
        const data = await resp.json();
        resultEl.innerHTML =
            '<div style="color:#059669;"><b>✅ 成功 (HTTP ' + resp.status + ')</b><br><pre>'
            + JSON.stringify(data, null, 2) + '</pre></div>';
    } catch(e) {
        resultEl.innerHTML = '<div style="color:#dc2626;"><b>❌ 失败</b><br>' + e.message + '</div>';
    }
});
</script>
"""

st.components.v1.html(test_html, height=350, scrolling=True)

st.markdown("---")
st.caption("💡 如果 HTML 测试显示成功，说明路由注册方案可用")
