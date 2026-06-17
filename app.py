"""
MBR 膜系统工艺设计工具 - Streamlit 主应用
用户点击"生成PDF计算书"按钮 → 后台同时生成 Word 和发送邮件
"""
import streamlit as st
from datetime import datetime
import base64
import requests

from mbr_calc import ProcessInput, compute_process, ALL_MODELS
from mbr_report import generate_pdf_report, generate_word_report

# ============================================================================
# Page 配置
# ============================================================================
st.set_page_config(
    page_title="MBR 膜设计工具 - 工艺计算书",
    page_icon="💧",
    layout="wide",
)

# 自定义样式
st.markdown(
    """
    <style>
    .block-container {padding-top: 1.5rem; padding-bottom: 2rem;}
    h1, h2, h3 {color: #1e40af;}
    .stButton > button {
        background-color: #1e40af; color: #fff; font-weight: 600;
        padding: 0.75rem 1.5rem; border-radius: 8px; border: none;
        transition: background 0.2s;
    }
    .stButton > button:hover {background-color: #1e3a8a;}
    .param-card {
        background: #f8fafc; padding: 1rem; border-radius: 10px;
        border: 1px solid #e2e8f0; margin-bottom: 0.75rem;
    }
    </style>
    """,
    unsafe_allow_html=True,
)

# ============================================================================
# 侧边栏：输入参数（简洁分组，无邮件配置）
# ============================================================================
st.sidebar.markdown("## ⚙️ 设计参数")

# --- 项目信息 ---
st.sidebar.markdown("### 📋 项目信息")
col_p1, col_p2 = st.sidebar.columns(2)
with col_p1:
    project_name = st.text_input("项目名称", value="MBR 膜系统工艺计算书")
with col_p2:
    designer = st.text_input("设计人", value="工程师")
design_date = st.sidebar.date_input("设计日期", value=datetime.now().date()).strftime("%Y-%m-%d")

# --- 设计流量 ---
st.sidebar.markdown("### 🌊 设计流量")
col_f1, col_f2 = st.sidebar.columns(2)
with col_f1:
    inp_Q = st.number_input("设计流量 (m³/d)", value=5000.0, min_value=1.0, step=100.0)
with col_f2:
    inp_Kz = st.number_input("变化系数 Kz", value=1.3, min_value=1.0, step=0.1)

# --- 进水水质 ---
st.sidebar.markdown("### 💧 进水水质")
col_w1, col_w2, col_w3 = st.sidebar.columns(3)
with col_w1:
    inp_cod = st.number_input("COD (mg/L)", value=400.0, min_value=0.0, step=10.0)
    inp_bod = st.number_input("BOD₅ (mg/L)", value=200.0, min_value=0.0, step=10.0)
    inp_nh3n = st.number_input("NH₃-N (mg/L)", value=35.0, min_value=0.0, step=5.0)
with col_w2:
    inp_ss = st.number_input("SS (mg/L)", value=150.0, min_value=0.0, step=10.0)
    inp_tn = st.number_input("TN (mg/L)", value=50.0, min_value=0.0, step=5.0)
    inp_tp = st.number_input("TP (mg/L)", value=5.0, min_value=0.0, step=1.0)
with col_w3:
    inp_ph = st.number_input("pH", value=7.2, min_value=0.0, max_value=14.0, step=0.1)
    inp_T = st.number_input("水温 (℃)", value=20.0, min_value=0.0, max_value=50.0, step=1.0)
    inp_MLSS = st.number_input("MLSS (mg/L)", value=8000.0, min_value=0.0, step=500.0)

# --- 膜组件 ---
st.sidebar.markdown("### 🧪 膜组件配置")
model_names = [f"{m.name} ({m.sheet_area}m²)" for m in ALL_MODELS]
col_m1, col_m2 = st.sidebar.columns(2)
with col_m1:
    inp_model_idx = st.selectbox(
        "膜元件型号", range(len(model_names)),
        format_func=lambda i: model_names[i], index=2,
    )
    inp_pools = st.number_input("池数", value=2, min_value=1, step=1)
with col_m2:
    inp_sheets = st.number_input("每架膜片数", value=30, min_value=5, step=1)
    inp_racks = st.number_input("每池架数", value=3, min_value=1, step=1)

# --- 运行参数 ---
st.sidebar.markdown("### ⚙️ 运行参数")
col_r1, col_r2, col_r3 = st.sidebar.columns(3)
with col_r1:
    inp_J25 = st.number_input("J25 基准通量", value=18.0, min_value=5.0, max_value=40.0, step=0.5)
    inp_fouling = st.number_input("污染系数", value=0.85, min_value=0.5, max_value=1.0, step=0.05)
    inp_SAD = st.number_input("SAD 曝气密度", value=150.0, min_value=100.0, max_value=300.0, step=5.0)
