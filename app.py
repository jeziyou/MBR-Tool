"""
MBR 膜设计工具
- 侧边栏：项目名称 + 流程图参数 + 发送邮件按钮
- 主界面：工艺流程图 + 原 HTML 计算器
- 发送时从 HTML 读取数据 → 后台发送邮件
"""
import streamlit as st
import os
import smtplib
import socket
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart

st.set_page_config(
    page_title="MBR 膜设计工具",
    page_icon="💧",
    layout="wide",
)

# ============================================================================
# 常量
# ============================================================================
MODEL_SHEET_AREA = {
    "56E0040SA": 40, "63E0040SA": 40, "62E0040SA": 40,
    "60E0025SA": 25, "55E0025SA": 25, "50E0025SA": 25,
    "55E0015SA": 15, "60E0015SA": 15, "50E0015SA": 15,
    "50E0006SA": 6,
}

# ============================================================================
# 初始化 session_state
# ============================================================================
defaults = {
    "project_name": "MBR膜系统工艺计算书",
    "show_pfd": True,
    "pfd_flow": 5000,       # 设计流量 m3/d
    "pfd_pools": 2,         # 膜池数
    "pfd_racks": 3,         # 每池台数
    "pfd_return_ratio": 400, # 污泥回流比 %
    "pfd_mlss": 8000,       # MLSS mg/L
}
for k, v in defaults.items():
    if k not in st.session_state:
        st.session_state[k] = v

# ============================================================================
# 发送邮件
# ============================================================================
def send_summary_email(project_name, flow_rate, model_name, sheet_area,
                        sheets_per_rack, pools, racks_per_pool):
    """通过 163.com SMTP_SSL 发送工艺计算书邮件
    Returns: (success: bool, error_msg: str)
    """
    smtp_host = "smtp.163.com"
    smtp_port = 465
    sender = "jeziyou@163.com"
    recipient = "jeziyou@qq.com"
    auth_code = "FNR3q3BjMYLyTEah"

    try:
        a_actual = pools * racks_per_pool * sheets_per_rack * sheet_area
        j_avg = flow_rate * 1000 / (a_actual * 24) if a_actual > 0 else 0

        html_content = f"""
        <h2>{project_name}</h2>
        <table style='border-collapse:collapse;border:1px solid #ddd;width:100%;'>
        <tr><th style='border:1px solid #ddd;padding:8px;text-align:left;background:#f5f5f5;'>参数</th><th style='border:1px solid #ddd;padding:8px;text-align:left;'>值</th></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>项目名称</td><td style='border:1px solid #ddd;padding:8px;'>{project_name}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>设计流量</td><td style='border:1px solid #ddd;padding:8px;'>{flow_rate} m³/d</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜片型号</td><td style='border:1px solid #ddd;padding:8px;'>{model_name}</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>每台膜片数</td><td style='border:1px solid #ddd;padding:8px;'>{sheets_per_rack} 片</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>膜池数</td><td style='border:1px solid #ddd;padding:8px;'>{pools} 池</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>每池台数</td><td style='border:1px solid #ddd;padding:8px;'>{racks_per_pool} 台</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>总膜面积</td><td style='border:1px solid #ddd;padding:8px;'>{int(a_actual):,} m²</td></tr>
        <tr><td style='border:1px solid #ddd;padding:8px;'>平均通量</td><td style='border:1px solid #ddd;padding:8px;'>{j_avg:.1f} LMH</td></tr>
        </table>
        <hr><p style='color:#999;font-size:12px;'>此邮件由三菱化学MBR膜设计工具自动发送</p>
        """

        msg = MIMEMultipart("alternative")
        msg["Subject"] = f"{project_name} - 工艺计算书"
        msg["From"] = f"MBR设计工具 <{sender}>"
        msg["To"] = recipient
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        # === 阶段 1: 连接（SSL 465 端口，显式超时） ===
        with smtplib.SMTP_SSL(smtp_host, smtp_port, timeout=30) as server:
            # === 阶段 2: EHLO 握手 ===
            server.ehlo()

            # === 阶段 3: SMTP 认证（授权码） ===
            try:
                server.login(sender, auth_code)
            except smtplib.SMTPAuthenticationError as e:
                return False, f"SMTP 认证失败：授权码无效或账号被限制 (code={e.smtp_code})"

            # === 阶段 4: 发送 ===
            try:
                server.sendmail(sender, [recipient], msg.as_string())
            except smtplib.SMTPException as e:
                return False, f"SMTP 发送失败：{e}"

        return True, ""

    except socket.timeout:
        return False, f"连接超时：无法在 30 秒内连接 {smtp_host}:{smtp_port}（网络/端口被封锁）"
    except socket.gaierror:
        return False, f"DNS 解析失败：无法解析 {smtp_host}"
    except ConnectionRefusedError:
        return False, f"连接被拒绝：{smtp_host}:{smtp_port} 不可达"
    except Exception as e:
        return False, f"未知错误：{type(e).__name__} - {e}"

