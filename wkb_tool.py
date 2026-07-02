import pandas as pd
from shapely import wkb
from shapely.errors import ShapelyError
import os
import sys

# 1、mac生成的是unix可执行文件
# 进入文件夹 cd /Users/xuming/python/PycharmProjects/让excel飞/常用工具
# 生成可执行文件 pyinstaller -F -w wkb_tool.py
# 2、windows生成的是exe可执行文件
# 安装 Python3.10
# pip install pandas shapely pyinstaller
# 将 wkb_tool.py 拷贝进 Windows 虚拟机；
# #进入文件夹 cd C:\Users\xuming\python\PycharmProjects\让excel飞\常用工具
# 生成可执行文件 pyinstaller -F wkb_tool.py 不加 -w：双击 exe，弹出黑色 CMD 窗口
# 生成可执行文件 pyinstaller -F -w wkb_tool.py 加 -w：只弹出软件界面，无黑色 CMD 窗口


def parse_wkb_all(hex_str):
    if pd.isna(hex_str) or str(hex_str).strip() == "":
        return ("", None, None)
    try:
        bin_wkb = bytes.fromhex(str(hex_str).strip())
        geom = wkb.loads(bin_wkb)
        wkt = geom.wkt
        lon = geom.centroid.x
        lat = geom.centroid.y
        return (wkt, lon, lat)
    except (ShapelyError, ValueError, TypeError):
        return ("无效WKB", None, None)

# 读取配置文件
CONFIG_FILE = "config.txt" # 定义配置文件名

def get_wkb_column():
    config_path = os.path.join(app_path, CONFIG_FILE)
    if not os.path.exists(config_path):
        # 如果配置文件不存在，创建一个默认的
        with open(config_path, 'w', encoding='utf-8') as f:
            f.write("polygon_geom") # 写入默认列名
        return "polygon_geom"
    
    with open(config_path, 'r', encoding='utf-8') as f:
        col_name = f.read().strip()
    return col_name

def main():
    # 自动获取当前程序所在文件夹（解决路径错位问题）
    if hasattr(sys, '_MEIPASS'):
        # 打包后临时目录
        app_path = os.path.dirname(sys.executable)
    else:
        # 本地py脚本运行
        app_path = os.path.dirname(os.path.abspath(__file__))
    
    INPUT_CSV_NAME = "原始数据.csv"
    INPUT_CSV = os.path.join(app_path, INPUT_CSV_NAME)
    OUTPUT_CSV = os.path.join(app_path, "解析后输出.csv")
    # ... 前面的路径定义 ...
    WKB_COL = get_wkb_column() # 调用函数获取列名
    CSV_ENCODING = "utf-8-sig"

    if not os.path.exists(INPUT_CSV):
        print(f"错误：程序同目录下未找到【{INPUT_CSV_NAME}】")
        print(f"程序存放路径：{app_path}")
        input("按回车退出...")
        return

    df = pd.read_csv(INPUT_CSV, encoding=CSV_ENCODING)
    print("读取CSV完成，列名：", df.columns.tolist())
    if WKB_COL not in df.columns:
        print(f"错误：表格不存在列【{WKB_COL}】")
        input("按回车退出...")
        return

    res = df[WKB_COL].apply(parse_wkb_all)
    df["WKT完整几何"] = [i[0] for i in res]
    df["中心点经度"] = [i[1] for i in res]
    df["中心点纬度"] = [i[2] for i in res]

    df.to_csv(OUTPUT_CSV, index=False, encoding=CSV_ENCODING)
    print(f"\n✅处理完成！输出文件：{OUTPUT_CSV}")
    input("\n按回车关闭窗口...")

if __name__ == "__main__":
    main()
