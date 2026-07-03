import math
import pandas as pd

PI = 3.14159265358979324
A = 6378245.0
EE = 0.006693421622965943

# 判断是否在中国境内
def out_of_china(lng, lat):
    if lng < 72.004 or lng > 137.8347:
        return True
    if lat < 0.8293 or lat > 55.8271:
        return True
    return False

# WGS84转GCJ02（内部计算用）
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

# GCJ02火星坐标 转 WGS84
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

# BD09百度坐标 转 GCJ02
def bd09_to_gcj02(bd_lng, bd_lat):
    x = bd_lng - 0.0065
    y = bd_lat - 0.006
    z = math.sqrt(x * x + y * y) - 0.00002 * math.sin(y * PI)
    theta = math.atan2(y, x) - 0.000003 * math.cos(x * PI)
    gcj_lng = z * math.cos(theta)
    gcj_lat = z * math.sin(theta)
    return [gcj_lng, gcj_lat]

# BD09百度坐标 直接转 WGS84
def bd09_to_wgs84(bd_lng, bd_lat):
    gcj = bd09_to_gcj02(bd_lng, bd_lat)
    return gcj02_to_wgs84(gcj[0], gcj[1])

# 内部辅助计算函数
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

# ===================== 批量Excel转换函数 =====================
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

# ===================== 测试示例 =====================
if __name__ == "__main__":
    # 单点测试
    # gcj_lng, gcj_lat = 121.473701, 31.230416
    # wgs = gcj02_to_wgs84(gcj_lng, gcj_lat)
    # print("GCJ02转WGS84：", round(wgs[0],6), round(wgs[1],6))

    # bd_lng, bd_lat = 121.480325, 31.236868
    # wgs2 = bd09_to_wgs84(bd_lng, bd_lat)
    # print("BD09转WGS84：", round(wgs2[0],6), round(wgs2[1],6))

    # 批量Excel转换（修改文件路径即可）
    batch_convert_excel(
        file_path="/Users/xuming/python/PycharmProjects/地址转经纬度/火星坐标转WGS84.xlsx",
        output_path="/Users/xuming/python/PycharmProjects/地址转经纬度/火星坐标转WGS84结果.xlsx",
        source_type="gcj02" # gcj02 / bd09
    )