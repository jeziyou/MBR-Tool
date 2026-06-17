"""
MBR 膜工艺计算核心模块（Python 版本，从 JS 的 ComputeProcess 函数移植）
"""
import math
from dataclasses import dataclass, field
from typing import Optional

# ============================================================================
# 膜模型数据（与 HTML 中 AllModels 保持一致）
# ============================================================================
@dataclass
class MembraneModel:
    name: str
    sheet_area: float  # m²
    pore_size: float   # μm
    mbr_type: str      # "UF" or "MF"
    rack_code: str
    frame_width: float   # mm
    frame_height: float  # mm
    frame_length: float  # mm


ALL_MODELS = [
    MembraneModel("56E0040SA", 40, 0.05, "UF", "56M", 30, 1250, 2000),
    MembraneModel("63E0040SA", 40, 0.1,  "UF", "63M", 30, 1250, 2000),
    MembraneModel("62E0040SA", 40, 0.2,  "MF", "62M", 30, 1250, 2000),
    MembraneModel("60E0025SA", 25, 0.4,  "MF", "60M", 30, 1250, 2000),
    MembraneModel("55E0025SA", 25, 0.05, "UF", "55M", 30, 1250, 2000),
    MembraneModel("50E0025SA", 25, 0.4,  "MF", "50M", 30, 1250, 2000),
    MembraneModel("55E0015SA", 15, 0.05, "UF", "55M", 30, 1250, 1300),
    MembraneModel("60E0015SA", 15, 0.4,  "MF", "60M", 30, 1250, 1300),
    MembraneModel("50E0015SA", 15, 0.4,  "MF", "50M", 30, 1250, 1300),
    MembraneModel("50E0006SA", 6,  0.4,  "MF", "50M", 44, 620, 1015),
]


# ============================================================================
# 膜架参数（与 HTML 中 rackParams40_25 / 15 / 6 保持一致）
# SheetArea=40/25 用同一个表
# ============================================================================
@dataclass
class RackParam:
    sheets: int
    width_mm: float
    length_mm: float
    dry_weight_kg: float
    wet_weight_kg: float
    air_flow_m3h: float
    proj_area_m2: float


def _build_rack(sheets, w, l, dry, wet, air, proj):
    return RackParam(sheets, w, l, dry, wet, air, proj)


