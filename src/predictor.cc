#include <Arduino.h>

#include "predictor.h"

// Restスコアに与えるペナルティ値（デフォルト:0.0, 可能範囲:-1.0~1.0）
// 正であればrestに判定されにくく、負であればrestに判定されやすくなる。
float REST_PENALTY = -0.5;

// MLを用いた判定
motion PredictML(
    float rock_score,
    float paper_score,
    float rest_score)
{
    rest_score = rest_score - REST_PENALTY;
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