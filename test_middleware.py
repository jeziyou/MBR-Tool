"""测试: 通过 Starlette Middleware 注册 API 路由"""
import streamlit as st
import gc
import json
import time

st.set_page_config(layout="wide")
st.title("⚡ Starlette Middleware 方案测试")

# ============================================================
# 方案: 向已启动的 Starlette 应用添加自定义中间件
# 中间件在路由匹配之前执行，所以不会被 Streamlit 默认路由覆盖
# ============================================================

from starlette.middleware.base import BaseHTTPMiddleware
from starlette.responses import JSONResponse, Response
import requests

# 定义邮件发送中间件
class EmailSendMiddleware(BaseHTTPMiddleware):
    async def dispatch(self, request, call_next):
        # 拦截 /api/send-email 请求
        if request.url.path == "/api/send-email" and request.method == "POST":
            try:
                body = await request.json()
                file_b64 = body.get("file_base64")
                filename = body.get("filename", "report.pdf")
                project_name = body.get("project_name", "MBR 计算书")

                if not file_b64:
                    return JSONResponse({"status": "error", "message": "缺少文件内容"}, status_code=400)

                # 调用 Resend API 发送邮件
                resp = requests.post(
                    "https://api.resend.com/emails",
                    headers={
                        "Authorization": "Bearer re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv",
                        "Content-Type": "application/json"
                    },
                    json={
                        "from": "MBR设计工具 <onboarding@resend.dev>",
                        "to": ["jeziyou@qq.com"],
                        "subject": f"{project_name} - 工艺计算书",
                        "html": f"<h2>{project_name}</h2><p>您好，这是由 MBR 设计工具自动生成的计算书。</p>",
                        "attachments": [{"filename": filename, "content": file_b64}]
                    },
                    timeout=30
                )

                if resp.status_code == 200:
                    return JSONResponse({
                        "status": "success",
                        "message": f"邮件已发送至 jeziyou@qq.com",
                        "filename": filename
                    })
                else:
                    return JSONResponse({
                        "status": "error",
                        "message": f"Resend API 失败 (HTTP {resp.status_code}): {resp.text[:200]}"
                    }, status_code=500)

            except Exception as e:
                return JSONResponse({"status": "error", "message": str(e)[:200]}, status_code=500)

        # 测试路由
        if request.url.path == "/api/test" and request.method in ["GET", "POST"]:
            if request.method == "POST":
                try:
                    body = await request.json()
                except:
                    body = {}
            else:
                body = {"note": "GET request received"}
            return JSONResponse({
                "status": "success",
                "message": "✅ Middleware 方案工作正常！",
                "data": body,
                "timestamp": time.strftime("%H:%M:%S")
            })

        # 其他请求继续走 Streamlit 正常流程
        response = await call_next(request)
        return response


# ============================================================
# 查找 Starlette 应用并添加中间件
# ============================================================

from starlette.applications import Starlette

middleware_added = False

# 搜索所有 Starlette 应用实例
apps = [obj for obj in gc.get_objects() if isinstance(obj, Starlette)]

if apps:
    st.write(f"找到 {len(apps)} 个 Starlette 应用")

    for i, app in enumerate(apps):
        # 添加中间件 - 需要插入到中间件列表的开头
        try:
            # Starlette 的 middleware 存储在 app.user_middleware
            # 但一旦应用启动，可能需要特殊处理
            if hasattr(app, 'user_middleware'):
                # 检查是否已经添加过
                already_added = any(
                    m.__class__.__name__ == "EmailSendMiddleware"
                    for m in app.user_middleware
                )
                if not already_added:
                    # 插入到列表开头（先执行）
                    app.user_middleware.insert(0, EmailSendMiddleware)
                    # 重建 middleware 栈
                    if hasattr(app, 'middleware_stack'):
                        try:
                            app.middleware_stack = app.build_middleware_stack()
                            middleware_added = True
                            st.success(f"✅ 已向应用 #{i+1} 添加邮件中间件并重建栈")
                        except Exception as e:
                            st.warning(f"重建中间件栈失败: {e} - 尝试其他方法")
                    else:
                        st.success(f"✅ 已向应用 #{i+1} 添加中间件到 user_middleware")
                        middleware_added = True
                else:
                    st.info(f"应用 #{i+1} 已有中间件")
            else:
                st.warning(f"应用 #{i+1} 没有 user_middleware 属性")
        except Exception as e:
            st.error(f"向应用 #{i+1} 添加中间件失败: {e}")

    # 备用方案: 如果 user_middleware 方式不工作，
    # 直接替换 app.middleware_stack
    if not middleware_added:
        st.warning("方法1失败，尝试直接替换 middleware_stack...")
        for app in apps:
            try:
                original_stack = app.middleware_stack
                async def new_stack(scope, receive, send):
                    if scope.get("type") == "http":
                        path = scope.get("path", "")
                        if path == "/api/send-email" or path == "/api/test":
                            # 创建一个简单的请求处理程序
                            from starlette.requests import Request
                            req = Request(scope, receive)
                            if path == "/api/test":
                                body = {}
                                if req.method == "POST":
                                    try:
                                        body = await req.json()
                                    except:
                                        pass
                                resp = JSONResponse({
                                    "status": "success",
                                    "message": "✅ 中间件栈替换方案工作正常！",
                                    "data": body
                                })
                                await resp(scope, receive, send)
                                return
                            if path == "/api/send-email":
                                body = await req.json()
                                # 简化的邮件发送
                                import requests as http_req
                                resp = http_req.post(
                                    "https://api.resend.com/emails",
                                    headers={
                                        "Authorization": "Bearer re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv",
                                        "Content-Type": "application/json"
                                    },
                                    json={
                                        "from": "MBR设计工具 <onboarding@resend.dev>",
                                        "to": ["jeziyou@qq.com"],
                                        "subject": body.get("project_name", "计算书"),
                                        "html": f"<h2>{body.get('project_name', 'MBR')}</h2>",
                                        "attachments": [{
                                            "filename": body.get("filename", "report.pdf"),
                                            "content": body.get("file_base64", "")
                                        }]
                                    },
                                    timeout=30
                                )
                                if resp.status_code == 200:
                                    r = JSONResponse({"status": "success", "message": "邮件已发送"})
                                else:
                                    r = JSONResponse({"status": "error", "message": f"HTTP {resp.status_code}"}, status_code=500)
                                await r(scope, receive, send)
                                return
                    await original_stack(scope, receive, send)
                app.middleware_stack = new_stack
                middleware_added = True
                st.success("✅ 已成功替换 middleware_stack")
            except Exception as e:
                st.error(f"替换 middleware_stack 失败: {e}")

