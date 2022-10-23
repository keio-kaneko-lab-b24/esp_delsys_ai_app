import numpy as np
import tensorflow as tf
from sklearn.model_selection import LeaveOneOut


def data_cnn_expand(x, cnn_height):
    CNN_HEIGHT = cnn_height
    expanded_x = np.zeros((x.shape[0], x.shape[1], x.shape[2], CNN_HEIGHT))
    for i, _x in enumerate(x):
        for j, __x in enumerate(_x):
            for k, __x in enumerate(__x):
                l = int(__x // (1/CNN_HEIGHT))
                l = min(l, CNN_HEIGHT-1)
                expanded_x[i, j, k, l] = 1.0
    expanded_x = expanded_x.transpose((0, 1, 3, 2))
    return expanded_x


def get_feature_from_sp(sp, label_to_int, steps=6, cnn_height=10):

    x = []
    y = []
    p = []
    # rock, paper
    for label in ["rock", "paper"]:
        cid_list = sp[sp.label == label].count_idx.unique()
        for cid in cid_list:
            rep = sp[sp.count_idx == cid]

            for i in range(int(len(rep) / steps) - 1):  # 最後の1秒は使用しない
                _rep = rep.iloc[i*steps:(i+1)*steps]
                x.append(_rep[["extensor_sp", "flexor_sp"]].values.tolist())
                y.append(label_to_int[label])
                p.append(_rep.index.tolist()[-1])

    # rest
    for label in ["rest"]:
        cid_list = sp[sp.label == label].count_idx.unique()
        for cid in cid_list[::2]:  # restは多くなりがちなので、1/2のみ使用する
            rep = sp[sp.count_idx == cid]

            for i in range(1, int(len(rep) / steps) - 1):  # 最初と最後の1秒は使用しない
                _rep = rep.iloc[i*steps:(i+1)*steps]
                x.append(_rep[["extensor_sp", "flexor_sp"]].values.tolist())
                y.append(label_to_int[label])
                p.append(_rep.index.tolist()[-1])

    x = np.array(x)
    # cnn用に整形
    x = data_cnn_expand(x, cnn_height)
    x = x.astype(np.float32)
    y = np.array(y)
    p = np.array(p)

    return x, y, p


def calc_result(y, t, threshold=0.5):
    int_to_label = {
        0: "rock",
        1: "paper",
        2: "rest"
    }

    result = {
        "rock": {"rock": 0, "paper": 0, "rest": 0},
        "paper": {"rock": 0, "paper": 0, "rest": 0},
        "rest": {"rock": 0, "paper": 0, "rest": 0}
    }

    for _y, _t in zip(y, t):
        for __y, __t in zip(_y, _t):
            __i = np.argmax(__t)  # 最大値を使用
            if __i in [0, 1]:
                # 閾値以下ならrestにする
                if __t[__i] < threshold:
                    __i = 2
            result[int_to_label[__y]][int_to_label[__i]] += 1

    return result


def model_train(model, sp, label_to_int, steps, cnn_height, detail=False):

    result = {}
    early_stopping = tf.keras.callbacks.EarlyStopping(
        monitor='loss', patience=2)

    # バリデーションによる性能評価をする場合
    if detail:
        sp["task"] = sp["task_name"] + sp["task_num"].apply(str)
        task_to_int = {t: i for i, t in enumerate(sp["task"].unique())}

        if len(task_to_int) == 1:
            print("task数が少なすぎて正確な評価ができませんでした。学習は問題なく実行されます。")
        else:
            sp["task"] = sp["task"].apply(lambda x: task_to_int[x])

            loo = LeaveOneOut()
            t = []
            loss = []
            acc = []
            x = []
            y = []
            p = []

            for train_index, test_index in loo.split(task_to_int):
                sp_train = sp[sp["task"].apply(lambda x: x in train_index)]
                sp_test = sp[sp["task"].apply(lambda x: x in test_index)]
                x_train, y_train, p_train = get_feature_from_sp(
                    sp_train, label_to_int, steps=steps, cnn_height=cnn_height)
                x_test, y_test, p_test = get_feature_from_sp(
                    sp_test, label_to_int, steps=steps, cnn_height=cnn_height)

                early_stopping = tf.keras.callbacks.EarlyStopping(
                    monitor='loss', patience=2)
                model.fit(x_train, y_train, epochs=500,
                          callbacks=[early_stopping], verbose=0)

                # 分析用にデータ蓄積
                x.append(x_test)
                y.append(y_test)
                p.append(p_test)

                test_loss, test_acc = model.evaluate(x_test, y_test, verbose=0)
                loss.append(test_loss)
                acc.append(test_acc)

                t_test = model.predict(x_test)
                t.append(t_test)

            result = calc_result(y, t, threshold=0.5)

    # 特徴量を抽出する
    x, y, _ = get_feature_from_sp(
        sp, label_to_int, steps=steps, cnn_height=cnn_height)
    # 学習する
    model.fit(x, y, epochs=500, callbacks=[early_stopping], verbose=0)

    return model, x, y, result


def convert_to_tflite(model, model_dir, dim, optimize=False):

    run_model = tf.function(lambda x: model(x))
    # 重要。InputShapeを固定する。
    BATCH_SIZE = 1
    DIM = dim
    concrete_func = run_model.get_concrete_function(
        tf.TensorSpec([BATCH_SIZE]+DIM, model.inputs[0].dtype))

    # モデルを一度保存する
    model.save(model_dir, save_format="tf", signatures=concrete_func)

    converter = tf.lite.TFLiteConverter.from_saved_model(model_dir)
    if optimize:
        converter.optimizations = [tf.lite.Optimize.DEFAULT]

    # 変換
    tflite_model = converter.convert()

    return tflite_model


def check_if_model_and_tfmodel_is_almost_equal(model, tflite_model, x):

    # Run the model with TensorFlow to get expected results.
    TEST_CASES = 10

    # Run the model with TensorFlow Lite
    interpreter = tf.lite.Interpreter(model_content=tflite_model)
    interpreter.allocate_tensors()
    input_details = interpreter.get_input_details()
    output_details = interpreter.get_output_details()

    for i in range(TEST_CASES):
        expected = model.predict(x[i:i+1])
        interpreter.set_tensor(input_details[0]["index"], x[i:i+1, :, :])
        interpreter.invoke()
        result = interpreter.get_tensor(output_details[0]["index"])

        # Assert if the result of TFLite model is consistent with the TF model.
        np.testing.assert_almost_equal(expected, result, decimal=6)

        # Please note: TfLite fused Lstm kernel is stateful, so we need to reset
        # the states.
        # Clean up internal states.
        interpreter.reset_all_variables()

    print("Done. The result of TensorFlow matches the result of TensorFlow Lite.")
