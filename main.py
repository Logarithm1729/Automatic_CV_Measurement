print("準備中...", "")

import pyvisa
import json
import os
import time

from modules import MeasurementCV, PlotData, OutputCSV

BASE_DIR = "/Users/極微太郎/Documents/CV測定プログラム"
os.chdir(BASE_DIR)

def setup():
    """
        [要約]
            グラフ保存やCSVファイルを保存するフォルダの生成、
            USBインスタンスを生成し出力する
        
        [引数]
            なし
        
        [return]
            USBインスタンス
    """
    
    IMG_PATH = os.path.join(BASE_DIR, "images")
    RES_PATH = os.path.join(BASE_DIR, "results")
    os.makedirs(IMG_PATH, exist_ok=True)
    os.makedirs(RES_PATH, exist_ok=True)
    
    rm = pyvisa.ResourceManager()
    # get resoruces connected this pc
    visa_list = rm.list_resources()
    # get cv-machine's info
    target_usb = visa_list[0]
    # initiarization cv-machine instance
    target_ins = rm.open_resource(target_usb)
    
    return target_ins

# config.jsonファイルの読み込み
config = json.load(open("./config.json", encoding="utf-8"))
base_info = config["測定情報"] # 測定情報の読み込み
graph_info = config["グラフ関連"] # グラフ情報の読み込み
csv_info = config["csvファイル出力"] # CSVファイル情報の読み込み

# 測定情報から以下の情報を取得
freq = base_info["周波数[Hz]"]
start = base_info["開始電圧[V]"]
end = base_info["終了電圧[V]"]
ticks = base_info["間隔[V]"]
times = base_info["測定回数"]

def error_check() -> bool:
    """
        [要約]
            configファイル内で不適な指定がされた時のチェックを行う
        
        [引数]
            なし
        
        [return]
            エラーの有無 {bool} -- [エラーがあればFalse, なければTrue]
    """
    if times < 2:
        print("繰り返し回数は2回以上にしてください")
        return False

    if graph_info["縦軸の最大値"] is not None and graph_info["縦軸の最小値"] is None:
        print("最大値、最小値の片方のみの指定はできません")
        return False

    if graph_info["縦軸の最小値"] is not None and graph_info["縦軸の最大値"] is None:
        print("最大値、最小値の片方のみの指定はできません")
        return False
    
    return True


def main() -> None:
    """
        [要約]
            modules.pyからクラスを読み込み、configファイルから取得した通りに必要な関数を実行していく
        
        [引数]
            なし
        
        [return]
            なし
    """
    
    if error_check() is False:
        print()
        print("３秒後に終了します...")
        time.sleep(3)
        exit()
    
    # 測定インスタンスを生成
    mcv = MeasurementCV(setup(), freq, start, end, ticks, times)
    data = mcv.get_voltage_sweap_data() # 測定結果の４次元Numpy配列
    
    # plot
    if graph_info["プレビューを表示"] or graph_info["グラフを保存"]:
        graph = PlotData(data,
                         linewidth=graph_info["線の太さ"],
                         linestyle=graph_info["線の種類"],
                         is_grid=graph_info["グリッドの表示"],
                         is_forward=graph_info["行きをプロット"],
                         is_back=graph_info["帰りをプロット"]
                         )
        
        if graph_info["平均値以外をプロット"]:
            graph.plot_avg_else()
        
        if graph_info["平均値をプロット"]:
            graph.plot_avg()

        if graph_info["縦軸の最大値"] is not None and graph_info["縦軸の最小値"] is not None:
            graph.figure_setup(
                y_range=(graph_info["縦軸の最大値"], graph_info["縦軸の最小値"])
            )
        
        if graph_info["プレビューを表示"]:
            graph.preview()
        
        if graph_info["グラフを保存"]:
            graph.save_figure(img_name=graph_info["グラフの保存名"],
                              is_stansparent=graph_info["背景透過"]
                              )
        

    # csv output
    if csv_info["csvへ出力"]:
        csv = OutputCSV(data, csv_info["csvフォルダ名"])
        csv.output()

if __name__ == "__main__":
    main()