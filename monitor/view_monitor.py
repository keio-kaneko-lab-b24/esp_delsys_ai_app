import re
import numpy as np
from itertools import count
import matplotlib.pyplot as plt
import matplotlib.gridspec as gridspec
from matplotlib.animation import FuncAnimation
import time
import json
import common

args = common.load_args()
monitor_file, label_file = common.load_files(args.taskType, args.taskNumber)

# パラメータ
with open("param.json") as f:
    param = json.load(f)


plt.rcParams['font.size'] = '10'
plt.style.use("fivethirtyeight")

# キャンパスの設定
fig = plt.figure(figsize=(12, 8))
outer = gridspec.GridSpec(2, 2, wspace=0.2, hspace=0.5)
inner = gridspec.GridSpecFromSubplotSpec(2, 1,
                                         subplot_spec=outer[0], wspace=0, hspace=1.2)

ax00 = plt.Subplot(fig, inner[0])
ax01 = plt.Subplot(fig, inner[1])
ax1 = plt.Subplot(fig, outer[1])
ax2 = plt.Subplot(fig, outer[2])
ax3 = plt.Subplot(fig, outer[3])

fig.add_subplot(ax00)
fig.add_subplot(ax01)
fig.add_subplot(ax1)
fig.add_subplot(ax2)
fig.add_subplot(ax3)

# アニメーションのフレーム間隔（ms）
animation_interval = 250

# monitorが生成されるまで待機
count = 0
while True:
    t = -99
    try:
        with open(monitor_file, "r") as f:
            break
    except:
        pass
    if t == -99:
        print("monitor.py: waiting for setup...")
        time.sleep(1)

        count += 1
        if count > 10:
            raise EOFError(f"{monitor_file}に不備があります。\n筋電計が接続されていることを確認してください。")
    else:
        break


def load():
    extensor_row = []
    flexor_row = []
    extensor_processed = []
    flexor_processed = []
    gu = []
    pa = []
    useML = True
    flexor_threshold = 0
    extensor_threshold = 0
    rock_flexor_lower_limit = 0
    rock_extensor_upper_limit = 0
    paper_extensor_lower_limit = 0
    paper_flexor_upper_limit = 0

    with open(monitor_file, "r") as file:
        for line in file.readlines():

            # 生データ
            mc = re.match("^([ef]): ([0-9]+)\n", line)
            if mc:
                if mc[1] == "e":
                    extensor_row.append(int(mc[2]))
                else:
                    flexor_row.append(int(mc[2]))
                continue

            # 信号処理後データ
            mc = re.match("^(e_sp): ([+-]?\\d+(?:\\.\\d+)?)\n", line)
            if mc:
                if mc[1] == "e_sp":
                    extensor_processed.append(float(mc[2]))
            mc = re.match("^(f_sp): ([+-]?\\d+(?:\\.\\d+)?)\n", line)
            if mc:
                if mc[1] == "f_sp":
                    flexor_processed.append(float(mc[2]))
                continue

            # 出力
            gr = re.search("out1 = ([0-9\\.]+), out2 = ([0-9\\.]+)", line)
            if gr:
                gu.append(float(gr.group(1)))
                pa.append(float(gr.group(2)))
                continue

            # UseMLパラメータ
            gr = re.search("UseML is (True|False)", line)
            if gr:
                if gr.group(1) == "True":
                    useML = True
                elif gr.group(1) == "False":
                    useML = False

            # 閾値
            gr = re.search("ExtensorThreshold: ([0-9\\.]+)", line)
            if gr:
                extensor_threshold = gr.group(1)
            gr = re.search("FlexorThreshold: ([0-9\\.]+)", line)
            if gr:
                flexor_threshold = gr.group(1)
            gr = re.search("RockFlexorLowerLimit: ([0-9\\.]+)", line)
            if gr:
                rock_flexor_lower_limit = gr.group(1)
            gr = re.search("RockExtensorUpperLimit: ([0-9\\.]+)", line)
            if gr:
                rock_extensor_upper_limit = gr.group(1)
            gr = re.search("PaperExtensorLowerLimit: ([0-9\\.]+)", line)
            if gr:
                paper_extensor_lower_limit = gr.group(1)
            gr = re.search("PaperFlexorUpperLimit: ([0-9\\.]+)", line)
            if gr:
                paper_flexor_upper_limit = gr.group(1)

    return extensor_row, flexor_row, extensor_processed, flexor_processed, gu, pa, useML,\
        extensor_threshold, flexor_threshold, rock_flexor_lower_limit, rock_extensor_upper_limit,\
        paper_extensor_lower_limit, paper_flexor_upper_limit