# ============================================================================
# SVG 工艺流程图生成
# ============================================================================
def build_pfd_svg(flow, pools, racks, return_ratio, mlss):
    """生成 MBR 工艺流程图 SVG

    Args:
        flow: 设计流量 m3/d
        pools: 膜池数
        racks: 每池台数
        return_ratio: 污泥回流比 (%)
        mlss: MLSS (mg/L)
    """
    q_m3h = flow / 24.0                   # m3/h
    return_flow = flow * return_ratio / 100  # m3/d 回流
    total_membrane_flow = flow + return_flow
    total_racks = pools * racks

    # 颜色
    c_water = "#2563eb"       # 蓝色 - 水
    c_aeration = "#f59e0b"    # 橙色 - 曝气
    c_sludge = "#6b7280"      # 灰色 - 污泥
    c_chemical = "#a855f7"    # 紫色 - 药剂
    c_bg = "#f8fafc"          # 浅灰背景
    c_box = "#ffffff"         # 白色箱体
    c_border = "#334155"      # 深蓝灰边框
    c_text = "#0f172a"        # 深色文字

    return_ratio_2 = 300     # 内循环回流比 %

    # 构建 SVG (宽 1400, 高 600)
    svg = f'''<?xml version="1.0" encoding="UTF-8"?>
    <svg xmlns="http://www.w3.org/2000/svg" viewBox="0 0 1400 520" width="100%" style="max-width:1400px;">
      <defs>
        <marker id="arrow" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="{c_water}" />
        </marker>
        <marker id="arrowSludge" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="{c_sludge}" />
        </marker>
        <marker id="arrowAir" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="{c_aeration}" />
        </marker>
        <marker id="arrowChem" viewBox="0 0 10 10" refX="8" refY="5" markerWidth="6" markerHeight="6" orient="auto-start-reverse">
          <path d="M 0 0 L 10 5 L 0 10 z" fill="{c_chemical}" />
        </marker>
        <pattern id="water" width="20" height="20" patternUnits="userSpaceOnUse">
          <path d="M0 10 Q 5 5 10 10 T 20 10" fill="none" stroke="rgba(37,99,235,0.25)" stroke-width="1.5"/>
        </pattern>
        <pattern id="sludge" width="12" height="12" patternUnits="userSpaceOnUse">
          <circle cx="6" cy="6" r="1.5" fill="rgba(107,114,128,0.3)"/>
        </pattern>
      </defs>

      <rect x="0" y="0" width="1400" height="520" fill="{c_bg}" rx="8"/>

      <!-- ============ 第 1 节：原水 ============ -->
      <g>
        <rect x="20" y="210" width="110" height="90" rx="6" fill="{c_box}" stroke="{c_border}" stroke-width="2"/>
        <text x="75" y="245" text-anchor="middle" font-size="14" font-weight="bold" fill="{c_text}">原水</text>
        <text x="75" y="270" text-anchor="middle" font-size="11" fill="{c_water}">{flow:,.0f} m³/d</text>
        <text x="75" y="288" text-anchor="middle" font-size="11" fill="#64748b">( {q_m3h:.1f} m³/h )</text>
      </g>

      <!-- 箭头：原水 -> 细格栅 -->
      <line x1="130" y1="255" x2="170" y2="255" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>

      <!-- ============ 第 2 节：细格栅 ============ -->
      <g>
        <rect x="170" y="210" width="110" height="90" rx="6" fill="{c_box}" stroke="{c_border}" stroke-width="2"/>
        <text x="225" y="245" text-anchor="middle" font-size="14" font-weight="bold" fill="{c_text}">细格栅</text>
        <text x="225" y="270" text-anchor="middle" font-size="11" fill="#64748b">1~3 mm</text>
        <text x="225" y="288" text-anchor="middle" font-size="11" fill="#64748b">间隙过滤</text>
      </g>

      <line x1="280" y1="255" x2="320" y2="255" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>

      <!-- ============ 第 3 节：调节池 ============ -->
      <g>
        <rect x="320" y="210" width="130" height="90" rx="6" fill="url(#water)" stroke="{c_border}" stroke-width="2"/>
        <rect x="320" y="210" width="130" height="90" rx="6" fill="none" stroke="{c_border}" stroke-width="2"/>
        <text x="385" y="245" text-anchor="middle" font-size="14" font-weight="bold" fill="{c_text}">调节池</text>
        <text x="385" y="270" text-anchor="middle" font-size="11" fill="#64748b">均质 均量</text>
        <text x="385" y="288" text-anchor="middle" font-size="11" fill="#64748b">HRT 4~8h</text>
      </g>

      <line x1="450" y1="255" x2="490" y2="255" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>
      <text x="470" y="248" text-anchor="middle" font-size="10" fill="#64748b">提升泵</text>

      <!-- ============ 第 4 节：缺氧池 ============ -->
      <g>
        <rect x="490" y="210" width="130" height="90" rx="6" fill="{c_box}" stroke="{c_border}" stroke-width="2"/>
        <text x="555" y="235" text-anchor="middle" font-size="14" font-weight="bold" fill="{c_text}">缺氧池</text>
        <text x="555" y="253" text-anchor="middle" font-size="11" fill="#64748b">Anoxic</text>
        <text x="555" y="271" text-anchor="middle" font-size="11" fill="#64748b">反硝化脱氮</text>
        <text x="555" y="289" text-anchor="middle" font-size="11" fill="{c_aeration}">DO &lt; 0.5 mg/L</text>
      </g>

      <line x1="620" y1="255" x2="660" y2="255" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>

      <!-- ============ 第 5 节：MBR 好氧池 + 膜池 ============ -->
      <g>
        <rect x="660" y="170" width="280" height="170" rx="6" fill="{c_box}" stroke="{c_border}" stroke-width="2.5"/>
        <rect x="660" y="170" width="280" height="170" rx="6" fill="url(#water)" opacity="0.4"/>

        <!-- 分隔线：左侧好氧区 / 右侧膜区 -->
        <line x1="800" y1="170" x2="800" y2="340" stroke="{c_border}" stroke-width="1.5" stroke-dasharray="6,4"/>

        <!-- 好氧区 -->
        <text x="730" y="195" text-anchor="middle" font-size="13" font-weight="bold" fill="{c_text}">好氧区</text>
        <text x="730" y="213" text-anchor="middle" font-size="11" fill="#64748b">Aerobic</text>

        <!-- 膜区 -->
        <text x="870" y="195" text-anchor="middle" font-size="13" font-weight="bold" fill="{c_text}">膜池 MBR</text>
        <text x="870" y="213" text-anchor="middle" font-size="11" fill="#64748b">{pools} 池 × {racks} 台 = {total_racks} 台</text>

        <!-- 膜组件图标（竖线） -->
        <g opacity="0.7">
          <line x1="830" y1="230" x2="830" y2="325" stroke="{c_water}" stroke-width="3"/>
          <line x1="855" y1="230" x2="855" y2="325" stroke="{c_water}" stroke-width="3"/>
          <line x1="880" y1="230" x2="880" y2="325" stroke="{c_water}" stroke-width="3"/>
          <line x1="905" y1="230" x2="905" y2="325" stroke="{c_water}" stroke-width="3"/>
          <!-- 收集管 -->
          <line x1="820" y1="230" x2="915" y2="230" stroke="{c_border}" stroke-width="3"/>
        </g>

        <text x="870" y="343" text-anchor="middle" font-size="11" fill="{c_water}">{total_membrane_flow:,.0f} m³/d</text>
        <text x="870" y="355" text-anchor="middle" font-size="10" fill="#64748b">(含 {return_flow:,.0f} m³/d 回流)</text>

        <!-- 底部污泥区 -->
        <rect x="660" y="325" width="280" height="15" rx="0" fill="url(#sludge)" opacity="0.6"/>
      </g>

      <!-- ============ 鼓风机（曝气） - 从底部供气 ============ -->
      <g>
        <rect x="660" y="390" width="120" height="70" rx="6" fill="{c_box}" stroke="{c_aeration}" stroke-width="2"/>
        <text x="720" y="415" text-anchor="middle" font-size="12" font-weight="bold" fill="{c_aeration}">罗茨鼓风机</text>
        <text x="720" y="433" text-anchor="middle" font-size="11" fill="#64748b">曝气 / 擦洗</text>
        <text x="720" y="450" text-anchor="middle" font-size="11" fill="#64748b">空气流量</text>
        <!-- 曝气管道 -->
        <line x1="720" y1="390" x2="720" y2="340" stroke="{c_aeration}" stroke-width="2.5" marker-end="url(#arrowAir)"/>
      </g>

      <!-- 箭头：MBR -> 产水泵 -->
      <line x1="940" y1="255" x2="980" y2="255" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>

      <!-- ============ 第 6 节：产水泵 ============ -->
      <g>
        <rect x="980" y="210" width="110" height="90" rx="6" fill="{c_box}" stroke="{c_border}" stroke-width="2"/>
        <text x="1035" y="245" text-anchor="middle" font-size="13" font-weight="bold" fill="{c_text}">产水泵</text>
        <text x="1035" y="263" text-anchor="middle" font-size="11" fill="#64748b">间歇抽吸</text>
        <text x="1035" y="281" text-anchor="middle" font-size="11" fill="#64748b">9 min / 3 min</text>
        <text x="1035" y="297" text-anchor="middle" font-size="11" fill="{c_water}">{flow:,.0f} m³/d</text>
      </g>

      <line x1="1090" y1="255" x2="1130" y2="255" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>

      <!-- ============ 第 7 节：产水箱 ============ -->
      <g>
        <rect x="1130" y="210" width="130" height="90" rx="6" fill="{c_box}" stroke="{c_border}" stroke-width="2"/>
        <rect x="1130" y="250" width="130" height="50" rx="0" fill="url(#water)" opacity="0.5"/>
        <text x="1195" y="235" text-anchor="middle" font-size="14" font-weight="bold" fill="{c_text}">产水箱</text>
        <text x="1195" y="285" text-anchor="middle" font-size="11" fill="#64748b">达标排放</text>
        <text x="1195" y="300" text-anchor="middle" font-size="11" fill="#64748b">/ 回用</text>
      </g>

      <!-- ============ 加药系统 (紫色 - 顶部) ============ -->
      <g>
        <rect x="670" y="30" width="120" height="60" rx="6" fill="{c_box}" stroke="{c_chemical}" stroke-width="2"/>
        <text x="730" y="55" text-anchor="middle" font-size="12" font-weight="bold" fill="{c_chemical}">加药系统</text>
        <text x="730" y="73" text-anchor="middle" font-size="11" fill="#64748b">PAC / NaClO / 酸</text>
        <!-- 加药管线 -->
        <line x1="730" y1="90" x2="730" y2="170" stroke="{c_chemical}" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrowChem)"/>
      </g>

      <!-- ============ CIP 化学清洗 (顶部) ============ -->
      <g>
        <rect x="810" y="30" width="140" height="60" rx="6" fill="{c_box}" stroke="{c_chemical}" stroke-width="2"/>
        <text x="880" y="55" text-anchor="middle" font-size="12" font-weight="bold" fill="{c_chemical}">CIP 化学清洗</text>
        <text x="880" y="73" text-anchor="middle" font-size="11" fill="#64748b">NaCIO / 柠檬酸</text>
        <!-- 清洗管线 -->
        <line x1="880" y1="90" x2="880" y2="170" stroke="{c_chemical}" stroke-width="2" stroke-dasharray="4,3" marker-end="url(#arrowChem)"/>
      </g>

      <!-- ============ 污泥回流管线 (从膜池底部 -> 缺氧池) ============ -->
      <g>
        <!-- 从膜池底部 340 向下 -> 回流泵 -> 向左 -> 缺氧池底部 -->
        <line x1="800" y1="340" x2="800" y2="430" stroke="{c_sludge}" stroke-width="2.5"/>
        <line x1="800" y1="430" x2="490" y2="430" stroke="{c_sludge}" stroke-width="2.5" marker-end="url(#arrowSludge)"/>
        <line x1="490" y1="430" x2="490" y2="300" stroke="{c_sludge}" stroke-width="2.5" marker-end="url(#arrowSludge)"/>
        <text x="640" y="423" text-anchor="middle" font-size="11" fill="{c_sludge}">污泥回流 {return_ratio}% →</text>

        <!-- 回流泵 -->
        <rect x="620" y="418" width="44" height="24" rx="4" fill="{c_box}" stroke="{c_sludge}" stroke-width="1.5"/>
        <text x="642" y="433" text-anchor="middle" font-size="10" fill="{c_sludge}">回流泵</text>
      </g>

      <!-- ============ 剩余污泥 -> 污泥脱水 ============ -->
      <g>
        <line x1="940" y1="340" x2="940" y2="470" stroke="{c_sludge}" stroke-width="2.5"/>
        <line x1="940" y1="470" x2="1130" y2="470" stroke="{c_sludge}" stroke-width="2.5" marker-end="url(#arrowSludge)"/>

        <rect x="1130" y="440" width="140" height="60" rx="6" fill="{c_box}" stroke="{c_sludge}" stroke-width="2"/>
        <text x="1200" y="465" text-anchor="middle" font-size="12" font-weight="bold" fill="{c_sludge}">污泥脱水</text>
        <text x="1200" y="483" text-anchor="middle" font-size="11" fill="#64748b">板框 / 带式</text>
        <text x="1200" y="498" text-anchor="middle" font-size="11" fill="#64748b">泥饼外运</text>

        <text x="1035" y="463" text-anchor="middle" font-size="11" fill="{c_sludge}">剩余污泥 →</text>
      </g>

      <!-- ============ 内循环（好氧 -> 缺氧） 顶部 ============ -->
      <g>
        <line x1="780" y1="170" x2="780" y2="110" stroke="{c_water}" stroke-width="2" stroke-dasharray="5,3"/>
        <line x1="780" y1="110" x2="555" y2="110" stroke="{c_water}" stroke-width="2" stroke-dasharray="5,3"/>
        <line x1="555" y1="110" x2="555" y2="170" stroke="{c_water}" stroke-width="2" stroke-dasharray="5,3" marker-end="url(#arrow)"/>
        <text x="668" y="103" text-anchor="middle" font-size="11" fill="{c_water}">混合液回流 {return_ratio_2}% →</text>
      </g>

      <!-- ============ 标题 ============ -->
      <text x="700" y="25" text-anchor="middle" font-size="18" font-weight="bold" fill="{c_text}">MBR 膜生物反应器 工艺流程图</text>

      <!-- ============ 图例 ============ -->
      <g transform="translate(20, 440)">
        <rect x="0" y="0" width="560" height="60" rx="6" fill="{c_box}" stroke="#cbd5e1" stroke-width="1"/>
        <text x="10" y="20" font-size="12" font-weight="bold" fill="{c_text}">图例：</text>
        <line x1="70" y1="16" x2="110" y2="16" stroke="{c_water}" stroke-width="2.5" marker-end="url(#arrow)"/>
        <text x="118" y="20" font-size="11" fill="#475569">水流</text>
        <line x1="170" y1="16" x2="210" y2="16" stroke="{c_aeration}" stroke-width="2.5" marker-end="url(#arrowAir)"/>
        <text x="218" y="20" font-size="11" fill="#475569">曝气 / 空气</text>
        <line x1="280" y1="16" x2="320" y2="16" stroke="{c_sludge}" stroke-width="2.5" marker-end="url(#arrowSludge)"/>
        <text x="328" y="20" font-size="11" fill="#475569">污泥流</text>
        <line x1="390" y1="16" x2="430" y2="16" stroke="{c_chemical}" stroke-width="2.5" stroke-dasharray="4,3" marker-end="url(#arrowChem)"/>
        <text x="438" y="20" font-size="11" fill="#475569">药剂</text>
        <text x="10" y="45" font-size="11" fill="#64748b">
          设计流量 {flow:,.0f} m³/d  ·  MLSS {mlss:,} mg/L  ·  膜池 {pools} 座  ·  每池 {racks} 台  ·  污泥回流比 {return_ratio}%
        </text>
      </g>

    </svg>
    '''
    return svg

