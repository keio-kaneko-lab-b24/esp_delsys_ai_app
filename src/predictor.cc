#include <Arduino.h>

#include "predictor.h"

// Restスコアに与えるペナルティ値（デフォルト:0.0, 可能範囲:-1.0~1.0）
// 正であればrestに判定されにくく、負であればrestに判定されやすくなる。
float rest_penalty = 0.0;

// MLの出力から判定を行う場合
motion PredictML(
    float rock_score,
    float paper_score,
    float rest_score)
{
    rest_score = rest_score - rest_penalty;
    if ((rock_score > paper_score) & (rock_score > rest_score))
    {
        return ROCK;
    }
    else if (paper_score > rest_score)
    {
        return PAPER;
    }
    return NONE;
}

// RMSと閾値から判定を行う場合
motion PredictThreshold(
    float extensor_value,
    float flexor_value,
    float rock_flexor_lower_limit,
    float rock_extensor_upper_limit,
    float paper_extensor_lower_limit,
    float paper_flexor_upper_limit)
{
    boolean paper = false;
    boolean rock = false;
    if ((extensor_value > paper_extensor_lower_limit) & (flexor_value < paper_flexor_upper_limit))
    {
        paper = true;
    }
    if ((flexor_value > rock_flexor_lower_limit) & (extensor_value < rock_extensor_upper_limit))
    {
        rock = true;
    }

    // paperにもrockにも判定された場合はNONEを返す。
    if ((paper == true) & (rock == false))
    {
        return PAPER;
    }
    else if ((rock == true) & (paper == false))
    {
        return ROCK;
    }
    else
    {
        return NONE;
    }
}