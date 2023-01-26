# 自動CV測定プログラム
- 半導体の特性の中でも重要なCV特性を自動で測定する
- 従来は手作業で行っていたがあまりも時間がかかるため作製した
- 今回のCV測定器のみではなく、modules.pyのMeasurementCVクラスのbase関数のクエリを変えるだけでその他の測定器でも使用できます

# CV測定器について
- メーカー
>HIOKI CV測定器

![machine](https://user-images.githubusercontent.com/76026039/214034119-28873e56-6968-4903-b956-4429d9756023.jpg)

- 測定電圧の限界値
>max: 2.5V
min: -2.5V

# 環境
- **python 3.x**
- pandas
- numpy
- matplotlib
- tqdm
- pyvisa

**これらがインストールされていない場合は以下のコマンドを実行してください**
```zsh
pip install numpy pandas matplotlib tqdm pyvisa

# Anacondaを使用する場合
conda install numpy pandas matplotlib tqdm pyvisa
```

### CV測定器との通信について
USBのCOMポートでの通信を採用した。COMポートとの通信のためPyVisaを使用している

# 機能
### 測定機能
1. 電圧掃引測定(周波数固定)
2. 繰り返し測定・行きと帰りの測定
3. 平均値算出


### 測定結果のプロット
1. 測定結果の波形をプレビュー表示
2. 測定結果の波形を保存
3. 平均値のみをプロットするなど、様々な指定可能

グラフのプレビュー
![terminal_graph](https://user-images.githubusercontent.com/76026039/214033712-2ff0641f-0c28-4f2a-b093-4c86caa9900c.png)

### 測定結果をCSVファイルへ出力
1. 指定された名前、もしくは現在時刻のフォルダ内に繰り返し分と平均値のCSVファイルが保存されます。

**フォルダの生成(フォルダ名が指定されていない場合は現在時刻)**
<br>

![folder](https://user-images.githubusercontent.com/76026039/214033563-0fb7fcae-f312-426a-92b5-dab1bfb0af95.png)

**フォルダ内のCSVファイル**
<br>

![csvfiles](https://user-images.githubusercontent.com/76026039/214033370-e430f236-11a0-41bc-8743-cd7997a0b17c.png)

# 使い方
config.jsonファイルを編集することで測定条件の変更やプロット、CSVファイルへの出力を選択できます。