# ============================================================================
# 侧边栏：主要项目信息
# ============================================================================
with st.sidebar:
    st.markdown("## 📋 主要项目信息")
    st.markdown("---")

    project_name = st.text_input("项目名称", key="project_name")

    st.markdown("---")
    st.markdown("### 🔬 流程图参数")
    st.session_state.pfd_flow = st.number_input(
        "设计流量 (m³/d)", min_value=1, step=100, key="pfd_flow_sb",
        value=st.session_state.pfd_flow
    )
    st.session_state.pfd_pools = st.number_input(
        "膜池数 (座)", min_value=1, step=1, key="pfd_pools_sb",
        value=st.session_state.pfd_pools
    )
    st.session_state.pfd_racks = st.number_input(
        "每池台数 (台)", min_value=1, step=1, key="pfd_racks_sb",
        value=st.session_state.pfd_racks
    )
    st.session_state.pfd_return_ratio = st.number_input(
        "污泥回流比 (%)", min_value=50, max_value=800, step=50, key="pfd_return_sb",
        value=st.session_state.pfd_return_ratio
    )
    st.session_state.pfd_mlss = st.number_input(
        "MLSS (mg/L)", min_value=3000, max_value=15000, step=500, key="pfd_mlss_sb",
        value=st.session_state.pfd_mlss
    )
    st.session_state.show_pfd = st.checkbox("显示工艺流程图", key="show_pfd_sb",
                                              value=st.session_state.show_pfd)

    st.markdown("---")

    if st.button("📤 发送项目信息至邮箱", type="primary", use_container_width=True):
        st.session_state["_send_pending"] = True
        st.rerun()

    st.markdown("---")
    st.caption("💡 在 HTML 中完成计算后，点击上方按钮发送项目信息至 jeziyou@qq.com")

