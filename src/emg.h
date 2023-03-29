#ifndef EMG_H_
#define EMG_H_

#include "model_param.h"

// BLEサンプリング頻度（1秒間に何回BLEをアップデートするか）
constexpr int BLE_HZ = 100;
// 判定頻度（1秒間に何回判定するか）
constexpr int PREDICT_HZ = 10;
// DELSYSからの入力配列の要素数（直近{EMG_LENGTH}個分の筋電を常に保持しておく）
const int EMG_LENGTH = 20;
// ML入力の要素数
const int BUFFER_SIZE = CHANNEL_NUMBER * MODEL_INPUT_HEIGHT * MODEL_INPUT_WIDTH;

// Delsysから取得したRMS（約1回/150ms）
extern volatile float extensor_value;
extern volatile float flexor_value;
// Delsysから取得したRMS配列
extern volatile float extensor_values[EMG_LENGTH];
extern volatile float flexor_values[EMG_LENGTH];
// Delsysから取得したRMS配列のインデックス
extern volatile int begin_index;

// 整列後のRMS配列
extern volatile float ar_extensor_values[EMG_LENGTH];
extern volatile float ar_flexor_values[EMG_LENGTH];

// 信号処理後のRMS配列
extern volatile float s_extensor_values[MODEL_INPUT_WIDTH];
extern volatile float s_flexor_values[MODEL_INPUT_WIDTH];

// カテゴライズ後のバッファ
extern volatile float buffer_input[BUFFER_SIZE];

extern void updataRMSFromString(
    std::string value);

extern void updataRMSWithSinCos();

#endif // EMG_H_