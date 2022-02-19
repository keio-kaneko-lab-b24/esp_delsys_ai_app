import re
import time
import pygame.mixer
from define_task import define_task
import common

args = common.load_args()
monitor_file, label_file = common.load_files(args.taskType, args.taskNumber)


def sound(source):
    '''音を鳴らす'''
    pygame.mixer.music.load(f"sound/{source}")
    pygame.mixer.music.play(1)


def instruct(instruction, keep_time):
    '''1つの指示（グー/パー/レスト）を教師ラベルとしてlabel.txtに追記する'''

    # monitor読み込み
    # 10ms以下で完了できる
    with open(monitor_file, "r") as f:
        for line in f.readlines()[::-1]:
            if "time: " in line:
                t = int(re.match(".*time:\ ?([.0-9]+)", line)[1])
                break

    # 教師として書き込み
    with open(label_file, "a") as f:
        f.write(f"{t}: {instruction}\n")

    # コマンドラインへ表示
    print(f"指示-> {instruction}をしてください。\n")

    # 音を鳴らす
    is_first = True
    for _ in range(keep_time):
        if is_first:
            sound(source="pi.mp3")
            is_first = False
        else:
            sound(source="po.mp3")

        # 正確にはinstruct全体で{keep_time}秒になる必要があるが、多少長くなっても問題ないのでこのまま
        time.sleep(1)

    return True


# =======
# タスク
# =======

# タスク取得
pre_task, task = define_task(args.taskType)

pygame.mixer.init()

# monitorがセットされているか確認
# 5秒待ってもセットされなければエラーを出す
count = 0
while True:
    t = -99
    with open(monitor_file, "r") as f:
        for line in f.readlines()[::-1]:
            if "time: " in line:
                t = int(re.sub("[^0-9]", "", line))
                break

    if t == -99:
        print("input_external.py: waiting for setup...")
        time.sleep(1)

        count += 1
        if count > 5:
            raise EOFError("monitor.txtに不備があります。\n筋電計が接続されていることを確認してください。")
    else:
        break

# 初期化
with open(label_file, "w") as f:
    f.write("\n")

# 5秒待機
waiting_time_seconds = 5
print(f"### {waiting_time_seconds}秒後に開始します ###")
for i in range(waiting_time_seconds, 0, -1):
    time.sleep(1)

# タスク用： pre-task + task
time.sleep(3)
all_task = pre_task + task

for task_ in all_task:

    instruction = task_[0]
    keep_time = task_[1]

    instruct(instruction=instruction, keep_time=keep_time)

pygame.mixer.music.stop()

print("課題は終了しました。Ctrl+Cを押してください。")