else:
    st.warning("⚠️ 未找到 Starlette 应用实例")

# ============================================================
# HTML 测试
# ============================================================
st.markdown("---")
st.subheader("📡 测试中间件路由")

test_html = f"""
<div style="padding:20px;background:#f0f4f8;border-radius:12px;">
    <p style="color:#64748b;">中间件状态: {'<span style="color:#059669;font-weight:bold;">✅ 已添加</span>' if middleware_added else '<span style="color:#dc2626;font-weight:bold;">❌ 未添加</span>'}</p>
    <button onclick="testRoute('/api/test', 'GET', null)"
            style="padding:10px 20px;background:#1d4ed8;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        1️⃣ GET /api/test
    </button>
    <button onclick="testRoute('/api/test', 'POST', {{hello: 'world'}})"
            style="padding:10px 20px;background:#7c3aed;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        2️⃣ POST /api/test
    </button>
    <button onclick="sendTestEmail()"
            style="padding:10px 20px;background:#059669;color:white;border:none;
                   border-radius:8px;cursor:pointer;margin:5px;font-weight:600;">
        3️⃣ POST /api/send-email (测试邮件)
    </button>
    <div id="results" style="margin-top:15px;padding:12px;background:white;
         border-radius:8px;font-size:13px;font-family:monospace;white-space:pre-wrap;">
        点击按钮测试中间件路由...
    </div>
</div>

<script>
async function testRoute(path, method, body) {{
    const el = document.getElementById('results');
    el.innerHTML = '⏳ 发送 ' + method + ' ' + path + '...';
    try {{
        const options = {{ method: method, headers: {{'Content-Type': 'application/json'}} }};
        if (body) options.body = JSON.stringify(body);
        const resp = await fetch(path, options);
        const text = await resp.text();
        let formatted;
        try {{ formatted = JSON.stringify(JSON.parse(text), null, 2); }}
        catch(e) {{ formatted = text; }}
        el.innerHTML = '<b>HTTP ' + resp.status + '</b>\\n' + formatted.slice(0, 800);
    }} catch(e) {{
        el.innerHTML = '<b style="color:red;">❌ 失败</b>\\n' + e.message;
    }}
}}

async function sendTestEmail() {{
    const el = document.getElementById('results');
    el.innerHTML = '⏳ 正在准备测试邮件数据...';
    // 创建一个简单的 base64 文件
    const content = 'This is a test email from Streamlit MBR Tool\\n'
        + 'Time: ' + new Date().toISOString();
    // 将文本转换为 base64
    const base64 = btoa(unescape(encodeURIComponent(content)));

    el.innerHTML = '⏳ 正在发送邮件请求到 /api/send-email...';
    try {{
        const resp = await fetch('/api/send-email', {{
            method: 'POST',
            headers: {{'Content-Type': 'application/json'}},
            body: JSON.stringify({{
                filename: 'test_email_' + Date.now() + '.txt',
                file_base64: base64,
                project_name: 'Streamlit 测试邮件 - ' + new Date().toLocaleString()
            }})
        }});
        const data = await resp.json();
        el.innerHTML = '<b>HTTP ' + resp.status + '</b>\\n'
            + '<pre>' + JSON.stringify(data, null, 2) + '</pre>';
    }} catch(e) {{
        el.innerHTML = '<b style="color:red;">❌ 发送失败</b>\\n' + e.message;
    }}
}}
</script>
"""

st.components.v1.html(test_html, height=450, scrolling=True)

st.markdown("---")
st.info("💡 **测试逻辑**: 如果 POST /api/test 返回 JSON 响应（非 HTML），说明中间件方案工作正常，可以用于邮件发送！")