RACK_PARAMS_40_25 = [
    _build_rack(5, 715, 1524, 350, 1050, 22.5, 0.4),
    _build_rack(6, 760, 1524, 370, 1110, 25.2, 0.456),
    _build_rack(7, 805, 1524, 390, 1170, 27.9, 0.512),
    _build_rack(8, 850, 1524, 410, 1230, 30.6, 0.568),
    _build_rack(9, 895, 1524, 430, 1290, 33.3, 0.624),
    _build_rack(10, 940, 1524, 450, 1350, 36, 0.68),
    _build_rack(11, 985, 1524, 470, 1410, 38.7, 0.736),
    _build_rack(12, 1030, 1524, 490, 1470, 41.4, 0.792),
    _build_rack(13, 1075, 1524, 510, 1530, 44.1, 0.848),
    _build_rack(14, 1120, 1524, 530, 1590, 46.8, 0.904),
    _build_rack(15, 1165, 1524, 550, 1650, 49.5, 0.96),
    _build_rack(16, 1210, 1524, 570, 1710, 52.2, 1.016),
    _build_rack(17, 1255, 1524, 590, 1770, 54.9, 1.072),
    _build_rack(18, 1300, 1524, 610, 1830, 57.6, 1.128),
    _build_rack(19, 1345, 1524, 630, 1890, 60.3, 1.184),
    _build_rack(20, 1390, 1524, 650, 1950, 63, 1.24),
    _build_rack(21, 1438, 1524, 670, 2010, 66.6, 1.296),
    _build_rack(22, 1486, 1524, 690, 2070, 70.2, 1.352),
    _build_rack(23, 1534, 1524, 710, 2130, 73.8, 1.408),
    _build_rack(24, 1582, 1524, 730, 2190, 77.4, 1.464),
    _build_rack(25, 1630, 1524, 750, 2250, 81, 1.52),
    _build_rack(26, 1678, 1524, 770, 2310, 84.6, 1.576),
    _build_rack(27, 1726, 1524, 790, 2370, 88.2, 1.632),
    _build_rack(28, 1774, 1524, 810, 2430, 91.8, 1.688),
    _build_rack(29, 1822, 1524, 830, 2490, 95.4, 1.744),
    _build_rack(30, 1870, 1524, 850, 2500, 99, 1.8),
    _build_rack(31, 1915, 1524, 870, 2560, 102.6, 1.856),
    _build_rack(32, 1960, 1524, 890, 2620, 106.2, 1.912),
    _build_rack(33, 2005, 1524, 910, 2680, 109.8, 1.968),
    _build_rack(34, 2050, 1524, 930, 2740, 113.4, 2.024),
    _build_rack(35, 2095, 1524, 950, 2800, 117, 2.08),
    _build_rack(36, 2140, 1524, 970, 2860, 120.6, 2.136),
    _build_rack(37, 2185, 1524, 990, 2920, 124.2, 2.192),
    _build_rack(38, 2230, 1524, 1010, 2980, 127.8, 2.248),
    _build_rack(39, 2275, 1524, 1030, 3040, 131.4, 2.304),
    _build_rack(40, 2320, 1524, 1050, 3150, 135, 2.36),
    _build_rack(41, 2375, 1524, 1080, 3240, 138.15, 2.422),
    _build_rack(42, 2430, 1524, 1110, 3330, 141.3, 2.484),
    _build_rack(43, 2484, 1524, 1140, 3420, 144.45, 2.546),
    _build_rack(44, 2539, 1524, 1170, 3510, 147.6, 2.608),
    _build_rack(45, 2594, 1524, 1200, 3600, 150.75, 2.67),
    _build_rack(46, 2649, 1524, 1230, 3690, 153.9, 2.732),
    _build_rack(47, 2704, 1524, 1260, 3780, 157.05, 2.794),
    _build_rack(48, 2758, 1524, 1290, 3870, 160.2, 2.856),
    _build_rack(49, 2813, 1524, 1320, 3960, 163.35, 2.918),
    _build_rack(50, 2868, 1524, 1350, 4050, 166.5, 2.98),
    _build_rack(51, 2923, 1524, 1380, 4140, 169.65, 3.042),
    _build_rack(52, 2978, 1524, 1410, 4230, 172.8, 3.104),
    _build_rack(53, 3032, 1524, 1440, 4320, 175.95, 3.166),
]

