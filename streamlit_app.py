import streamlit as st
import os

st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    layout="wide",
    initial_sidebar_state="collapsed",
)

# 读取 HTML 文件
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# 全屏内嵌渲染
st.components.v1.html(html_content, height=1080, scrolling=True)