def animate(i):
    ax00.cla()
    ax01.cla()
    ax1.cla()
    ax2.cla()
    ax3.cla()

    extensor_row, flexor_row, extensor_processed, flexor_processed, gu, pa, useML, extensor_threshold, flexor_threshold, rock_flexor_lower_limit, rock_extensor_upper_limit, paper_extensor_lower_limit, paper_flexor_upper_limit = load()

    try:
        # 生データ
        view_yaxis_max = param["monitor"]["view_monitor"]["raw_data_view_yaxis_max"]
        view_yaxis_min = param["monitor"]["view_monitor"]["raw_data_view_yaxis_min"]
        extensor_row = extensor_row[-500:]
        flexor_row = flexor_row[-500:]
        axis_x = np.arange(len(extensor_row))
        axis_x = axis_x / 100  # 注意： 「100」は筋電のHzなどによって変動する
        ax00.plot(axis_x, extensor_row, label='extensor',
                  color=u'#1f77b4', linewidth=1)
        # ax00.plot(axis_x, np.ones(len(extensor_row)) * view_yaxis_max, alpha=0)
        # ax00.plot(axis_x, np.ones(len(extensor_row)) * view_yaxis_min, alpha=0)
        ax00.legend(loc='upper right')
        ax00.set_ylabel('(mV)', fontsize=12)

        ax01.plot(axis_x, flexor_row, label='flexor',
                  color=u'#ff7f0e', linewidth=1)
        # ax01.plot(axis_x, np.ones(len(extensor_row)) * view_yaxis_max, alpha=0)
        # ax01.plot(axis_x, np.ones(len(extensor_row)) * view_yaxis_min, alpha=0)
        ax01.legend(loc='upper right')
        ax01.set_xlabel('time(s)', fontsize=12)
        ax01.set_ylabel('(mV)', fontsize=12)

        # 信号処理後データ
        extensor_processed = extensor_processed[-50:]
        flexor_processed = flexor_processed[-50:]
        axis_x = np.arange(len(extensor_processed))
        axis_x = axis_x / 10  # 注意： 「10」はPREDICT_HZなどによって変動する
        ax1.plot(axis_x, flexor_processed,
                 label='flexor', color=u'#ff7f0e')
        ax1.plot(axis_x, extensor_processed,
                 label='extensor', color=u'#1f77b4')
        # プロットの上限と下限を設定
        view_yaxis_max = param["monitor"]["view_monitor"]["sp_data_view_yaxis_max"]
        view_yaxis_min = param["monitor"]["view_monitor"]["sp_data_view_yaxis_min"]
        ax1.plot(axis_x, np.ones(len(extensor_processed))
                 * view_yaxis_max, alpha=0)
        ax1.plot(axis_x, np.ones(len(extensor_processed))
                 * view_yaxis_min, alpha=0)
        ax1.legend(loc='upper right')
        ax1.set_title("PROCESSED EMG", size=14)
        ax1.set_xlabel('time(s)', fontsize=12)
        ax1.set_ylabel('(mV)', fontsize=12)

        # 判定結果
        pa = pa[-50:]
        gu = gu[-50:]
        axis_x = np.arange(len(pa))
        axis_x = axis_x / 10  # 注意： 「10」はPREDICT_HZなどによって変動する
        ax2.plot(axis_x, gu, label='rock', color=u'#ff7f0e')
        ax2.plot(axis_x, pa, label='paper', color=u'#1f77b4')
        ax2.plot(axis_x, np.ones(len(pa)), alpha=0)
        ax2.plot(axis_x, np.zeros(len(pa)), alpha=0)
        ax2.legend(loc='upper right')
        ax2.set_xlabel('time(s)', fontsize=12)

        useML_text = "ML: True\n" if useML else "ML: False\n"
        if useML:
            threshold_text = f"Rock: {flexor_threshold}\nPaper: {extensor_threshold}"
        else:
            threshold_text1 = f"Rock :  Flexor  > {rock_flexor_lower_limit}, Extensor < {rock_extensor_upper_limit}\n"
            threshold_text2 = f"Paper: Extensor > {paper_extensor_lower_limit},  Flexor  < {paper_flexor_upper_limit}"
            threshold_text = threshold_text1 + threshold_text2
        ax2.set_title(useML_text + threshold_text, size=14)

    except:
        pass


ani = FuncAnimation(plt.gcf(), animate, interval=animation_interval)

plt.show()