with col_r2:
    inp_suction_on = st.number_input("抽吸-开 (min)", value=7.0, min_value=1.0, max_value=10.0, step=0.5)
    inp_suction_off = st.number_input("抽吸-停 (min)", value=1.0, min_value=0.5, max_value=10.0, step=0.5)
    inp_pool_level = st.number_input("池内液位 (m)", value=3.5, min_value=0.5, step=0.5)
with col_r3:
    inp_pipe_loss = st.number_input("管路损失 (m)", value=0.5, min_value=0.0, step=0.2)
    inp_pump_head = st.number_input("产水泵扬程 (m)", value=6.5, min_value=0.0, step=0.5)
    inp_pump_eff = st.number_input("产水泵效率 (%)", value=75, min_value=30, max_value=95, step=1) / 100.0

col_r4, col_r5 = st.sidebar.columns(2)
with col_r4:
    inp_return_ratio = st.number_input("回流比", value=3.0, min_value=0.0, step=0.5)
    inp_return_head = st.number_input("回流泵扬程 (m)", value=0.5, min_value=0.0, step=0.1)
    inp_return_eff = st.number_input("回流泵效率 (%)", value=70, min_value=30, max_value=95, step=1) / 100.0
with col_r5:
    inp_fan_eff = st.number_input("风机效率 (%)", value=90, min_value=45, max_value=98, step=1) / 100.0

st.sidebar.markdown("---")


# ============================================================================
# 主区：标题 + 生成按钮 + 结果展示
# ============================================================================
st.markdown("## 🔵 MBR 膜系统工艺设计工具 — 计算书生成")
st.markdown("在左侧调整设计参数，点击下方按钮生成计算书。")

st.markdown("---")

# ======== 辅助：构造输入参数 ========
def _build_input():
    return ProcessInput(
        Q=inp_Q, Kz=inp_Kz,
        cod_in=inp_cod, bod_in=inp_bod, nh3n_in=inp_nh3n,
        ss_in=inp_ss, tn_in=inp_tn, tp_in=inp_tp,
        ph_value=inp_ph, T=inp_T, MLSS=inp_MLSS,
        model_index=inp_model_idx,
        sheets_per_rack=int(inp_sheets),
        pools=int(inp_pools),
        racks_per_pool=int(inp_racks),
        J25=inp_J25, fouling_factor=inp_fouling, SAD=inp_SAD,
        suction_on=inp_suction_on, suction_off=inp_suction_off,
        pool_level=inp_pool_level, pipe_loss=inp_pipe_loss,
        permeate_pump_head=inp_pump_head, permeate_pump_eff=inp_pump_eff,
        return_ratio=inp_return_ratio,
        return_pump_head=inp_return_head, return_pump_eff=inp_return_eff,
        fan_efficiency=inp_fan_eff,
        enable_bio_blower=False,
    )


# ======== 辅助：发送邮件（后台静默） ========
def _send_email_background(file_bytes, file_type_label, result_data):
    try:
        RESEND_API_KEY = "re_H7RY9sKy_BC1N6hNun5iYykHYygj1gvYv"
        SENDER_EMAIL = "MBR设计工具 <onboarding@resend.dev>"
        DEFAULT_RECIPIENT = "jeziyou@qq.com"

        ext = "pdf" if file_type_label == "PDF" else "docx"
        filename = f"{project_name}.{ext}"

        payload = {
            "from": SENDER_EMAIL,
            "to": [DEFAULT_RECIPIENT],
            "subject": f"{project_name} - 工艺计算书 ({file_type_label})",
            "html": (
                f"<h2>{project_name}</h2>"
                f"<p>您好，</p>"
                f"<p>这是由三菱化学MBR膜设计工具自动生成的工艺计算书（{file_type_label}），请查收附件。</p>"
                f"<hr><p style='color:#666;font-size:12px;'>"
                f"设计流量：{int(inp_Q)} m³/d　|　膜面积：{int(result_data.a_actual)} m²<br>"
                f"平均通量：{result_data.j_avg:.1f} LMH　|　总功率：{result_data.total_power:.1f} kW</p>"
                f"<p style='color:#999;font-size:12px;'>此邮件由 MBR膜设计工具 - STERAPORE 自动发送</p>"
            ),
            "attachments": [{
                "filename": filename,
                "content": base64.b64encode(file_bytes).decode("utf-8"),
            }],
        }
        resp = requests.post(
            "https://api.resend.com/emails",
            json=payload,
            headers={
                "Authorization": f"Bearer {RESEND_API_KEY}",
                "Content-Type": "application/json",
            },
            timeout=30,
        )
        if resp.status_code == 200:
            return f"✅ 邮件已发送至 {DEFAULT_RECIPIENT}"
        return f"⚠️ 邮件发送失败 (HTTP {resp.status_code})"
    except Exception as e:
        return f"⚠️ 邮件发送异常: {str(e)[:80]}"


