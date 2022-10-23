#ifndef EMG_H_
#define EMG_H_

#include "param.h"

const int EMG_LENGTH = 20;
const int BUFFER_SIZE = kChannleNumber * kModelInputHeight * kModelInputWidth;

// 共通：信号処理後の値
extern volatile float extensor_value;
extern volatile float flexor_value;

extern volatile int begin_index;

// Delsysから取得したRMS（約1回/150ms）
extern volatile float extensor_values[EMG_LENGTH];
extern volatile float flexor_values[EMG_LENGTH];

// 整列後のRMS
extern volatile float ar_extensor_values[EMG_LENGTH];
extern volatile float ar_flexor_values[EMG_LENGTH];

// 信号処理後のRMS
extern volatile float s_extensor_values[kModelInputWidth];
extern volatile float s_flexor_values[kModelInputWidth];

// カテゴライズ後のバッファ
extern volatile float buffer_input[BUFFER_SIZE];

extern void updataRMSFromString(
    std::string value);

extern void updataRMSWithSinCos();

#endif // EMG_H_