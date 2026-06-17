"""测试 Streamlit runtime 结构"""
import streamlit as st
import time

st.set_page_config(layout="wide")

# 尝试找到 Tornado Application
from streamlit.runtime import Runtime

try:
    runtime = Runtime.instance()
    st.write("Runtime:", type(runtime).__name__)
    st.write("Runtime 非私有属性:", [a for a in dir(runtime) if not a.startswith('__')])

    # 检查各个可能的属性
    for attr in ["_server", "_local_server", "server", "_proxy", "_session_mgr"]:
        obj = getattr(runtime, attr, None)
        if obj is not None:
            st.subheader(f"runtime.{attr}: {type(obj).__name__}")
            st.write("属性:", [a for a in dir(obj) if not a.startswith('__')])

            # 尝试深入查找 Tornado Application
            for inner in ["_app", "app", "_tornado_app", "_server", "server"]:
                inner_obj = getattr(obj, inner, None)
                if inner_obj is not None:
                    st.write(f"  → .{inner}: {type(inner_obj).__name__}")
                    if hasattr(inner_obj, "add_handlers"):
                        st.write("     ✅ 有 add_handlers 方法！")
                        st.write("     可以注册路由")

except Exception as e:
    st.error(f"错误: {e}")

st.markdown("---")
st.info("正在测试 Tornado 路由注册...")
