"""激进测试: 通过 gc 搜索 Starlette 应用"""
import streamlit as st
import gc
import time

st.set_page_config(layout="wide")

st.title("🔬 搜索 Starlette 应用实例")

# 方法1: 搜索所有 Starlette 应用实例
from starlette.applications import Starlette

found_apps = []
for obj in gc.get_objects():
    try:
        if isinstance(obj, Starlette):
            found_apps.append(obj)
    except:
        pass

if found_apps:
    st.success(f"✅ 找到 {len(found_apps)} 个 Starlette 应用实例！")

    # 尝试向第一个实例添加路由
    app = found_apps[0]
    st.write(f"类型: {type(app).__name__}")
    st.write(f"当前路由数: {len(app.routes)}")
    st.write(f"前5个路由:")
    for r in app.routes[:5]:
        st.code(f"  {type(r).__name__}: {getattr(r, 'path', 'N/A')}")

    # 添加测试路由
    from starlette.routing import Route
    from starlette.responses import JSONResponse

    async def test_email(request):
        try:
            body = await request.json()
        except:
            body = {}
        return JSONResponse({
            "status": "success",
            "message": "✅ 通过 gc 搜索添加的路由工作正常！",
            "data": str(body)[:200]
        })

    app.routes.append(Route('/api/send-email', test_email, methods=['POST']))
    st.success(f"✅ 已添加 /api/send-email 路由！当前路由数: {len(app.routes)}")

    # 添加更多测试路由
    async def test_route(request):
        return JSONResponse({"status": "success", "message": "测试路由也工作正常！"})
    app.routes.append(Route('/api/test', test_route, methods=['GET', 'POST']))
    st.success("✅ 已添加 /api/test 路由")

else:
    st.warning("⚠️ 未能找到 Starlette 应用实例")
    st.info("尝试其他搜索方式...")

    # 方法2: 搜索所有有 routes 属性的对象
    st.subheader("搜索所有有 routes 列表的对象")
    route_objects = []
    for obj in gc.get_objects():
        try:
            if hasattr(obj, 'routes') and isinstance(getattr(obj, 'routes', None), list):
                if len(getattr(obj, 'routes', [])) > 0:
                    route_objects.append(obj)
        except:
            pass
    st.write(f"找到 {len(route_objects)} 个有 routes 的对象")
    for obj in route_objects[:10]:
        st.code(f"  {type(obj).__name__}: routes={len(obj.routes)}")

# ============================================================
# HTML 测试
# ============================================================
st.markdown("---")
st.subheader("📡 测试路由")

test_html = """
<div style="padding:20px;background:#f0f4f8;border-radius:12px;">
    <h3>前端路由测试</h3>
    <button onclick="testRoute('/api/send-email', 'POST', {filename: 'test.pdf'})"
            style="padding:10px 20px;background:#059669;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        POST /api/send-email
    </button>
    <button onclick="testRoute('/api/test', 'POST', {hello: 'world'})"
            style="padding:10px 20px;background:#1d4ed8;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        POST /api/test
    </button>
    <button onclick="testRoute('/api/test', 'GET', null)"
            style="padding:10px 20px;background:#7c3aed;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        GET /api/test
    </button>
    <button onclick="testRoute('/api/nonexistent', 'GET', null)"
            style="padding:10px 20px;background:#64748b;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        GET /api/nonexistent (对照)
    </button>
    <div id="results" style="margin-top:15px;padding:12px;background:white;
         border-radius:8px;font-size:13px;font-family:monospace;white-space:pre-wrap;">
        点击上方按钮测试...
    </div>
</div>

<script>
async function testRoute(path, method, body) {
    const resultsEl = document.getElementById('results');
    resultsEl.textContent = '⏳ 发送 ' + method + ' ' + path + ' ...';
    try {
        const options = {
            method: method,
            headers: {'Content-Type': 'application/json'}
        };
        if (body) options.body = JSON.stringify(body);
        const resp = await fetch(path, options);
        const text = await resp.text();
        let formatted;
        try { formatted = JSON.stringify(JSON.parse(text), null, 2); }
        catch(e) { formatted = text; }
        resultsEl.innerHTML =
            '<b>HTTP ' + resp.status + '</b>\\n' + formatted.slice(0, 500);
    } catch(e) {
        resultsEl.innerHTML = '<b style="color:red;">❌ 失败</b>\\n' + e.message;
    }
}
</script>
"""

st.components.v1.html(test_html, height=400, scrolling=True)

st.markdown("---")
st.info("💡 如果上方测试按钮返回 JSON（status: success），说明通过 gc 搜索动态注册路由的方案可行！")
