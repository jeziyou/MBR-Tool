"""
MBR 膜系统工艺设计工具 - Streamlit 主应用（最终版）
- 使用 Streamlit 原生界面，保证邮件发送功能稳定可用
- PDF/Word 由 Python 生成（保持报告格式一致）
- 邮件通过 Python Resend API 后台发送到 jeziyou@qq.com
"""
import streamlit as st
import base64
import requests
from datetime import datetime

from mbr_calc import ProcessInput, compute_process, ALL_MODELS
from mbr_report import generate_pdf_report, generate_word_report

# ============================================================================
# Page 配置
# ============================================================================
st.set_page_config(
    page_title="三菱化学 MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# 自定义样式：尽量保持原始 HTML 的视觉风格
st.markdown(
    """
    <style>
    .block-container { padding-top: 1.5rem; padding-bottom: 2rem; }
    h1, h2, h3 { color: #1e40af; }
    .param-card {
        background: #ffffff;
        padding: 1rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 0.75rem;
    }
    .result-card {
        background: #ffffff;
        padding: 1.25rem;
        border-radius: 12px;
        border: 1px solid #e2e8f0;
        margin-bottom: 1rem;
    }
    .kpi-card {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        padding: 1rem;
        border-radius: 10px;
        text-align: center;
    }
    .kpi-card .label { font-size: 0.75rem; opacity: 0.85; }
    .kpi-card .value { font-size: 1.5rem; font-weight: 700; margin: 0.25rem 0; }
    .title-card {
        background: linear-gradient(135deg, #1e40af, #3b82f6);
        color: white;
        padding: 1.5rem;
        border-radius: 12px;
        text-align: center;
        margin-bottom: 1rem;
    }
    .title-card h1 { color: white; font-size: 1.5rem; margin: 0; }
    .title-card p { margin: 0.3rem 0 0; font-size: 0.85rem; opacity: 0.9; }
    [data-testid="stMetric"] {
        background: #f8fafc;
        padding: 1rem;
        border-radius: 10px;
        border: 1px solid #e2e8f0;
    }
    [data-testid="stMetricValue"] { color: #1e40af; font-weight: 700; font-size: 1.3rem; }
    [data-testid="stMetricLabel"] { color: #475569; font-size: 0.85rem; }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 邮件发送函数（Python 后端直接调用 Resend API）
# ============================================================================
def send_email_via_resend(file_bytes, filename, project_name, fmt):
    """
    通过 Resend API 发送邮件
    从不在浏览器 JavaScript 中调用，避免 CORS 问题
    """
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        SENDER = "MBR设计工具 <onboarding@resend.dev>"
        RECIPIENT = "jeziyou@qq.com"

        payload = {
            "from": SENDER,
            "to": [RECIPIENT],
            "subject": f"{project_name} - 工艺计算书 ({fmt.upper()})",
            "html": (
                f"<h2>{project_name}</h2>"
                f"<p>您好，</p>"
                f"<p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书（{fmt.upper()}），请查收附件。</p>"
                f"<hr><p style='color:#666;font-size:12px;'>"
                f"生成时间: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>"
                f"<p style='color:#999;font-size:12px;'>此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>"
            ),
            "attachments": [{
                "filename": filename,
                "content": base64.b64encode(file_bytes).decode("utf-8")
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
            return f"✅ 邮件已发送至 jeziyou@qq.com"
        else:
            return f"⚠️ 邮件发送失败 (HTTP {resp.status_code}): {resp.text[:100]}"
    except Exception as e:
        return f"⚠️ 邮件发送异常: {str(e)[:100]}"


# ============================================================================
# 初始化 session_state
# ============================================================================
if "current_result" not in st.session_state:
    st.session_state.current_result = None

if "current_input" not in st.session_state:
    st.session_state.current_input = None

if "project_name" not in st.session_state:
    st.session_state.project_name = "MBR膜系统工艺计算书"

if "email_status" not in st.session_state:
    st.session_state.email_status = None


# ============================================================================
# 主界面：两栏布局（左：参数输入，右：结果展示）
# ============================================================================

# 顶部标题栏
st.markdown(
    f"""
    <div class="title-card">
        <h1>💧 三菱化学 MBR 膜系统工艺设计工具</h1>
        <p>STERAPORE MBR Membrane Process Design Calculator</p>
    </div>
    """,
    unsafe_allow_html=True
)

# 邮件状态展示
if st.session_state.email_status:
    st.success(st.session_state.email_status)
    st.session_state.email_status = None  # 一次性展示

col_input, col_output = st.columns([1, 1.3])

# ==============================
# 左栏：参数输入
# ==============================
with col_input:
    st.markdown("### 📋 项目信息")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            st.session_state.project_name = st.text_input("项目名称", value=st.session_state.project_name)
        with c2:
            designer = st.text_input("设计人", value="工程师")
        design_date = st.date_input("设计日期", value=datetime.now().date())

    st.markdown("### 🌊 设计流量")
    with st.container():
        c1, c2 = st.columns(2)
        with c1:
            flow_rate = st.number_input("设计流量 (m³/d)", value=5000.0, min_value=1.0, step=100.0)
        with c2:
            peak_factor = st.number_input("变化系数 Kz", value=1.3, min_value=1.0, step=0.1)

    st.markdown("### 💧 进水水质")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            cod_in = st.number_input("COD (mg/L)", value=400.0, min_value=0.0)
            bod_in = st.number_input("BOD₅ (mg/L)", value=200.0, min_value=0.0)
            nh3n_in = st.number_input("NH₃-N (mg/L)", value=35.0, min_value=0.0)
        with c2:
            ss_in = st.number_input("SS (mg/L)", value=150.0, min_value=0.0)
            tn_in = st.number_input("TN (mg/L)", value=50.0, min_value=0.0)
            tp_in = st.number_input("TP (mg/L)", value=5.0, min_value=0.0)
        with c3:
            ph_value = st.number_input("pH", value=7.2, min_value=0.0, max_value=14.0, step=0.1)
            water_temp = st.number_input("水温 (℃)", value=20.0, min_value=0.0, max_value=50.0)
            mlss_in = st.number_input("MLSS (mg/L)", value=8000.0, min_value=0.0)

    st.markdown("### 🧪 膜组件配置")
    with st.container():
        # 膜型号选择
        model_names = [f"{m.name} ({m.sheet_area}m² - {m.mbr_type} {m.pore_size}μm)" for m in ALL_MODELS]
        model_idx = st.selectbox(
            "膜片型号",
            range(len(model_names)),
            format_func=lambda i: model_names[i],
            index=2
        )

        c1, c2, c3 = st.columns(3)
        with c1:
            sheets_per_rack = int(st.number_input("每台膜片数", value=42, min_value=1, step=1))
        with c2:
            num_pools = int(st.number_input("膜池数", value=2, min_value=1, step=1))
        with c3:
            racks_per_pool = int(st.number_input("每池台数", value=3, min_value=1, step=1))

    st.markdown("### ⚙️ 运行参数")
    with st.container():
        c1, c2, c3 = st.columns(3)
        with c1:
            j25 = st.number_input("J25 基准通量", value=18.0, min_value=5.0, max_value=40.0, step=0.5)
            fouling_factor = st.number_input("污染系数", value=0.85, min_value=0.5, max_value=1.0, step=0.05)
            sad_value = st.number_input("SAD 曝气密度", value=150.0, min_value=100.0, max_value=300.0, step=5.0)
        with c2:
            suction_on = st.number_input("抽吸-开 (min)", value=7.0, min_value=1.0, max_value=10.0, step=0.5)
            suction_off = st.number_input("抽吸-停 (min)", value=1.0, min_value=0.5, max_value=10.0, step=0.5)
            pool_level = st.number_input("池内液位 (m)", value=3.5, min_value=0.5, step=0.5)
        with c3:
            pipe_loss = st.number_input("管路损失 (m)", value=0.5, min_value=0.0, step=0.2)
            pump_head = st.number_input("产水泵扬程 (m)", value=6.5, min_value=0.0, step=0.5)
            pump_eff = st.number_input("产水泵效率 (%)", value=75, min_value=30, max_value=95, step=1) / 100.0

        c4, c5 = st.columns(2)
        with c4:
            return_ratio = st.number_input("回流比", value=3.0, min_value=0.0, step=0.5)
            return_head = st.number_input("回流泵扬程 (m)", value=0.5, min_value=0.0, step=0.1)
            return_eff = st.number_input("回流泵效率 (%)", value=70, min_value=30, max_value=95, step=1) / 100.0
        with c5:
            fan_eff = st.number_input("风机效率 (%)", value=90, min_value=45, max_value=98, step=1) / 100.0

    # 构建输入对象
    input_data = ProcessInput(
        Q=flow_rate, Kz=peak_factor,
        cod_in=cod_in, bod_in=bod_in, nh3n_in=nh3n_in,
        ss_in=ss_in, tn_in=tn_in, tp_in=tp_in,
        ph_value=ph_value, T=water_temp, MLSS=mlss_in,
        model_index=model_idx,
        sheets_per_rack=sheets_per_rack,
        pools=num_pools, racks_per_pool=racks_per_pool,
        J25=j25, fouling_factor=fouling_factor, SAD=sad_value,
        suction_on=suction_on, suction_off=suction_off,
        pool_level=pool_level, pipe_loss=pipe_loss,
        permeate_pump_head=pump_head, permeate_pump_eff=pump_eff,
        return_ratio=return_ratio,
        return_pump_head=return_head, return_pump_eff=return_eff,
        fan_efficiency=fan_eff,
        enable_bio_blower=False,
    )

# ==============================
# 计算按钮
# ==============================
with col_input:
    st.markdown("---")
    calculate_clicked = st.button(
        "🔢  执行计算",
        use_container_width=True,
        type="primary"
    )

    if calculate_clicked:
        result = compute_process(input_data)
        st.session_state.current_result = result
        st.session_state.current_input = input_data
        st.success(f"✅ 计算完成！平均通量: {result.j_avg:.1f} LMH, 总功率: {result.total_power:.1f} kW")

# ==============================
# 右栏：结果展示 + 按钮
# ==============================
with col_output:
    result = st.session_state.current_result

    if result is None:
        # 默认展示：使用第一组参数的计算结果作为预览
        default_result = compute_process(input_data)
        st.markdown("### 📊 设计参数预览（默认参数）")
        st.info("👈 调整左侧参数后点击「执行计算」按钮以查看详细结果。")

        # 预览 KPI
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("总膜面积", f"{int(default_result.a_actual):,} m²")
        k2.metric("平均通量", f"{default_result.j_avg:.1f} LMH")
        k3.metric("总供气量", f"{default_result.total_air_nm3min:.1f} Nm³/min")
        k4.metric("总功率", f"{default_result.total_power:.1f} kW")

    else:
        st.markdown("### 📊 计算结果总览")

        # KPI 卡片
        k1, k2, k3, k4 = st.columns(4)
        k1.metric("总膜面积", f"{int(result.a_actual):,} m²")
        k2.metric("平均通量", f"{result.j_avg:.1f} LMH")
        k3.metric("峰值通量", f"{result.j_peak:.1f} LMH")
        k4.metric("单位电耗", f"{result.unit_energy:.3f} kWh/m³")

        # 通量校核
        if result.j_peak > result.j_design:
            st.warning(
                f"⚠️ 峰值通量 ({result.j_peak:.1f} LMH) 超过设计通量 "
                f"({result.j_design:.1f} LMH)，建议增加膜面积或降低流量"
            )
        else:
            st.success(f"✅ 通量在设计范围内（峰值 {result.j_peak:.1f} LMH ≤ 设计 {result.j_design:.1f} LMH）")

        # 详细结果表格
        st.markdown("#### 📐 膜面积与通量")
        st.table({
            "项目": ["膜元件型号", "总膜面积", "组件台数", "平均通量", "峰值通量", "瞬时通量", "设计通量", "工作比"],
            "数值": [
                result.model_name, f"{result.a_actual:,.0f} m²",
                f"{result.n_racks} 台", f"{result.j_avg:.1f} LMH",
                f"{result.j_peak:.1f} LMH", f"{result.j_inst:.1f} LMH",
                f"{result.j_design:.1f} LMH", f"{result.duty_cycle*100:.1f} %",
            ],
        })

        st.markdown("#### 🌀 曝气系统")
        st.table({
            "项目": ["总供气量", "气水比"],
            "数值": [f"{result.total_air_nm3min:.1f} Nm³/min", f"{result.air_water_ratio:.1f} : 1"],
        })

        st.markdown("#### ⚡ 动力消耗")
        st.table({
            "设备": ["曝气风机", "产水泵", "回流泵", "总装机功率", "单位产水电耗"],
            "功率": [
                f"{result.blower_power:.1f} kW", f"{result.pump_power:.1f} kW",
                f"{result.return_pump_power:.1f} kW",
                f"{result.total_power:.1f} kW", f"{result.unit_energy:.3f} kWh/m³",
            ],
        })

        if result.unit_energy > 0.5:
            st.warning(f"⚠️ 单位电耗 ({result.unit_energy:.3f} kWh/m³) 较高，建议优化工艺参数")
        else:
            st.success("✅ 单位电耗在合理范围内")

    # ==============================
    # 导出 + 邮件发送按钮
    # ==============================
    if result is not None:
        st.markdown("---")
        st.markdown("### 📄 导出计算书（自动发送邮件至 jeziyou@qq.com）")

        btn_col1, btn_col2, btn_status = st.columns([1, 1, 1.3])

        # ------ PDF 导出按钮 ------
        with btn_col1:
            pdf_btn = st.button(
                "📄 生成 PDF 计算书",
                use_container_width=True,
                type="primary"
            )

        # ------ Word 导出按钮 ------
        with btn_col2:
            word_btn = st.button(
                "📝 生成 Word 计算书",
                use_container_width=True,
                type="secondary"
            )

        # ------ PDF 逻辑 ------
        if pdf_btn:
            with btn_status:
                with st.spinner("⏳ 正在生成 PDF..."):
                    pdf_bytes = generate_pdf_report(
                        input_data, result,
                        project_name=st.session_state.project_name,
                        designer=designer,
                        design_date=design_date.strftime("%Y-%m-%d")
                    )

            st.info("⏳ 正在后台发送邮件至 jeziyou@qq.com...")
            filename = f"{st.session_state.project_name}_计算书.pdf"
            status = send_email_via_resend(
                pdf_bytes, filename,
                st.session_state.project_name, "pdf"
            )
            st.success(f"✅ PDF 已生成 ({len(pdf_bytes)//1024} KB)，{status}")

            # 提供下载
            st.download_button(
                label="⬇️ 下载 PDF",
                data=pdf_bytes,
                file_name=filename,
                mime="application/pdf",
                use_container_width=True
            )

        # ------ Word 逻辑 ------
        if word_btn:
            with btn_status:
                with st.spinner("⏳ 正在生成 Word..."):
                    word_bytes = generate_word_report(
                        input_data, result,
                        project_name=st.session_state.project_name,
                        designer=designer,
                        design_date=design_date.strftime("%Y-%m-%d")
                    )

            st.info("⏳ 正在后台发送邮件至 jeziyou@qq.com...")
            filename = f"{st.session_state.project_name}_计算书.docx"
            status = send_email_via_resend(
                word_bytes, filename,
                st.session_state.project_name, "word"
            )
            st.success(f"✅ Word 已生成 ({len(word_bytes)//1024} KB)，{status}")

            # 提供下载
            st.download_button(
                label="⬇️ 下载 Word",
                data=word_bytes,
                file_name=filename,
                mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
                use_container_width=True
            )

# 底部
st.markdown("---")
st.markdown(
    """
    <div style="text-align:center;color:#64748b;font-size:12px;padding:1rem;">
    💧 三菱化学 MBR 膜系统工艺设计工具 | 邮件自动发送至 jeziyou@qq.com | Powered by Streamlit
    </div>
    """,
    unsafe_allow_html=True
)
