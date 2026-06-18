#!/usr/bin/env python3
"""
三菱化学MBR膜设计工具 — Shiny for Python 重构版
优化版面布局，保持计算逻辑与内容完全一致
"""

import math
import io
import base64
from datetime import date, timedelta
from shiny import App, ui, render, reactive
import matplotlib
matplotlib.use("Agg")
import matplotlib.pyplot as plt
import matplotlib.patches as mpatches
from matplotlib.patches import FancyBboxPatch
import numpy as np
import plotly.graph_objects as go
import plotly.express as px

# =============================================================================
# DATA: AllModels (10 models, ported from original HTML)
# =============================================================================
ALL_MODELS = [
    {"Name": "56E0040SA", "SheetArea": 40, "PoreSize": 0.05, "MbrType": "UF", "RackCode": "56M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 2000},
    {"Name": "63E0040SA", "SheetArea": 40, "PoreSize": 0.1, "MbrType": "UF", "RackCode": "63M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 2000},
    {"Name": "62E0040SA", "SheetArea": 40, "PoreSize": 0.2, "MbrType": "MF", "RackCode": "62M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 2000},
    {"Name": "60E0025SA", "SheetArea": 25, "PoreSize": 0.4, "MbrType": "MF", "RackCode": "60M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 2000},
    {"Name": "55E0025SA", "SheetArea": 25, "PoreSize": 0.05, "MbrType": "UF", "RackCode": "55M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 2000},
    {"Name": "50E0025SA", "SheetArea": 25, "PoreSize": 0.4, "MbrType": "MF", "RackCode": "50M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 2000},
    {"Name": "55E0015SA", "SheetArea": 15, "PoreSize": 0.05, "MbrType": "UF", "RackCode": "55M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 1300},
    {"Name": "60E0015SA", "SheetArea": 15, "PoreSize": 0.4, "MbrType": "MF", "RackCode": "60M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 1300},
    {"Name": "50E0015SA", "SheetArea": 15, "PoreSize": 0.4, "MbrType": "MF", "RackCode": "50M", "FrameWidth": 30, "FrameHeight": 1250, "FrameLength": 1300},
    {"Name": "50E0006SA", "SheetArea": 6, "PoreSize": 0.4, "MbrType": "MF", "RackCode": "50M", "FrameWidth": 44, "FrameHeight": 620, "FrameLength": 1015},
]

# =============================================================================
# RACK PARAMETER TABLES
# =============================================================================
RACK_PARAMS_40_25 = [
    {"Sheets": s, "Width": 715 + (s-5)*45, "Length": 1524,
     "DryWeight": 350 + (s-5)*20, "WetWeight": 1050 + (s-5)*60,
     "AirFlow": 22.5 + (s-5)*2.7, "ProjArea": 0.4 + (s-5)*0.056}
    for s in range(5, 61)
]
# Fix exact values for continuity
for i, s in enumerate(range(5, 61)):
    RACK_PARAMS_40_25[i]["Width"] = [715,760,805,850,895,940,985,1030,1075,1120,1165,1210,1255,1300,1345,1390,1438,1486,1534,1582,1630,1678,1726,1774,1822,1870,1915,1960,2005,2050,2095,2140,2185,2230,2275,2320,2375,2430,2484,2539,2594,2649,2704,2758,2813,2868,2923,2978,3032,3087,3142,3197,3252,3306,3361,3416][i]
    RACK_PARAMS_40_25[i]["DryWeight"] = [350,370,390,410,430,450,470,490,510,530,550,570,590,610,630,650,670,690,710,730,750,770,790,810,830,850,870,890,910,930,950,970,990,1010,1030,1050,1080,1110,1140,1170,1200,1230,1260,1290,1320,1350,1380,1410,1440,1470,1500,1530,1560,1590,1620,1650][i]
    RACK_PARAMS_40_25[i]["WetWeight"] = [1050,1110,1170,1230,1290,1350,1410,1470,1530,1590,1650,1710,1770,1830,1890,1950,2010,2070,2130,2190,2250,2310,2370,2430,2490,2500,2560,2620,2680,2740,2800,2860,2920,2980,3040,3150,3240,3330,3420,3510,3600,3690,3780,3870,3960,4050,4140,4230,4320,4410,4500,4590,4680,4770,4860,4950][i]
    RACK_PARAMS_40_25[i]["AirFlow"] = [22.5,25.2,27.9,30.6,33.3,36,38.7,41.4,44.1,46.8,49.5,52.2,54.9,57.6,60.3,63,66.6,70.2,73.8,77.4,81,84.6,88.2,91.8,95.4,99,102.6,106.2,109.8,113.4,117,120.6,124.2,127.8,131.4,135,138.15,141.3,144.45,147.6,150.75,153.9,157.05,160.2,163.35,166.5,169.65,172.8,175.95,179.1,182.25,185.4,188.55,191.7,194.85,198][i]
    RACK_PARAMS_40_25[i]["ProjArea"] = [0.4,0.456,0.512,0.568,0.624,0.68,0.736,0.792,0.848,0.904,0.96,1.016,1.072,1.128,1.184,1.24,1.296,1.352,1.408,1.464,1.52,1.576,1.632,1.688,1.744,1.8,1.856,1.912,1.968,2.024,2.08,2.136,2.192,2.248,2.304,2.36,2.422,2.484,2.546,2.608,2.67,2.732,2.794,2.856,2.918,2.98,3.042,3.104,3.166,3.228,3.29,3.352,3.414,3.476,3.538,3.6][i]

RACK_PARAMS_15 = [
    {"Sheets": s, "Width": 715 + (s-5)*45, "Length": 1524,
     "DryWeight": 275 + (s-5)*15, "WetWeight": 500 + (s-5)*50,
     "AirFlow": 22.5 + (s-5)*2.7, "ProjArea": 0.4 + (s-5)*0.056}
    for s in range(5, 61)
]
for i, s in enumerate(range(5, 61)):
    RACK_PARAMS_15[i]["Width"] = [715,760,805,850,895,940,985,1030,1075,1120,1165,1210,1255,1300,1345,1390,1438,1486,1534,1582,1630,1678,1726,1774,1822,1870,1915,1960,2005,2050,2095,2140,2185,2230,2275,2320,2375,2430,2484,2539,2594,2649,2704,2758,2813,2868,2923,2978,3032,3087,3142,3197,3252,3306,3361,3416][i]
    RACK_PARAMS_15[i]["DryWeight"] = [275,290,305,320,335,350,365,380,395,410,425,440,455,470,485,500,520,540,560,580,600,620,640,660,680,700,715,730,745,760,775,790,805,820,835,850,1020,1040,1060,1080,1100,1120,1140,1160,1180,1200,1220,1240,1260,1280,1300,1320,1340,1360,1380,1400][i]
    RACK_PARAMS_15[i]["WetWeight"] = [500,550,600,650,700,750,800,850,900,950,1000,1050,1100,1150,1200,1250,1305,1360,1415,1470,1525,1580,1635,1690,1745,1800,1855,1910,1965,2020,2075,2130,2185,2240,2295,2350,2410,2470,2530,2590,2650,2710,2770,2830,2890,2950,3010,3070,3130,3190,3250,3310,3370,3430,3490,3550][i]
    RACK_PARAMS_15[i]["AirFlow"] = RACK_PARAMS_40_25[i]["AirFlow"]
    RACK_PARAMS_15[i]["ProjArea"] = RACK_PARAMS_40_25[i]["ProjArea"]

RACK_PARAMS_6 = [
    {"Sheets": s, "Width": 600 + (s-5)*44, "Length": 720,
     "DryWeight": 75 + (s-5)*7, "WetWeight": max(0, (s-5)*60),
     "AirFlow": 12.5 + (s-5)*1.5, "ProjArea": 0.16 + (s-5)*0.032}
    for s in range(5, 31)
]
for i, s in enumerate(range(5, 31)):
    RACK_PARAMS_6[i]["Width"] = [600,644,688,732,776,820,864,908,952,996,1040,1084,1128,1172,1216,1260,1304,1348,1392,1436,1480,1524,1568,1612,1656,1700][i]
    RACK_PARAMS_6[i]["WetWeight"] = [0,60,120,180,240,300,320,340,360,380,400,420,440,460,480,500,520,540,560,580,600,620,640,660,680,700][i]


# =============================================================================
# CORE CALCULATION ENGINE
# =============================================================================
def water_viscosity(temp_c):
    """Andrade equation: η = A × 10^(B/(T-C))"""
    T = temp_c + 273.15
    A, B, C = 0.00179, 570.58, 137.02
    return A * math.pow(10, B / (T - C))


def get_rack_param(sheet_area, sheets):
    if sheet_area in (40, 25):
        table = RACK_PARAMS_40_25
    elif sheet_area == 15:
        table = RACK_PARAMS_15
    elif sheet_area == 6:
        table = RACK_PARAMS_6
    else:
        return None
    for r in table:
        if r["Sheets"] == sheets:
            return r
    return None


def compute_process(inp):
    """Full MBR process calculation - ported exactly from original ComputeProcess"""
    # Input validation
    if inp["ModelIndex"] < 0 or inp["ModelIndex"] >= len(ALL_MODELS):
        raise ValueError(f"ModelIndex out of bounds")
    if inp["Pools"] <= 0 or inp["RacksPerPool"] <= 0:
        raise ValueError("Pools and RacksPerPool must be > 0")
    if inp["Q"] <= 0:
        raise ValueError("Q must be > 0")
    if inp["SuctionOn"] + inp["SuctionOff"] <= 0:
        raise ValueError("SuctionOn+SuctionOff must be > 0")
    if inp["FanEfficiency"] <= 0 or inp["FanEfficiency"] > 1.0:
        raise ValueError("FanEfficiency must be in (0, 1]")

    model = ALL_MODELS[inp["ModelIndex"]]

    # Membrane area
    A_rack = model["SheetArea"] * inp["SheetsPerRack"]
    n_racks = inp["Pools"] * inp["RacksPerPool"]
    A_actual = n_racks * A_rack

    # Flows
    Qh_avg = inp["Q"] / 24.0
    Qh_peak = inp["Q"] * inp["Kz"] / 24.0

    # Flux (LMH)
    J_avg = (Qh_avg * 1000) / A_actual
    J_peak = (Qh_peak * 1000) / A_actual

    duty_cycle = inp["SuctionOn"] / (inp["SuctionOn"] + inp["SuctionOff"])
    J_inst = J_avg / duty_cycle

    # Design flux with temperature/MLSS/fouling correction
    mu25 = water_viscosity(25)
    muT = water_viscosity(inp["T"])
    fT = mu25 / muT
    fMLSS = math.exp(-0.0001 * (inp["MLSS"] - 8000))
    JDesign = inp["J25"] * fT * fMLSS * inp["FoulingFactor"]

    # Rack parameters
    rp = get_rack_param(model["SheetArea"], inp["SheetsPerRack"])
    if not rp:
        raise ValueError(f"RackParam not found")
    proj_area_per_rack = rp["ProjArea"]

    # Aeration
    total_air_nm3h = proj_area_per_rack * inp["SAD"] * n_racks
    total_air_nm3min = total_air_nm3h / 60.0
    air_water_ratio = total_air_nm3h / Qh_avg

    # Blower power
    pressure_head = inp["PoolLevel"] + inp["PipeLoss"]
    fan_pressure_pa = pressure_head * 1000.0 * 9.81
    blower_power = (total_air_nm3h * fan_pressure_pa) / (3600.0 * 1000.0 * inp["FanEfficiency"])

    # Permeate pump power
    pump_power_max = (Qh_peak * inp["PermeatePumpHead"] * 9.81) / (3600.0 * inp["PermeatePumpEff"])
    pump_power = pump_power_max * duty_cycle

    # Return sludge pump power
    return_flow = Qh_avg * inp["ReturnRatio"]
    return_pump_power = (return_flow * inp["ReturnPumpHead"] * 9.81) / (3600.0 * inp["ReturnPumpEff"])

    # Biological aeration blower
    bio_blower_power = 0.0
    if inp["EnableBioBlower"] and inp["BioBlowerEff"] > 0:
        air_flow_nm3h = Qh_avg * inp["BioAirWaterRatio"]
        bio_fan_pressure = inp["PoolLevel"] + 2.0
        bio_fan_pressure_pa = bio_fan_pressure * 1000.0 * 9.81
        bio_blower_power = (air_flow_nm3h * bio_fan_pressure_pa) / (3600.0 * 1000.0 * inp["BioBlowerEff"])

    # Total power and unit energy
    total_power = blower_power + pump_power + return_pump_power + bio_blower_power
    unit_energy = total_power * 24.0 / inp["Q"]

    # Chemical consumption
    ceb_freq_per_year = inp["CebFreq"] * 52.0
    nacl_per_year = (A_actual * inp["CebVolume"] * inp["CebNaClO"] / 1e9) * ceb_freq_per_year + \
        (A_actual * inp["CipVolume"] * inp["CipNaClO"] / 1e9) * inp["CipFreq"]
    citric_per_year = (A_actual * inp["CebVolume"] * inp["CebCitric"] / 1e9) * ceb_freq_per_year + \
        (A_actual * inp["CipVolume"] * inp["CipCitric"] / 1e9) * inp["CipFreq"]
    wash_water_per_year = A_actual * (inp["CebVolume"] * ceb_freq_per_year + inp["CipVolume"] * inp["CipFreq"]) / 1000.0

    return {
        "ModelName": model["Name"],
        "AActual": A_actual,
        "NRacks": n_racks,
        "RacksPerPool": inp["RacksPerPool"],
        "JAvg": J_avg,
        "JPeak": J_peak,
        "JInst": J_inst,
        "JDesign": JDesign,
        "DutyCycle": duty_cycle,
        "TotalAirNm3min": total_air_nm3min,
        "AirWaterRatio": air_water_ratio,
        "ProjAreaPerRack": proj_area_per_rack,
        "BlowerPower": blower_power,
        "PumpPower": pump_power,
        "PumpPowerMax": pump_power_max,
        "ReturnPumpPower": return_pump_power,
        "BioBlowerPower": bio_blower_power,
        "TotalPower": total_power,
        "UnitEnergy": unit_energy,
        "NaClOPerYear": nacl_per_year,
        "CitricPerYear": citric_per_year,
        "WashWaterPerYear": wash_water_per_year,
        "ReturnFlow": return_flow,
        "FanPressurePa": fan_pressure_pa,
        "RackParam": rp,
    }


def flux_check_msg(j_peak, j_design):
    if j_design > 0 and j_peak > j_design:
        return False, f"峰值通量 {j_peak:.1f} LMH 超过设计通量 {j_design:.1f} LMH — 建议减小流量或增加膜面积"
    return True, "峰值通量在设计范围内"


def energy_check_msg(unit_energy):
    if unit_energy > 0.5:
        return False, "单位电耗超过 0.5 kWh/m³ — 建议优化工艺"
    return True, "单位电耗在合理范围内"


# =============================================================================
# OPERATIONS SIMULATION (ported from original runSimulation)
# =============================================================================
def run_simulation(ops):
    """Darcy-based TMP simulation"""
    sim_days = ops["simDays"]
    tmp_values = [ops["tmpInitial"]]
    base_tmp = ops["tmpInitial"]
    # Darcy factor
    darcy_factor = ops["J_avg"] / 3.6
    base_tmp_calc = ops["Rm"] * darcy_factor
    if base_tmp_calc < 2:
        base_tmp_calc = 2

    # Flux & MLSS factors
    flux_factor = (ops["J_avg"] / 20) ** 1.5
    mlss_factor = (ops["MLSS"] / 8000) ** 0.8
    temp_factor = (20 / ops["T"]) ** 0.5

    # Cake layer rate
    ceb_cycle_days = ops["cebFreqW"] * 7  # days between CEB
    cake_rate = ops["dRc"] * 0.1 * darcy_factor / ceb_cycle_days * flux_factor * mlss_factor
    # Irreversible rate
    irrev_rate = ops["rfRate"] * flux_factor * mlss_factor * temp_factor

    # Running state
    cake_accum = base_tmp * 0.05  # starting cake
    irrev_accum = 0.0
    ceb_count = 0
    cip_count = 0
    events = []
    ceb_days = []
    cip_days = []

    base_resist = []
    cake_resist = []
    irrev_resist = []

    for day in range(1, sim_days + 1):
        # Acceleration factors
        stage_factor = 1.0
        current_tmp = base_tmp + cake_accum + irrev_accum
        if current_tmp > 30:
            stage_factor = 2.5
        elif current_tmp > 15:
            stage_factor = 1.5

        # Accumulate cake (reversible) and irreversible
        cake_accum += cake_rate * stage_factor
        irrev_accum += irrev_rate * stage_factor

        current_tmp = base_tmp + cake_accum + irrev_accum

        # Check CIP first
        if current_tmp >= ops["cipTrigger"] and day > 7:
            cip_count += 1
            cip_days.append(day)
            events.append((day, f"CIP #{cip_count} @ TMP={current_tmp:.1f}kPa"))
            # CIP removes cake and partially irreversible
            cake_accum = 0
            irrev_accum *= ops["cipResidual"]
            irrev_accum = irrev_accum * (1 - 0.70 * ops["cipRecovery"] / 100)
            cip_count_real = cip_count
        elif current_tmp >= ops["cebTrigger"] and day > 3:
            ceb_count += 1
            ceb_days.append(day)
            events.append((day, f"CEB #{ceb_count} @ TMP={current_tmp:.1f}kPa"))
            # CEB clears cake
            removal = ops["cebRecovery"] / 100 * max(0.3, 1 - ops["bwResidual"] * 15)
            cake_accum = cake_accum * (1 - removal)
            cip_count_real = cip_count

        current_tmp = base_tmp + cake_accum + irrev_accum
        tmp_values.append(current_tmp)
        base_resist.append(base_tmp)
        cake_resist.append(cake_accum)
        irrev_resist.append(irrev_accum)

    # Membrane life estimation
    if len(tmp_values) > 30:
        recent = tmp_values[-30:]
        delta = recent[-1] - recent[0]
        if delta > 0:
            rate_per_day = delta / 30
            days_to_stop = (ops["stopTrigger"] - tmp_values[-1]) / rate_per_day
            membrane_life = (sim_days + days_to_stop) / 365
        else:
            membrane_life = 10
    else:
        membrane_life = 10

    annual_decay = (tmp_values[-1] - tmp_values[0]) / sim_days * 365 if sim_days > 0 else 0

    # Cost
    run_cost = ceb_count * 500 + cip_count * 5000

    return {
        "tmpValues": tmp_values,
        "baseResist": base_resist,
        "cakeResist": cake_resist,
        "irrevResist": irrev_resist,
        "cebCount": ceb_count,
        "cipCount": cip_count,
        "cebDays": ceb_days,
        "cipDays": cip_days,
        "events": events,
        "finalTmp": tmp_values[-1],
        "membraneLife": membrane_life,
        "annualDecay": annual_decay,
        "runCost": run_cost,
        "simDays": sim_days,
    }


# =============================================================================
# UTILITY: Tank layout image (matplotlib)
# =============================================================================
def draw_tank_layout_image(input_data, result, comp_spacing, wall_spacing, pool_wall_thick):
    rp = result["RackParam"]
    comp_long = rp["Length"]  # drawn as width
    comp_short = rp["Width"]  # drawn as height
    n_comp = input_data["RacksPerPool"]
    n_pools = input_data["Pools"]

    pool_inner_w = (n_comp - 1) * comp_spacing + comp_long + 2 * wall_spacing if n_comp > 1 else comp_long + 2 * wall_spacing
    pool_inner_h = comp_short + 2 * wall_spacing
    pool_outer_w = pool_inner_w + 2 * pool_wall_thick
    pool_outer_h = pool_inner_h + 2 * pool_wall_thick

    pools_per_row = min(n_pools, max(1, 3))
    num_rows = max(1, (n_pools + pools_per_row - 1) // pools_per_row)

    fig, ax = plt.subplots(figsize=(12, max(4, num_rows * 3.5)))
    ax.set_aspect('equal')
    ax.set_facecolor('#fefce8')

    colors = ['#dbeafe', '#d1fae5', '#fef3c7', '#fce7f3', '#e0e7ff', '#ede9fe']
    rack_colors = ['#3b82f6', '#10b981', '#f59e0b', '#ec4899', '#6366f1', '#a855f7']

    for p in range(n_pools):
        row = p // pools_per_row
        col = p % pools_per_row
        px = col * (pool_outer_w + 300)
        py = row * (pool_outer_h + 300)

        # Pool interior
        rect = FancyBboxPatch((px + pool_wall_thick, py + pool_wall_thick),
                              pool_inner_w, pool_inner_h,
                              boxstyle="round,pad=0", edgecolor='#93c5fd',
                              facecolor=colors[p % len(colors)], linewidth=1.5)
        ax.add_patch(rect)

        # Pool walls
        outer_rect = FancyBboxPatch((px, py), pool_outer_w, pool_outer_h,
                                    boxstyle="round,pad=0", edgecolor='#475569',
                                    facecolor='none', linewidth=2.5)
        ax.add_patch(outer_rect)

        # Pool label
        ax.text(px + pool_outer_w / 2, py - 80, f"膜池 #{p+1}",
                ha='center', va='bottom', fontsize=11, fontweight='bold', color='#1e40af')

        # Racks
        for i in range(n_comp):
            cx = px + pool_wall_thick + wall_spacing + i * comp_spacing
            cy = py + pool_wall_thick + wall_spacing
            rect = FancyBboxPatch((cx, cy), comp_long, comp_short,
                                  boxstyle="round,pad=0", edgecolor='#1e3a8a',
                                  facecolor=rack_colors[p % len(rack_colors)], linewidth=1.5, alpha=0.85)
            ax.add_patch(rect)
            ax.text(cx + comp_long / 2, cy + comp_short / 2, str(i + 1),
                    ha='center', va='center', fontsize=9, fontweight='bold', color='white')

    ax.set_xlim(-100, pools_per_row * (pool_outer_w + 300) + 100)
    ax.set_ylim(-200, num_rows * (pool_outer_h + 300) + 100)
    ax.invert_yaxis()
    ax.axis('off')
    ax.set_title(f"膜池平面布置图 — 共 {n_pools} 格 × {n_comp} 台/池", fontsize=13, fontweight='bold', color='#1e40af', pad=10)

    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight', facecolor='#fefce8')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64, pool_inner_w, pool_inner_h, pool_outer_w, pool_outer_h


# =============================================================================
# UTILITY: Temperature correction curves (matplotlib)
# =============================================================================
def draw_temp_correction_curves():
    fig, (ax1, ax2) = plt.subplots(1, 2, figsize=(10, 4.5))

    temps = np.linspace(10, 35, 26)
    viscosities = np.array([water_viscosity(t) for t in temps])
    mu25 = water_viscosity(25)

    # Flux ∝ 1/μ (TMP constant)
    rel_flux = mu25 / viscosities
    ax1.plot(temps, rel_flux, 'o-', color='#0891b2', linewidth=2.5, markersize=5)
    ax1.set_title("TMP不变时，通量随温度变化", fontsize=12, fontweight='bold', color='#0891b2')
    ax1.set_xlabel("温度 (°C)")
    ax1.set_ylabel("相对通量 J/J₂₅")
    ax1.grid(True, alpha=0.3)
    ax1.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax1.axvline(x=25, color='gray', linestyle='--', alpha=0.5)

    # TMP ∝ μ (flux constant)
    rel_tmp = viscosities / mu25
    ax2.plot(temps, rel_tmp, 's-', color='#ea580c', linewidth=2.5, markersize=5)
    ax2.set_title("通量不变时，TMP随温度变化", fontsize=12, fontweight='bold', color='#ea580c')
    ax2.set_xlabel("温度 (°C)")
    ax2.set_ylabel("相对TMP TMP/TMP₂₅")
    ax2.grid(True, alpha=0.3)
    ax2.axhline(y=1.0, color='gray', linestyle='--', alpha=0.5)
    ax2.axvline(x=25, color='gray', linestyle='--', alpha=0.5)

    fig.tight_layout()
    buf = io.BytesIO()
    fig.savefig(buf, format='png', dpi=100, bbox_inches='tight')
    buf.seek(0)
    img_base64 = base64.b64encode(buf.read()).decode('utf-8')
    plt.close(fig)
    return img_base64


# =============================================================================
# UTILITY: Plotly charts for ops tab
# =============================================================================
def create_tmp_chart(sim_result):
    days = list(range(len(sim_result["tmpValues"])))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=sim_result["tmpValues"], mode='lines',
                             name='TMP', line=dict(color='#2563eb', width=2)))
    fig.add_trace(go.Scatter(x=[0, days[-1]], y=[sim_result.get("cebTrigger", 25)]*2,
                             mode='lines', name='CEB触发', line=dict(color='#f59e0b', dash='dash', width=1.5)))
    fig.add_trace(go.Scatter(x=[0, days[-1]], y=[sim_result.get("cipTrigger", 35)]*2,
                             mode='lines', name='CIP触发', line=dict(color='#dc2626', dash='dash', width=1.5)))
    fig.add_trace(go.Scatter(x=[0, days[-1]], y=[sim_result.get("stopTrigger", 45)]*2,
                             mode='lines', name='停机报警', line=dict(color='#7c3aed', dash='dot', width=1.5)))

    fig.update_layout(
        title="TMP 趋势预测", xaxis_title="天数", yaxis_title="TMP (kPa)",
        template="plotly_white", height=350, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


def create_fouling_chart(sim_result):
    days = list(range(1, len(sim_result["baseResist"]) + 1))
    fig = go.Figure()
    fig.add_trace(go.Scatter(x=days, y=sim_result["baseResist"], mode='lines',
                             name='基础阻力 Rm', stackgroup='one',
                             line=dict(color='#3b82f6', width=1.5),
                             fillcolor='rgba(59,130,246,0.2)'))
    fig.add_trace(go.Scatter(x=days, y=sim_result["cakeResist"], mode='lines',
                             name='滤饼层 Rc', stackgroup='one',
                             line=dict(color='#f59e0b', width=1.5),
                             fillcolor='rgba(245,158,11,0.2)'))
    fig.add_trace(go.Scatter(x=days, y=sim_result["irrevResist"], mode='lines',
                             name='不可逆 Rf', stackgroup='one',
                             line=dict(color='#dc2626', width=1.5),
                             fillcolor='rgba(220,38,38,0.2)'))

    fig.update_layout(
        title="膜污染阻力累积分析", xaxis_title="天数", yaxis_title="TMP (kPa)",
        template="plotly_white", height=300, margin=dict(l=10, r=10, t=40, b=10),
        legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
    )
    return fig


# =============================================================================
# SHINY APP UI
# =============================================================================
app_ui = ui.page_fluid(
    ui.tags.head(
        ui.tags.meta(charset="UTF-8"),
        ui.tags.meta(name="viewport", content="width=device-width, initial-scale=1.0"),
        ui.tags.title("三菱化学MBR膜设计工具"),
        ui.tags.style("""
            :root {
                --primary: #1d4ed8;
                --primary-light: #dbeafe;
                --bg: #f0f4f8;
                --card-bg: #ffffff;
                --border: #e2e8f0;
                --text: #0f172a;
                --text-secondary: #334155;
                --text-muted: #64748b;
                --radius: 12px;
                --shadow: 0 1px 3px rgba(0,0,0,0.06), 0 1px 2px rgba(0,0,0,0.04);
            }
            body { background: var(--bg); font-family: -apple-system, BlinkMacSystemFont, "Segoe UI", Roboto, "Noto Sans SC", sans-serif; }
            .nav-brand { display: flex; align-items: center; gap: 10px; padding: 12px 20px; background: linear-gradient(135deg, #1e3a8a, #1d4ed8); color: white; border-radius: 0 0 12px 12px; }
            .nav-brand .brand-icon { width: 36px; height: 36px; background: rgba(255,255,255,0.2); border-radius: 10px; display: flex; align-items: center; justify-content: center; font-size: 18px; }
            .nav-brand h1 { font-size: 16px; font-weight: 700; margin: 0; }
            .card { background: var(--card-bg); border-radius: var(--radius); box-shadow: var(--shadow); border: 1px solid var(--border); padding: 20px; margin-bottom: 16px; }
            .card-header { font-size: 14px; font-weight: 700; color: var(--text); margin-bottom: 16px; display: flex; align-items: center; gap: 8px; }
            .card-header .step { width: 28px; height: 28px; background: linear-gradient(135deg, #1d4ed8, #3b82f6); color: white; border-radius: 8px; display: flex; align-items: center; justify-content: center; font-size: 12px; font-weight: 700; }
            .kpi-card { background: white; border-radius: var(--radius); padding: 16px; border: 1px solid var(--border); text-align: center; }
            .kpi-card .kpi-label { font-size: 10px; font-weight: 700; color: var(--text-muted); text-transform: uppercase; letter-spacing: 0.05em; }
            .kpi-card .kpi-value { font-size: 24px; font-weight: 800; color: var(--primary); margin: 4px 0; }
            .kpi-card .kpi-sub { font-size: 10px; color: var(--text-muted); }
            .alert { padding: 10px 14px; border-radius: 8px; font-size: 13px; margin: 4px 0; }
            .alert-ok { background: #ecfdf5; color: #065f46; border-left: 4px solid #059669; }
            .alert-warn { background: #fffbeb; color: #92400e; border-left: 4px solid #d97706; }
            .alert-danger { background: #fef2f2; color: #991b1b; border-left: 4px solid #dc2626; }
            .alert-info { background: #eff6ff; color: #1e40af; border-left: 4px solid #2563eb; }
            .info-bar { font-size: 12px; color: var(--text-muted); background: #f8fafc; padding: 8px 12px; border-radius: 8px; border: 1px solid #f1f5f9; margin-top: 8px; }
            .data-table { width: 100%; border-collapse: collapse; font-size: 12px; }
            .data-table th { background: #f8fafc; padding: 8px 10px; text-align: left; font-weight: 600; color: var(--text-muted); font-size: 11px; text-transform: uppercase; border-bottom: 2px solid var(--border); }
            .data-table td { padding: 8px 10px; border-bottom: 1px solid #f1f5f9; }
            .data-table tr:hover td { background: #f8fafc; }
            .quickref-table { width: 100%; border-collapse: collapse; font-size: 13px; }
            .quickref-table th { background: #1d4ed8; color: white; padding: 8px 10px; text-align: left; font-weight: 600; }
            .quickref-table td { padding: 6px 10px; border-bottom: 1px solid #e2e8f0; }
            .quickref-table tr:nth-child(even) td { background: #f8fafc; }
            .config-grid { display: grid; grid-template-columns: repeat(auto-fit, minmax(140px, 1fr)); gap: 8px; }
            .config-item { background: #f8fafc; padding: 10px; border-radius: 8px; text-align: center; border: 1px solid #f1f5f9; }
            .config-item .label { font-size: 10px; color: var(--text-muted); }
            .config-item .value { font-size: 14px; font-weight: 700; color: var(--primary); margin-top: 2px; }
            .section-title { font-size: 18px; font-weight: 700; color: #1d4ed8; border-bottom: 2px solid #1d4ed8; padding-bottom: 8px; margin: 24px 0 12px; }
            .sub-title { font-size: 15px; font-weight: 700; color: #334155; margin: 16px 0 8px; }
            .nav-tabs { display: flex; gap: 2px; background: white; border-bottom: 1px solid var(--border); padding: 0 20px; }
            .nav-tabs .nav-link { padding: 12px 24px; font-size: 13px; font-weight: 500; color: var(--text-muted); border: none; border-bottom: 3px solid transparent; background: transparent; cursor: pointer; transition: all 0.2s; }
            .nav-tabs .nav-link:hover { color: var(--primary); background: var(--primary-light); }
            .nav-tabs .nav-link.active { color: var(--primary); font-weight: 600; border-bottom-color: var(--primary); background: var(--primary-light); }
            .btn-primary { background: linear-gradient(135deg, #1d4ed8, #2563eb); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; }
            .btn-primary:hover { box-shadow: 0 4px 12px rgba(29,78,216,0.35); }
            .btn-success { background: linear-gradient(135deg, #059669, #10b981); color: white; border: none; padding: 10px 20px; border-radius: 8px; font-weight: 600; cursor: pointer; font-size: 14px; }
            .btn-sm { padding: 6px 12px; font-size: 12px; }
            .form-label { font-size: 11px; font-weight: 600; color: var(--text-secondary); margin-bottom: 4px; display: block; }
            input.form-control, select.form-control { width: 100%; padding: 8px 10px; font-size: 13px; border: 1.5px solid var(--border); border-radius: 8px; }
            input.form-control:focus, select.form-control:focus { outline: none; border-color: #93c5fd; box-shadow: 0 0 0 3px rgba(59,130,246,0.12); }
            .form-badge { display: inline-block; padding: 2px 6px; font-size: 10px; font-weight: 600; border-radius: 4px; background: var(--primary-light); color: var(--primary); }
            .result-cell { background: #f8fafc; padding: 12px; border-radius: 8px; border: 1px solid #f1f5f9; }
            .result-cell h4 { font-size: 11px; font-weight: 700; color: var(--text-secondary); margin: 0 0 8px; }
            .result-table { width: 100%; font-size: 12px; }
            .result-table td { padding: 4px 0; }
            .result-table td:first-child { color: var(--text-muted); }
            .result-table td:last-child { text-align: right; font-weight: 600; }
            .chem-card { text-align: center; padding: 16px; border-radius: 8px; }
            .chem-card .label { font-size: 10px; font-weight: 600; text-transform: uppercase; }
            .chem-card .value { font-size: 24px; font-weight: 800; margin-top: 4px; }
            .chem-card .unit { font-size: 10px; color: #64748b; }
        """),
    ),
    # Nav bar
    ui.tags.div(
        ui.tags.div(
            ui.tags.div("🔬", class_="brand-icon"),
            ui.tags.h1("三菱化学MBR膜设计工具"),
            class_="nav-brand",
        ),
    ),
    # Tab navigation
    ui.tags.div(
        ui.navset_tab(
            ui.nav_panel("工艺计算", ui.tags.div(id="tab-process")),
            ui.nav_panel("速查表", ui.tags.div(id="tab-quickref")),
            ui.nav_panel("运行评估", ui.tags.div(id="tab-ops")),
            id="mainTabs",
            selected="工艺计算",
        ),
        class_="nav-tabs",
    ),
    # Main content area
    ui.tags.div(
        ui.output_ui("main_content"),
        style="padding: 20px; max-width: 1480px; margin: 0 auto;",
    ),
    ui.tags.div(style="height: 40px;"),
)


# =============================================================================
# SHINY SERVER LOGIC
# =============================================================================
def server(input, output, session):
    # Reactive values
    calc_result = reactive.Value(None)
    calc_input = reactive.Value(None)
    calc_raw_input = reactive.Value(None)
    selected_model = reactive.Value(ALL_MODELS[1])  # default 63E0040SA
    selected_sheet_area = reactive.Value(40)
    selected_sheets = reactive.Value(42)
    ops_sim_result = reactive.Value(None)

    # ========================================================================
    # MAIN CONTENT RENDERER (based on active tab)
    # ========================================================================
    @render.ui
    def main_content():
        tab = input.mainTabs()
        if tab == "工艺计算":
            return render_process_tab()
        elif tab == "速查表":
            return render_quickref_tab()
        elif tab == "运行评估":
            return render_ops_tab()
        return ui.tags.p("请选择标签页")

    # ========================================================================
    # PROCESS TAB
    # ========================================================================
    def render_process_tab():
        return ui.tags.div(
            ui.tags.div(
                # LEFT PANEL
                ui.tags.div(
                    # Project Info
                    ui.tags.div(
                        ui.tags.div(
                            ui.tags.span("1", class_="step"),
                            "项目信息",
                            class_="card-header",
                        ),
                        ui.tags.div(
                            ui.tags.div("基本信息", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                            ui.tags.div(
                                ui.tags.div(ui.tags.label("项目名称", class_="form-label"), ui.input_text("projectName", "", placeholder="请输入项目名称")),
                                ui.tags.div(ui.tags.label("委托单位", class_="form-label"), ui.input_text("clientUnit", "", placeholder="请输入委托单位")),
                                ui.tags.div(ui.tags.label("设计单位", class_="form-label"), ui.input_text("designUnit", "", placeholder="请输入设计单位")),
                                ui.tags.div(ui.tags.label("设计人", class_="form-label"), ui.input_text("designerName", "", placeholder="请输入设计人")),
                                ui.tags.div(ui.tags.label("设计阶段", class_="form-label"), ui.input_select("designStage", {"preliminary": "初步设计", "construction": "施工图设计", "feasibility": "可研阶段", "tender": "技术投标"}, label="")),
                                ui.tags.div(ui.tags.label("设计日期", class_="form-label"), ui.input_date("designDate", value=date.today().isoformat())),
                                style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                            ),
                        ),
                        class_="card",
                    ),
                    # Feed Water
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("2", class_="step"), "进水水质与水量", class_="card-header"),
                        ui.tags.div(
                            ui.tags.div("水量参数", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                            ui.tags.div(
                                ui.tags.div(ui.tags.label("设计水量 Q (m³/d)", class_="form-label"), ui.input_numeric("flowRate", 5000, "", min=1)),
                                ui.tags.div(ui.tags.label("峰值系数 Kz", class_="form-label"), ui.input_numeric("peakFactor", 1.3, "", min=1, max=3, step=0.1)),
                                style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                            ),
                            ui.tags.div(
                                ui.output_text("peak_flow_display"),
                                ui.output_text("avg_hourly_display"),
                                class_="info-bar",
                                style="display:flex;justify-content:space-between;",
                            ),
                        ),
                        ui.tags.div(
                            ui.tags.div("进水水质 (mg/L)", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                            ui.tags.div(
                                ui.tags.div(ui.tags.label("COD", class_="form-label"), ui.input_numeric("codIn", 400, "", min=0)),
                                ui.tags.div(ui.tags.label("BOD₅", class_="form-label"), ui.input_numeric("bodIn", 200, "", min=0)),
                                ui.tags.div(ui.tags.label("NH₃-N", class_="form-label"), ui.input_numeric("nh3nIn", 35, "", min=0)),
                                ui.tags.div(ui.tags.label("SS", class_="form-label"), ui.input_numeric("ssIn", 150, "", min=0)),
                                ui.tags.div(ui.tags.label("TN", class_="form-label"), ui.input_numeric("tnIn", 50, "", min=0)),
                                ui.tags.div(ui.tags.label("TP", class_="form-label"), ui.input_numeric("tpIn", 5, "", min=0)),
                                ui.tags.div(ui.tags.label("pH", class_="form-label"), ui.input_numeric("phValue", 7.2, "", min=0, max=14, step=0.1)),
                                ui.tags.div(ui.tags.label("水温 T (°C)", class_="form-label"), ui.input_numeric("waterTemp", 20, "", min=0, max=50)),
                                ui.tags.div(ui.tags.label("MLSS (mg/L)", class_="form-label"), ui.input_numeric("mlssIn", 8000, "", min=0)),
                                style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;",
                            ),
                        ),
                        class_="card",
                    ),
                    # Effluent Standard
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("3", class_="step"), "出水标准", class_="card-header"),
                        ui.tags.div(
                            ui.tags.div("排放标准", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                            ui.input_select("effluentStandard", {"1A": "GB 18918-2002 一级A", "1B": "GB 18918-2002 一级B", "SW4": "GB 3838-2002 地表水IV类", "reuse": "城市杂用水回用标准", "custom": "自定义"}, selected="1A", label=""),
                            ui.tags.div(
                                ui.tags.div(ui.tags.label("COD (mg/L)", class_="form-label"), ui.input_numeric("codOut", 30, "", min=0)),
                                ui.tags.div(ui.tags.label("NH₃-N (mg/L)", class_="form-label"), ui.input_numeric("nh3nOut", 1.5, "", min=0, step=0.1)),
                                ui.tags.div(ui.tags.label("TN (mg/L)", class_="form-label"), ui.input_numeric("tnOut", 15, "", min=0)),
                                ui.tags.div(ui.tags.label("SS (mg/L)", class_="form-label"), ui.input_numeric("ssOut", 5, "", min=0)),
                                style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr;gap:12px;margin-top:12px;",
                            ),
                        ),
                        class_="card",
                    ),
                    # Membrane Configuration
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("4", class_="step"), "膜组件配置", class_="card-header"),
                        ui.tags.div(
                            ui.tags.div("膜型号选择", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                            ui.input_select("membraneModel",
                                {str(i): f"{m['Name']} - {m['MbrType']} {m['PoreSize']}μm {m['SheetArea']}m² PVDF" for i, m in enumerate(ALL_MODELS)},
                                selected="1", label=""),
                            ui.output_ui("model_spec_info"),
                            ui.tags.div(
                                ui.tags.div(ui.tags.label("每台膜片数", class_="form-label"), ui.output_ui("sheet_options")),
                                ui.tags.div(ui.tags.label("膜池数 (格)", class_="form-label"), ui.input_numeric("membranePools", 2, "", min=1)),
                                ui.tags.div(ui.tags.label("每池台数", class_="form-label"), ui.input_numeric("membraneSeries", 3, "", min=1)),
                                style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:12px;",
                            ),
                            ui.tags.div(
                                ui.output_ui("rack_info_grid"),
                                style="margin-top:12px;",
                            ),
                            ui.tags.div(
                                ui.tags.span("完整型号: ", style="color:#64748b;"),
                                ui.output_text("full_model_display", inline=True),
                                " | 投影面积: ",
                                ui.output_text("proj_area_display", inline=True),
                                " m²/台",
                                class_="info-bar",
                            ),
                        ),
                        ui.tags.div(
                            ui.tags.div("通量参数", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                            ui.tags.div(
                                ui.tags.div(ui.tags.label("设计平均通量 (LMH)", class_="form-label"), ui.output_text("design_flux_display")),
                                ui.tags.div(ui.tags.label("峰值通量 (LMH)", class_="form-label"), ui.output_text("peak_flux_display")),
                                style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                            ),
                            ui.tags.div(
                                "当前平均通量：",
                                ui.output_text("actual_avg_flux", inline=True),
                                " LMH",
                                class_="info-bar",
                                style="display:flex;justify-content:space-between;",
                            ),
                            ui.output_ui("flux_alert"),
                        ),
                        class_="card",
                    ),
                    # Advanced Settings
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("5", class_="step"), "高级设置", class_="card-header"),
                        ui.input_checkbox("showAdvanced", "展开高级设置", False),
                        ui.output_ui("advanced_settings"),
                        class_="card",
                    ),
                    # Action Buttons
                    ui.tags.div(
                        ui.tags.button("计算", id="btnCalculate", class_="btn-primary", style="margin-right:12px;"),
                        ui.tags.button("重置", id="btnReset", class_="btn-success", style="margin-right:12px;"),
                        style="display:flex;align-items:center;margin-bottom:16px;",
                    ),
                    style="width:560px;flex-shrink:0;",
                ),
                # RIGHT PANEL - Outputs
                ui.tags.div(
                    ui.output_ui("process_output"),
                    style="flex:1;min-width:0;",
                ),
                style="display:flex;gap:24px;flex-wrap:wrap;",
            ),
        )

    # ========================================================================
    # SHEET OPTIONS DROPDOWN
    # ========================================================================
    @render.ui
    def sheet_options():
        m = selected_model()
        area = m["SheetArea"]
        rng = range(5, 31) if area == 6 else range(5, 61)
        choices = {str(s): f"{s} 片" for s in rng}
        sel = str(min(max(selected_sheets(), rng.start), rng.stop - 1))
        return ui.input_select("membraneSheets", choices, selected=sel, label="")

    # ========================================================================
    # MODEL SPEC INFO
    # ========================================================================
    @render.ui
    def model_spec_info():
        m = selected_model()
        return ui.tags.div(
            ui.tags.div(
                ui.tags.div(ui.tags.span("单片面积", style="color:#64748b;"), ui.tags.br(), ui.tags.strong(f"{m['SheetArea']} m²")),
                ui.tags.div(ui.tags.span("孔径", style="color:#64748b;"), ui.tags.br(), ui.tags.strong(f"{m['PoreSize']} μm")),
                ui.tags.div(ui.tags.span("膜类型", style="color:#64748b;"), ui.tags.br(), ui.tags.strong(m["MbrType"])),
                ui.tags.div(ui.tags.span("对应组件", style="color:#64748b;"), ui.tags.br(), ui.tags.strong(m["RackCode"])),
                ui.tags.div(ui.tags.span("尺寸 (mm)", style="color:#64748b;"), ui.tags.br(), ui.tags.strong(f"{m['FrameWidth']}×{m['FrameHeight']}×{m['FrameLength']}")),
                style="display:grid;grid-template-columns:1fr 1fr 1fr 1fr 1fr;gap:8px;color:#334155;",
            ),
            style="background:#f0f4ff;border:1px solid #dbeafe;border-radius:8px;padding:12px;margin-top:8px;font-size:13px;",
        )

    # ========================================================================
    # RACK INFO GRID
    # ========================================================================
    @render.ui
    def rack_info_grid():
        m = selected_model()
        s = selected_sheets()
        rp = get_rack_param(m["SheetArea"], s)
        if rp:
            return ui.tags.div(
                ui.tags.div(ui.tags.div("组件宽度", class_="label"), ui.tags.div(f"{rp['Width']} mm", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("组件长度", class_="label"), ui.tags.div(f"{rp['Length']} mm", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("干重", class_="label"), ui.tags.div(f"{rp['DryWeight']} kg", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("湿重", class_="label"), ui.tags.div(f"{rp['WetWeight']} kg", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("曝气管清洗", class_="label"), ui.tags.div(f"{rp['AirFlow']} L/min", class_="value"), class_="config-item"),
                class_="config-grid",
            )
        return ui.tags.p("请选择有效的膜片数", style="color:#94a3b8;font-size:12px;")

    # ========================================================================
    # FLOW DISPLAYS
    # ========================================================================
    @render.text
    def peak_flow_display():
        Q = input.flowRate() or 5000
        Kz = input.peakFactor() or 1.3
        return f"峰值水量: {Q * Kz:,.0f} m³/d"

    @render.text
    def avg_hourly_display():
        Q = input.flowRate() or 5000
        return f"平均时流量: {Q / 24:.1f} m³/h"

    @render.text
    def full_model_display():
        m = selected_model()
        s = selected_sheets()
        prefix = m["Name"][:2]
        return f"{prefix}M{m['SheetArea'] * s}FP"

    @render.text
    def proj_area_display():
        m = selected_model()
        s = selected_sheets()
        rp = get_rack_param(m["SheetArea"], s)
        return f"{rp['ProjArea']:.2f}" if rp else "—"

    @render.text
    def design_flux_display():
        r = calc_result()
        return f"{r['JAvg']:.1f}" if r else "—"

    @render.text
    def peak_flux_display():
        r = calc_result()
        return f"{r['JPeak']:.1f}" if r else "—"

    @render.text
    def actual_avg_flux():
        r = calc_result()
        return f"{r['JAvg']:.1f}" if r else "—"

    @render.ui
    def flux_alert():
        r = calc_result()
        if not r:
            return ""
        if r["JPeak"] > 30:
            return ui.tags.div("峰值通量超过30LMH，请增加膜池数量或每池台数，或降低峰值系数", class_="alert alert-danger")
        elif r["JAvg"] > 25:
            return ui.tags.div("平均通量偏高(>25LMH)，污染风险增加", class_="alert alert-warn")
        return ui.tags.div("通量校核通过，配置合理", class_="alert alert-ok")

    # ========================================================================
    # ADVANCED SETTINGS
    # ========================================================================
    @render.ui
    def advanced_settings():
        if not input.showAdvanced():
            return ""
        return ui.tags.div(
            # Design params
            ui.tags.div(
                ui.tags.div("设计参数", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                ui.tags.div(
                    ui.tags.div(ui.tags.label("设计通量 J₂₅ (LMH)", class_="form-label"), ui.input_numeric("j25", 18, "", min=5, max=40, step=0.5)),
                    ui.tags.div(ui.tags.label("污染因子", class_="form-label"), ui.input_numeric("foulingFactor", 0.85, "", min=0.5, max=1, step=0.05)),
                    ui.tags.div(ui.tags.label("曝气强度 (Nm³/m²·h)", class_="form-label"), ui.input_numeric("sadValue", 150, "", min=100, max=150, step=5)),
                    style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                ),
            ),
            # Suction cycle
            ui.tags.div(
                ui.tags.div("抽吸周期", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                ui.tags.div(
                    ui.tags.div(ui.tags.label("抽吸时间 (min)", class_="form-label"), ui.input_numeric("suctionOnTime", 7, "", min=1, max=7, step=0.5)),
                    ui.tags.div(ui.tags.label("停抽时间 (min)", class_="form-label"), ui.input_numeric("suctionOffTime", 1, "", min=1, max=10, step=0.5)),
                    style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                ),
                ui.tags.div(ui.output_text("duty_cycle_display"), class_="info-bar"),
            ),
            # Hydraulics
            ui.tags.div(
                ui.tags.div("液位与泵参数", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                ui.tags.div(
                    ui.tags.div(ui.tags.label("膜池有效液位 (m)", class_="form-label"), ui.input_numeric("poolLevel", 3.5, "", step=0.5, min=0)),
                    ui.tags.div(ui.tags.label("管路阻力损失 (m H₂O)", class_="form-label"), ui.input_numeric("pipeLoss", 0.5, "", step=0.2, min=0)),
                    style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                ),
                ui.tags.div(
                    ui.tags.div(ui.tags.label("产水泵扬程 (m)", class_="form-label"), ui.input_numeric("permeatePumpHead", 6.5, "", step=0.5, min=0)),
                    ui.tags.div(ui.tags.label("产水泵效率 (%)", class_="form-label"), ui.input_numeric("permeatePumpEff", 75, "", step=1, min=50, max=95)),
                    style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px;",
                ),
                ui.tags.div(
                    ui.tags.div(ui.tags.label("回流比 R", class_="form-label"), ui.input_numeric("returnRatio", 3, "", step=0.5, min=0)),
                    ui.tags.div(ui.tags.label("回流泵扬程 (m)", class_="form-label"), ui.input_numeric("returnPumpHead", 0.5, "", step=0.1, min=0)),
                    ui.tags.div(ui.tags.label("回流泵效率 (%)", class_="form-label"), ui.input_numeric("returnPumpEff", 70, "", step=1, min=50, max=95)),
                    style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;margin-top:8px;",
                ),
            ),
            # Aeration
            ui.tags.div(
                ui.tags.div("曝气系统", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                ui.tags.div(
                    ui.tags.div(ui.tags.label("风机类型", class_="form-label"), ui.input_select("fanType", {"roots": "罗茨鼓风机 (55-75%)", "centrifugal": "离心鼓风机 (75-88%)", "air_suspension": "空气悬浮离心鼓风机 (85-92%)", "maglev": "磁悬浮离心鼓风机 (85-97%)"}, selected="maglev", label="")),
                    ui.tags.div(ui.tags.label("风机效率 (%)", class_="form-label"), ui.input_numeric("fanEfficiency", 90, "", step=1, min=45, max=98)),
                    style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                ),
            ),
            # Bio blower
            ui.tags.div(
                ui.input_checkbox("enableBioBlower", "好氧池曝气系统（生化供氧，可选）", False),
                ui.output_ui("bio_blower_params"),
                style="margin-top:12px;",
            ),
            # CEB/CIP
            ui.tags.div(
                ui.tags.div("化学清洗 (CEB/CIP)", style="font-size:11px;font-weight:700;color:#64748b;margin-bottom:12px;"),
                ui.tags.div(
                    ui.tags.div("维护清洗 (CEB)", style="font-weight:600;font-size:12px;margin-bottom:8px;color:#334155;"),
                    ui.tags.div(
                        ui.tags.div(ui.tags.label("NaClO (mg/L)", class_="form-label"), ui.input_numeric("cebNaClO", 500, "")),
                        ui.tags.div(ui.tags.label("柠檬酸 (mg/L)", class_="form-label"), ui.input_numeric("cebCitric", 2000, "")),
                        ui.tags.div(ui.tags.label("频率 (次/周)", class_="form-label"), ui.input_numeric("cebFreq", 1, "")),
                        style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;",
                    ),
                    ui.tags.div(
                        ui.tags.div(ui.tags.label("浸泡时间 (min)", class_="form-label"), ui.input_numeric("cebSoakTime", 30, "")),
                        ui.tags.div(ui.tags.label("清洗液用量 (L/m²)", class_="form-label"), ui.input_numeric("cebVolume", 2.2, "", step=0.1)),
                        style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px;",
                    ),
                    style="padding:12px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:12px;",
                ),
                ui.tags.div(
                    ui.tags.div("恢复清洗 (CIP)", style="font-weight:600;font-size:12px;margin-bottom:8px;color:#334155;"),
                    ui.tags.div(
                        ui.tags.div(ui.tags.label("NaClO (mg/L)", class_="form-label"), ui.input_numeric("cipNaClO", 3000, "")),
                        ui.tags.div(ui.tags.label("柠檬酸 (mg/L)", class_="form-label"), ui.input_numeric("cipCitric", 5000, "")),
                        ui.tags.div(ui.tags.label("频率 (次/年)", class_="form-label"), ui.input_numeric("cipFreq", 4, "")),
                        style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:12px;",
                    ),
                    ui.tags.div(
                        ui.tags.div(ui.tags.label("浸泡时间 (h)", class_="form-label"), ui.input_numeric("cipSoakTime", 6, "")),
                        ui.tags.div(ui.tags.label("清洗液用量 (L/m²)", class_="form-label"), ui.input_numeric("cipVolume", 2.2, "", step=0.1)),
                        style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px;",
                    ),
                    style="padding:12px;border:1px solid #e2e8f0;border-radius:8px;margin-bottom:12px;",
                ),
                ui.tags.div(
                    ui.tags.div("浓药液浓度（用于在线稀释）", style="font-weight:600;font-size:12px;margin-bottom:8px;color:#475569;"),
                    ui.tags.div(
                        ui.tags.div(ui.tags.label("NaClO 浓液 (%)", class_="form-label"), ui.input_numeric("concNaClO", 10, "", step=0.5, min=0.1)),
                        ui.tags.div(ui.tags.label("柠檬酸浓液 (%)", class_="form-label"), ui.input_numeric("concCitric", 20, "", step=0.5, min=0.1)),
                        style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                    ),
                    style="padding:12px;background:#f8fafc;border:1px dashed #e2e8f0;border-radius:8px;",
                ),
                style="margin-top:12px;",
            ),
            style="margin-top:16px;",
        )

    @render.ui
    def bio_blower_params():
        if not input.enableBioBlower():
            return ""
        return ui.tags.div(
            ui.tags.div(
                ui.tags.div(ui.tags.label("气水比 (Nm³/m³)", class_="form-label"), ui.input_numeric("bioAirWaterRatio", 6.0, "", step=0.5, min=2)),
                ui.tags.div(ui.tags.label("风机效率 (%)", class_="form-label"), ui.input_numeric("bioBlowerEfficiency", 70, "", step=1, min=50, max=95)),
                style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
            ),
            ui.tags.div(
                ui.tags.div(ui.tags.label("工作台数", class_="form-label"), ui.input_numeric("bioBlowerWork", 2, "", min=1)),
                ui.tags.div(ui.tags.label("备用台数", class_="form-label"), ui.input_numeric("bioBlowerStandby", 1, "", min=0)),
                style="display:grid;grid-template-columns:1fr 1fr;gap:12px;margin-top:8px;",
            ),
            style="margin-top:8px;",
        )

    @render.text
    def duty_cycle_display():
        on_t = input.suctionOnTime() or 7
        off_t = input.suctionOffTime() or 1
        dc = on_t / (on_t + off_t) * 100
        return f"占空比: {dc:.1f}%"

    # ========================================================================
    # PROCESS OUTPUT PANEL
    # ========================================================================
    @render.ui
    def process_output():
        r = calc_result()
        inp = calc_input()
        raw = calc_raw_input()
        if not r or not inp:
            return ui.tags.div(
                ui.tags.div(
                    ui.tags.h1("MBR膜系统计算书", style="color:#1d4ed8;font-size:20px;font-weight:800;"),
                    ui.tags.p("设计依据: STERAPORE MBR设计规范", style="color:#94a3b8;font-size:12px;"),
                    style="text-align:center;padding:24px;border-bottom:3px solid #1d4ed8;margin-bottom:16px;background:white;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);",
                ),
                ui.tags.div(
                    ui.tags.p("请完成参数输入并点击「计算」按钮获取设计方案。", style="color:#64748b;text-align:center;padding:40px;"),
                    style="background:white;border-radius:12px;border:1px solid #e2e8f0;",
                ),
            )

        m = selected_model()
        rack_area = m["SheetArea"] * selected_sheets()
        Q = inp["Q"]
        Kz = inp["Kz"]
        pools = inp["Pools"]
        proj_name = (input.projectName() or "项目名称").strip() or "项目名称"

        # KPI Cards
        kpi_html = ui.tags.div(
            ui.tags.div(ui.tags.div("总膜面积", class_="kpi-label"), ui.tags.div(f"{r['AActual']:,.0f}", class_="kpi-value"), ui.tags.div("m²", class_="kpi-sub"), class_="kpi-card"),
            ui.tags.div(ui.tags.div("组件台数", class_="kpi-label"), ui.tags.div(f"{r['NRacks']}", class_="kpi-value"), ui.tags.div("台", class_="kpi-sub"), class_="kpi-card"),
            ui.tags.div(ui.tags.div("峰值通量", class_="kpi-label"), ui.tags.div(f"{r['JPeak']:.1f}", class_="kpi-value"), ui.tags.div("LMH", class_="kpi-sub"), class_="kpi-card"),
            ui.tags.div(ui.tags.div("单位电耗", class_="kpi-label"), ui.tags.div(f"{r['UnitEnergy']:.3f}", class_="kpi-value"), ui.tags.div("kWh/m³", class_="kpi-sub"), class_="kpi-card"),
            style="display:grid;grid-template-columns:repeat(4, 1fr);gap:16px;margin-bottom:16px;",
        )

        # Core Config
        core_config = ui.tags.div(
            ui.tags.div("膜系统核心配置", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.tags.div(
                ui.tags.div(ui.tags.div("膜型号", class_="label"), ui.tags.div(m["Name"], class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("单片面积", class_="label"), ui.tags.div(f"{m['SheetArea']} m²", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("每台片数", class_="label"), ui.tags.div(f"{selected_sheets()} 片", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("膜池格数", class_="label"), ui.tags.div(f"{pools} 格", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("每池台数", class_="label"), ui.tags.div(f"{inp['RacksPerPool']} 台", class_="value"), class_="config-item"),
                ui.tags.div(ui.tags.div("总台数", class_="label"), ui.tags.div(f"{r['NRacks']} 台", class_="value"), class_="config-item"),
                class_="config-grid",
            ),
            class_="card",
        )

        # Result Tables
        result_tables = ui.tags.div(
            ui.tags.div("计算结果汇总", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.tags.div(
                ui.tags.div(
                    ui.tags.h4("设计流量"),
                    ui.tags.table(
                        ui.tags.tr(ui.tags.td("平均日流量"), ui.tags.td(f"{Q:,.0f} m³/d")),
                        ui.tags.tr(ui.tags.td("峰值日流量"), ui.tags.td(f"{Q * Kz:,.0f} m³/d")),
                        ui.tags.tr(ui.tags.td("平均时流量"), ui.tags.td(f"{Q / 24:.1f} m³/h")),
                        class_="result-table",
                    ),
                    class_="result-cell",
                ),
                ui.tags.div(
                    ui.tags.h4("膜面积"),
                    ui.tags.table(
                        ui.tags.tr(ui.tags.td("单片膜面积"), ui.tags.td(f"{m['SheetArea']} m²")),
                        ui.tags.tr(ui.tags.td("每台膜面积"), ui.tags.td(f"{rack_area:.0f} m²/台")),
                        ui.tags.tr(ui.tags.td("总膜面积"), ui.tags.td(f"{r['AActual']:,.0f} m²")),
                        class_="result-table",
                    ),
                    class_="result-cell",
                ),
                ui.tags.div(
                    ui.tags.h4("通量参数"),
                    ui.tags.table(
                        ui.tags.tr(ui.tags.td("设计平均通量"), ui.tags.td(f"{r['JAvg']:.1f} LMH")),
                        ui.tags.tr(ui.tags.td("峰值通量"), ui.tags.td(f"{r['JPeak']:.1f} LMH")),
                        ui.tags.tr(ui.tags.td("瞬时通量"), ui.tags.td(f"{r['JInst']:.1f} LMH")),
                        class_="result-table",
                    ),
                    class_="result-cell",
                ),
                ui.tags.div(
                    ui.tags.h4("曝气与功率"),
                    ui.tags.table(
                        ui.tags.tr(ui.tags.td("总擦洗气量"), ui.tags.td(f"{r['TotalAirNm3min']:.1f} Nm³/min")),
                        ui.tags.tr(ui.tags.td("风机轴功率"), ui.tags.td(f"{r['BlowerPower']:.1f} kW")),
                        ui.tags.tr(ui.tags.td("气水比"), ui.tags.td(f"{r['AirWaterRatio']:.1f}:1")),
                        class_="result-table",
                    ),
                    class_="result-cell",
                ),
                style="display:grid;grid-template-columns:1fr 1fr;gap:16px;",
            ),
            class_="card",
        )

        # Equipment Table
        equip_html = build_equipment_table(inp, r, raw, m)
        equipment_table = ui.tags.div(
            ui.tags.div("主要设备清单", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            equip_html,
            class_="card",
        )

        # Chemical estimate
        chem_html = ui.tags.div(
            ui.tags.div("清洗药剂年用量估算", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.tags.div(
                ui.tags.div(ui.tags.div("NaClO (10%溶液)", class_="label"), ui.tags.div(f"{r['NaClOPerYear']:.1f}", class_="value"), ui.tags.div("t/年", class_="unit"), class_="chem-card", style="background:#eff6ff;border:1px solid #dbeafe;"),
                ui.tags.div(ui.tags.div("柠檬酸 (固体)", class_="label"), ui.tags.div(f"{r['CitricPerYear']:.1f}", class_="value"), ui.tags.div("t/年", class_="unit"), class_="chem-card", style="background:#ecfdf5;border:1px solid #bbf7d0;"),
                ui.tags.div(ui.tags.div("清洗水耗", class_="label"), ui.tags.div(f"{r['WashWaterPerYear']:,.0f}", class_="value"), ui.tags.div("m³/年", class_="unit"), class_="chem-card", style="background:#fffbeb;border:1px solid #fde68a;"),
                style="display:grid;grid-template-columns:1fr 1fr 1fr;gap:16px;",
            ),
            class_="card",
        )

        # Suggestions
        f_ok, f_msg = flux_check_msg(r["JPeak"], r["JDesign"])
        e_ok, e_msg = energy_check_msg(r["UnitEnergy"])
        suggestions = ui.tags.div(
            ui.tags.div("设计建议与风险提示", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.tags.div(
                ui.tags.div(f"峰值通量合格 ({r['JPeak']:.1f} LMH)" if f_ok else f_msg, class_="alert alert-ok" if f_ok else "alert alert-danger"),
                ui.tags.div(f"平均通量合理 ({r['JAvg']:.1f} LMH)" if r["JAvg"] <= 25 else f"平均通量偏高 ({r['JAvg']:.1f} > 25 LMH)", class_="alert alert-ok" if r["JAvg"] <= 25 else "alert alert-warn"),
                ui.tags.div(f"单位电耗合理 ({r['UnitEnergy']:.3f} kWh/m³)" if e_ok else e_msg, class_="alert alert-ok" if e_ok else "alert alert-warn"),
                ui.tags.div(
                    f"当前平均通量 {r['JAvg']:.1f} LMH，"
                    f"{'建议降低通量或增加膜组件' if r['JAvg'] > 25 else '通量在合理范围'}。"
                    f"风机效率设定 {inp['FanEfficiency']*100:.0f}%，轴功率 {r['BlowerPower']:.1f}kW。"
                    f"峰值通量 {'超标' if r['JPeak'] > 30 else '合格'}。"
                    f"产水泵扬程 {inp['PermeatePumpHead']:.1f}m，效率 {inp['PermeatePumpEff']*100:.0f}%；"
                    f"回流泵扬程 {inp['ReturnPumpHead']:.1f}m，效率 {inp['ReturnPumpEff']*100:.0f}%。",
                    class_="alert alert-info",
                ),
            ),
            class_="card",
        )

        # Tank Layout
        img_b64, piw, pih, pow_, poh = draw_tank_layout_image(inp, r, 2200, 500, 300)
        layout_html = ui.tags.div(
            ui.tags.div("膜池平面布置图", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.tags.img(src=f"data:image/png;base64,{img_b64}", style="width:100%;max-width:784px;border-radius:8px;border:1px solid #e2e8f0;"),
            ui.tags.div(
                ui.tags.div(ui.tags.div("单池净尺寸", style="font-size:10px;font-weight:600;color:#64748b;"), ui.tags.div(f"{piw/1000:.2f} × {pih/1000:.2f} m", style="font-size:14px;font-weight:700;color:#1d4ed8;"), style="background:#f8fafc;padding:8px;border-radius:8px;border:1px solid #e2e8f0;"),
                ui.tags.div(ui.tags.div("单池外缘", style="font-size:10px;font-weight:600;color:#64748b;"), ui.tags.div(f"{pow_/1000:.2f} × {poh/1000:.2f} m", style="font-size:14px;font-weight:700;color:#1d4ed8;"), style="background:#f8fafc;padding:8px;border-radius:8px;border:1px solid #e2e8f0;"),
                ui.tags.div(ui.tags.div("总膜面积", style="font-size:10px;font-weight:600;color:#64748b;"), ui.tags.div(f"{r['AActual']:,.0f} m²", style="font-size:14px;font-weight:700;color:#1d4ed8;"), style="background:#f8fafc;padding:8px;border-radius:8px;border:1px solid #e2e8f0;"),
                style="display:grid;grid-template-columns:repeat(auto-fit, minmax(170px, 1fr));gap:8px;margin-top:12px;",
            ),
            class_="card",
        )

        # Project title
        title_html = ui.tags.div(
            ui.tags.h1(f"{proj_name} MBR膜系统工艺计算书", style="color:#1d4ed8;font-size:20px;font-weight:800;"),
            ui.tags.p(f"设计依据: STERAPORE MBR设计规范 | 生成日期: {date.today().strftime('%Y年%m月%d日')}", style="color:#94a3b8;font-size:12px;"),
            style="text-align:center;padding:24px;border-bottom:3px solid #1d4ed8;margin-bottom:16px;background:white;border-radius:12px;box-shadow:0 1px 3px rgba(0,0,0,0.06);",
        )

        return ui.tags.div(title_html, kpi_html, core_config, result_tables, equipment_table, chem_html, suggestions, layout_html)


    # ========================================================================
    # EQUIPMENT TABLE BUILDER
    # ========================================================================
    def build_equipment_table(inp, r, raw, model):
        if raw is None:
            raw = inp

        def calc_chem_volumes(total_vol_l, target_mg_per_l, conc_percent):
            if conc_percent <= 0 or target_mg_per_l <= 0:
                return {"concVol": 0, "waterVol": total_vol_l}
            conc_mg_per_l = conc_percent * 10000
            conc_vol = total_vol_l * target_mg_per_l / conc_mg_per_l
            if conc_vol > total_vol_l:
                conc_vol = total_vol_l
            water_vol = total_vol_l - conc_vol
            return {"concVol": conc_vol, "waterVol": water_vol}

        def fmt_flow(flow):
            if flow < 10:
                return f"{flow:.1f}"
            return f"{round(flow)}"

        rp = r["RackParam"]
        total_air_clean = (rp["AirFlow"] * r["NRacks"]) / 1000 if rp else 0
        pools = inp["Pools"]
        spare_count = 1 if pools <= 5 else 2
        work_count = pools
        total_count = work_count + spare_count
        return_work = raw.get("returnPumpWork", 2) if isinstance(raw, dict) else 2
        return_standby = raw.get("returnPumpStandby", 1) if isinstance(raw, dict) else 1
        return_total = return_work + return_standby
        single_return_flow = r["ReturnFlow"] / return_work

        fan_type_map = {"roots": "罗茨鼓风机", "centrifugal": "离心鼓风机", "air_suspension": "空气悬浮离心鼓风机", "maglev": "磁悬浮离心鼓风机"}
        fan_type_name = fan_type_map.get(inp.get("FanType", "maglev"), "罗茨鼓风机")

        pool_area = r["AActual"] / pools
        rack_area = model["SheetArea"] * selected_sheets()
        prefix = model["Name"][:2]

        ceb_total_vol = inp["CebVolume"] * pool_area
        ceb_naclo = calc_chem_volumes(ceb_total_vol, inp["CebNaClO"], inp["ConcNaClO"])
        ceb_citric = calc_chem_volumes(ceb_total_vol, inp["CebCitric"], inp["ConcCitric"])
        cip_total_vol = inp["CipVolume"] * pool_area
        cip_naclo = calc_chem_volumes(cip_total_vol, inp["CipNaClO"], inp["ConcNaClO"])
        cip_citric = calc_chem_volumes(cip_total_vol, inp["CipCitric"], inp["ConcCitric"])
        water_vols = [ceb_naclo["waterVol"], ceb_citric["waterVol"], cip_naclo["waterVol"], cip_citric["waterVol"]]
        max_water_vol = max(water_vols + [0])
        dilution_pump_flow = max_water_vol / 30

        Qh_peak = inp["Q"] * inp["Kz"] / 24
        permeate_eff_pct = f"{inp['PermeatePumpEff']*100:.0f}"
        return_eff_pct = f"{inp['ReturnPumpEff']*100:.0f}"

        equipment = [
            ["膜组器", f"{prefix}M{rack_area:.0f}FP ({rack_area:.0f}m²/台, {selected_sheets()}片)", f"{r['NRacks']} 台", f"{pools}池 × {r['RacksPerPool']}台/池"],
            ["膜过滤泵", f"单台流量 {Qh_peak/pools:.1f} m³/h, H={inp['PermeatePumpHead']:.1f}m, η={permeate_eff_pct}%", f"工作 {work_count} 台，备用 {spare_count} 台（共 {total_count} 台）", "自吸泵或离心泵+真空系统"],
            ["抽真空系统", f"真空泵组+真空罐，抽气量≥{max(0.5, r['AActual']*0.002):.1f} m³/min", "1 套", "用于膜系统抽真空启动"],
            ["膜池风机", f"类型:{fan_type_name}，单台风量 {r['TotalAirNm3min']/pools:.1f} Nm³/min, 风压{r['FanPressurePa']/1000:.1f}kPa", f"工作 {work_count} 台，备用 {spare_count} 台（共 {total_count} 台）", f"变频控制，轴功率{r['BlowerPower']/work_count:.1f}kW/台"],
            ["曝气管清洗泵", f"{total_air_clean:.2f} m³/min", "1 台 (建议备用)", "用于膜组件曝气管路清洗"],
            ["CEB 次氯酸钠泵", f"计量泵, {fmt_flow(ceb_naclo['concVol']/30)} L/min", "1 台 (备用1台)", f"浓药液浓度{inp['ConcNaClO']}%，稀释后{inp['CebNaClO']}mg/L"],
            ["CEB 柠檬酸泵", f"计量泵, {fmt_flow(ceb_citric['concVol']/30)} L/min", "1 台 (备用1台)", f"浓药液浓度{inp['ConcCitric']}%，稀释后{inp['CebCitric']}mg/L"],
            ["CIP 次氯酸钠泵", f"计量泵, {fmt_flow(cip_naclo['concVol']/30)} L/min", "1 台 (备用1台)", f"浓药液浓度{inp['ConcNaClO']}%，稀释后{inp['CipNaClO']}mg/L"],
            ["CIP 柠檬酸泵", f"计量泵, {fmt_flow(cip_citric['concVol']/30)} L/min", "1 台 (备用1台)", f"浓药液浓度{inp['ConcCitric']}%，稀释后{inp['CipCitric']}mg/L"],
            ["稀释水泵", f"离心泵, {dilution_pump_flow*0.06:.1f} m³/h", "1 台 (备用1台)", f"用于在线稀释，最大流量来自{max_water_vol:.0f}L/30min"],
            ["污泥回流泵", f"单台流量 {single_return_flow:.1f} m³/h, H={inp['ReturnPumpHead']:.1f}m, η={return_eff_pct}%", f"工作 {return_work} 台，备用 {return_standby} 台（共 {return_total} 台）", f"回流比 {inp['ReturnRatio']}，总回流流量 {r['ReturnFlow']:.0f} m³/h"],
        ]

        if inp.get("EnableBioBlower", False):
            total_air = inp["Q"] / 24 * inp["BioAirWaterRatio"]
            single_air = total_air / inp["BioBlowerWork"]
            bio_eff_pct = f"{inp['BioBlowerEff']*100:.0f}"
            equipment.append([
                "好氧池风机",
                f"类型:{fan_type_name}，单台风量 {single_air:.1f} Nm³/h, 风压{inp['PoolLevel']+2:.1f}mH₂O",
                f"工作 {inp['BioBlowerWork']} 台，备用 {inp['BioBlowerStandby']} 台（共 {inp['BioBlowerWork']+inp['BioBlowerStandby']} 台）",
                f"生化供氧，轴功率{r['BioBlowerPower']/inp['BioBlowerWork']:.1f}kW/台",
            ])

        rows = []
        for i, eq in enumerate(equipment):
            rows.append(ui.tags.tr(
                ui.tags.td(str(i+1), style="text-align:center;color:#94a3b8;"),
                ui.tags.td(eq[0], style="font-weight:600;"),
                ui.tags.td(eq[1]),
                ui.tags.td(eq[2]),
                ui.tags.td(eq[3], style="color:#94a3b8;"),
            ))

        return ui.tags.div(
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(
                    ui.tags.th("序号"), ui.tags.th("设备名称"), ui.tags.th("规格参数"), ui.tags.th("数量"), ui.tags.th("备注"),
                )),
                ui.tags.tbody(*rows),
                class_="data-table",
            ),
            style="overflow-x:auto;",
        )

    # ========================================================================
    # MODEL SELECTION REACTIVITY
    # ========================================================================
    @reactive.Effect
    def _update_model():
        idx = int(input.membraneModel() or 1)
        if 0 <= idx < len(ALL_MODELS):
            selected_model.set(ALL_MODELS[idx])
            selected_sheet_area.set(ALL_MODELS[idx]["SheetArea"])

    @reactive.Effect
    def _update_sheets():
        try:
            s = int(input.membraneSheets() or 42)
            selected_sheets.set(s)
        except (ValueError, TypeError):
            pass

    # ========================================================================
    # CALCULATE BUTTON
    # ========================================================================
    @reactive.Effect
    @reactive.event(input.btnCalculate)
    def _do_calculate():
        try:
            m = selected_model()
            inp = {
                "Q": input.flowRate() or 5000,
                "Kz": input.peakFactor() or 1.3,
                "COD": input.codIn() or 400,
                "NH3N": input.nh3nIn() or 35,
                "SS": input.ssIn() or 150,
                "T": input.waterTemp() or 20,
                "MLSS": input.mlssIn() or 8000,
                "ModelIndex": int(input.membraneModel() or 1),
                "SheetsPerRack": selected_sheets(),
                "Pools": input.membranePools() or 2,
                "RacksPerPool": input.membraneSeries() or 3,
                "J25": input.j25() or 18,
                "FoulingFactor": input.foulingFactor() or 0.85,
                "SAD": input.sadValue() or 150,
                "SuctionOn": input.suctionOnTime() or 7,
                "SuctionOff": input.suctionOffTime() or 1,
                "PoolLevel": input.poolLevel() or 3.5,
                "PipeLoss": input.pipeLoss() or 0.5,
                "FanEfficiency": (input.fanEfficiency() or 90) / 100,
                "PermeatePumpHead": input.permeatePumpHead() or 6.5,
                "PermeatePumpEff": (input.permeatePumpEff() or 75) / 100,
                "ReturnRatio": input.returnRatio() or 3,
                "ReturnPumpHead": input.returnPumpHead() or 0.5,
                "ReturnPumpEff": (input.returnPumpEff() or 70) / 100,
                "EnableBioBlower": input.enableBioBlower() or False,
                "BioAirWaterRatio": input.bioAirWaterRatio() or 6.0,
                "BioBlowerEff": (input.bioBlowerEfficiency() or 70) / 100,
                "BioBlowerWork": input.bioBlowerWork() or 2,
                "BioBlowerStandby": input.bioBlowerStandby() or 1,
                "CebFreq": input.cebFreq() or 1,
                "CipFreq": input.cipFreq() or 4,
                "CebVolume": input.cebVolume() or 2.2,
                "CipVolume": input.cipVolume() or 2.2,
                "CebNaClO": input.cebNaClO() or 500,
                "CipNaClO": input.cipNaClO() or 3000,
                "CebCitric": input.cebCitric() or 2000,
                "CipCitric": input.cipCitric() or 5000,
                "ConcNaClO": input.concNaClO() or 10,
                "ConcCitric": input.concCitric() or 20,
                "FanType": input.fanType() or "maglev",
            }
            r = compute_process(inp)
            calc_result.set(r)
            calc_input.set(inp)
            calc_raw_input.set(inp)
        except Exception as e:
            import traceback
            traceback.print_exc()
            calc_result.set(None)

    # ========================================================================
    # RESET BUTTON
    # ========================================================================
    @reactive.Effect
    @reactive.event(input.btnReset)
    def _do_reset():
        calc_result.set(None)
        calc_input.set(None)
        ui.update_numeric("flowRate", value=5000)
        ui.update_numeric("peakFactor", value=1.3)
        ui.update_numeric("codIn", value=400)
        ui.update_numeric("bodIn", value=200)
        ui.update_numeric("nh3nIn", value=35)
        ui.update_numeric("ssIn", value=150)
        ui.update_numeric("tnIn", value=50)
        ui.update_numeric("tpIn", value=5)
        ui.update_numeric("phValue", value=7.2)
        ui.update_numeric("waterTemp", value=20)
        ui.update_numeric("mlssIn", value=8000)
        ui.update_select("membraneModel", selected="1")
        ui.update_numeric("membranePools", value=2)
        ui.update_numeric("membraneSeries", value=3)
        ui.update_select("effluentStandard", selected="1A")
        ui.update_numeric("codOut", value=30)
        ui.update_numeric("nh3nOut", value=1.5)
        ui.update_numeric("tnOut", value=15)
        ui.update_numeric("ssOut", value=5)
        ui.update_numeric("j25", value=18)
        ui.update_numeric("foulingFactor", value=0.85)
        ui.update_numeric("sadValue", value=150)
        ui.update_numeric("suctionOnTime", value=7)
        ui.update_numeric("suctionOffTime", value=1)
        ui.update_numeric("poolLevel", value=3.5)
        ui.update_numeric("pipeLoss", value=0.5)
        ui.update_numeric("fanEfficiency", value=90)
        ui.update_numeric("permeatePumpHead", value=6.5)
        ui.update_numeric("permeatePumpEff", value=75)
        ui.update_numeric("returnRatio", value=3)
        ui.update_numeric("returnPumpHead", value=0.5)
        ui.update_numeric("returnPumpEff", value=70)
        ui.update_checkbox("enableBioBlower", value=False)
        ui.update_numeric("cebNaClO", value=500)
        ui.update_numeric("cebCitric", value=2000)
        ui.update_numeric("cebFreq", value=1)
        ui.update_numeric("cebSoakTime", value=30)
        ui.update_numeric("cebVolume", value=2.2)
        ui.update_numeric("cipNaClO", value=3000)
        ui.update_numeric("cipCitric", value=5000)
        ui.update_numeric("cipFreq", value=4)
        ui.update_numeric("cipSoakTime", value=6)
        ui.update_numeric("cipVolume", value=2.2)
        ui.update_numeric("concNaClO", value=10)
        ui.update_numeric("concCitric", value=20)
        selected_model.set(ALL_MODELS[1])
        selected_sheet_area.set(40)
        selected_sheets.set(42)

    # ========================================================================
    # QUICKREF TAB
    # ========================================================================
    def render_quickref_tab():
        temp_img = draw_temp_correction_curves()
        return ui.tags.div(
            # Section 1: 设计参数
            ui.tags.h2("一、设计参数", class_="section-title"),
            ui.tags.h3("原水条件", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("水温"), ui.tags.td("15~35"), ui.tags.td("℃"), ui.tags.td("最低≥13℃, >40℃需降温")),
                    ui.tags.tr(ui.tags.td("pH"), ui.tags.td("6~8"), ui.tags.td("-"), ui.tags.td("超出范围需中和处理")),
                    ui.tags.tr(ui.tags.td("隔栅精度"), ui.tags.td("0.5~1.0"), ui.tags.td("mm"), ui.tags.td("超细格栅, 推荐孔型内进流网板")),
                    ui.tags.tr(ui.tags.td("动植物油"), ui.tags.td("&lt;150"), ui.tags.td("mg/L"), ui.tags.td("超过需前处理")),
                    ui.tags.tr(ui.tags.td("矿物油"), ui.tags.td("禁止流入"), ui.tags.td("-"), ui.tags.td("难以生物分解, 严禁入膜池")),
                    ui.tags.tr(ui.tags.td("BOD/COD"), ui.tags.td("&gt;0.3"), ui.tags.td("-"), ui.tags.td("&lt;0.3时可生化性差")),
                    ui.tags.tr(ui.tags.td("C/N比"), ui.tags.td("&gt;3.5"), ui.tags.td("-"), ui.tags.td("低于3.5时宜投加碳源")),
                    ui.tags.tr(ui.tags.td("铁 (Fe)"), ui.tags.td("&lt;30"), ui.tags.td("ppm"), ui.tags.td("超过需预处理")),
                    ui.tags.tr(ui.tags.td("锰 (Mn)"), ui.tags.td("&lt;10"), ui.tags.td("ppm"), ui.tags.td("超过需预处理")),
                    ui.tags.tr(ui.tags.td("钙 (Ca)"), ui.tags.td("&lt;100"), ui.tags.td("ppm"), ui.tags.td("超过需预处理, 注意结垢")),
                    ui.tags.tr(ui.tags.td("硅 (Si)"), ui.tags.td("&lt;30"), ui.tags.td("ppm"), ui.tags.td("草酸清洗有效但注意草酸钙")),
                ),
                class_="quickref-table",
            ),
            ui.tags.h3("负荷设计", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("污泥负荷 Ls"), ui.tags.td("&lt;0.1"), ui.tags.td("kgBOD5/kgMLSS·d"), ui.tags.td("-")),
                    ui.tags.tr(ui.tags.td("容积负荷"), ui.tags.td("&lt;1"), ui.tags.td("kgBOD5/m³·d"), ui.tags.td("-")),
                ),
                class_="quickref-table",
            ),
            ui.tags.h3("膜池设计", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("MLSS"), ui.tags.td("3000~12000"), ui.tags.td("mg/L"), ui.tags.td("-")),
                    ui.tags.tr(ui.tags.td("MLVSS/MLSS"), ui.tags.td("0.4~0.7"), ui.tags.td("-"), ui.tags.td("挥发性悬浮固体比例")),
                    ui.tags.tr(ui.tags.td("水深"), ui.tags.td("&gt;3"), ui.tags.td("m"), ui.tags.td("膜池设计水深")),
                    ui.tags.tr(ui.tags.td("水平度"), ui.tags.td("&lt;3"), ui.tags.td("mm/m"), ui.tags.td("影响曝气均匀性")),
                    ui.tags.tr(ui.tags.td("HRT"), ui.tags.td("0.5~1.2"), ui.tags.td("h"), ui.tags.td("满足膜平面布置要求")),
                    ui.tags.tr(ui.tags.td("抽吸/停止"), ui.tags.td("≤7 / ≥1"), ui.tags.td("min"), ui.tags.td("间歇运行, 停止中持续曝气")),
                    ui.tags.tr(ui.tags.td("运行时间占比"), ui.tags.td("80~90%"), ui.tags.td("%"), ui.tags.td("延长清洗周期")),
                ),
                class_="quickref-table",
            ),
            ui.tags.h3("运行参数", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("DO (好氧区)"), ui.tags.td("1~2"), ui.tags.td("mg/L"), ui.tags.td("不宜低于1")),
                    ui.tags.tr(ui.tags.td("DO (缺氧区)"), ui.tags.td("&lt;0.5"), ui.tags.td("mg/L"), ui.tags.td("脱氮要求")),
                    ui.tags.tr(ui.tags.td("DO (厌氧区)"), ui.tags.td("&lt;0.2"), ui.tags.td("mg/L"), ui.tags.td("除磷要求")),
                    ui.tags.tr(ui.tags.td("SRT"), ui.tags.td("15~25"), ui.tags.td("d"), ui.tags.td("污泥龄控制")),
                    ui.tags.tr(ui.tags.td("污泥粘度"), ui.tags.td("&lt;30"), ui.tags.td("cps"), ui.tags.td("过高影响过滤和溶氧")),
                    ui.tags.tr(ui.tags.td("硝化速率"), ui.tags.td("0.02~0.08"), ui.tags.td("kgNH3-N/kgMLSS·d"), ui.tags.td("20℃时")),
                    ui.tags.tr(ui.tags.td("脱氮速率"), ui.tags.td("0.03~0.06"), ui.tags.td("kgNO3-N/kgMLSS·d"), ui.tags.td("20℃, 按1.026^(T-20)修正")),
                ),
                class_="quickref-table",
            ),
            # Section 2: 膜通量与曝气
            ui.tags.h2("二、膜通量与曝气", class_="section-title"),
            ui.tags.h3("膜通量", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("平均通量"), ui.tags.td("8~33"), ui.tags.td("L/m²·h"), ui.tags.td("浸没式中空纤维膜")),
                    ui.tags.tr(ui.tags.td("产水浊度"), ui.tags.td("&lt;1"), ui.tags.td("NTU"), ui.tags.td("出水水质要求")),
                    ui.tags.tr(ui.tags.td("跨膜压差"), ui.tags.td("&lt;30"), ui.tags.td("kPa"), ui.tags.td("超过需物理清洗")),
                    ui.tags.tr(ui.tags.td("初始压差"), ui.tags.td("5~6"), ui.tags.td("kPa"), ui.tags.td("运行压力预计初始+50~60kPa")),
                    ui.tags.tr(ui.tags.td("压差清洗阈值"), ui.tags.td("初始+15"), ui.tags.td("kPa"), ui.tags.td("超过此值需恢复清洗")),
                ),
                class_="quickref-table",
            ),
            ui.tags.h3("膜材料", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("膜寿命 (PVDF)"), ui.tags.td("3~10"), ui.tags.td("年"), ui.tags.td("不同清洗频率、废水类型、运行维护条件下膜使用年限不同")),
                ),
                class_="quickref-table",
            ),
            ui.tags.h3("曝气", class_="sub-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("参数"), ui.tags.th("要求"), ui.tags.th("单位"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("SAD"), ui.tags.td("100~150"), ui.tags.td("Nm³/m²·h"), ui.tags.td("单位占地面积吹扫气量")),
                    ui.tags.tr(ui.tags.td("曝气孔孔径"), ui.tags.td("5"), ui.tags.td("mm"), ui.tags.td("流速>20m/s, 不锈钢材质")),
                ),
                class_="quickref-table",
            ),
            # Section 3: 回流比
            ui.tags.h2("三、回流比", class_="section-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("回流类型"), ui.tags.th("要求"), ui.tags.th("代号"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("膜池→好氧池"), ui.tags.td("300~500%"), ui.tags.td("R1"), ui.tags.td("3~5倍")),
                    ui.tags.tr(ui.tags.td("好氧池→缺氧池"), ui.tags.td("200~300%"), ui.tags.td("R2"), ui.tags.td("2~3倍")),
                    ui.tags.tr(ui.tags.td("缺氧池→厌氧池"), ui.tags.td("100~200%"), ui.tags.td("R3"), ui.tags.td("1~2倍")),
                ),
                class_="quickref-table",
            ),
            # Section 4: 清洗维护
            ui.tags.h2("四、清洗维护", class_="section-title"),
            ui.tags.p("三菱化学PVDF材质膜有三种化学清洗方法: 逆通液清洗(维护清洗)、在线清洗(恢复清洗)、系统外清洗(浸泡清洗)", style="color:#475569;font-size:13px;"),
            ui.tags.p("使用药液: NaClO (去除有机物和生物污堵) | 酸 (去除无机物污堵)", style="color:#475569;font-size:13px;"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("清洗方式"), ui.tags.th("用量 (L/m²膜)"), ui.tags.th("浓度 (mg/L)"), ui.tags.th("备注"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("维护清洗 (低)"), ui.tags.td("2"), ui.tags.td("500"), ui.tags.td("每周1次, NaClO溶液, 30~60分钟/次")),
                    ui.tags.tr(ui.tags.td("恢复清洗 (高)"), ui.tags.td("2"), ui.tags.td("3000"), ui.tags.td("每3个月1次或压差>15kPa, NaClO溶液")),
                    ui.tags.tr(ui.tags.td("浸没清洗"), ui.tags.td("-"), ui.tags.td("3000"), ui.tags.td("在线清洗后压差不能恢复时, 6~24小时/次")),
                    ui.tags.tr(ui.tags.td("酸清洗"), ui.tags.td("-"), ui.tags.td("1%~2%"), ui.tags.td("根据实际情况调整, 参照膜使用手册")),
                ),
                class_="quickref-table",
            ),
            ui.tags.div(ui.tags.strong("禁止使用氢氧化钠 (NaOH) 清洗三菱膜"), ", 会导致膜老化脱皮!", class_="alert alert-warn"),
            # Section 5: 故障处理
            ui.tags.h2("五、故障处理", class_="section-title"),
            ui.tags.table(
                ui.tags.thead(ui.tags.tr(ui.tags.th("症状"), ui.tags.th("原因"), ui.tags.th("对策"))),
                ui.tags.tbody(
                    ui.tags.tr(ui.tags.td("压差上升"), ui.tags.td("无曝气 (风机故障)"), ui.tags.td("确认风机是否异常停止/故障/曝气不均匀")),
                    ui.tags.tr(ui.tags.td("压差上升"), ui.tags.td("MLSS过高"), ui.tags.td("排泥至3000~12000mg/L范围")),
                    ui.tags.tr(ui.tags.td("压差上升"), ui.tags.td("油类流入"), ui.tags.td("设置油水分离, 矿物油禁止流入")),
                    ui.tags.tr(ui.tags.td("压差上升"), ui.tags.td("曝气不足"), ui.tags.td("检查分流, 确保额定风量")),
                    ui.tags.tr(ui.tags.td("氮超标"), ui.tags.td("DO不足"), ui.tags.td("好氧区DO保持1~2mg/L")),
                    ui.tags.tr(ui.tags.td("产水浊度>1NTU"), ui.tags.td("管道泄漏/膜破损"), ui.tags.td("停止产水, 检查管道密封和膜完整性")),
                    ui.tags.tr(ui.tags.td("透水率下降"), ui.tags.td("膜污染"), ui.tags.td("调整运行参数, 增加MC频率")),
                ),
                class_="quickref-table",
            ),
            # Section 6: 检漏与安装
            ui.tags.h2("六、检漏与安装", class_="section-title"),
            ui.tags.div(
                ui.tags.p("检漏步骤:", style="font-weight:600;"),
                ui.tags.ol(
                    ui.tags.li("水槽满水"), ui.tags.li("集水管一侧堵头 / 一侧接气"),
                    ui.tags.li("静置10min"), ui.tags.li("加压28kPa找漏点"),
                    ui.tags.li("环氧树脂修补"),
                ),
                style="background:#f8fafc;padding:12px;border-radius:8px;",
            ),
            ui.tags.div(ui.tags.strong("用空气检漏 (禁止水泵)"), " | 起吊角度 ≤ 60° | 膜组件器中心距 2200mm | 曝气管距膜底 ≥ 200mm | 顶部距水面 > 500mm", class_="alert alert-warn"),
            # Section 7: 安全与控制
            ui.tags.h2("七、安全与控制", class_="section-title"),
            ui.tags.ul(
                ui.tags.li("风机故障必须联动停抽吸泵, 防止污泥固化"),
                ui.tags.li("泵尽量装液位下方, 设破虹吸装置, 吸程不宜 < 6m"),
                ui.tags.li("启动顺序: 搅拌机 → 循环泵 → 风机 → 抽吸泵"),
                ui.tags.li("膜池与产水系统联动: 污泥回流泵全停时膜池不能产水"),
                ui.tags.li(ui.tags.strong("严禁硅类消泡剂"), " (吸附膜面导致压差上升且无法药洗)"),
                ui.tags.li("膜片取出后12小时内须浸泡一次保持湿润"),
                ui.tags.li("原则上不需要反洗 (backwash)"),
                ui.tags.li("MLVSS 通常为 MLSS 的 70~80%"),
                style="font-size:13px;color:#334155;line-height:1.8;",
            ),
            # Section 8: 温度校正曲线
            ui.tags.h2("八、温度校正曲线（以25°C为基准）", class_="section-title"),
            ui.tags.p("膜通量和TMP随水温变化，主要由水的粘度变化引起。", style="color:#94a3b8;font-size:13px;"),
            ui.tags.img(src=f"data:image/png;base64,{temp_img}", style="width:100%;max-width:800px;border-radius:8px;"),
            ui.tags.p("注：校正系数基于Andrade方程计算，η = A × 10^(B/(T-C))，其中A=0.00179, B=570.58, C=137.02", style="color:#94a3b8;font-size:11px;font-style:italic;"),
            class_="card",
        )

    # ========================================================================
    # OPS TAB
    # ========================================================================
    def render_ops_tab():
        return ui.tags.div(
            ui.tags.div(
                # LEFT
                ui.tags.div(
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("1", class_="step"), "运行条件", class_="card-header"),
                        ui.tags.div(
                            ui.tags.div(ui.tags.label("平均日水量 (m³/d)", class_="form-label"), ui.input_numeric("opsAvgFlow", 5000, "", min=0)),
                            ui.tags.div(ui.tags.label("初始TMP (kPa)", class_="form-label"), ui.input_numeric("opsTmpInitial", 10, "", min=0, step=0.1)),
                            ui.tags.div(ui.tags.label("冬季水温 (°C)", class_="form-label"), ui.input_numeric("opsTempWinter", 10, "", min=0, max=40)),
                            ui.tags.div(ui.tags.label("夏季水温 (°C)", class_="form-label"), ui.input_numeric("opsTempSummer", 28, "", min=0, max=40)),
                            style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                        ),
                        class_="card",
                    ),
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("2", class_="step"), "膜阻力模型", class_="card-header"),
                        ui.tags.div(
                            ui.tags.div(ui.tags.label("膜固有阻力 Rm (10¹² m⁻¹)", class_="form-label"), ui.input_numeric("opsRm", 1.5, "", min=0.5, max=8, step=0.1)),
                            ui.tags.div(ui.tags.label("反洗后残留率 (%)", class_="form-label"), ui.input_numeric("opsBwResidual", 0.05, "", min=0.01, max=2, step=0.01)),
                            ui.tags.div(ui.tags.label("蛋糕层峰值增量 dRc (10¹¹ m⁻¹)", class_="form-label"), ui.input_numeric("opsDRc", 1.5, "", min=0.3, max=5, step=0.1)),
                            ui.tags.div(ui.tags.label("不可逆污染速率 (kPa/d)", class_="form-label"), ui.input_numeric("opsRfRate", 0.02, "", min=0.01, max=0.50, step=0.01)),
                            style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                        ),
                        class_="card",
                    ),
                    ui.tags.div(
                        ui.tags.div(ui.tags.span("3", class_="step"), "清洗设定", class_="card-header"),
                        ui.tags.div(
                            ui.tags.div(ui.tags.label("CEB恢复率 (%)", class_="form-label"), ui.input_numeric("opsCebRecovery", 60, "", min=20, max=90, step=5)),
                            ui.tags.div(ui.tags.label("CIP恢复率 (%)", class_="form-label"), ui.input_numeric("opsCipRecovery", 95, "", min=80, max=100, step=5)),
                            ui.tags.div(ui.tags.label("CEB触发压力 (kPa)", class_="form-label"), ui.input_numeric("opsCebTrigger", 25, "", min=10, max=40, step=1)),
                            ui.tags.div(ui.tags.label("CIP触发压力 (kPa)", class_="form-label"), ui.input_numeric("opsCipTrigger", 35, "", min=20, max=60, step=1)),
                            ui.tags.div(ui.tags.label("停机报警压力 (kPa)", class_="form-label"), ui.input_numeric("opsStopTrigger", 45, "", min=25, max=70, step=1)),
                            ui.tags.div(ui.tags.label("CIP后残留系数", class_="form-label"), ui.input_numeric("opsCipResidual", 1.02, "", min=1.0, max=1.10, step=0.01)),
                            style="display:grid;grid-template-columns:1fr 1fr;gap:12px;",
                        ),
                        ui.tags.div(
                            ui.tags.label("模拟天数", class_="form-label"),
                            ui.input_numeric("opsSimDays", 365, "", min=30, max=3650, step=1),
                            style="margin-top:12px;",
                        ),
                        class_="card",
                    ),
                    ui.tags.button("运行模拟", id="btnRunSim", class_="btn-primary", style="width:100%;"),
                    style="width:480px;flex-shrink:0;",
                ),
                # RIGHT
                ui.tags.div(
                    ui.output_ui("ops_output"),
                    style="flex:1;min-width:0;",
                ),
                style="display:flex;gap:24px;flex-wrap:wrap;",
            ),
        )

    @render.ui
    def ops_output():
        sim = ops_sim_result()
        if not sim:
            return ui.tags.div(
                ui.tags.p("请设置运行参数并点击「运行模拟」按钮。", style="color:#64748b;text-align:center;padding:40px;"),
                style="background:white;border-radius:12px;border:1px solid #e2e8f0;",
            )

        # TMP chart
        tmp_fig = create_tmp_chart(sim)
        # Inject trigger values into chart
        tmp_fig.data[1].y = [sim.get("cebTrigger", 25)] * 2
        tmp_fig.data[2].y = [sim.get("cipTrigger", 35)] * 2
        tmp_fig.data[3].y = [sim.get("stopTrigger", 45)] * 2

        tmp_html = ui.tags.div(
            ui.tags.div("TMP 趋势预测", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.output_plotly("ops_tmp_chart"),
            class_="card",
        )

        # Fouling chart
        fouling_html = ui.tags.div(
            ui.tags.div("膜污染阻力累积分析", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.output_plotly("ops_fouling_chart"),
            class_="card",
        )

        # KPI
        kpi_html = ui.tags.div(
            ui.tags.div(
                ui.tags.div("预计CEB次数", class_="kpi-label"),
                ui.tags.div(f"{sim['cebCount']}", class_="kpi-value"),
                ui.tags.div("次/模拟期", class_="kpi-sub"),
                class_="kpi-card",
            ),
            ui.tags.div(
                ui.tags.div("预计CIP次数", class_="kpi-label"),
                ui.tags.div(f"{sim['cipCount']}", class_="kpi-value"),
                ui.tags.div("次/模拟期", class_="kpi-sub"),
                class_="kpi-card",
            ),
            ui.tags.div(
                ui.tags.div("最终TMP", class_="kpi-label"),
                ui.tags.div(f"{sim['finalTmp']:.1f}", class_="kpi-value"),
                ui.tags.div("kPa", class_="kpi-sub"),
                class_="kpi-card",
            ),
            style="display:grid;grid-template-columns:repeat(3, 1fr);gap:16px;margin:16px 0;",
        )

        # Details
        ceb_interval = sim["simDays"] / sim["cebCount"] if sim["cebCount"] > 0 else sim["simDays"]
        cip_interval = sim["simDays"] / sim["cipCount"] if sim["cipCount"] > 0 else sim["simDays"]
        details_html = ui.tags.div(
            ui.tags.div("清洗与寿命预测", style="font-size:14px;font-weight:700;margin-bottom:12px;"),
            ui.tags.div(
                ui.tags.div(
                    ui.tags.h4("清洗预测"),
                    ui.tags.table(
                        ui.tags.tr(ui.tags.td("CEB间隔"), ui.tags.td(f"{ceb_interval:.0f} 天")),
                        ui.tags.tr(ui.tags.td("CIP间隔"), ui.tags.td(f"{cip_interval:.0f} 天")),
                        ui.tags.tr(ui.tags.td("停机天数"), ui.tags.td(f"{sim['cebCount'] + sim['cipCount']} 天")),
                        class_="result-table",
                    ),
                    class_="result-cell",
                ),
                ui.tags.div(
                    ui.tags.h4("膜寿命预测"),
                    ui.tags.table(
                        ui.tags.tr(ui.tags.td("预计膜寿命"), ui.tags.td(f"{sim['membraneLife']:.1f} 年")),
                        ui.tags.tr(ui.tags.td("年通量衰减"), ui.tags.td(f"{sim['annualDecay']:.2f} kPa/年")),
                        ui.tags.tr(ui.tags.td("运行成本"), ui.tags.td(f"¥{sim['runCost']:,.0f}")),
                        class_="result-table",
                    ),
                    class_="result-cell",
                ),
                style="display:grid;grid-template-columns:1fr 1fr;gap:16px;",
            ),
            class_="card",
        )

        return ui.tags.div(tmp_html, fouling_html, kpi_html, details_html)

    # Store for chart rendering
    ops_chart_data = reactive.Value(None)

    @reactive.Effect
    @reactive.event(input.btnRunSim)
    def _do_simulation():
        try:
            avg_flow = input.opsAvgFlow() or 5000
            ops = {
                "avgFlow": avg_flow,
                "tmpInitial": input.opsTmpInitial() or 10,
                "T": input.opsTempWinter() or 10,
                "J_avg": avg_flow / 24 * 1000 / (calc_result()["AActual"] if calc_result() else 5000),
                "MLSS": input.mlssIn() or 8000,
                "Rm": input.opsRm() or 1.5,
                "bwResidual": input.opsBwResidual() or 0.05,
                "dRc": input.opsDRc() or 1.5,
                "rfRate": input.opsRfRate() or 0.02,
                "cebRecovery": input.opsCebRecovery() or 60,
                "cipRecovery": input.opsCipRecovery() or 95,
                "cebTrigger": input.opsCebTrigger() or 25,
                "cipTrigger": input.opsCipTrigger() or 35,
                "stopTrigger": input.opsStopTrigger() or 45,
                "cipResidual": input.opsCipResidual() or 1.02,
                "simDays": input.opsSimDays() or 365,
                "cebFreqW": input.cebFreq() or 1,
            }
            # Use process result for J_avg if available
            if calc_result():
                ops["J_avg"] = calc_result()["JAvg"]
                ops["AActual"] = calc_result()["AActual"]

            result = run_simulation(ops)
            result["cebTrigger"] = ops["cebTrigger"]
            result["cipTrigger"] = ops["cipTrigger"]
            result["stopTrigger"] = ops["stopTrigger"]
            ops_sim_result.set(result)
            ops_chart_data.set(result)
        except Exception as e:
            import traceback
            traceback.print_exc()

    @render.plotly
    def ops_tmp_chart():
        sim = ops_chart_data()
        if not sim:
            return go.Figure()
        days = list(range(len(sim["tmpValues"])))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=sim["tmpValues"], mode='lines', name='TMP', line=dict(color='#2563eb', width=2)))
        fig.add_trace(go.Scatter(x=[0, days[-1]], y=[sim.get("cebTrigger", 25)]*2, mode='lines', name='CEB触发', line=dict(color='#f59e0b', dash='dash', width=1.5)))
        fig.add_trace(go.Scatter(x=[0, days[-1]], y=[sim.get("cipTrigger", 35)]*2, mode='lines', name='CIP触发', line=dict(color='#dc2626', dash='dash', width=1.5)))
        fig.add_trace(go.Scatter(x=[0, days[-1]], y=[sim.get("stopTrigger", 45)]*2, mode='lines', name='停机报警', line=dict(color='#7c3aed', dash='dot', width=1.5)))
        fig.update_layout(
            title="TMP 趋势预测", xaxis_title="天数", yaxis_title="TMP (kPa)",
            template="plotly_white", height=350, margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig

    @render.plotly
    def ops_fouling_chart():
        sim = ops_chart_data()
        if not sim:
            return go.Figure()
        days = list(range(1, len(sim["baseResist"]) + 1))
        fig = go.Figure()
        fig.add_trace(go.Scatter(x=days, y=sim["baseResist"], mode='lines',
                                 name='基础阻力 Rm', stackgroup='one',
                                 line=dict(color='#3b82f6', width=1.5),
                                 fillcolor='rgba(59,130,246,0.2)'))
        fig.add_trace(go.Scatter(x=days, y=sim["cakeResist"], mode='lines',
                                 name='滤饼层 Rc', stackgroup='one',
                                 line=dict(color='#f59e0b', width=1.5),
                                 fillcolor='rgba(245,158,11,0.2)'))
        fig.add_trace(go.Scatter(x=days, y=sim["irrevResist"], mode='lines',
                                 name='不可逆 Rf', stackgroup='one',
                                 line=dict(color='#dc2626', width=1.5),
                                 fillcolor='rgba(220,38,38,0.2)'))
        fig.update_layout(
            title="膜污染阻力累积分析", xaxis_title="天数", yaxis_title="TMP (kPa)",
            template="plotly_white", height=300, margin=dict(l=10, r=10, t=40, b=10),
            legend=dict(orientation="h", yanchor="bottom", y=1.02, xanchor="right", x=1)
        )
        return fig


# =============================================================================
# CREATE APP
# =============================================================================
app = App(app_ui, server)