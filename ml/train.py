import pandas as pd
import numpy as np
import os
import random as rn
import tensorflow as tf
import subprocess
import time

from lib.normalize import normalize
from lib.delete_missrep import delete_missrep
from lib.delete_spike import delete_spike
from lib.delete_last_cid import delete_last_cid
from lib.util_ml import model_train, convert_to_tflite, check_if_model_and_tfmodel_is_almost_equal

os.environ['TF_CPP_MIN_LOG_LEVEL'] = '3'

# シードの固定
# https://pretagteam.com/question/results-not-reproducible-with-keras-and-tensorflow-in-python
os.environ['PYTHONHASHSEED'] = '0'
np.random.seed(37)
rn.seed(1254)
tf.random.set_seed(1234)

# ===============
# 基本パラメータ
# ===============
LABEL_TO_INT = {"rock": 0, "paper": 1, "rest": 2}  # 各ラベルに対する出力ノード
INPUT_SIZE = 2  # 筋電の数。デフォルト：2 （EDC, FDP）
PARAM_PATH = "./src/param.h"  # パラメータを保存するパス
MODEL_DIR = "./ml/dataset/model"  # Kerasモデルのパス
TFLITE_MODEL_PATH = "./ml/dataset/model.tflite"  # TFLiteモデルのパス
C_MODEL_PATH = "./src/model.cpp"  # Cモデルのパス
MODEL_TRAIN_DETAIL = True  # モデル学習時の詳細を表示する

# ===============
# 調整パラメータ
# ===============
SPIKE_DISTANCE = 1  # スパイクとして検出するピーク幅。
MISSREP_RATE = 0.3  # 不要データの閾値。最大が1に対して{MISSREP_RATE}未満の筋電のものは除外する。
# 正規化の最大値を決めるパラメータ。試技中のRMSのうち、分位数{quantile}%の値を1に正規化する。
NORMALIZE_QUANTILE = 0.9
# 正規化の最小値を決めるパラメータ。安静時のRMSにおいて、平均+{std_weight}*SDの値を0に正規化する。
NORMALIZE_STD_WEIGHT = 2
STEPS = 3  # 入力するRMS数。デフォルト：3 （150ms間隔でRMSを取得したときの約1秒分）
CNN_HEIGHT = 25  # cnnの高さ。デフォルト：25（正規化されたRMS値を25分割してCNNに入力する）
CNN_KERNEL_SIZE = 3  # cnnのカーネルサイズ
CNN_KERNEL_NUM = 3  # cnnのカーネル数


def dict_to_cfile(data, data_int, filename, defname, _round=False):
    txt = ""
    txt += f"#ifndef {defname}_H_\n"
    txt += f"#define {defname}_H_\n"
    txt += f"\n"
    for k, v in data.items():
        txt += f"const float {k} = {round(v, _round) if _round else v};\n"
    for k, v in data_int.items():
        txt += f"const int {k} = {int(v)};\n"
    txt += f"\n"
    txt += f"#endif // {defname}_H_"
    with open(filename, "w") as f:
        f.write(txt)


def main(sp):
    # ====
    # 前処理
    # ====

    # スパイク除去
    sp = delete_spike(sp, distance=SPIKE_DISTANCE)

    # ノイズ除去・正規化
    sp, normalize_stats = normalize(
        sp, quantile=NORMALIZE_QUANTILE, std_weight=NORMALIZE_STD_WEIGHT)

    # 不要な学習データ除去
    sp = delete_missrep(sp, ratio=MISSREP_RATE)

    # 最後の試技（課題後のrest）を削除
    sp = delete_last_cid(sp)

    # ====
    # 学習
    # ====

    # CNNモデルの構築
    model = tf.keras.models.Sequential([
        tf.keras.layers.Input(
            shape=(STEPS, CNN_HEIGHT, INPUT_SIZE), name='input'),
        tf.keras.layers.Conv2D(
            CNN_KERNEL_NUM, (CNN_KERNEL_SIZE, CNN_HEIGHT), padding="same"),
        tf.keras.layers.MaxPooling2D((STEPS, 1)),  # なくても変わらない
        tf.keras.layers.Flatten(),
        tf.keras.layers.Dense(3, activation=tf.nn.softmax, name='output')
    ])

    model.compile(optimizer='adam',
                  loss='sparse_categorical_crossentropy',
                  metrics=['accuracy'])

    # CNNモデルの学習
    model, x, y, result = model_train(
        model,
        sp,
        label_to_int=LABEL_TO_INT,
        steps=STEPS,
        cnn_height=CNN_HEIGHT,
        detail=MODEL_TRAIN_DETAIL,
    )

    # ModelをTFLiteModelに変換する
    tflite_model = convert_to_tflite(model, model_dir=MODEL_DIR, dim=[
                                     STEPS, CNN_HEIGHT, INPUT_SIZE], optimize=True)

    # ModelとTFLiteModelが同じ出力であることを確認する
    check_if_model_and_tfmodel_is_almost_equal(model, tflite_model, x)

    # 保存
    with open(TFLITE_MODEL_PATH, 'wb') as f:
        f.write(tflite_model)

    # Cファイルに変換
    subprocess.Popen(
        f"xxd -i {TFLITE_MODEL_PATH} > {C_MODEL_PATH}", shell=True)

    # パラメータ保存
    param = {}
    param["kNormalizeMax"] = normalize_stats.normalize_max
    param["kNormalizeMin"] = normalize_stats.normalize_min
    param_int = {}
    param_int["kModelInputWidth"] = STEPS
    param_int["kModelInputHeight"] = CNN_HEIGHT
    param_int["kChannleNumber"] = INPUT_SIZE
    dict_to_cfile(param, param_int, PARAM_PATH, defname="PARAM", _round=6)

    return result


start_time = time.perf_counter()

sp = pd.read_json("./ml/dataset/sp.json")
result = main(sp)

end_time = time.perf_counter()

print("\n**FINISH**\n")
print(f"■ 経過時間\n{end_time - start_time: .1f}秒")
print(f"■ 学習結果\n", result)
