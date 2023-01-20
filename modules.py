import numpy as np
import pandas as pd
from matplotlib import pyplot as plt
from time import strftime
import tqdm
import os

BASE_DIR = "/Users/極微太郎/Documents/CV測定プログラム"
CSV_DIR = os.path.join(BASE_DIR, "results")
IMG_DIR = os.path.join(BASE_DIR, "images")

def format_to_date(name: str, last: str):
    if name != "": return name + last

    return strftime("%Y_%m_%d_%H_%M_%S") + last

class MeasurementCV:
    def __init__(self, instance, freq, start, end, ticks, times) -> None:       
        if start > end:
            self.ticks = -ticks
        else:
            self.ticks = ticks
        
        self.ins = instance
        self.freq = freq
        self.start = start
        self.end = end
        self.times = times
        self.size = int((self.end - self.start) // self.ticks + 1)

    def imp_to_C(self, imp):
        return (2*np.pi*self.freq*float(imp))**-1

    def get_machine_name(self) -> str:
        self.ins.write("*IDN?")
        output = self.ins.read()
        return output

    def check_error(self) -> str:
        self.ins.write("*ESR?")
        output = self.ins.read()
        return output

    def base(self, voltage):
        """
        This function only get one output at specific freq and voltage.
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
        # this dimention means times, (forward, back), datasize, (voltage, C)
        result = np.zeros((self.times + 1, 2, self.size, 2))

        for t in range(self.times):
            print("-"*100)
            print(f"{t+1}回目 測定開始")
            print("-"*100)
            # forward
            print("start >>> end 測定中...")
            for idx, v in enumerate(tqdm.tqdm(np.arange(self.start, self.end, self.ticks))):
                imp, phase = self.base(v)
                result[t, 0, idx, 0] = v
                result[t, 0, idx, 1] = self.imp_to_C(imp)
            print()
            
            # back
            print("end >>> start 測定中...")
            for idx, v in enumerate(tqdm.tqdm(np.arange(self.end, self.start, -self.ticks))):
                imp, phase = self.base(v)
                result[t, 1, idx, 0] = v
                result[t, 1, idx, 1] = self.imp_to_C(imp)
            print()
            
            print(f"{t+1}回目 測定終了")
            print()

        # calculate average
        # forward
        for idx, v in enumerate(np.arange(self.start, self.end, self.ticks)):
            result[-1, 0, idx, 0] = v
            result[-1, 0, idx, 1] = np.average(result[:-1, 0, idx, 1])
        
        # back
        for idx, v in enumerate(np.arange(self.end, self.start, -self.ticks)):
            result[-1, 1, idx, 0] = v
            result[-1, 1, idx, 1] = np.average(result[:-1, 1, idx, 1])

        return result


class PlotData:

    def __init__(self, data, linewidth, linestyle, is_grid, is_forward, is_back) -> None:
        self.data = data
        self.times = data.shape[0] - 1
        self.linewidth = linewidth
        self.linestyle = linestyle
        self.is_grid = is_grid
        self.is_forward = is_forward
        self.is_back = is_back
        self.fig = plt.figure(dpi=100)
    
    def figure_setup(self, y_range):
        y_min, y_max = y_range
        plt.ylim(y_min, y_max)
        
    
    def plot_avg_else(self):
        for t in range(self.times):
            if self.is_forward:
                plt.plot(self.data[t, 0, :, 0], self.data[t, 0, :, 1], label=f"foward {t+1}times", lw=self.linewidth, linestyle=self.linestyle)
            
            if self.is_back:
                plt.plot(self.data[t, 1, :, 0], self.data[t, 1, :, 1], label=f"back {t+1}times", lw=self.linewidth, linestyle=self.linestyle)

    def plot_avg(self):
        if self.is_forward:
            plt.plot(self.data[-1, 0, :, 0], self.data[-1, 0, :, 1], label=f"foward average", lw=self.linewidth, linestyle=self.linestyle)
            
        if self.is_back:
            plt.plot(self.data[-1, 1, :, 0], self.data[-1, 1, :, 1], label=f"back average", lw=self.linewidth, linestyle=self.linestyle)

    def preview(self):
        plt.legend()
        plt.grid(self.is_grid)
        plt.show()
    
    def save_figure(self, img_name, is_stansparent):
        plt.legend()
        plt.grid(self.is_grid)
        img_name = format_to_date(img_name, ".png")
        IMG_PATH = os.path.join(IMG_DIR, img_name)
        plt.savefig(IMG_PATH, transparent=is_stansparent, dpi=400)

class OutputCSV:
    
    def __init__(self, data, dir_name) -> None:
        self.data = data
        self.times = data.shape[0] - 1
        self.dir_name = format_to_date(dir_name, "")
    
    def output(self):
        SAVE_DIR = os.path.join(CSV_DIR, self.dir_name)
        os.makedirs(SAVE_DIR, exist_ok=True)
        
        # except average
        for t in range(self.times):
            for i in range(2):
                vector = "行き" if i == 0 else "帰り"
                file_name = os.path.join(SAVE_DIR, f"{t+1}回目_{vector}.csv")
                tmp = pd.DataFrame(self.data[t, i])
                tmp.to_csv(file_name)
        
        # average
        for i in range(2):
            vector = "行き" if i == 0 else "帰り"
            file_name = os.path.join(SAVE_DIR, f"平均値_{vector}.csv")
            tmp = pd.DataFrame(self.data[-1, i])
            tmp.to_csv(file_name)
        
        return