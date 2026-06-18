#!/bin/bash
# Azure Web App - Streamlit 启动脚本
# 在 Azure Portal 中配置: Configuration → General Settings → Startup Command
# 填写: startup.sh

python -m streamlit run app.py \
    --server.port 8000 \
    --server.address 0.0.0.0 \
    --server.headless true \
    --server.enableXsrfProtection false \
    --server.enableCORS true \
    --global.developmentMode false
