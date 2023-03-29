#include "neural_network.h"
#include "model.h"
#include "model_param.h"
#include "tensorflow/lite/micro/all_ops_resolver.h"
#include "tensorflow/lite/micro/micro_error_reporter.h"
#include "tensorflow/lite/micro/micro_interpreter.h"
#include "tensorflow/lite/schema/schema_generated.h"
#include "tensorflow/lite/version.h"

/**
 * 参考：https://github.com/atomic14/tensorflow-lite-esp32
 */

const int kArenaSize = 30 * 1024;

NeuralNetwork::NeuralNetwork()
{
    error_reporter = new tflite::MicroErrorReporter();

    model = tflite::GetModel(__ml_dataset_model_tflite);
    if (model->version() != TFLITE_SCHEMA_VERSION)
    {
        TF_LITE_REPORT_ERROR(error_reporter, "Model provided is schema version %d not equal to supported version %d.",
                             model->version(), TFLITE_SCHEMA_VERSION);
        return;
    }
    // This pulls in the operators implementations we need
    resolver = new tflite::MicroMutableOpResolver<10>();
    resolver->AddSoftmax();
    resolver->AddReshape();
    resolver->AddFullyConnected();
    resolver->AddMaxPool2D();
    resolver->AddConv2D();

    tensor_arena = (uint8_t *)malloc(kArenaSize);
    if (!tensor_arena)
    {
        TF_LITE_REPORT_ERROR(error_reporter, "Could not allocate arena");
        return;
    }

    // Build an interpreter to run the model with.
    interpreter = new tflite::MicroInterpreter(
        model, *resolver, tensor_arena, kArenaSize, error_reporter);

    // Allocate memory from the tensor_arena for the model's tensors.
    TfLiteStatus allocate_status = interpreter->AllocateTensors();
    if (allocate_status != kTfLiteOk)
    {
        TF_LITE_REPORT_ERROR(error_reporter, "AllocateTensors() failed");
        return;
    }

    size_t used_bytes = interpreter->arena_used_bytes();
    TF_LITE_REPORT_ERROR(error_reporter, "Used bytes %d\n", used_bytes);

    // Obtain pointers to the model's input and output tensors.
    input = interpreter->input(0);
    output = interpreter->output(0);

    // パラメータチェック
    if ((input->dims->size != 4) ||
        (input->dims->data[0] != 1) ||
        (input->dims->data[1] != MODEL_INPUT_WIDTH) ||
        (input->dims->data[2] != MODEL_INPUT_HEIGHT) ||
        (input->dims->data[3] != CHANNEL_NUMBER) ||
        (input->type != kTfLiteFloat32))
    {
        TF_LITE_REPORT_ERROR(error_reporter, "model parameter failed");
        return;
    }
}

float *NeuralNetwork::getInputBuffer()
{
    return input->data.f;
}

float *NeuralNetwork::predict()
{
    interpreter->Invoke();
    return output->data.f;
}