# ======== 辅助：显示结果展示（两个按钮共享） ========
def _render_results(result_data, pdf_bytes=None, word_bytes=None):
    st.markdown("---")
    st.markdown("### 📊 计算结果总览")

    c1, c2, c3, c4 = st.columns(4)
    c1.metric("总膜面积", f"{int(result_data.a_actual):,} m²")
    c2.metric("平均通量", f"{result_data.j_avg:.1f} LMH")
    c3.metric("峰值通量", f"{result_data.j_peak:.1f} LMH")
    c4.metric("设计通量", f"{result_data.j_design:.1f} LMH")

    c5, c6, c7 = st.columns(3)
    c5.metric("总供气量", f"{result_data.total_air_nm3min:.1f} Nm³/min")
    c6.metric("总装机功率", f"{result_data.total_power:.1f} kW")
    c7.metric("单位电耗", f"{result_data.unit_energy:.3f} kWh/m³")

    st.markdown("---")

    if result_data.j_peak > result_data.j_design:
        st.warning(
            f"⚠️ 峰值通量 ({result_data.j_peak:.1f} LMH) 超过设计通量 "
            f"({result_data.j_design:.1f} LMH)，建议增加膜面积或降低流量"
        )
    else:
        st.success("✅ 通量在设计范围内")

    if result_data.unit_energy > 0.5:
        st.warning(f"⚠️ 单位电耗 ({result_data.unit_energy:.3f} kWh/m³) 较高，建议优化工艺参数")
    else:
        st.success("✅ 单位电耗在合理范围内")

    cola, colb = st.columns(2)

    with cola:
        st.markdown("#### 📐 膜面积与通量")
        st.table({
            "项目": ["膜元件型号", "总膜面积", "总架数", "平均通量", "峰值通量", "瞬时通量", "设计通量", "工作比"],
            "数值": [
                result_data.model_name, f"{result_data.a_actual:,.0f} m²",
                f"{result_data.n_racks} 架", f"{result_data.j_avg:.1f} LMH",
                f"{result_data.j_peak:.1f} LMH", f"{result_data.j_inst:.1f} LMH",
                f"{result_data.j_design:.1f} LMH", f"{result_data.duty_cycle*100:.1f} %",
            ],
        })
        st.markdown("#### 🌀 曝气系统")
        st.table({
            "项目": ["总供气量", "气水比"],
            "数值": [f"{result_data.total_air_nm3min:.1f} Nm³/min", f"{result_data.air_water_ratio:.1f} : 1"],
        })

    with colb:
        st.markdown("#### ⚡ 动力消耗")
        st.table({
            "设备": ["曝气风机", "产水泵", "回流泵", "生物曝气风机", "总装机功率", "单位产水电耗"],
            "功率": [
                f"{result_data.blower_power:.1f} kW", f"{result_data.pump_power:.1f} kW",
                f"{result_data.return_pump_power:.1f} kW", f"{result_data.bio_blower_power:.1f} kW",
                f"{result_data.total_power:.1f} kW", f"{result_data.unit_energy:.3f} kWh/m³",
            ],
        })
        st.markdown("#### 🧪 化学清洗药剂")
        st.table({
            "项目": ["NaClO 年耗量", "柠檬酸年耗量", "清洗水耗"],
            "数值": [
                f"{result_data.naclo_per_year:.3f} t/a", f"{result_data.citric_per_year:.3f} t/a",
                f"{result_data.wash_water_per_year:.1f} m³/a",
            ],
        })

    st.markdown("---")
    st.markdown("### 📥 下载")
    if pdf_bytes is not None:
        st.download_button(
            label="⬇️ 下载 PDF 计算书", data=pdf_bytes,
            file_name=f"{project_name}.pdf", mime="application/pdf",
        )
    if word_bytes is not None:
        st.download_button(
            label="⬇️ 下载 Word 计算书", data=word_bytes,
            file_name=f"{project_name}.docx",
            mime="application/vnd.openxmlformats-officedocument.wordprocessingml.document",
        )


