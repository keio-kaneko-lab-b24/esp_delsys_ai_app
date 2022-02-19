'''学習のためのデータセットを作成する関数'''

import argparse
import os
import re
import glob
import pandas as pd
import time


# パラメータ
parser = argparse.ArgumentParser()
parser.add_argument('--useTask', nargs='*')
parser.add_argument('--test', action='store_true')
args = parser.parse_args()
useTask = args.useTask

# ファイルパス
label_file_path = f"{os.path.dirname(__file__)}/../monitor/file/label/"
monitor_file_path = f"{os.path.dirname(__file__)}/../monitor/file/monitor/"
dataset_file_path = f"{os.path.dirname(__file__)}/dataset/"


def fix_times(times):
    # label.txtが故障している場合の修復
    # https://github.com/tmizuguc/esp_app/issues/8
    fixed_times = times.copy()
    for t_i, t in enumerate(times):
        if t_i == 0:
            continue
        if t < times[t_i - 1]:
            fixed_times[t_i] = times[t_i - 1] + 3000
    return fixed_times


def load_label_data(task_name, task_num):
    '''labelファイルから教示ラベルを読み込む'''
    try:
        with open(label_file_path + f"label_{task_name}_{task_num}.txt", "r") as f:
            times = []
            labels = []

            for line in f.readlines():
                gr = re.search("^([0-9]+): ([a-z]+)\n", line)
                if gr:
                    times.append(int(gr.group(1)))
                    labels.append(gr.group(2))
    except:
        raise FileNotFoundError

    # label.txtが故障している場合の修復
    # https://github.com/tmizuguc/esp_app/issues/8
    times = fix_times(times)

    df_label = pd.DataFrame({"time": times, "label": labels})

    return df_label


def load_emg_sp_data(task_name, task_num):
    '''monotorファイルからRMS筋電を読み込む'''
    try:
        with open(monitor_file_path + f"monitor_{task_name}_{task_num}.txt", "r") as f:
            lines = f.readlines()
    except:
        raise FileNotFoundError

    _time = False
    _extensor_sp = False
    _flexor_sp = False
    times = []
    extensor_sps = []
    flexor_sps = []

    for line in lines:
        if "time:" in line:
            # 通常は「time: 12505」のようになっているが，
            # 稀に「out1 = 0, out2 = 0;time: 120585」のようになっている場合があるのでre.matchで対応
            _time = int(re.match(".*time:\ ?([.0-9]+)", line)[1])

        mc = re.match("^(e_sp): ([+-]?\\d+(?:\\.\\d+)?)\n", line)
        if mc:
            if mc[1] == "e_sp":
                _extensor_sp = float(mc[2])
        mc = re.match("^(f_sp): ([+-]?\\d+(?:\\.\\d+)?)\n", line)
        if mc:
            if mc[1] == "f_sp":
                _flexor_sp = float(mc[2])

        if (_time is not False) & (_extensor_sp is not False) & (_flexor_sp is not False):
            times.append(_time)
            extensor_sps.append(_extensor_sp)
            flexor_sps.append(_flexor_sp)
            _time = False
            _extensor_sp = False
            _flexor_sp = False

        # f_spのみ、f_spとe_spのみの場合は途中から記録できた場合なので、棄却する
        if (_flexor_sp is not False) & (_extensor_sp is False) & (_time is False):
            _time = False
            _extensor_sp = False
            _flexor_sp = False
        if (_flexor_sp is not False) & (_extensor_sp is not False) & (_time is False):
            _time = False
            _extensor_sp = False
            _flexor_sp = False

    df_emg_sp = pd.DataFrame(
        {"time": times, "extensor_sp": extensor_sps, "flexor_sp": flexor_sps})

    return df_emg_sp


def load_sp_dataset(task_name, task_num):
    '''label, monotorファイルから，教示信号とRMS筋電のデータセットを作成する'''
    df_label = load_label_data(task_name, task_num)
    df_emg_sp = load_emg_sp_data(task_name, task_num)

    _df = pd.merge_asof(df_emg_sp, df_label, on="time",
                        direction="backward").dropna()

    _df["task_name"] = task_name
    _df["task_num"] = task_num

    # 整理
    _df = _df[["task_name", "task_num", "label",
               "extensor_sp", "flexor_sp", "time"]]
    return _df


def get_task_num(task_name):
    '''使用可能なtask_num一覧を取得する'''
    label_files = glob.glob(f"{label_file_path}/*{task_name}_[0-9]*")
    label_num = [int(re.match(
        f".+label_{task_name}_(.+).txt", label_file)[1]) for label_file in label_files]

    monitor_files = glob.glob(f"{monitor_file_path}/*{task_name}_[0-9]**")
    monitor_num = [int(re.match(
        f".+monitor_{task_name}_(.+).txt", monitor_file)[1]) for monitor_file in monitor_files]

    return list(set(label_num) & set(monitor_num))


def add_count_idx(df):
    '''データセットに教示番号（count_idx）を付与する'''
    df = df.reset_index(drop=True)

    last_label = None
    count_idx = -1
    count_idx_list = []
    for i in df.index:
        row = df.iloc[i]
        label = row["label"]
        if label == last_label:
            count_idx_list.append(count_idx)
            pass
        else:
            last_label = label
            count_idx += 1
            count_idx_list.append(count_idx)

    df["count_idx"] = count_idx_list
    return df


start_time = time.perf_counter()

_df_sp_list = []
use_tasks = []
cannot_use_tasks = []
for task_name in useTask:

    task_num_list = get_task_num(task_name)
    for task_num in task_num_list:
        try:
            _df_sp = load_sp_dataset(task_name, task_num)
            _df_sp_list.append(_df_sp)
            use_tasks.append(f"{task_name} {task_num}")
        except:
            cannot_use_tasks.append(f"{task_name} {task_num}")

df_sp = pd.concat(_df_sp_list)
df_sp = add_count_idx(df_sp)

# 保存
df_sp.to_json(dataset_file_path + "sp.json", orient='records')

end_time = time.perf_counter()

# レポート
print("\n**FINISH**\n")
print(f"■ 経過時間\n{end_time - start_time: .1f}秒")
if len(use_tasks) > 0:
    print("■ 使用タスク")
    for t in use_tasks:
        print(t)

if len(cannot_use_tasks) > 0:
    print("■ 使用不可タスク")
    for t in cannot_use_tasks:
        print(t)

print("■ データ数")
print(f"{len(df_sp)}")
