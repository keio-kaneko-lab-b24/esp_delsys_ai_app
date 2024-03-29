#include <Arduino.h>

#include "main.h"
#include "ble.h"
#include "output_handler.h"
#include "motion.h"
#include "predictor.h"
#include "emg.h"
#include "signal_processor.h"
#include "model.h"
#include "model_param.h"
#include "neural_network.h"

NeuralNetwork *nn;

TaskHandle_t TaskIO;
TaskHandle_t TaskMain;

// セマフォ
SemaphoreHandle_t xMutex = NULL;

char main_s[64];
long last_sample_micros = 0;
long last_process_micros = 0;
long prediction_micros = 0;

// IOスレッド
void TaskIOcode(void *pvParameters)
{
  for (;;)
  {
    // 毎秒 {BLE_HZ} 回実行される
    if ((micros() - last_sample_micros) < (1000 * 1000 / BLE_HZ))
    {
      continue;
    }
    last_sample_micros = micros();

    UpdateBLEConnection();

    // デバッグ用：SinCos波でEMGを作成する。
    // updataRMSWithSinCos();
    // unsigned long currentMillis = xTaskGetTickCount();
    // sprintf(main_s, "time: %lu\ne_sp: %f\nf_sp: %f", currentMillis, extensor_value, flexor_value);
    // Serial.println(main_s);
    // sprintf(main_s, "begin_index: %d", begin_index);
    // Serial.println(main_s);

    // ウォッチドッグのために必要
    // https://github.com/espressif/arduino-esp32/issues/3001
    // https://lang-ship.com/blog/work/esp32-freertos-l03-multitask/#toc12
    vTaskDelay(1);

    // スレッドセーフな処理
    if (xSemaphoreTake(xMutex, (portTickType)100) == pdTRUE)
    {
      xSemaphoreGive(xMutex);
    }
  }
};

// Mainスレッド
void TaskMaincode(void *pvParameters)
{
  for (;;)
  {
    // 毎秒 {PREDICT_HZ} 回実行される
    if ((micros() - last_process_micros) < (1000 * 1000 / PREDICT_HZ))
    {
      continue;
    }
    last_process_micros = micros();

    // ウォッチドッグのために必要
    // https://github.com/espressif/arduino-esp32/issues/3001
    // https://lang-ship.com/blog/work/esp32-freertos-l03-multitask/#toc12
    vTaskDelay(1);

    // スレッドセーフな処理
    prediction_micros = micros();
    if (xSemaphoreTake(xMutex, (portTickType)100) == pdTRUE)
    {
      SignalProcess();

      xSemaphoreGive(xMutex);
    }

    // 直近のRMSが0の場合は、Restに判定
    float last_extensor = s_extensor_values[MODEL_INPUT_WIDTH - 1];
    float last_flexor = s_flexor_values[MODEL_INPUT_WIDTH - 1];
    if ((last_extensor == 0) & (last_flexor == 0))
    {
      motion motion = NONE;
      HandleOutput(motion);
      continue;
    }

    // 推論
    float *input_buffer = nn->getInputBuffer();
    for (int i = 0; i < BUFFER_SIZE; i++)
    {
      input_buffer[i] = buffer_input[i];
    }
    float *result = nn->predict();
    Serial.printf("prediction: %.2f, %.2f, %.2f\n", result[0], result[1], result[2]);

    // 判定
    motion motion = NONE;
    motion = PredictML(result[0], result[1], result[2]);

    // ロボットへ出力
    HandleOutput(motion);

    // 推論時間
    Serial.printf("推論時間 = %ld micros\n", micros() - prediction_micros);
  }
};

void setup()
{
  delay(3000);
  Serial.begin(115200);

  SetUpBLE();

  OutputSetup();

  nn = new NeuralNetwork();

  xMutex = xSemaphoreCreateMutex();
  xTaskCreatePinnedToCore(TaskIOcode, "TaskIO", 4096, NULL, 2, &TaskIO, 0); // Task1実行
  delay(500);
  xTaskCreatePinnedToCore(TaskMaincode, "TaskMain", 4096, NULL, 2, &TaskMain, 1); // Task2実行
  delay(500);

  Serial.println("[setup] finished.");
}

void loop()
{
  // loopは使用しないので、削除する
  vTaskDelete(NULL);
}