RACK_PARAMS_15 = [
    _build_rack(5, 715, 1300, 280, 840, 18, 0.33),
    _build_rack(6, 760, 1300, 296, 888, 21.6, 0.37),
    _build_rack(7, 805, 1300, 312, 936, 25.2, 0.41),
    _build_rack(8, 850, 1300, 328, 984, 28.8, 0.45),
    _build_rack(9, 895, 1300, 344, 1032, 32.4, 0.49),
    _build_rack(10, 940, 1300, 360, 1080, 36, 0.53),
    _build_rack(11, 985, 1300, 376, 1128, 39.6, 0.57),
    _build_rack(12, 1030, 1300, 392, 1176, 43.2, 0.61),
    _build_rack(13, 1075, 1300, 408, 1224, 46.8, 0.65),
    _build_rack(14, 1120, 1300, 424, 1272, 50.4, 0.69),
    _build_rack(15, 1165, 1300, 440, 1320, 54, 0.73),
    _build_rack(16, 1210, 1300, 456, 1368, 57.6, 0.77),
    _build_rack(17, 1255, 1300, 472, 1416, 61.2, 0.81),
    _build_rack(18, 1300, 1300, 488, 1464, 64.8, 0.85),
    _build_rack(19, 1345, 1300, 504, 1512, 68.4, 0.89),
    _build_rack(20, 1390, 1300, 520, 1560, 72, 0.93),
    _build_rack(21, 1438, 1300, 536, 1608, 75.6, 0.97),
    _build_rack(22, 1486, 1300, 552, 1656, 79.2, 1.01),
    _build_rack(23, 1534, 1300, 568, 1704, 82.8, 1.05),
    _build_rack(24, 1582, 1300, 584, 1752, 86.4, 1.09),
    _build_rack(25, 1630, 1300, 600, 1800, 90, 1.13),
    _build_rack(26, 1678, 1300, 616, 1848, 93.6, 1.17),
    _build_rack(27, 1726, 1300, 632, 1896, 97.2, 1.21),
    _build_rack(28, 1774, 1300, 648, 1944, 100.8, 1.25),
    _build_rack(29, 1822, 1300, 664, 1992, 104.4, 1.29),
    _build_rack(30, 1870, 1300, 680, 2040, 108, 1.33),
    _build_rack(31, 1915, 1300, 696, 2088, 111.6, 1.37),
    _build_rack(32, 1960, 1300, 712, 2136, 115.2, 1.41),
    _build_rack(33, 2005, 1300, 728, 2184, 118.8, 1.45),
    _build_rack(34, 2050, 1300, 744, 2232, 122.4, 1.49),
    _build_rack(35, 2095, 1300, 760, 2280, 126, 1.53),
    _build_rack(36, 2140, 1300, 776, 2328, 129.6, 1.57),
    _build_rack(37, 2185, 1300, 792, 2376, 133.2, 1.61),
    _build_rack(38, 2230, 1300, 808, 2424, 136.8, 1.65),
    _build_rack(39, 2275, 1300, 824, 2472, 140.4, 1.69),
    _build_rack(40, 2320, 1300, 840, 2520, 144, 1.73),
]

RACK_PARAMS_6 = [
    _build_rack(5, 715, 1015, 200, 600, 13.5, 0.25),
    _build_rack(6, 760, 1015, 215, 645, 16.2, 0.28),
    _build_rack(7, 805, 1015, 230, 690, 18.9, 0.31),
    _build_rack(8, 850, 1015, 245, 735, 21.6, 0.34),
    _build_rack(9, 895, 1015, 260, 780, 24.3, 0.37),
    _build_rack(10, 940, 1015, 275, 825, 27, 0.4),
    _build_rack(11, 985, 1015, 290, 870, 29.7, 0.43),
    _build_rack(12, 1030, 1015, 305, 915, 32.4, 0.46),
    _build_rack(13, 1075, 1015, 320, 960, 35.1, 0.49),
    _build_rack(14, 1120, 1015, 335, 1005, 37.8, 0.52),
    _build_rack(15, 1165, 1015, 350, 1050, 40.5, 0.55),
    _build_rack(16, 1210, 1015, 365, 1095, 43.2, 0.58),
    _build_rack(17, 1255, 1015, 380, 1140, 45.9, 0.61),
    _build_rack(18, 1300, 1015, 395, 1185, 48.6, 0.64),
    _build_rack(19, 1345, 1015, 410, 1230, 51.3, 0.67),
    _build_rack(20, 1390, 1015, 425, 1275, 54, 0.70),
]


def get_rack_param(sheet_area, sheets_per_rack):
    """根据膜片面积和每架膜片数，获取膜架参数"""
    if sheet_area in (40, 25):
        table = RACK_PARAMS_40_25
    elif sheet_area == 15:
        table = RACK_PARAMS_15
    elif sheet_area == 6:
        table = RACK_PARAMS_6
    else:
        return None
    for r in table:
        if r.sheets == sheets_per_rack:
            return r
    return None


