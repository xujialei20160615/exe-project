import math
import pandas as pd
import os
import sys

# 常量定义
PI = 3.14159265358979324
A = 6378245.0
EE = 0.006693421622965943

# ===================== 路径处理函数 =====================
def get_app_path():
    """获取程序当前运行目录（兼容打包后的exe）"""
    if hasattr(sys, '_MEIPASS'):
        # 打包后的exe运行环境
        return os.path.dirname(sys.executable)
    else:
        # 本地开发环境
        return os.path.dirname(os.path.abspath(__file__))

# ===================== 坐标转换函数 =====================
def out_of_china(lng, lat):
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False

def transform_lat(x, y):
    ret = -100.0 + 2.0 * x + 3.0 * y + 0.2 * y * y + 0.1 * x * y + 0.2 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(y * PI) + 40.0 * math.sin(y / 3.0 * PI)) * 2.0 / 3.0
    ret += (160.0 * math.sin(y / 12.0 * PI) + 320.0 * math.sin(y * PI / 30.0)) * 2.0 / 3.0
    return ret

def transform_lng(x, y):
    ret = 300.0 + x + 2.0 * y + 0.1 * x * x + 0.1 * x * y + 0.1 * math.sqrt(abs(x))
    ret += (20.0 * math.sin(6.0 * x * PI) + 20.0 * math.sin(2.0 * x * PI)) * 2.0 / 3.0
    ret += (20.0 * math.sin(x * PI) + 40.0 * math.sin(x / 3.0 * PI)) * 2.0 / 3.0
    ret += (150.0 * math.sin(x / 12.0 * PI) + 300.0 * math.sin(x / 30.0 * PI)) * 2.0 / 3.0
    return ret

def wgs84_to_gcj02(wgs_lng, wgs_lat):
    if out_of_china(wgs_lng, wgs_lat):
        return [wgs_lng, wgs_lat]
    dlat = transform_lat(wgs_lng - 105.0, wgs_lat - 35.0)
    dlng = transform_lng(wgs_lng - 105.0, wgs_lat - 35.0)
    radlat = wgs_lat / 180.0 * PI
    magic = math.sin(radlat)
    magic = 1 - EE * magic * magic
    sqrtmagic = math.sqrt(magic)
    dlat = (dlat * 180.0) / ((A * (1 - EE)) / (magic * sqrtmagic) * PI)
    dlng = (dlng * 180.0) / (A / sqrtmagic * math.cos(radlat) * PI)
    gcj_lng = wgs_lng + dlng
    gcj_lat = wgs_lat + dlat
    return [gcj_lng, gcj_lat]

def gcj02_to_wgs84(gcj_lng, gcj_lat):
    if out_of_china(gcj_lng, gcj_lat):
        return [gcj_lng, gcj_lat]
    wgs_lng = gcj_lng
    wgs_lat = gcj_lat
    minlng = wgs_lng - 0.1
    maxlng = wgs_lng + 0.1
    minlat = wgs_lat - 0.1
    maxlat = wgs_lat + 0.1
    for _ in range(30):
        midlng = (minlng + maxlng) / 2
        midlat = (minlat + maxlat) / 2
        temp = wgs84_to_gcj02(midlng, midlat)
        dlng = temp[0] - gcj_lng
        dlat = temp[1] - gcj_lat
        if abs(dlng) < 1e-7 and abs(dlat) < 1e-7:
            break
        if temp[0] > gcj_lng:
            maxlng = midlng
        else:
            minlng = midlng
        if temp[1] > gcj_lat:
            maxlat = midlat
        else:
            minlat = midlat
    return [midlng, midlat]

def bd09_to_gcj02(bd_lng, bd_lat):
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * PI)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return [gcj_lng, gcj_lat]

def bd09_to_wgs84(bd_lng, bd_lat):
    gcj = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj[0], gcj[1])

# ===================== 业务逻辑函数 =====================
def batch_convert_excel(file_path, output_path, source_type="gcj02"):
    df = pd.read_excel(file_path, engine="openpyxl")
    
    def convert_row(row):
        lng = row["经度"]
        lat = row["纬度"]
        if pd.isna(lng) or pd.isna(lat):
            return (None, None)
        if source_type == "gcj02":
            res = gcj02_to_wgs84(lng, lat)
        elif source_type == "bd09":
            res = bd09_to_wgs84(lng, lat)
        return (res[0], res[1])
        
    df["WGS84经度"], df["WGS84纬度"] = zip(*df.apply(convert_row, axis=1))
    df.to_excel(output_path, index=False, engine="openpyxl")
    print(f"转换完成，输出文件：{output_path}")

# ===================== 配置读取函数 =====================
CONFIG_FILE = "config.txt"

def get_source_type():
    # 获取程序所在目录
    app_path = get_app_path()
    config_path = os.path.join(app_path, CONFIG_FILE)
    
    if not os.path.exists(config_path):
        # 如果配置文件不存在，创建默认的
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("gcj02")
        return "gcj02"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        t = f.read().strip().lower()
    return t if t in ("gcj02", "bd09") else "gcj02"

# ===================== 主入口 =====================
def main():
    app_path = get_app_path()
    # 重点：这里硬编码了 input.xlsx 和 output.xlsx
    # 这意味着你的 Excel 必须叫 input.xlsx，输出会生成 output.xlsx
    input_excel = os.path.join(app_path, "input.xlsx")
    output_excel = os.path.join(app_path, "output.xlsx")

    if not os.path.exists(input_excel):
        print("❌ 错误：在当前程序目录下未找到 'input.xlsx'")
        print(f"当前程序所在路径：{app_path}")
        print("请确保 Excel 文件名为 input.xlsx 并放在同一目录下！")
        input("按回车键退出...")
        return

    try:
        source_type = get_source_type()
        print(f"✅ 当前模式：{source_type} -> WGS84")
        batch_convert_excel(input_excel, output_excel, source_type)
        print(f"✅ 转换完成！结果已保存至：{output_excel}")
    except Exception as e:
        print(f"❌ 发生未知错误：{e}")

    input("按回车键关闭窗口...")

if __name__ == "__main__":
    main()
