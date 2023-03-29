#include <Arduino.h>

#include "signal_processor.h"
#include "model_param.h"
#include "emg.h"

char sp_s[100];

/**
 * 信号処理
 */
void SignalProcess()
{
    // 整列
    ArrangeArray(
        extensor_values,
        flexor_values,
        ar_extensor_values,
        ar_flexor_values,
        begin_index,
        EMG_LENGTH);

    // 直近 {MODEL_INPUT_WIDTH}個を推論に使用する
    for (int i = 0; i < MODEL_INPUT_WIDTH; ++i)
    {
        s_extensor_values[i] = ar_extensor_values[EMG_LENGTH - MODEL_INPUT_WIDTH + i];
        s_flexor_values[i] = ar_flexor_values[EMG_LENGTH - MODEL_INPUT_WIDTH + i];
    }

    unsigned long currentMillis = xTaskGetTickCount();
    sprintf(sp_s, "time: %lu\ne_sp: %f\nf_sp: %f", currentMillis, s_extensor_values[MODEL_INPUT_WIDTH - 1], s_flexor_values[MODEL_INPUT_WIDTH - 1]);
    Serial.println(sp_s);

    // 正規化(0-1)
    for (int i = 0; i < MODEL_INPUT_WIDTH; ++i)
    {
        s_extensor_values[i] = _NormalizeZeroOne(s_extensor_values[i]);
        s_flexor_values[i] = _NormalizeZeroOne(s_flexor_values[i]);
    }

    // カテゴリ化
    Categorize(
        s_extensor_values,
        s_flexor_values,
        buffer_input,
        MODEL_INPUT_WIDTH,
        MODEL_INPUT_HEIGHT);
}

/**
 * リングバッファの整列
 */
void ArrangeArray(
    volatile float extensor_values[],
    volatile float flexor_values[],
    volatile float ar_extensor_values[],
    volatile float ar_flexor_values[],
    volatile int begin_index,
    const int value_length)
{
    for (int i = 0; i < value_length; ++i)
    {
        int ring_array_index = begin_index + i;
        if (ring_array_index >= value_length)
        {
            ring_array_index -= value_length;
        }
        ar_extensor_values[i] = extensor_values[ring_array_index];
        ar_flexor_values[i] = flexor_values[ring_array_index];
    }
}

/**
 * 正規化（0-1）（1つのみ）
 */
float _NormalizeZeroOne(float value)
{
    float n_value = (value - NORMALIZE_MIN) / (NORMALIZE_MAX - NORMALIZE_MIN);
    if (n_value >= 1)
    {
        return 1;
    }
    else if (n_value <= 0)
    {
        return 0;
    }
    return n_value;
}

/**
 * カテゴライズ
 */
void Categorize(
    volatile float n_extensor_values[],
    volatile float n_flexor_values[],
    volatile float buffer_input[],
    const int input_width,
    const int input_height)
{

    // 初期化
    for (size_t i = 0; i < BUFFER_SIZE; i++)
    {
        buffer_input[i] = 0.0;
    }

    for (int i = 0; i < input_width; ++i)
    {
        int e_index_ = _CategorizeIndex(n_extensor_values[i]);
        int f_index_ = _CategorizeIndex(n_flexor_values[i]);
        int base_index = i * input_height * 2;
        int e_index = base_index + (e_index_ * 2);
        int f_index = base_index + (f_index_ * 2) + 1;
        // sprintf(sp_s, "cnn_index: %f -> %d , %f -> %d", d_extensor_values[i], e_index, d_flexor_values[i], f_index);
        // Serial.println(sp_s);
        buffer_input[e_index] = 1.0;
        buffer_input[f_index] = 1.0;
    }
}

/**
 * カテゴライズIndexの取得
 */
int _CategorizeIndex(float value)
{
    int index = floor(value * MODEL_INPUT_HEIGHT);
    if (index >= MODEL_INPUT_HEIGHT)
    {
        index = MODEL_INPUT_HEIGHT - 1;
    }
    return index;
}