# ============================================================================
# 输入参数
# ============================================================================
@dataclass
class ProcessInput:
    # 设计流量
    Q: float = 5000.0          # m3/d 设计流量
    Kz: float = 1.3            # 总变化系数

    # 进水水质
    cod_in: float = 400.0
    bod_in: float = 200.0
    nh3n_in: float = 35.0
    ss_in: float = 150.0
    tn_in: float = 50.0
    tp_in: float = 5.0
    ph_value: float = 7.2
    T: float = 20.0             # 水温 ℃
    MLSS: float = 8000.0        # mg/L

    # 膜组件选择
    model_index: int = 2        # 对应 ALL_MODELS[2] = 62E0040SA
    sheets_per_rack: int = 30    # 每架膜片数
    pools: int = 2               # 池数
    racks_per_pool: int = 3      # 每池架数

    # 通量相关
    J25: float = 18.0            # 25℃ 基准通量 LMH
    fouling_factor: float = 0.85
    SAD: float = 150.0           # m3/(m2·h) 比曝气密度

    # 抽吸节奏
    suction_on: float = 7.0      # min
    suction_off: float = 1.0     # min

    # 泵/风机参数
    pool_level: float = 3.5      # m 液位
    pipe_loss: float = 0.5       # m 管路损失
    permeate_pump_head: float = 6.5  # m
    permeate_pump_eff: float = 0.75
    return_ratio: float = 3.0
    return_pump_head: float = 0.5
    return_pump_eff: float = 0.70
    fan_efficiency: float = 0.90

    # 生物曝气（可选）
    enable_bio_blower: bool = False
    bio_air_water_ratio: float = 6.0
    bio_blower_eff: float = 0.70

    # 化学清洗参数
    ceb_freq: float = 1.0         # 次/周
    ceb_volume: float = 2.2       # L/m2
    ceb_naclo: float = 500.0      # mg/L NaClO
    ceb_citric: float = 2000.0    # mg/L 柠檬酸
    cip_freq: float = 4.0         # 次/年
    cip_volume: float = 2.2       # L/m2
    cip_naclo: float = 3000.0     # mg/L
    cip_citric: float = 5000.0    # mg/L


# ============================================================================
# 计算结果
# ============================================================================
@dataclass
class ProcessResult:
    model_name: str
    a_actual: float          # 实际膜面积 m2
    n_racks: int             # 总架数
    racks_per_pool: int
    j_avg: float             # 平均通量 LMH
    j_peak: float            # 峰值通量 LMH
    j_inst: float            # 瞬时通量 LMH
    j_design: float          # 设计通量 LMH
    duty_cycle: float        # 工作比
    total_air_nm3min: float  # 总供气量 Nm3/min
    air_water_ratio: float   # 气水比
    proj_area_per_rack: float
    blower_power: float      # kW
    pump_power: float        # kW
    pump_power_max: float
    return_pump_power: float
    bio_blower_power: float
    total_power: float
    unit_energy: float       # kWh/m3
    naclo_per_year: float    # t/a
    citric_per_year: float
    wash_water_per_year: float  # m3/a
    return_flow: float
    rack_param: Optional[RackParam] = None


# ============================================================================
# 核心计算
# ============================================================================
def water_viscosity(temp_c):
    """Andrade 方程计算水的黏度 (Pa·s)"""
    T = temp_c + 273.15
    A = 0.00179
    B = 570.58
    C = 137.02
    return A * math.pow(10, B / (T - C))


