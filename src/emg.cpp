#include <Arduino.h>

#include "emg.h"
#include "param_ml.h"

volatile float extensor_value = 0;
volatile float flexor_value = 0;

volatile int begin_index = 0;
volatile float extensor_values[EMG_LENGTH] = {0};
volatile float flexor_values[EMG_LENGTH] = {0};
volatile float ar_extensor_values[EMG_LENGTH] = {0};
volatile float ar_flexor_values[EMG_LENGTH] = {0};
volatile float s_extensor_values[kModelInputWidth] = {0};
volatile float s_flexor_values[kModelInputWidth] = {0};
volatile float buffer_input[kModelInputWidth * kModelInputHeight * kChannleNumber] = {0};

// EMGの値を更新する
// @value （例）"E: 0.012345, F: 0.056789, E5"
void updataRMSFromString(
    std::string value)
{
    // Indexをずらして格納していく
    begin_index += 1;
    if (begin_index >= EMG_LENGTH)
    {
        begin_index = 0;
    }

    size_t pos = 0;
    std::string delimiter = ",";

    // TODO: もっとよい書き方
    // ExtensorのRMS値を取得
    while ((pos = value.find(delimiter)) != std::string::npos)
    {
        std::string e_token = value.substr(2, 100); // 多めに100文字目まで取得
        const char *e_str = e_token.c_str();
        extensor_value = atof(e_str);
        extensor_values[begin_index] = atof(e_str);
        value.erase(0, pos + delimiter.length());
        break;
    }

    // FlexorのRMS値を取得
    while ((pos = value.find(delimiter)) != std::string::npos)
    {
        std::string f_token = value.substr(3, 100); // 多めに100文字目まで取得
        const char *f_str = f_token.c_str();
        flexor_value = atof(f_str);
        flexor_values[begin_index] = atof(f_str);
        value.erase(0, pos + delimiter.length());
        break;
    }
}

// （デバッグ用）EMGの値をSinCos波で更新する
void updataRMSWithSinCos()
{
    // Indexをずらして格納していく
    begin_index += 1;
    if (begin_index >= EMG_LENGTH)
    {
        begin_index = 0;
    }

    double rad = begin_index * (360 / EMG_LENGTH) * 3.14 / 180.0;
    extensor_value = 1.0 + cos(rad);
    extensor_values[begin_index] = 1.0 + cos(rad);
    flexor_value = 1.0 + sin(rad);
    flexor_values[begin_index] = 1.0 + sin(rad);
}