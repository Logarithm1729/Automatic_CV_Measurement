import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from time import strftime
import tqdm
import os
from typing import List, Tuple

BASE_DIR = "/Users/極微太郎/Documents/CV測定プログラム"
CSV_DIR = os.path.join(BASE_DIR, "results")
IMG_DIR = os.path.join(BASE_DIR, "images")

def format_to_date(name: str, last: str):
    if name != "": return name + last

    return strftime("%Y_%m_%d_%H_%M_%S") + last

class MeasurementCV:
    def __init__(self, instance, freq, start, end, ticks, times) -> None:       
        
        # 開始電圧が終了電圧より低い場合、以下の処理で反転させる
        if start > end:
            self.ticks = -ticks
        else:
            self.ticks = ticks
        
        self.ins = instance # USB通信のインスタンス
        self.freq = freq # 周波数
        self.start = start # 開始電圧
        self.end = end # 終了電圧
        self.times = times #　測定回数
        self.size = int((self.end - self.start) // self.ticks + 1) # データサイズ

    def imp_to_C(self, imp: float) -> float:
        """
        [要約]
            CV測定器からはインピーダンスと位相が出力される。
            この関数はインピーダンスからキャパシタンスを変換する
        
        [引数]
            imp {float} -- [インピーダンス]
        
        [return]
            C {float} -- [キャパシタンス]
        """
        
        return (2*np.pi*self.freq*float(imp))**-1

    def get_machine_name(self) -> str:
        """
        [要約]
            CV測定器の情報を取得し、出力する
        
        [引数]
            なし
        
        [return]
            機器情報 {str} -- [型番や機器名]
        """
        
        self.ins.write("*IDN?")
        output = self.ins.read()
        return output

    def check_error(self) -> str:
        """
        [要約]
            CV測定器でのエラーを確認し、出力する
        
        [引数]
            なし
        
        [return]
            エラー情報 {str} -- [エラー情報]
        """
        
        self.ins.write("*ESR?")
        output = self.ins.read()
        return output

    def base(self, voltage: float) -> Tuple[str, str]:
        """
        [要約]
            任意の電圧の一点を測定し出力する
            周波数はself.freqを使用する
        
        [引数]
            voltage {float} -- [電圧値]
        
        [return]
            測定結果 {tuple(str, str)} -- [tupleの中身 >> (インピーダンス, 位相)]
        """

        # config
        self.ins.write("*RST")
        self.ins.write(":TRIGger EXTernal")
        self.ins.write(f":FREQuency {self.freq}")
        self.ins.write(":LEVel V")
        self.ins.write(f":LEVel:VOLTage {voltage}")
        self.ins.write(":SPEEd SLOW")

        # measurement
        self.ins.write("*TRG")
        self.ins.write(":MEASure?")

        # get data and format
        data = self.ins.read()
        data = list(map(lambda x: x.replace(" ", ""), data.split(",")))

        # return impedance
        return data[0], data[1]

    def get_voltage_sweap_data(self):
        """
        [要約]
            周波数固定で電圧を掃引する測定を行う
            開始電圧や終了電圧、周波数と測定回数はselfから引用している
        
        [引数]
            なし
        
        [return]
            測定結果の4次元配列 {numpy.ndarray} -- [
                1次元 -> 測定回数 (平均値を格納するため+1している)
                2次元 -> 行きと帰り
                3次元 -> データサイズ (0V ~ 1Vで0.1Vずつなら10となる)
                4次元 -> 電圧とキャパシタンス
            ]
        """
        
        # 結果用のNumpy配列生成し、0で初期化
        result = np.zeros((self.times + 1, 2, self.size, 2))

        # 測定回数のループ
        for t in range(self.times):
            print("-"*100)
            print(f"{t+1}回目 測定開始")
            print("-"*100)
            
            # 行きの測定
            print("start >>> end 測定中...")
            for idx, v in enumerate(tqdm.tqdm(np.arange(self.start, self.end, self.ticks))):
                imp, phase = self.base(v)
                result[t, 0, idx, 0] = v
                result[t, 0, idx, 1] = self.imp_to_C(imp)
            print()
            
            # 帰りの測定
            print("end >>> start 測定中...")
            for idx, v in enumerate(tqdm.tqdm(np.arange(self.end, self.start, -self.ticks))):
                imp, phase = self.base(v)
                result[t, 1, idx, 0] = v
                result[t, 1, idx, 1] = self.imp_to_C(imp)
            print()
            
            print(f"{t+1}回目 測定終了")
            print()

        # 以下、平均値を計算し取得する
        
        # 行きの平均値
        for idx, v in enumerate(np.arange(self.start, self.end, self.ticks)):
            result[-1, 0, idx, 0] = v
            result[-1, 0, idx, 1] = np.average(result[:-1, 0, idx, 1])
        
        # 帰りの平均値
        for idx, v in enumerate(np.arange(self.end, self.start, -self.ticks)):
            result[-1, 1, idx, 0] = v
            result[-1, 1, idx, 1] = np.average(result[:-1, 1, idx, 1])

        return result

class PlotData:

    def __init__(self, data, linewidth, linestyle, is_grid, is_forward, is_back) -> None:
        self.data = data # Numpy配列を取得
        self.times = data.shape[0] - 1 # 測定回数を取得 (平均値の分を引く)
        self.linewidth = linewidth # グラフの線の太さ
        self.linestyle = linestyle # グラフの線スタイル
        self.is_grid = is_grid # グリッド表示
        self.is_forward = is_forward # 行きをプロットするかどうか
        self.is_back = is_back # 帰りをプロットするかどうか
        self.fig = plt.figure(dpi=100) # フィギュアの生成
    
    def figure_setup(self, y_range: Tuple[float, float]) -> None:
        """
        [要約]
            グラフ表示のmax, minなど指定された時に実行する関数
        
        [引数]
            y_range {tuple(float, float)} -- [ tuple(max, min) ]
                    
        [return]
            なし
        """
        y_min, y_max = y_range
        plt.ylim(y_min, y_max)
        
    
    def plot_avg_else(self) -> None:
        """
        [要約]
            測定回数分の結果をプロットする
        
        [引数]
            なし
        
        [return]
            なし
        """
        
        # 測定回数のループ
        for t in range(self.times):
            # もし行きのプロットをするなら、プロットする
            if self.is_forward:
                plt.plot(self.data[t, 0, :, 0], self.data[t, 0, :, 1], label=f"foward {t+1}times", lw=self.linewidth, linestyle=self.linestyle)
            
            # もし帰りのプロットをするなら、プロットする
            if self.is_back:
                plt.plot(self.data[t, 1, :, 0], self.data[t, 1, :, 1], label=f"back {t+1}times", lw=self.linewidth, linestyle=self.linestyle)

    def plot_avg(self) -> None:
        """
        [要約]
            平均値をプロットする
        
        [引数]
            なし
        
        [return]
            なし
        """
        
        # もし行きのプロットをするなら、プロットする
        if self.is_forward:
            plt.plot(self.data[-1, 0, :, 0], self.data[-1, 0, :, 1], label=f"foward average", lw=self.linewidth, linestyle=self.linestyle)
        
        # もし帰りのプロットをするなら、プロットする
        if self.is_back:
            plt.plot(self.data[-1, 1, :, 0], self.data[-1, 1, :, 1], label=f"back average", lw=self.linewidth, linestyle=self.linestyle)

    def preview(self) -> None:
        """
        [要約]
            PC画面上にプロット結果を表示する
        
        [引数]
            なし
        
        [return]
            なし
        """
        plt.legend()
        plt.grid(self.is_grid)
        plt.show()
    
    def save_figure(self, img_name: str, is_stansparent: bool) -> None:
        """
        [要約]
            プロット結果を保存する
        
        [引数]
            img_name {str} -- [画像保存名で指定がなければ現在時刻に変換する]
            is_transparent {bool} -- [保存する画像の背景を透過させるかどうか]
        
        [return]
            なし
        """
        
        plt.legend()
        plt.grid(self.is_grid)
        img_name = format_to_date(img_name, ".png")
        IMG_PATH = os.path.join(IMG_DIR, img_name)
        plt.savefig(IMG_PATH, transparent=is_stansparent, dpi=400)

class OutputCSV:
    
    def __init__(self, data, dir_name) -> None:
        self.data = data # Numpy配列を取得
        self.times = data.shape[0] - 1 # 測定回数を取得 (平均値の分を引く)
        self.dir_name = format_to_date(dir_name, "") # 複数のCSVファイルを保存するフォルダの名前
    
    def output(self) -> None:
        """
        [要約]
            CSVファイルをディレクトリに保存していく
        
        [引数]
            なし
        
        [return]
            なし
        """
        
        SAVE_DIR = os.path.join(CSV_DIR, self.dir_name)
        os.makedirs(SAVE_DIR, exist_ok=True)
        
        # 測定回数分をCSVファイルへ変換・出力
        for t in range(self.times):
            for i in range(2):
                vector = "行き" if i == 0 else "帰り"
                file_name = os.path.join(SAVE_DIR, f"{t+1}回目_{vector}.csv")
                tmp = pd.DataFrame(self.data[t, i])
                tmp.to_csv(file_name)
        
        # 平均値をCSVファイルへ変換・出力
        for i in range(2):
            vector = "行き" if i == 0 else "帰り"
            file_name = os.path.join(SAVE_DIR, f"平均値_{vector}.csv")
            tmp = pd.DataFrame(self.data[-1, i])
            tmp.to_csv(file_name)