def compute_process(inp: ProcessInput) -> ProcessResult:
    """复刻 JS 中 ComputeProcess 的计算逻辑"""
    model = ALL_MODELS[inp.model_index]

    # 膜面积
    a_rack = model.sheet_area * inp.sheets_per_rack
    n_racks = inp.pools * inp.racks_per_pool
    a_actual = n_racks * a_rack

    # 流量
    qh_avg = inp.Q / 24.0
    qh_peak = inp.Q * inp.Kz / 24.0

    # 通量
    j_avg = (qh_avg * 1000) / a_actual
    j_peak = (qh_peak * 1000) / a_actual
    duty_cycle = inp.suction_on / (inp.suction_on + inp.suction_off)
    j_inst = j_avg / duty_cycle

    # 设计通量
    mu25 = water_viscosity(25)
    muT = water_viscosity(inp.T)
    f_T = mu25 / muT
    f_MLSS = math.exp(-0.0001 * (inp.MLSS - 8000))
    j_design = inp.J25 * f_T * f_MLSS * inp.fouling_factor

    # 膜架参数
    rp = get_rack_param(model.sheet_area, inp.sheets_per_rack)
    proj_area_per_rack = rp.proj_area_m2 if rp else 0.0

    # 曝气
    total_air_nm3h = proj_area_per_rack * inp.SAD * n_racks
    total_air_nm3min = total_air_nm3h / 60.0
    air_water_ratio = total_air_nm3h / qh_avg

    # 风机功率
    pressure_head = inp.pool_level + inp.pipe_loss
    fan_pressure_pa = pressure_head * 1000.0 * 9.81
    blower_power = (total_air_nm3h * fan_pressure_pa) / (3600.0 * 1000.0 * inp.fan_efficiency)

    # 产水泵功率
    pump_power_max = (qh_peak * inp.permeate_pump_head * 9.81) / (3600.0 * inp.permeate_pump_eff)
    pump_power = pump_power_max * duty_cycle

    # 回流泵功率
    return_flow = qh_avg * inp.return_ratio
    return_pump_power = (return_flow * inp.return_pump_head * 9.81) / (3600.0 * inp.return_pump_eff)

    # 生物曝气风机
    bio_blower_power = 0.0
    if inp.enable_bio_blower and inp.bio_blower_eff > 0:
        bio_air_flow = qh_avg * inp.bio_air_water_ratio
        bio_fan_pressure = inp.pool_level + 2.0
        bio_fan_pressure_pa = bio_fan_pressure * 1000 * 9.81
        bio_blower_power = (bio_air_flow * bio_fan_pressure_pa) / (3600.0 * 1000.0 * inp.bio_blower_eff)

    # 总功率与单位电耗
    total_power = blower_power + pump_power + return_pump_power + bio_blower_power
    unit_energy = total_power * 24.0 / inp.Q

    # 化学药剂
    ceb_freq_per_year = inp.ceb_freq * 52.0
    naclo_per_year = (a_actual * inp.ceb_volume * inp.ceb_naclo / 1e9) * ceb_freq_per_year + \
                     (a_actual * inp.cip_volume * inp.cip_naclo / 1e9) * inp.cip_freq
    citric_per_year = (a_actual * inp.ceb_volume * inp.ceb_citric / 1e9) * ceb_freq_per_year + \
                      (a_actual * inp.cip_volume * inp.cip_citric / 1e9) * inp.cip_freq
    wash_water_per_year = a_actual * (inp.ceb_volume * ceb_freq_per_year + inp.cip_volume * inp.cip_freq) / 1000.0

    return ProcessResult(
        model_name=model.name,
        a_actual=a_actual,
        n_racks=n_racks,
        racks_per_pool=inp.racks_per_pool,
        j_avg=j_avg,
        j_peak=j_peak,
        j_inst=j_inst,
        j_design=j_design,
        duty_cycle=duty_cycle,
        total_air_nm3min=total_air_nm3min,
        air_water_ratio=air_water_ratio,
        proj_area_per_rack=proj_area_per_rack,
        blower_power=blower_power,
        pump_power=pump_power,
        pump_power_max=pump_power_max,
        return_pump_power=return_pump_power,
        bio_blower_power=bio_blower_power,
        total_power=total_power,
        unit_energy=unit_energy,
        naclo_per_year=naclo_per_year,
        citric_per_year=citric_per_year,
        wash_water_per_year=wash_water_per_year,
        return_flow=return_flow,
        rack_param=rp,
    )
