import re
import cv2
import matplotlib.pyplot as plt
from matplotlib.animation import FuncAnimation
import common

args = common.load_args()
monitor_file, label_file = common.load_files(args.taskType, args.taskNumber)

fig = plt.figure(figsize=(5, 5))
ax = fig.add_subplot(111)

# アニメーションのフレーム間隔（ms）
animation_interval = 50

# 画像ファイル読み込み
paper_img = cv2.resize(cv2.imread('images/paper_real.jpg'), (200, 200))
paper_img = cv2.cvtColor(paper_img, cv2.COLOR_BGR2RGB)

rock_img = cv2.resize(cv2.imread('images/rock_real.jpg'), (200, 200))
rock_img = cv2.cvtColor(rock_img, cv2.COLOR_BGR2RGB)

rest_img = cv2.resize(cv2.imread('images/rest_real.jpg'), (200, 200))
rest_img = cv2.cvtColor(rest_img, cv2.COLOR_BGR2RGB)

if args.flipImage:
    paper_img = cv2.flip(paper_img, 1)
    rock_img = cv2.flip(rock_img, 1)
    rest_img = cv2.flip(rest_img, 1)


def load_state():
    try:
        with open(label_file, "r") as f:
            line = f.readlines()[-1]
            state = line.split(":")[1]
            state = re.sub(r"\n|\ ", "", state)
    except:
        state = "rest"
    return state


def animate(i):
    ax.cla()
    state = load_state()

    # stateが変化していたら再描写
    if state == "rock":
        plt.imshow(rock_img)
    elif state == "paper":
        plt.imshow(paper_img)
    else:
        plt.imshow(rest_img)


ani = FuncAnimation(plt.gcf(), animate, interval=animation_interval)

plt.show()