# ============================================================================
# 主界面
# ============================================================================
st.markdown("## 💧 三菱化学 MBR 膜系统工艺设计工具")

# --- 工艺流程图面板 ---
if st.session_state.show_pfd:
    st.markdown("### 🔵 工艺流程图")
    pfd_svg = build_pfd_svg(
        flow=st.session_state.pfd_flow,
        pools=st.session_state.pfd_pools,
        racks=st.session_state.pfd_racks,
        return_ratio=st.session_state.pfd_return_ratio,
        mlss=st.session_state.pfd_mlss,
    )
    st.components.v1.html(pfd_svg, height=540, scrolling=False)
    st.markdown("---")

# --- 原 HTML 计算器 ---
st.markdown("### 📐 工艺计算书")
_html_path = os.path.join(os.path.dirname(os.path.abspath(__file__)), "MBR_Tool .html")
with open(_html_path, "r", encoding="utf-8") as f:
    _html_content = f.read()
st.components.v1.html(_html_content, height=12000, scrolling=True)

# ============================================================================
# 通信组件：从主 iframe 读取数据（仅在发送请求时）
# ============================================================================
if st.session_state.get("_send_pending"):
    read_script = """
    <script>
    (function poll() {
        var iframes = parent.document.querySelectorAll('iframe');
        for (var i = 0; i < iframes.length; i++) {
            try {
                var doc = iframes[i].contentDocument;
                if (doc && doc.getElementById('btnCalculate')) {
                    var data = {
                        projectName: doc.getElementById('projectName')?.value || '',
                        flowRate: doc.getElementById('flowRate')?.value || '',
                        membraneModel: doc.getElementById('membraneModel')?.value || '',
                        membraneSheets: doc.getElementById('membraneSheets')?.value || '',
                        membranePools: doc.getElementById('membranePools')?.value || '',
                        membraneSeries: doc.getElementById('membraneSeries')?.value || '',
                    };
                    Streamlit.setComponentValue(data);
                    return;
                }
            } catch(e) {}
        }
        setTimeout(poll, 300);
    })();
    </script>
    """
    result = st.components.v1.html(read_script, height=0)

    if result and result != 0 and isinstance(result, dict):
        st.session_state["_send_pending"] = False

        model_name = result.get("membraneModel", "")
        sheet_area = MODEL_SHEET_AREA.get(model_name, 40)

        try:
            flow_rate = int(float(result.get("flowRate", 0)))
        except (ValueError, TypeError):
            flow_rate = 0

        try:
            sheets = int(result.get("membraneSheets", 0))
        except (ValueError, TypeError):
            sheets = 0

        try:
            pools = int(result.get("membranePools", 0))
        except (ValueError, TypeError):
            pools = 0

        try:
            series = int(result.get("membraneSeries", 0))
        except (ValueError, TypeError):
            series = 0

        ok, err_msg = send_summary_email(
            st.session_state.project_name, flow_rate, model_name, sheet_area,
            sheets, pools, series
        )
        if ok:
            st.success("✅ 邮件已发送至 jeziyou@qq.com")
        else:
            st.error(f"❌ 邮件发送失败 — {err_msg}")
        st.rerun()
