#include <Arduino.h>
#include <honk-detector_inferencing.h>
#include "driver/i2s.h"
#include <esp_task_wdt.h>
#include "esp_heap_caps.h"

// ——— Pin mapping ———
#define I2S_PORT    I2S_NUM_0
#define I2S_BCK_PIN 7
#define I2S_WS_PIN  16
#define I2S_SD_PIN  15

// ——— Model parameters ———
static const uint32_t SAMPLE_RATE      = EI_CLASSIFIER_FREQUENCY;        // e.g. 16000 Hz
static const size_t   SLICE_SIZE       = EI_CLASSIFIER_SLICE_SIZE;       // e.g. 400 samples
static const size_t   RAW_SAMPLE_COUNT = EI_CLASSIFIER_RAW_SAMPLE_COUNT; // e.g. 16000 samples

// ——— PSRAM-allocated audio buffers ———
static int16_t *windowBuffer = nullptr;  // ~32 KB sliding window
static int16_t *sliceBuf     = nullptr;  // ~0.8 KB per-slice buffer

// ——— Smoothing state ———
static float avgScore[EI_CLASSIFIER_LABEL_COUNT] = {0};
static const float DETECTION_THRESHOLD = 0.2f;

// ——— Edge Impulse signal callback ———
static int get_signal_data(size_t offset, size_t length, float *out_ptr) {
  for (size_t i = 0; i < length; i++) {
    // apply extra mic gain (×8) before normalizing
    out_ptr[i] = (windowBuffer[offset + i] * 8) / 32768.0f;
  }
  return 0;
}

void setup() {
  Serial.begin(115200);
  while (!Serial);

  ei_printf("Starting continuous inferencing @ %u Hz\n", SAMPLE_RATE);

  // 1) Verify that PSRAM is present
  if (ESP.getPsramSize() == 0) {
    Serial.println("❌ No PSRAM detected! Halting.");
    while (1) { delay(1000); }
  }
  Serial.printf("✅ PSRAM size: %u bytes\n", ESP.getPsramSize());

  // 2) Allocate audio buffers in PSRAM
  windowBuffer = (int16_t*) heap_caps_malloc(
    RAW_SAMPLE_COUNT * sizeof(int16_t),
    MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT
  );
  sliceBuf = (int16_t*) heap_caps_malloc(
    SLICE_SIZE * sizeof(int16_t),
    MALLOC_CAP_SPIRAM | MALLOC_CAP_8BIT
  );
  if (!windowBuffer || !sliceBuf) {
    Serial.println("❌ Failed to allocate audio buffers in PSRAM");
    while (1) { delay(1000); }
  }
  Serial.println("✅ Audio buffers allocated in PSRAM");

  // 3) Initialize the Edge Impulse classifier (internal Tensor arena)
  run_classifier_init();

  // 4) Task Watchdog Timer (30 s)
  esp_task_wdt_init(30, false);
  esp_task_wdt_add(NULL);

  // 5) Configure I²S for microphone input
  i2s_config_t i2s_cfg = {
    .mode            = i2s_mode_t(I2S_MODE_MASTER | I2S_MODE_RX),
    .sample_rate     = SAMPLE_RATE,
    .bits_per_sample = I2S_BITS_PER_SAMPLE_16BIT,
    .channel_format  = I2S_CHANNEL_FMT_ONLY_LEFT,
    .communication_format = I2S_COMM_FORMAT_STAND_I2S,
    .intr_alloc_flags= 0,
    .dma_buf_count   = 4,
    .dma_buf_len     = 256,  // must be between 8 and 1024
    .use_apll        = false,
    .tx_desc_auto_clear = false,
    .fixed_mclk      = -1
  };
  i2s_pin_config_t pin_cfg = {
    .bck_io_num   = (gpio_num_t)I2S_BCK_PIN,
    .ws_io_num    = (gpio_num_t)I2S_WS_PIN,
    .data_out_num = I2S_PIN_NO_CHANGE,
    .data_in_num  = (gpio_num_t)I2S_SD_PIN
  };
  i2s_driver_install(I2S_PORT, &i2s_cfg, 0, nullptr);
  i2s_set_pin(I2S_PORT, &pin_cfg);
  i2s_zero_dma_buffer(I2S_PORT);
  pinMode(8, OUTPUT);
  digitalWrite(8, LOW);
  Serial.println("✅ I²S initialized");
  ei_printf("Setup complete—entering continuous loop\n");
}

void loop() {
  // Reset the Task WDT before blocking operations
  esp_task_wdt_reset();

  // 1) Read one slice of audio into PSRAM buffer
  size_t bytesRead = 0;
  i2s_read(
    I2S_PORT,
    sliceBuf,
    SLICE_SIZE * sizeof(sliceBuf[0]),
    &bytesRead,
    portMAX_DELAY
  );

  // 2) Slide the existing window and append new slice
  memmove(windowBuffer,
          windowBuffer + SLICE_SIZE,
          (RAW_SAMPLE_COUNT - SLICE_SIZE) * sizeof(windowBuffer[0]));
  memcpy(windowBuffer + (RAW_SAMPLE_COUNT - SLICE_SIZE),
         sliceBuf,
         SLICE_SIZE * sizeof(sliceBuf[0]));

  // 3) Prepare signal struct by assignment
  signal_t signal;
  signal.get_data     = get_signal_data;
  signal.total_length = RAW_SAMPLE_COUNT;

  // 4) Run continuous classification
  ei_impulse_result_t result;
  EI_IMPULSE_ERROR err = run_classifier_continuous(
    &signal, &result, /* debug = */ false
  );

  // Reset WDT after inference
  esp_task_wdt_reset();

  if (err == EI_IMPULSE_OK) {
    // 5a) Debug: print all raw scores
    ei_printf("--- Raw scores ---\n");
    for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
      ei_printf("  %s: %.6f\n",
                result.classification[i].label,
                result.classification[i].value);
    }
    ei_printf("Anomaly: %.6f\n", result.anomaly);
    ei_printf("------------------\n");
    bool isHonk = false;
    ei_printf("--- IsHonk :");
    for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
      float threshold = 0.3;
      if(result.classification[i].label == "honk" && result.classification[i].value > threshold){
        isHonk = true;
      } 
    }
    if(isHonk) ei_printf( "  True\n");
    else ei_printf("  False\n");
    digitalWrite(8, isHonk);
    // // 5b) Smooth and threshold
    // for (size_t i = 0; i < EI_CLASSIFIER_LABEL_COUNT; i++) {
    //   avgScore[i] = 0.3f * result.classification[i].value
    //               + 0.7f * avgScore[i];
    //   if (avgScore[i] >= DETECTION_THRESHOLD) {
    //     ei_printf("Detect %s: %.2f\n",
    //               result.classification[i].label,
    //               avgScore[i]);
    //   }
    // }
  }
  else {
    ei_printf("ERR: run_classifier_continuous %d\n", err);
  }

  // Let FreeRTOS idle task run (services its own watchdog)
  yield();
}
