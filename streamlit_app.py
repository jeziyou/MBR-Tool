import streamlit as st
import os

st.set_page_config(
    page_title="三菱化学MBR膜设计工具",
    page_icon="🧪",
    layout="wide",
)

# 读取HTML文件
html_path = os.path.join(os.path.dirname(__file__), "MBR_Tool.html")
with open(html_path, "r", encoding="utf-8") as f:
    html_content = f.read()

# 嵌入HTML
st.components.v1.html(html_content, height=10000, scrolling=True)