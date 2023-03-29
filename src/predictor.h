#ifndef PREDICTOR_H_
#define PREDICTOR_H_

#include "motion.h"

extern motion PredictML(
    float rock_score,
    float paper_score,
    float rest_score);

#endif