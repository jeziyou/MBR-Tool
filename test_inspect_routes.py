"""检查 Streamlit 实际路由结构"""
import streamlit as st
import gc

st.set_page_config(layout="wide")
st.title("🔍 Streamlit 路由结构分析")

# 搜索所有 Starlette 应用和相关对象
from starlette.applications import Starlette
from starlette.routing import Route, Mount

apps = [obj for obj in gc.get_objects() if isinstance(obj, Starlette)]
st.write(f"找到 {len(apps)} 个 Starlette 应用")

for i, app in enumerate(apps):
    st.subheader(f"应用 #{i+1}: {type(app).__name__}")
    st.write(f"路由数量: {len(app.routes)}")
    st.write(f"路由类型分布:")
    route_types = {}
    for r in app.routes:
        t = type(r).__name__
        route_types[t] = route_types.get(t, 0) + 1
    st.json(route_types)

    # 打印所有路由路径
    st.write("所有路由路径（前50个）:")
    paths = []
    for idx, r in enumerate(app.routes):
        path = getattr(r, 'path', getattr(r, 'path_regex', 'N/A'))
        if hasattr(r, 'routes'):
            # Mount 对象
            sub_routes = getattr(r, 'routes', [])
            paths.append(f"{idx}: [Mount] {path} ({len(sub_routes)} sub-routes)")
        else:
            methods = getattr(r, 'methods', 'N/A')
            paths.append(f"{idx}: [Route] {path} methods={methods}")
    st.code("\n".join(paths[:50]))

    # 检查是否有通配符路由
    for r in app.routes:
        path = str(getattr(r, 'path', ''))
        if '{' in path or path == '' or path == '/':
            st.warning(f"可能的通配符路由: {path} (type={type(r).__name__})")

# 也搜索 Route 实例
routes_found = [obj for obj in gc.get_objects() if isinstance(obj, Route)]
st.write(f"找到 {len(routes_found)} 个独立的 Route 对象")

mounts_found = [obj for obj in gc.get_objects() if isinstance(obj, Mount)]
st.write(f"找到 {len(mounts_found)} 个 Mount 对象")
for m in mounts_found[:5]:
    st.code(f"Mount path={getattr(m, 'path', 'N/A')}, routes={len(getattr(m, 'routes', []))}")