# === 主按钮：PDF / Word 两个按钮 ===
col_btn1, col_btn2, col_status = st.columns([1, 1, 2])

with col_btn1:
    pdf_clicked = st.button("📄 生成PDF计算书", use_container_width=True, type="primary")
with col_btn2:
    word_clicked = st.button("📝 生成Word计算书", use_container_width=True, type="secondary")

status_container = col_status.empty()

# ====== 点击了 PDF 按钮 ======
if pdf_clicked:
    try:
        status_container.info("⏳ 正在计算 ...")
        inp = _build_input()
        result = compute_process(inp)
        status_container.info("📄 正在生成 PDF ...")
        pdf_data = generate_pdf_report(inp, result, project_name=project_name, designer=designer, design_date=design_date)

        status_container.markdown(
            f"<div style='background:#f0fdf4;padding:10px 16px;border-radius:8px;"
            f"border:1px solid #86efac;'>"
            f"<b style='color:#166534;'>✅ PDF 已生成 ({len(pdf_data)//1024} KB)</b><br>"
            f"<span style='color:#15803d;font-size:13px;'>⏳ 后台正在发送邮件 ...</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        email_status = _send_email_background(pdf_data, "PDF", result)

        status_container.markdown(
            f"<div style='background:#f0fdf4;padding:10px 16px;border-radius:8px;"
            f"border:1px solid #86efac;'>"
            f"<b style='color:#166534;'>✅ PDF 已生成</b><br>"
            f"<span style='color:#15803d;font-size:13px;'>{email_status}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        _render_results(result, pdf_bytes=pdf_data)
    except Exception as e:
        st.error(f"❌ 生成失败: {e}")

# ====== 点击了 Word 按钮 ======
elif word_clicked:
    try:
        status_container.info("⏳ 正在计算 ...")
        inp = _build_input()
        result = compute_process(inp)
        status_container.info("📝 正在生成 Word ...")
        word_data = generate_word_report(inp, result, project_name=project_name, designer=designer, design_date=design_date)

        status_container.markdown(
            f"<div style='background:#f0fdf4;padding:10px 16px;border-radius:8px;"
            f"border:1px solid #86efac;'>"
            f"<b style='color:#166534;'>✅ Word 已生成 ({len(word_data)//1024} KB)</b><br>"
            f"<span style='color:#15803d;font-size:13px;'>⏳ 后台正在发送邮件 ...</span>"
            f"</div>",
            unsafe_allow_html=True,
        )

        email_status = _send_email_background(word_data, "Word", result)

        status_container.markdown(
            f"<div style='background:#f0fdf4;padding:10px 16px;border-radius:8px;"
            f"border:1px solid #86efac;'>"
            f"<b style='color:#166534;'>✅ Word 已生成</b><br>"
            f"<span style='color:#15803d;font-size:13px;'>{email_status}</span>"
            f"</div>",
            unsafe_allow_html=True,
        )
        _render_results(result, word_bytes=word_data)
    except Exception as e:
        st.error(f"❌ 生成失败: {e}")

# ====== 未点击任何按钮 ======
else:
    st.info("👈 在左侧调整设计参数后，点击上方「📄 生成PDF计算书」或「📝 生成Word计算书」按钮。"
            "邮件将在后台同步发送至 jeziyou@qq.com，无需手动操作。")
    st.markdown("### 📑 使用说明")
    with st.expander("📖 查看完整使用说明", expanded=True):
        st.markdown(
            """
            **🔹 第 1 步：调整参数**
            在左侧边栏修改设计流量、进水水质、膜组件型号与运行参数。

            **🔹 第 2 步：点击生成**
            - 点击「📄 生成PDF计算书」→ 生成 PDF + 后台发邮件（含 PDF 附件）
            - 点击「📝 生成Word计算书」→ 生成 Word + 后台发邮件（含 Word 附件）

            **🔹 第 3 步：下载与查看**
            - 页面显示完整计算结果与通量校核提示
            - 可直接下载对应文件
            - 邮件自动发送至 jeziyou@qq.com，用户无感
            """
        )

    st.markdown("### 🔍 默认参数快速预览")
    preview_inp = _build_input()
    preview_result = compute_process(preview_inp)
    p1, p2, p3, p4 = st.columns(4)
    p1.metric("总膜面积", f"{int(preview_result.a_actual):,} m²")
    p2.metric("平均通量", f"{preview_result.j_avg:.1f} LMH")
    p3.metric("总供气量", f"{preview_result.total_air_nm3min:.1f} Nm³/min")
    p4.metric("总功率", f"{preview_result.total_power:.1f} kW")
