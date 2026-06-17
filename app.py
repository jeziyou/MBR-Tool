"""
MBR 膜系统工艺设计工具 - Streamlit 主应用
- 保留原始 HTML 界面（通过 components.html 展示）
- 保留前端 PDF/Word 生成逻辑（html2canvas + jsPDF + docx.js）
- 邮件发送通过 Streamlit 后端自定义路由 /api/send-email 转发到 Resend API
"""
import streamlit as st
import os
import json
import requests
import threading
import time

# ============================================================================
# Page 配置
# ============================================================================
st.set_page_config(
    page_title="MBR 膜设计工具 - 工艺计算书",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 后端路由：/api/send-email（在 Streamlit 启动时注册 Tornado 路由）
# ============================================================================
def _setup_tornado_route():
    """向 Streamlit 的底层 Tornado 服务器注册 /api/send-email 路由"""
    try:
        from tornado.web import RequestHandler

        class SendEmailHandler(RequestHandler):
            def set_default_headers(self):
                self.set_header("Access-Control-Allow-Origin", "*")
                self.set_header("Access-Control-Allow-Headers", "Content-Type")
                self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

            def options(self):
                self.set_status(204)
                self.finish()

            def post(self):
                try:
                    data = json.loads(self.request.body)
                    file_base64 = data.get("file_base64")
                    filename = data.get("filename", "MBR计算书")
                    project_name = data.get("project_name", "MBR膜系统工艺计算书")
                    fmt = data.get("format", "pdf")

                    if not file_base64:
                        self.set_status(400)
                        self.write(json.dumps({
                            "status": "error",
                            "message": "缺少文件内容"
                        }))
                        return

                    RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
                    DEFAULT_RECIPIENT = "jeziyou@qq.com"

                    payload = {
                        "from": "MBR设计工具 <onboarding@resend.dev>",
                        "to": [DEFAULT_RECIPIENT],
                        "subject": f"{project_name} - 工艺计算书 ({fmt.upper()})",
                        "html": (
                            f"<h2>{project_name}</h2>"
                            f"<p>您好，</p>"
                            f"<p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书（{fmt.upper()}），请查收附件。</p>"
                            f"<hr><p style='color:#999;font-size:12px;'>此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>"
                        ),
                        "attachments": [{
                            "filename": filename,
                            "content": file_base64
                        }]
                    }

                    resp = requests.post(
                        "https://api.resend.com/emails",
                        json=payload,
                        headers={
                            "Authorization": f"Bearer {RESEND_API_KEY}",
                            "Content-Type": "application/json"
                        },
                        timeout=30
                    )

                    if resp.status_code == 200:
                        self.write(json.dumps({
                            "status": "success",
                            "message": f"邮件已发送至 {DEFAULT_RECIPIENT}"
                        }))
                    else:
                        self.set_status(500)
                        self.write(json.dumps({
                            "status": "error",
                            "message": f"邮件发送失败 (HTTP {resp.status_code})"
                        }))

                except Exception as e:
                    self.set_status(500)
                    self.write(json.dumps({
                        "status": "error",
                        "message": str(e)[:200]
                    }))

        # --- 向 Streamlit 的 Tornado Application 注册路由 ---
        try:
            # 方法1: 通过 streamlit.runtime 访问
            from streamlit.runtime import Runtime
            runtime = Runtime.instance()

            # 尝试找到 Tornado Application 对象
            tornado_app = None
            # 遍历 runtime 的属性
            for attr_name in ["_server", "_local_server", "server"]:
                server_obj = getattr(runtime, attr_name, None)
                if server_obj is not None:
                    # 查找 Tornado Application
                    for inner_attr in ["_app", "app", "_tornado_app"]:
                        app_obj = getattr(server_obj, inner_attr, None)
                        if app_obj is not None and hasattr(app_obj, "add_handlers"):
                            tornado_app = app_obj
                            break

            # 备用方法: 检查是否能通过 _get_or_create_server 获取
            if tornado_app is None:
                try:
                    from streamlit.web.server import Server
                    # 遍历运行时的对象树
                    obj_tree = [runtime]
                    visited = set()
                    while obj_tree and tornado_app is None:
                        obj = obj_tree.pop(0)
                        obj_id = id(obj)
                        if obj_id in visited:
                            continue
                        visited.add(obj_id)
                        try:
                            if hasattr(obj, "add_handlers") and hasattr(obj, "default_router"):
                                tornado_app = obj
                                break
                            # 继续遍历属性
                            for attr in dir(obj):
                                if attr.startswith('_') and not attr.startswith('__'):
                                    try:
                                        val = getattr(obj, attr, None)
                                        if val is not None and not isinstance(val, (str, int, float, bool, list, dict, tuple)):
                                            obj_tree.append(val)
                                    except:
                                        pass
                        except:
                            pass
                except Exception:
                    pass

            if tornado_app is not None:
                tornado_app.add_handlers(r".*", [
                    (r"/api/send-email", SendEmailHandler),
                ])
                return True
            else:
                return False

        except Exception:
            return False

    except Exception:
        return False


# 尝试用另一种方法: 直接访问 Tornado Application
def _setup_tornado_route_alt():
    """备用方法：通过 IOLoop 和全局对象查找 Tornado Application"""
    try:
        from tornado.web import RequestHandler

        class SendEmailHandler(RequestHandler):
            def set_default_headers(self):
                self.set_header("Access-Control-Allow-Origin", "*")
                self.set_header("Access-Control-Allow-Headers", "Content-Type")
                self.set_header("Access-Control-Allow-Methods", "POST, OPTIONS")

            def options(self):
                self.set_status(204)
                self.finish()

            def post(self):
                try:
                    data = json.loads(self.request.body)
                    file_base64 = data.get("file_base64")
                    filename = data.get("filename", "MBR计算书")
                    project_name = data.get("project_name", "MBR膜系统工艺计算书")
                    fmt = data.get("format", "pdf")

                    if not file_base64:
                        self.set_status(400)
                        self.write(json.dumps({"status": "error", "message": "缺少文件内容"}))
                        return

                    RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
                    DEFAULT_RECIPIENT = "jeziyou@qq.com"

                    payload = {
                        "from": "MBR设计工具 <onboarding@resend.dev>",
                        "to": [DEFAULT_RECIPIENT],
                        "subject": f"{project_name} - 工艺计算书 ({fmt.upper()})",
                        "html": (
                            f"<h2>{project_name}</h2><p>您好，</p>"
                            f"<p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书（{fmt.upper()}），请查收附件。</p>"
                            f"<hr><p style='color:#999;font-size:12px;'>此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>"
                        ),
                        "attachments": [{"filename": filename, "content": file_base64}]
                    }

                    resp = requests.post(
                        "https://api.resend.com/emails",
                        json=payload,
                        headers={"Authorization": f"Bearer {RESEND_API_KEY}", "Content-Type": "application/json"},
                        timeout=30
                    )

                    if resp.status_code == 200:
                        self.write(json.dumps({"status": "success", "message": f"邮件已发送至 {DEFAULT_RECIPIENT}"}))
                    else:
                        self.set_status(500)
                        self.write(json.dumps({"status": "error", "message": f"邮件发送失败 (HTTP {resp.status_code})"}))

                except Exception as e:
                    self.set_status(500)
                    self.write(json.dumps({"status": "error", "message": str(e)[:200]}))

        # 尝试从模块全局变量查找
        import sys
        for mod_name, mod in list(sys.modules.items()):
            if "streamlit" in mod_name:
                for attr_name in dir(mod):
                    try:
                        attr = getattr(mod, attr_name)
                        if hasattr(attr, "add_handlers") and hasattr(attr, "default_router"):
                            attr.add_handlers(r".*", [(r"/api/send-email", SendEmailHandler)])
                            return True
                    except:
                        pass

        return False
    except Exception:
        return False


@st.cache_resource(show_spinner=False)
def _initialize_backend():
    """初始化后端邮件发送路由（只执行一次）"""
    success = _setup_tornado_route()
    if not success:
        success = _setup_tornado_route_alt()
    return success


# ============================================================================
# 读取 HTML 内容
# ============================================================================
@st.cache_resource(show_spinner=False)
def _load_html():
    html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
    with open(html_path, "r", encoding="utf-8") as f:
        return f.read()


# ============================================================================
# 主界面
# ============================================================================

# 初始化后端路由
route_ready = _initialize_backend()

html_content = _load_html()

# 顶部提示栏（简洁，不干扰主界面）
col1, col2 = st.columns([3, 1])
with col1:
    if route_ready:
        st.success("✅ 邮件服务就绪 — 点击HTML中的「📄 导出计算书 PDF」或「📝 导出计算书 Word」按钮，"
                   "生成的计算书将同时后台发送至 jeziyou@qq.com")
    else:
        st.warning("⚠️ 邮件路由未就绪 — 仍可使用HTML界面生成和下载PDF/Word计算书")
with col2:
    st.markdown("**📄 PDF / 📝 Word** 按钮位于左侧面板底部")

st.markdown("---")

# 嵌入原始HTML界面（使用 components.html，保持完整交互）
st.components.v1.html(html_content, height=12000, scrolling=True)

# 底部说明
st.markdown("---")
st.markdown(
    """
    <div style='text-align:center;color:#64748b;font-size:12px;padding:1rem;'>
    💧 三菱化学 MBR 膜系统工艺设计工具 | 邮件自动发送至 jeziyou@qq.com | Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
