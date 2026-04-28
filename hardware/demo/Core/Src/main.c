/* USER CODE BEGIN Header */
/**
  ******************************************************************************
  * @file           : main.c
  * @brief          : Main program body
  ******************************************************************************
  * @attention
  *
  * <h2><center>&copy; Copyright (c) 2026 STMicroelectronics.
  * All rights reserved.</center></h2>
  *
  * This software component is licensed by ST under BSD 3-Clause license,
  * the "License"; You may not use this file except in compliance with the
  * License. You may obtain a copy of the License at:
  *                        opensource.org/licenses/BSD-3-Clause
  *
  ******************************************************************************
  */
/* USER CODE END Header */
/* Includes ------------------------------------------------------------------*/
#include "main.h"
#include "gpio.h"

/* Private includes ----------------------------------------------------------*/
/* USER CODE BEGIN Includes */
#include <stdbool.h>
#include <stdlib.h>
#include <stdio.h>
#include <string.h>

#include "oled.h"
#include "usart.h"

/* USER CODE END Includes */

/* Private typedef -----------------------------------------------------------*/
/* USER CODE BEGIN PTD */

/* USER CODE END PTD */

/* Private define ------------------------------------------------------------*/
/* USER CODE BEGIN PD */
#define APP_DEVICE_ID "DEVICE_001"
#define APP_TELEMETRY_INTERVAL_MS 15000U
#define APP_NB_TELEMETRY_ENABLED 1
#define APP_NB_RESPONSE_DRAIN_MS 1500U
#define APP_NB_DOWNLINK_POLL_INTERVAL_MS 10000U
#define APP_NB_DOWNLINK_READ_MS 700U
#define APP_NB_BOOT_READY_WAIT_MS 2000U
#define APP_NB_READY_CHECK_INTERVAL_MS 3000U
#define APP_NB_ATTACH_WAIT_MS 2500U
#define APP_NB_ATTACH_RETRY_INTERVAL_MS 3000U
#define APP_NB_IDLE_GAP_MS 120U
#define APP_NB_SERVER_ADDR "221.229.214.202"
#define APP_NB_SERVER_PORT 5683U
#define APP_NB_APN "CTNB"
#define APP_UPLOAD_TOGGLE_CLICKS 3U
#define APP_UPLOAD_TOGGLE_WINDOW_MS 1200U
#define APP_K1_DEBOUNCE_MS 60U
/* USER CODE END PD */

/* Private macro -------------------------------------------------------------*/
/* USER CODE BEGIN PM */

/* USER CODE END PM */

/* Private variables ---------------------------------------------------------*/

/* USER CODE BEGIN PV */
static const GPIO_PinState RELAY_ACTIVE_STATE = GPIO_PIN_SET;
static const float RELAY1_ON_THRESHOLD_C = 25.0f;
static const float RELAY1_OFF_THRESHOLD_C = 24.0f;
static bool relay1_manual_override = false;
static GPIO_PinState relay1_manual_state = GPIO_PIN_RESET;
static bool relay1_auto_on = false;
static bool relay2_manual_override = false;
static GPIO_PinState relay2_manual_state = GPIO_PIN_RESET;
static bool fill_light_manual_override = false;
static GPIO_PinState fill_light_manual_state = GPIO_PIN_RESET;
static bool nb_upload_enabled = false;
static bool nb_network_ready = false;
static bool nb_downlink_poll_enabled = false;
static bool nb_pending_immediate_downlink_poll = false;
static bool nb_pending_first_telemetry = false;
static bool nb_trace_enabled = true;
static bool app_main_screen_active = false;
static bool nb_last_attached = false;
static bool nb_last_registered = false;
static bool nb_last_mo_ready = false;
static uint8_t nb_ready_stage = 0U;
static uint8_t nb_downlink_no_response_count = 0U;
static uint32_t nb_last_attach_retry_tick = 0U;
static bool nb_boot_success_pending = false;
static uint32_t nb_boot_success_tick = 0U;

/* USER CODE END PV */

/* Private function prototypes -----------------------------------------------*/
void SystemClock_Config(void);
/* USER CODE BEGIN PFP */
static void SHT3X_SDA_Output(void);
static void SHT3X_SDA_Input(void);
static void DelayUs(uint32_t us);
static void SHT3X_BusDelayUs(uint32_t us);
static void SHT3X_Start(void);
static void SHT3X_Stop(void);
static bool SHT3X_WriteByte(uint8_t value);
static uint8_t SHT3X_ReadByte(bool ack);
static bool SHT3X_ReadMeasurement(float *temperature, float *humidity);
static bool SHT3X_CheckCrc(const uint8_t *data, uint8_t crc);
static void App_ShowLine(uint8_t x, uint8_t page, const char *text);
static void App_ShowBootStatus(const char *title, const char *detail);
static const char *App_NbReadyStageText(void);
static void App_DrawMainScreen(void);
static void App_UpdateStatusLine(void);
static void App_UpdateDisplay(float temperature, float humidity, bool sensor_ok);
static const char *App_RelayStateText(GPIO_PinState pin_state);
static void App_UpdateField(uint8_t x, uint8_t page, char *cache, size_t cache_size, const char *text);
static void App_FormatFixed1(char *buffer, size_t buffer_size, const char *prefix, float value, const char *suffix);
static void App_FormatNumberFixed1(char *buffer, size_t buffer_size, float value);
static void App_ApplyRelayState(GPIO_TypeDef *port, uint16_t pin, bool is_on);
static void App_ApplyFillLightState(bool is_on);
static void App_SendTelemetry(float temperature, float humidity, bool sensor_ok);
static void App_NbInit(void);
static bool App_NbSendCommand(const char *command, uint32_t wait_ms);
static bool App_NbSendPayload(const char *payload);
static bool App_BytesToHex(const char *input, char *output, size_t output_size);
static int App_HexNibble(char value);
static bool App_HexToText(const char *input, char *output, size_t output_size);
static bool App_HexToBytes(const char *input, uint8_t *output, size_t output_size, size_t *decoded_length);
static int App_Base64Value(char value);
static bool App_Base64ToText(const char *input, char *output, size_t output_size);
static bool App_TryHandleDecodedDownlink(const char *payload_text);
static bool App_TryHandleLegacyCtDownlink(const char *hex_payload);
static size_t App_NbReadResponse(char *buffer, size_t buffer_size, uint32_t timeout_ms);
static void App_NbDrainResponse(uint32_t timeout_ms);
static void App_NbMirrorPendingOutput(void);
static void App_NbSetReady(bool ready);
static bool App_NbQueryNetworkReady(bool trace);
static void App_NbPollDownlink(void);
static void App_NbHandleResponse(const char *response);
static bool App_NbResponseHasToken(const char *response, const char *token);
static bool App_NbResponseIsSuccess(const char *response);
static void App_SetUploadEnabled(bool enabled);
static void App_HandleK1UploadToggle(void);
static void App_SetDownlinkPollEnabled(bool enabled);
static void App_HandleK2DownlinkToggle(void);
static void App_SendAck(long command_id, const char *status);
static bool App_ExtractJsonString(const char *json, const char *key, char *value, size_t value_size);
static bool App_ExtractJsonLong(const char *json, const char *key, long *value);
static void App_HandleCommandLine(const char *line);
static void App_NbRecoverDownlinkSession(void);

/* USER CODE END PFP */

/* Private user code ---------------------------------------------------------*/
/* USER CODE BEGIN 0 */
static void SHT3X_SDA_Output(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  GPIO_InitStruct.Pin = SHT3X_SDA_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_OUTPUT_PP;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(SHT3X_SDA_GPIO_Port, &GPIO_InitStruct);
}

static void SHT3X_SDA_Input(void)
{
  GPIO_InitTypeDef GPIO_InitStruct = {0};

  GPIO_InitStruct.Pin = SHT3X_SDA_Pin;
  GPIO_InitStruct.Mode = GPIO_MODE_INPUT;
  GPIO_InitStruct.Pull = GPIO_PULLUP;
  GPIO_InitStruct.Speed = GPIO_SPEED_FREQ_LOW;
  HAL_GPIO_Init(SHT3X_SDA_GPIO_Port, &GPIO_InitStruct);
}

static void DelayUs(uint32_t us)
{
  uint32_t cycles_per_us = SystemCoreClock / 1000000U;
  uint32_t total_cycles = us * cycles_per_us / 5U;

  while (total_cycles-- > 0U) {
    __NOP();
  }
}

static void SHT3X_BusDelayUs(uint32_t us)
{
  DelayUs(us);
}

static void SHT3X_Start(void)
{
  SHT3X_SDA_Output();
  HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin, GPIO_PIN_SET);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_SET);
  SHT3X_BusDelayUs(1U);
  HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin, GPIO_PIN_RESET);
  SHT3X_BusDelayUs(10U);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_RESET);
  SHT3X_BusDelayUs(10U);
}

static void SHT3X_Stop(void)
{
  SHT3X_SDA_Output();
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin, GPIO_PIN_RESET);
  SHT3X_BusDelayUs(4U);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_SET);
  SHT3X_BusDelayUs(4U);
  HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin, GPIO_PIN_SET);
  SHT3X_BusDelayUs(4U);
}

static bool SHT3X_WriteByte(uint8_t value)
{
  SHT3X_SDA_Output();
  for (uint8_t bit = 0; bit < 8U; ++bit) {
    HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin,
                      ((value & 0x80U) != 0U) ? GPIO_PIN_SET : GPIO_PIN_RESET);
    SHT3X_BusDelayUs(1U);
    HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_SET);
    SHT3X_BusDelayUs(5U);
    HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_RESET);
    SHT3X_BusDelayUs(1U);
    value <<= 1U;
  }

  SHT3X_SDA_Input();
  SHT3X_BusDelayUs(1U);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_SET);
  SHT3X_BusDelayUs(1U);
  bool ack = (HAL_GPIO_ReadPin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin) == GPIO_PIN_RESET);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_RESET);
  SHT3X_BusDelayUs(20U);
  return ack;
}

static uint8_t SHT3X_ReadByte(bool ack)
{
  uint8_t value = 0U;

  SHT3X_SDA_Input();
  for (uint8_t bit = 0; bit < 8U; ++bit) {
    value <<= 1U;
    HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_SET);
    SHT3X_BusDelayUs(4U);
    if (HAL_GPIO_ReadPin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin) == GPIO_PIN_SET) {
      value |= 0x01U;
    }
    HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_RESET);
    SHT3X_BusDelayUs(1U);
  }

  SHT3X_SDA_Output();
  HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin, ack ? GPIO_PIN_RESET : GPIO_PIN_SET);
  SHT3X_BusDelayUs(1U);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_SET);
  SHT3X_BusDelayUs(5U);
  HAL_GPIO_WritePin(SHT3X_SCL_GPIO_Port, SHT3X_SCL_Pin, GPIO_PIN_RESET);
  HAL_GPIO_WritePin(SHT3X_SDA_GPIO_Port, SHT3X_SDA_Pin, GPIO_PIN_SET);
  SHT3X_BusDelayUs(20U);

  return value;
}

static bool SHT3X_CheckCrc(const uint8_t *data, uint8_t crc)
{
  uint8_t calc = 0xFFU;

  for (uint8_t i = 0; i < 2U; ++i) {
    calc ^= data[i];
    for (uint8_t bit = 0; bit < 8U; ++bit) {
      if ((calc & 0x80U) != 0U) {
        calc = (uint8_t)((calc << 1U) ^ 0x31U);
      } else {
        calc <<= 1U;
      }
    }
  }

  return calc == crc;
}

static bool SHT3X_ReadMeasurement(float *temperature, float *humidity)
{
  uint8_t rx[6] = {0};
  uint16_t raw_temp = 0U;
  uint16_t raw_humi = 0U;

  SHT3X_Start();
  if (!SHT3X_WriteByte(0x88U) || !SHT3X_WriteByte(0x24U) || !SHT3X_WriteByte(0x00U)) {
    SHT3X_Stop();
    return false;
  }
  SHT3X_Stop();

  HAL_Delay(20);

  SHT3X_Start();
  if (!SHT3X_WriteByte(0x89U)) {
    SHT3X_Stop();
    return false;
  }

  for (uint8_t i = 0; i < 6U; ++i) {
    rx[i] = SHT3X_ReadByte(i < 5U);
  }
  SHT3X_Stop();

  if (!SHT3X_CheckCrc(&rx[0], rx[2]) || !SHT3X_CheckCrc(&rx[3], rx[5])) {
    return false;
  }

  raw_temp = (uint16_t)((rx[0] << 8U) | rx[1]);
  raw_humi = (uint16_t)((rx[3] << 8U) | rx[4]);

  *temperature = -45.0f + (175.0f * (float)raw_temp / 65535.0f);
  *humidity = 100.0f * (float)raw_humi / 65535.0f;

  if ((*temperature < -40.0f) || (*temperature > 125.0f) || (*humidity < 0.0f) || (*humidity > 100.0f)) {
    return false;
  }

  return true;
}

static const char *App_RelayStateText(GPIO_PinState pin_state)
{
  return (pin_state == RELAY_ACTIVE_STATE) ? "ON" : "OFF";
}

static void App_ShowLine(uint8_t x, uint8_t page, const char *text)
{
  char line[22];
  size_t len = 0U;

  while ((text[len] != '\0') && (len < (sizeof(line) - 1U))) {
    line[len] = text[len];
    ++len;
  }
  while (len < (sizeof(line) - 1U)) {
    line[len++] = ' ';
  }
  line[sizeof(line) - 1U] = '\0';

  OLED_ShowString(x, page, line);
}

static void App_ShowBootStatus(const char *title, const char *detail)
{
  OLED_Clear();
  App_ShowLine(0, 0, "NB-IOT CONNECT");
  App_ShowLine(0, 1, title != NULL ? title : "");
  App_ShowLine(0, 2, detail != NULL ? detail : "");
  App_ShowLine(0, 3, "WAIT...");
}

static void App_UpdateStatusLine(void)
{
  char line[22];

  snprintf(line, sizeof(line), "UP:%s DO:%s",
           nb_upload_enabled ? "ON" : "OFF",
           nb_downlink_poll_enabled ? "ON" : "OFF");
  App_ShowLine(0, 3, line);
}

static void App_DrawMainScreen(void)
{
  OLED_Clear();
  App_ShowLine(0, 0, "R1:OFF");
  App_ShowLine(64, 0, "R2:OFF");
  App_ShowLine(0, 2, "T:WAIT");
  App_ShowLine(64, 2, "H:WAIT");
  App_UpdateStatusLine();
  app_main_screen_active = true;
}

static void App_UpdateField(uint8_t x, uint8_t page, char *cache, size_t cache_size, const char *text)
{
  char field[11];
  size_t len = 0U;

  while ((text[len] != '\0') && (len < (sizeof(field) - 1U))) {
    field[len] = text[len];
    ++len;
  }
  while (len < (sizeof(field) - 1U)) {
    field[len++] = ' ';
  }
  field[sizeof(field) - 1U] = '\0';

  if (strncmp(cache, field, cache_size) != 0) {
    strncpy(cache, field, cache_size);
    cache[cache_size - 1U] = '\0';
    OLED_ShowString(x, page, cache);
  }
}

static void App_FormatFixed1(char *buffer, size_t buffer_size, const char *prefix, float value, const char *suffix)
{
  int scaled = (int)(value * 10.0f);
  int integer_part = scaled / 10;
  int decimal_part = scaled >= 0 ? (scaled % 10) : -(scaled % 10);

  if ((value < 0.0f) && (integer_part == 0)) {
    snprintf(buffer, buffer_size, "%s-0.%d%s", prefix, decimal_part, suffix);
  } else {
    snprintf(buffer, buffer_size, "%s%d.%d%s", prefix, integer_part, decimal_part, suffix);
  }
}

static void App_FormatNumberFixed1(char *buffer, size_t buffer_size, float value)
{
  App_FormatFixed1(buffer, buffer_size, "", value, "");
}

static void App_UpdateDisplay(float temperature, float humidity, bool sensor_ok)
{
  static char r1_cache[11] = "";
  static char r2_cache[11] = "";
  static char t_cache[11] = "";
  static char h_cache[11] = "";
  char line[16];

  if (!app_main_screen_active) {
    return;
  }

  snprintf(line, sizeof(line), "R1:%s", App_RelayStateText(HAL_GPIO_ReadPin(RELAY1_GPIO_Port, RELAY1_Pin)));
  App_UpdateField(0, 0, r1_cache, sizeof(r1_cache), line);

  snprintf(line, sizeof(line), "R2:%s", App_RelayStateText(HAL_GPIO_ReadPin(RELAY2_GPIO_Port, RELAY2_Pin)));
  App_UpdateField(64, 0, r2_cache, sizeof(r2_cache), line);

  if (sensor_ok) {
    App_FormatFixed1(line, sizeof(line), "T:", temperature, "C");
    App_UpdateField(0, 2, t_cache, sizeof(t_cache), line);

    App_FormatFixed1(line, sizeof(line), "H:", humidity, "%");
    App_UpdateField(64, 2, h_cache, sizeof(h_cache), line);
  }
}

static void App_ApplyRelayState(GPIO_TypeDef *port, uint16_t pin, bool is_on)
{
  HAL_GPIO_WritePin(port, pin, is_on ? RELAY_ACTIVE_STATE : GPIO_PIN_RESET);
}

static const char *App_NbReadyStageText(void)
{
  switch (nb_ready_stage) {
    case 0U:
      return "STATUS: ATTACH";
    case 1U:
      return "STATUS: REGISTER";
    case 2U:
      return "STATUS: SESSION";
    case 3U:
      return "STATUS: SUCCESS";
    default:
      return "STATUS: ATTACH";
  }
}

static void App_ApplyFillLightState(bool is_on)
{
  GPIO_PinState led_state = is_on ? GPIO_PIN_RESET : GPIO_PIN_SET;

  HAL_GPIO_WritePin(LED_R_GPIO_Port, LED_R_Pin | LED_G_Pin | LED_B_Pin, led_state);
}

static void App_SendTelemetry(float temperature, float humidity, bool sensor_ok)
{
  char message[160];
  char pc_message[168];
  char temperature_text[12];
  char humidity_text[12];

  if (!sensor_ok) {
    return;
  }

  App_FormatNumberFixed1(temperature_text, sizeof(temperature_text), temperature);
  App_FormatNumberFixed1(humidity_text, sizeof(humidity_text), humidity);
  snprintf(message, sizeof(message),
           "{\"device_id\":\"%s\",\"temperature\":%s,\"humidity\":%s,\"co2_concentration\":null,\"ammonia_concentration\":null}",
           APP_DEVICE_ID, temperature_text, humidity_text);
  snprintf(pc_message, sizeof(pc_message), "%s\r\n", message);
  APP_UART_SendText(pc_message);

#if APP_NB_TELEMETRY_ENABLED
  (void)App_NbSendPayload(message);
#endif
}

static void App_NbInit(void)
{
#if APP_NB_TELEMETRY_ENABLED
  char command[96];

  App_NbSetReady(false);
  nb_last_attached = false;
  nb_last_registered = false;
  nb_last_mo_ready = false;
  nb_ready_stage = 0U;
  nb_boot_success_pending = false;
  nb_boot_success_tick = 0U;
  App_ShowBootStatus("STATUS: START", "POWER ON +2S");
  HAL_Delay(APP_NB_BOOT_READY_WAIT_MS);
  App_NbDrainResponse(300U);
  App_ShowBootStatus("STATUS: INIT", "ATE1 / CFUN / NCDP");
  (void)App_NbSendCommand("ATE1\r\n", 1000U);
  (void)App_NbSendCommand("AT+CFUN=0\r\n", 3000U);
  snprintf(command, sizeof(command), "AT+NCDP=%s,%u\r\n", APP_NB_SERVER_ADDR, APP_NB_SERVER_PORT);
  (void)App_NbSendCommand(command, 1500U);
  (void)App_NbSendCommand("AT+CFUN=1\r\n", 5000U);
  HAL_Delay(3000U);
  App_ShowBootStatus("STATUS: ATTACH", "WAIT NETWORK");
  (void)App_NbSendCommand("AT+CEDRXS=0,5\r\n", 1500U);
  (void)App_NbSendCommand("AT+CPSMS=0\r\n", 1500U);
  snprintf(command, sizeof(command), "AT+CGDCONT=1,\"IP\",\"%s\"\r\n", APP_NB_APN);
  (void)App_NbSendCommand(command, 1500U);
  (void)App_NbSendCommand("AT+CGATT=1\r\n", 1500U);
  (void)App_NbSendCommand("AT+NNMI=2\r\n", 1500U);
  nb_last_attach_retry_tick = HAL_GetTick();
  (void)App_NbQueryNetworkReady(true);
#endif
}

static bool App_NbSendCommand(const char *command, uint32_t wait_ms)
{
  char response[256];

  if (command == NULL) {
    return false;
  }

  App_NbDrainResponse(80U);
  if (APP_NB_UART_SendText(command) != HAL_OK) {
    return false;
  }

  if (App_NbReadResponse(response, sizeof(response), wait_ms) == 0U) {
    return false;
  }

  return App_NbResponseIsSuccess(response);
}

static bool App_NbSendPayload(const char *payload)
{
  char hex_payload[320];
  char at_command[352];
  size_t payload_length = 0U;

  if ((payload == NULL) || (payload[0] == '\0')) {
    return false;
  }

  if (!nb_network_ready) {
    return false;
  }

  payload_length = strlen(payload);
  if ((payload_length == 0U) || (payload_length > 159U)) {
    return false;
  }

  if (!App_BytesToHex(payload, hex_payload, sizeof(hex_payload))) {
    return false;
  }

  snprintf(at_command, sizeof(at_command), "AT+NMGS=%u,%s\r\n", (unsigned int)payload_length, hex_payload);
  if (!App_NbSendCommand(at_command, APP_NB_RESPONSE_DRAIN_MS)) {
    App_NbSetReady(false);
    return false;
  }

  return true;
}

static bool App_BytesToHex(const char *input, char *output, size_t output_size)
{
  static const char hex_chars[] = "0123456789ABCDEF";
  size_t input_length = 0U;
  size_t i = 0U;

  if ((input == NULL) || (output == NULL) || (output_size == 0U)) {
    return false;
  }

  input_length = strlen(input);
  if ((input_length * 2U + 1U) > output_size) {
    return false;
  }

  for (i = 0U; i < input_length; ++i) {
    uint8_t value = (uint8_t)input[i];
    output[i * 2U] = hex_chars[(value >> 4U) & 0x0FU];
    output[i * 2U + 1U] = hex_chars[value & 0x0FU];
  }
  output[input_length * 2U] = '\0';

  return true;
}

static void App_NbDrainResponse(uint32_t timeout_ms)
{
  char response[256];
  (void)App_NbReadResponse(response, sizeof(response), timeout_ms);
}

static void App_NbMirrorPendingOutput(void)
{
#if APP_NB_TELEMETRY_ENABLED
  uint8_t value = 0U;
  char response[256];
  size_t length = 0U;

  while (APP_NB_UART_ReadByte(&value, 1U) == HAL_OK) {
    (void)HAL_UART_Transmit(&huart1, &value, 1U, 20U);
    if (length < (sizeof(response) - 1U)) {
      response[length++] = (char)value;
      response[length] = '\0';
    }
  }

  if (length > 0U) {
    App_NbHandleResponse(response);
  }
#endif
}

static void App_NbSetReady(bool ready)
{
  if (nb_network_ready == ready) {
    return;
  }

  nb_network_ready = ready;
}

static bool App_NbQueryNetworkReady(bool trace)
{
#if APP_NB_TELEMETRY_ENABLED
  char response[256];
  bool attached = nb_last_attached;
  bool registered = nb_last_registered;
  bool mo_ready = nb_last_mo_ready;
  bool previous_trace = nb_trace_enabled;

  nb_trace_enabled = trace;
  App_NbDrainResponse(80U);

  if (APP_NB_UART_SendText("AT+CGATT?\r\n") == HAL_OK) {
    if (App_NbReadResponse(response, sizeof(response), 1500U) > 0U) {
      attached = (strstr(response, "+CGATT:1") != NULL);
    }
  }

  if (!attached) {
    registered = false;
    mo_ready = false;
    nb_ready_stage = 0U;
  } else if (APP_NB_UART_SendText("AT+CEREG?\r\n") == HAL_OK) {
    if (App_NbReadResponse(response, sizeof(response), 1500U) > 0U) {
      registered = (strstr(response, "+CEREG:0,1") != NULL) || (strstr(response, "+CEREG:1,1") != NULL);
    }
  }

  if (!registered) {
    mo_ready = false;
    nb_ready_stage = 1U;
  } else if (APP_NB_UART_SendText("AT+NMSTATUS?\r\n") == HAL_OK) {
    if (App_NbReadResponse(response, sizeof(response), 1500U) > 0U) {
      mo_ready = (strstr(response, "MO_DATA_ENABLED") != NULL);
    }
  }

  if (attached && registered && !mo_ready) {
    nb_ready_stage = 2U;
  } else if (attached && registered && mo_ready) {
    nb_ready_stage = 3U;
  }

  nb_last_attached = attached;
  nb_last_registered = registered;
  nb_last_mo_ready = mo_ready;
  nb_trace_enabled = previous_trace;
  App_NbSetReady(attached && registered && mo_ready);
  return nb_network_ready;
#else
  (void)trace;
  return false;
#endif
}

static bool App_NbResponseHasToken(const char *response, const char *token)
{
  return (response != NULL) && (token != NULL) && (strstr(response, token) != NULL);
}

static bool App_NbResponseIsSuccess(const char *response)
{
  if (response == NULL) {
    return false;
  }

  if (App_NbResponseHasToken(response, "+CME ERROR") ||
      App_NbResponseHasToken(response, "+CMS ERROR") ||
      App_NbResponseHasToken(response, "ERROR")) {
    return false;
  }

  return App_NbResponseHasToken(response, "OK");
}

static int App_HexNibble(char value)
{
  if ((value >= '0') && (value <= '9')) {
    return value - '0';
  }
  if ((value >= 'A') && (value <= 'F')) {
    return value - 'A' + 10;
  }
  if ((value >= 'a') && (value <= 'f')) {
    return value - 'a' + 10;
  }
  return -1;
}

static bool App_HexToText(const char *input, char *output, size_t output_size)
{
  size_t input_length = 0U;
  size_t i = 0U;
  size_t out_index = 0U;

  if ((input == NULL) || (output == NULL) || (output_size == 0U)) {
    return false;
  }

  input_length = strlen(input);
  if ((input_length == 0U) || ((input_length % 2U) != 0U) || ((input_length / 2U + 1U) > output_size)) {
    return false;
  }

  for (i = 0U; i < input_length; i += 2U) {
    int high = App_HexNibble(input[i]);
    int low = App_HexNibble(input[i + 1U]);
    if ((high < 0) || (low < 0)) {
      return false;
    }
    output[out_index++] = (char)((high << 4) | low);
  }
  output[out_index] = '\0';

  return true;
}

static bool App_HexToBytes(const char *input, uint8_t *output, size_t output_size, size_t *decoded_length)
{
  size_t input_length = 0U;
  size_t out_index = 0U;
  size_t i = 0U;

  if ((input == NULL) || (output == NULL) || (output_size == 0U)) {
    return false;
  }

  input_length = strlen(input);
  if ((input_length == 0U) || ((input_length % 2U) != 0U) || ((input_length / 2U) > output_size)) {
    return false;
  }

  for (i = 0U; i < input_length; i += 2U) {
    int high = App_HexNibble(input[i]);
    int low = App_HexNibble(input[i + 1U]);

    if ((high < 0) || (low < 0)) {
      return false;
    }

    output[out_index++] = (uint8_t)((high << 4) | low);
  }

  if (decoded_length != NULL) {
    *decoded_length = out_index;
  }

  return true;
}

static int App_Base64Value(char value)
{
  if ((value >= 'A') && (value <= 'Z')) {
    return value - 'A';
  }
  if ((value >= 'a') && (value <= 'z')) {
    return value - 'a' + 26;
  }
  if ((value >= '0') && (value <= '9')) {
    return value - '0' + 52;
  }
  if (value == '+') {
    return 62;
  }
  if (value == '/') {
    return 63;
  }
  if (value == '=') {
    return -2;
  }
  return -1;
}

static bool App_Base64ToText(const char *input, char *output, size_t output_size)
{
  size_t out_index = 0U;
  int block[4];
  int block_index = 0;
  const char *cursor = input;

  if ((input == NULL) || (output == NULL) || (output_size == 0U)) {
    return false;
  }

  while (*cursor != '\0') {
    int value = App_Base64Value(*cursor++);
    if (value < 0) {
      if (value == -2) {
        block[block_index++] = -2;
      } else {
        continue;
      }
    } else {
      block[block_index++] = value;
    }

    if (block_index == 4) {
      uint32_t triple = 0U;
      int padding = 0;
      int i = 0;

      for (i = 0; i < 4; ++i) {
        if (block[i] == -2) {
          block[i] = 0;
          ++padding;
        }
        triple = (triple << 6U) | (uint32_t)block[i];
      }

      if ((out_index + 3U) >= output_size) {
        return false;
      }

      output[out_index++] = (char)((triple >> 16U) & 0xFFU);
      if (padding < 2) {
        output[out_index++] = (char)((triple >> 8U) & 0xFFU);
      }
      if (padding < 1) {
        output[out_index++] = (char)(triple & 0xFFU);
      }
      block_index = 0;
    }
  }

  output[out_index] = '\0';
  return out_index > 0U;
}

static bool App_TryHandleDecodedDownlink(const char *payload_text)
{
  char decoded_base64[160];

  if (payload_text == NULL) {
    return false;
  }

  if (payload_text[0] == '{') {
    App_HandleCommandLine(payload_text);
    return true;
  }

  if (App_Base64ToText(payload_text, decoded_base64, sizeof(decoded_base64)) && (decoded_base64[0] == '{')) {
    App_HandleCommandLine(decoded_base64);
    return true;
  }

  return false;
}

static bool App_TryHandleLegacyCtDownlink(const char *hex_payload)
{
  uint8_t packet[64];
  size_t packet_length = 0U;
  uint8_t user_cmd = 0U;

  if (!App_HexToBytes(hex_payload, packet, sizeof(packet), &packet_length)) {
    return false;
  }

  if (packet_length < 6U) {
    return false;
  }

  if (packet[0] != 0x01U) {
    return false;
  }

  user_cmd = packet[3];

  switch (user_cmd) {
    case 0x01U: /* CTL_LED */
      fill_light_manual_override = true;
      fill_light_manual_state = (fill_light_manual_state == GPIO_PIN_SET) ? GPIO_PIN_RESET : GPIO_PIN_SET;
      App_ApplyFillLightState(fill_light_manual_state == GPIO_PIN_SET);
      return true;

    case 0x03U: /* CTL_SWITCH_1 */
      relay1_manual_override = true;
      relay1_manual_state = (relay1_manual_state == RELAY_ACTIVE_STATE) ? GPIO_PIN_RESET : RELAY_ACTIVE_STATE;
      App_ApplyRelayState(RELAY1_GPIO_Port, RELAY1_Pin, relay1_manual_state == RELAY_ACTIVE_STATE);
      return true;

    case 0x04U: /* CTL_SWITCH_2 */
      relay2_manual_override = true;
      relay2_manual_state = (relay2_manual_state == RELAY_ACTIVE_STATE) ? GPIO_PIN_RESET : RELAY_ACTIVE_STATE;
      App_ApplyRelayState(RELAY2_GPIO_Port, RELAY2_Pin, relay2_manual_state == RELAY_ACTIVE_STATE);
      return true;

    default:
      return false;
  }
}

static size_t App_NbReadResponse(char *buffer, size_t buffer_size, uint32_t timeout_ms)
{
  uint8_t value = 0U;
  uint32_t start_tick = HAL_GetTick();
  uint32_t last_data_tick = start_tick;
  size_t length = 0U;

  if ((buffer == NULL) || (buffer_size == 0U)) {
    return 0U;
  }

  while ((HAL_GetTick() - start_tick) < timeout_ms) {
    if (APP_NB_UART_ReadByte(&value, 20U) != HAL_OK) {
      continue;
    }
    last_data_tick = HAL_GetTick();
    if (nb_trace_enabled) {
      (void)HAL_UART_Transmit(&huart1, &value, 1U, 20U);
    }
    if (length < (buffer_size - 1U)) {
      buffer[length++] = (char)value;
      buffer[length] = '\0';
      if (App_NbResponseHasToken(buffer, "\r\nOK\r\n") ||
          App_NbResponseHasToken(buffer, "\r\nERROR\r\n") ||
          App_NbResponseHasToken(buffer, "+CME ERROR") ||
          App_NbResponseHasToken(buffer, "+CMS ERROR")) {
        break;
      }
    }
  }

  buffer[length] = '\0';
  return length;
}

static void App_NbPollDownlink(void)
{
#if APP_NB_TELEMETRY_ENABLED
  char response[256];
  char queue_status[128];
  bool nmgr_ok = false;
  bool nqmgr_ok = false;

  if (!nb_network_ready) {
    APP_UART_SendText("[NB POLL] WAIT READY\r\n");
    return;
  }

  APP_UART_SendText("[NB POLL] AT+NMGR\r\n");
  App_NbDrainResponse(80U);
  if (APP_NB_UART_SendText("AT+NMGR\r\n") != HAL_OK) {
    APP_UART_SendText("[NB POLL] SEND FAIL\r\n");
    App_NbSetReady(false);
    if (nb_downlink_no_response_count < 255U) {
      ++nb_downlink_no_response_count;
    }
    if (nb_downlink_no_response_count >= 3U) {
      App_NbRecoverDownlinkSession();
    }
    return;
  }
  if (App_NbReadResponse(response, sizeof(response), APP_NB_DOWNLINK_READ_MS) > 0U) {
    nmgr_ok = true;
    App_NbHandleResponse(response);
  } else {
    APP_UART_SendText("[NB POLL] NO RESPONSE\r\n");
  }

  APP_UART_SendText("[NB POLL] AT+NQMGR\r\n");
  if (APP_NB_UART_SendText("AT+NQMGR\r\n") == HAL_OK) {
    if (App_NbReadResponse(queue_status, sizeof(queue_status), 800U) == 0U) {
      APP_UART_SendText("[NB POLL] NQMGR NO RESPONSE\r\n");
    } else {
      nqmgr_ok = true;
    }
  } else {
    APP_UART_SendText("[NB POLL] NQMGR SEND FAIL\r\n");
  }

  if (nmgr_ok || nqmgr_ok) {
    nb_downlink_no_response_count = 0U;
  } else {
    if (nb_downlink_no_response_count < 255U) {
      ++nb_downlink_no_response_count;
    }
    if (nb_downlink_no_response_count >= 3U) {
      App_NbRecoverDownlinkSession();
    }
  }
#endif
}

static void App_NbRecoverDownlinkSession(void)
{
#if APP_NB_TELEMETRY_ENABLED
  APP_UART_SendText("[NB POLL] RECOVER SESSION\r\n");
  nb_downlink_no_response_count = 0U;
  App_NbSetReady(false);
  (void)App_NbSendCommand("AT+NNMI=2\r\n", 1500U);
  if (!App_NbQueryNetworkReady(true)) {
    APP_UART_SendText("[NB POLL] REINIT BC28\r\n");
    App_NbInit();
  }
  nb_pending_immediate_downlink_poll = true;
#endif
}

static void App_NbHandleResponse(const char *response)
{
  const char *cursor = response;

  if (response == NULL) {
    return;
  }

  while (*cursor != '\0') {
    const char *line_end = strstr(cursor, "\r\n");
    size_t line_length = line_end != NULL ? (size_t)(line_end - cursor) : strlen(cursor);
    char line[256];
    const char *payload_start = NULL;
    char hex_payload[224];
    char decoded_payload[160];
    size_t hex_length = 0U;

    if (line_length >= sizeof(line)) {
      line_length = sizeof(line) - 1U;
    }

    memcpy(line, cursor, line_length);
    line[line_length] = '\0';

    while ((line[0] == ' ') || (line[0] == '\t')) {
      memmove(line, line + 1, strlen(line));
    }

    if ((strcmp(line, "+NNMI") == 0) || (strcmp(line, "+NNMI\r") == 0)) {
      nb_pending_immediate_downlink_poll = true;
      APP_UART_SendText("[NB POLL] NNMI TRIGGER\r\n");
    }

    if ((strncmp(line, "+NNMI:", 6U) == 0) || (strncmp(line, "+NMGR:", 6U) == 0)) {
      const char *scan = line;
      while ((scan = strchr(scan, ',')) != NULL) {
        const char *candidate = scan + 1;
        while ((*candidate == ' ') || (*candidate == '\t') || (*candidate == '"')) {
          ++candidate;
        }
        if (App_HexNibble(*candidate) >= 0) {
          payload_start = candidate;
          break;
        }
        scan = candidate;
      }
    } else if ((line[0] >= '0') && (line[0] <= '9')) {
      const char *scan = line;
      while ((scan = strchr(scan, ',')) != NULL) {
        const char *candidate = scan + 1;
        while ((*candidate == ' ') || (*candidate == '\t') || (*candidate == '"')) {
          ++candidate;
        }
        if (App_HexNibble(*candidate) >= 0) {
          payload_start = candidate;
          break;
        }
        scan = candidate;
      }
    }

    if (payload_start != NULL) {
      while ((App_HexNibble(*payload_start) >= 0) && (hex_length < (sizeof(hex_payload) - 1U))) {
        hex_payload[hex_length++] = *payload_start++;
      }
      hex_payload[hex_length] = '\0';

      if (App_HexToText(hex_payload, decoded_payload, sizeof(decoded_payload))) {
        if (!App_TryHandleDecodedDownlink(decoded_payload)) {
          (void)App_TryHandleLegacyCtDownlink(hex_payload);
        }
      } else {
        (void)App_TryHandleLegacyCtDownlink(hex_payload);
      }
    }

    if (line_end == NULL) {
      break;
    }
    cursor = line_end + 2U;
  }
}

static void App_SetUploadEnabled(bool enabled)
{
  const char *log_text = enabled ? "[NB UPLOAD] ON\r\n" : "[NB UPLOAD] OFF\r\n";

  nb_upload_enabled = enabled;
  nb_pending_first_telemetry = enabled;
  APP_UART_SendText(log_text);
  if (app_main_screen_active) {
    App_UpdateStatusLine();
  }
}

static void App_HandleK1UploadToggle(void)
{
  static GPIO_PinState last_raw_state = GPIO_PIN_SET;
  static GPIO_PinState stable_state = GPIO_PIN_SET;
  static uint32_t last_change_tick = 0U;
  static uint32_t first_click_tick = 0U;
  static uint8_t click_count = 0U;

  GPIO_PinState raw_state = HAL_GPIO_ReadPin(K1_GPIO_Port, K1_Pin);
  uint32_t now = HAL_GetTick();

  if (raw_state != last_raw_state) {
    last_raw_state = raw_state;
    last_change_tick = now;
  }

  if ((now - last_change_tick) < APP_K1_DEBOUNCE_MS) {
    return;
  }

  if (raw_state == stable_state) {
    if ((click_count > 0U) && ((now - first_click_tick) > APP_UPLOAD_TOGGLE_WINDOW_MS)) {
      click_count = 0U;
    }
    return;
  }

  stable_state = raw_state;
  if (stable_state == GPIO_PIN_RESET) {
    if ((click_count == 0U) || ((now - first_click_tick) > APP_UPLOAD_TOGGLE_WINDOW_MS)) {
      first_click_tick = now;
      click_count = 1U;
    } else {
      ++click_count;
    }

    if (click_count >= APP_UPLOAD_TOGGLE_CLICKS) {
      click_count = 0U;
      App_SetUploadEnabled(!nb_upload_enabled);
    }
  }
}

static void App_SetDownlinkPollEnabled(bool enabled)
{
  const char *log_text = enabled ? "[NB DOWNLINK] ON\r\n" : "[NB DOWNLINK] OFF\r\n";

  nb_downlink_poll_enabled = enabled;
  nb_pending_immediate_downlink_poll = enabled;
  APP_UART_SendText(log_text);
  if (app_main_screen_active) {
    App_UpdateStatusLine();
  }
}

static void App_HandleK2DownlinkToggle(void)
{
  static GPIO_PinState last_raw_state = GPIO_PIN_SET;
  static GPIO_PinState stable_state = GPIO_PIN_SET;
  static uint32_t last_change_tick = 0U;
  static uint32_t first_click_tick = 0U;
  static uint8_t click_count = 0U;

  GPIO_PinState raw_state = HAL_GPIO_ReadPin(K2_GPIO_Port, K2_Pin);
  uint32_t now = HAL_GetTick();

  if (raw_state != last_raw_state) {
    last_raw_state = raw_state;
    last_change_tick = now;
  }

  if ((now - last_change_tick) < APP_K1_DEBOUNCE_MS) {
    return;
  }

  if (raw_state == stable_state) {
    if ((click_count > 0U) && ((now - first_click_tick) > APP_UPLOAD_TOGGLE_WINDOW_MS)) {
      click_count = 0U;
    }
    return;
  }

  stable_state = raw_state;
  if (stable_state == GPIO_PIN_RESET) {
    if ((click_count == 0U) || ((now - first_click_tick) > APP_UPLOAD_TOGGLE_WINDOW_MS)) {
      first_click_tick = now;
      click_count = 1U;
    } else {
      ++click_count;
    }

    if (click_count >= APP_UPLOAD_TOGGLE_CLICKS) {
      click_count = 0U;
      App_SetDownlinkPollEnabled(!nb_downlink_poll_enabled);
    }
  }
}

static void App_SendAck(long command_id, const char *status)
{
  char message[96];

  snprintf(message, sizeof(message),
           "{\"device_id\":\"%s\",\"type\":\"ack\",\"command_id\":%ld,\"status\":\"%s\"}\r\n",
           APP_DEVICE_ID, command_id, status);
  APP_UART_SendText(message);
#if APP_NB_TELEMETRY_ENABLED
  if (nb_network_ready) {
    char nb_message[96];
    snprintf(nb_message, sizeof(nb_message),
             "{\"device_id\":\"%s\",\"type\":\"ack\",\"command_id\":%ld,\"status\":\"%s\"}",
             APP_DEVICE_ID, command_id, status);
    (void)App_NbSendPayload(nb_message);
  }
#endif
}

static bool App_ExtractJsonString(const char *json, const char *key, char *value, size_t value_size)
{
  char pattern[32];
  const char *start = NULL;
  const char *end = NULL;
  size_t copy_length = 0U;

  if ((json == NULL) || (key == NULL) || (value == NULL) || (value_size == 0U)) {
    return false;
  }

  snprintf(pattern, sizeof(pattern), "\"%s\":\"", key);
  start = strstr(json, pattern);
  if (start == NULL) {
    return false;
  }

  start += strlen(pattern);
  end = strchr(start, '"');
  if (end == NULL) {
    return false;
  }

  copy_length = (size_t)(end - start);
  if (copy_length >= value_size) {
    copy_length = value_size - 1U;
  }

  memcpy(value, start, copy_length);
  value[copy_length] = '\0';
  return true;
}

static bool App_ExtractJsonLong(const char *json, const char *key, long *value)
{
  char pattern[32];
  char *end_ptr = NULL;
  const char *start = NULL;

  if ((json == NULL) || (key == NULL) || (value == NULL)) {
    return false;
  }

  snprintf(pattern, sizeof(pattern), "\"%s\":", key);
  start = strstr(json, pattern);
  if (start == NULL) {
    return false;
  }

  start += strlen(pattern);
  *value = strtol(start, &end_ptr, 10);
  return end_ptr != start;
}

static void App_HandleCommandLine(const char *line)
{
  char target[24];
  char command[16];
  long command_id = 0L;
  bool target_ok = false;
  bool command_ok = false;

  if (line == NULL) {
    return;
  }

  target_ok = App_ExtractJsonString(line, "target", target, sizeof(target));
  if (!target_ok) {
    target_ok = App_ExtractJsonString(line, "target_component", target, sizeof(target));
  }
  command_ok = App_ExtractJsonString(line, "command", command, sizeof(command));
  if (!command_ok) {
    command_ok = App_ExtractJsonString(line, "command_type", command, sizeof(command));
  }

  if (!App_ExtractJsonLong(line, "command_id", &command_id)) {
    (void)App_ExtractJsonLong(line, "id", &command_id);
  }

  if ((command_id == 0L) || !target_ok || !command_ok) {
    return;
  }

  if ((strcmp(target, "relay1") == 0) || (strcmp(target, "fan") == 0)) {
    if (strcmp(command, "ON") == 0) {
      relay1_manual_override = true;
      relay1_manual_state = RELAY_ACTIVE_STATE;
      App_ApplyRelayState(RELAY1_GPIO_Port, RELAY1_Pin, true);
      App_SendAck(command_id, "ok");
    } else if (strcmp(command, "OFF") == 0) {
      relay1_manual_override = true;
      relay1_manual_state = GPIO_PIN_RESET;
      App_ApplyRelayState(RELAY1_GPIO_Port, RELAY1_Pin, false);
      App_SendAck(command_id, "ok");
    } else if (strcmp(command, "AUTO") == 0) {
      relay1_manual_override = false;
      App_SendAck(command_id, "ok");
    } else {
      App_SendAck(command_id, "unsupported");
    }
  } else if ((strcmp(target, "relay2") == 0) || (strcmp(target, "cooling_pad") == 0) || (strcmp(target, "pump") == 0)) {
    if (strcmp(command, "ON") == 0) {
      relay2_manual_override = true;
      relay2_manual_state = RELAY_ACTIVE_STATE;
      App_ApplyRelayState(RELAY2_GPIO_Port, RELAY2_Pin, true);
      App_SendAck(command_id, "ok");
    } else if (strcmp(command, "OFF") == 0) {
      relay2_manual_override = true;
      relay2_manual_state = GPIO_PIN_RESET;
      App_ApplyRelayState(RELAY2_GPIO_Port, RELAY2_Pin, false);
      App_SendAck(command_id, "ok");
    } else if (strcmp(command, "AUTO") == 0) {
      relay2_manual_override = false;
      App_SendAck(command_id, "ok");
    } else {
      App_SendAck(command_id, "unsupported");
    }
  } else if ((strcmp(target, "fill_light") == 0) || (strcmp(target, "light") == 0) || (strcmp(target, "led") == 0)) {
    if (strcmp(command, "ON") == 0) {
      fill_light_manual_override = true;
      fill_light_manual_state = GPIO_PIN_SET;
      App_ApplyFillLightState(true);
      App_SendAck(command_id, "ok");
    } else if (strcmp(command, "OFF") == 0) {
      fill_light_manual_override = true;
      fill_light_manual_state = GPIO_PIN_RESET;
      App_ApplyFillLightState(false);
      App_SendAck(command_id, "ok");
    } else if (strcmp(command, "AUTO") == 0) {
      fill_light_manual_override = false;
      App_SendAck(command_id, "ok");
    } else {
      App_SendAck(command_id, "unsupported");
    }
  } else {
    App_SendAck(command_id, "unsupported");
  }
}

/* USER CODE END 0 */

/**
  * @brief  The application entry point.
  * @retval int
  */
int main(void)
{
  /* USER CODE BEGIN 1 */
  float temperature = 0.0f;
  float humidity = 0.0f;
  char boot_detail[22];
  bool sensor_ok = false;
  bool has_valid_sensor_data = false;
  uint32_t last_update_tick = 0U;
  uint32_t last_telemetry_tick = 0U;
  uint32_t last_downlink_poll_tick = 0U;
  uint32_t last_network_ready_check_tick = 0U;
  char uart_line[128];

  /* USER CODE END 1 */

  /* MCU Configuration--------------------------------------------------------*/

  /* Reset of all peripherals, Initializes the Flash interface and the Systick. */
  HAL_Init();

  /* USER CODE BEGIN Init */

  /* USER CODE END Init */

  /* Configure the system clock */
  SystemClock_Config();

  /* USER CODE BEGIN SysInit */

  /* USER CODE END SysInit */

  /* Initialize all configured peripherals */
  MX_GPIO_Init();
  MX_USART1_UART_Init();
  MX_USART3_UART_Init();
  /* USER CODE BEGIN 2 */
  APP_UART_StartReceiveIT();
  HAL_GPIO_WritePin(LED_R_GPIO_Port, LED_R_Pin|LED_G_Pin|LED_B_Pin, GPIO_PIN_SET);
  OLED_Init();
  OLED_Clear();
  app_main_screen_active = false;
  App_SetUploadEnabled(false);
  App_SetDownlinkPollEnabled(false);
  App_NbInit();
  snprintf(boot_detail, sizeof(boot_detail), "A:%d R:%d M:%d",
           nb_last_attached ? 1 : 0,
           nb_last_registered ? 1 : 0,
           nb_last_mo_ready ? 1 : 0);
  App_ShowBootStatus(App_NbReadyStageText(), boot_detail);
  last_network_ready_check_tick = HAL_GetTick();

  /* USER CODE END 2 */


  /* Infinite loop */
  /* USER CODE BEGIN WHILE */
  while (1)
  {
    /* USER CODE END WHILE */

    /* USER CODE BEGIN 3 */
    App_HandleK1UploadToggle();
    App_HandleK2DownlinkToggle();

    if (APP_UART_GetLine(uart_line, sizeof(uart_line)) != 0U) {
      App_HandleCommandLine(uart_line);
    }

    if ((HAL_GetTick() - last_update_tick) >= 500U) {
      last_update_tick = HAL_GetTick();
      sensor_ok = SHT3X_ReadMeasurement(&temperature, &humidity);
      if (sensor_ok) {
        has_valid_sensor_data = true;
        if (relay1_manual_override) {
          HAL_GPIO_WritePin(RELAY1_GPIO_Port, RELAY1_Pin, relay1_manual_state);
        } else {
          if (temperature >= RELAY1_ON_THRESHOLD_C) {
            relay1_auto_on = true;
          } else if (temperature <= RELAY1_OFF_THRESHOLD_C) {
            relay1_auto_on = false;
          }

          App_ApplyRelayState(RELAY1_GPIO_Port, RELAY1_Pin, relay1_auto_on);
        }

        if (relay2_manual_override) {
          HAL_GPIO_WritePin(RELAY2_GPIO_Port, RELAY2_Pin, relay2_manual_state);
        }

        if (fill_light_manual_override) {
          App_ApplyFillLightState(fill_light_manual_state == GPIO_PIN_SET);
        }
      }

      App_UpdateDisplay(temperature, humidity, has_valid_sensor_data);
    }

    if (!app_main_screen_active) {
      if (!nb_network_ready && ((HAL_GetTick() - last_network_ready_check_tick) >= APP_NB_READY_CHECK_INTERVAL_MS)) {
        last_network_ready_check_tick = HAL_GetTick();
        (void)App_NbQueryNetworkReady(true);
        snprintf(boot_detail, sizeof(boot_detail), "A:%d R:%d M:%d",
                 nb_last_attached ? 1 : 0,
                 nb_last_registered ? 1 : 0,
                 nb_last_mo_ready ? 1 : 0);
        App_ShowBootStatus(App_NbReadyStageText(), boot_detail);
      }

      if (nb_network_ready) {
        if (!nb_boot_success_pending) {
          App_ShowBootStatus("STATUS: SUCCESS", "NETWORK READY");
          nb_boot_success_pending = true;
          nb_boot_success_tick = HAL_GetTick();
        } else if ((HAL_GetTick() - nb_boot_success_tick) >= 1000U) {
          App_DrawMainScreen();
        }
      }
    } else if (!nb_network_ready && ((HAL_GetTick() - last_network_ready_check_tick) >= APP_NB_READY_CHECK_INTERVAL_MS)) {
      last_network_ready_check_tick = HAL_GetTick();
      (void)App_NbQueryNetworkReady(true);
    }

    if (nb_upload_enabled && nb_network_ready && nb_pending_first_telemetry && has_valid_sensor_data) {
      last_telemetry_tick = HAL_GetTick();
      App_SendTelemetry(temperature, humidity, sensor_ok);
      nb_pending_first_telemetry = false;
    } else if (nb_upload_enabled && nb_network_ready && has_valid_sensor_data && ((HAL_GetTick() - last_telemetry_tick) >= APP_TELEMETRY_INTERVAL_MS)) {
      last_telemetry_tick = HAL_GetTick();
      App_SendTelemetry(temperature, humidity, sensor_ok);
    }

    if (nb_downlink_poll_enabled &&
        (nb_pending_immediate_downlink_poll ||
         ((HAL_GetTick() - last_downlink_poll_tick) >= APP_NB_DOWNLINK_POLL_INTERVAL_MS))) {
      last_downlink_poll_tick = HAL_GetTick();
      nb_pending_immediate_downlink_poll = false;
      App_NbPollDownlink();
    }

    App_NbMirrorPendingOutput();
  }
  /* USER CODE END 3 */
}

/**
  * @brief System Clock Configuration
  * @retval None
  */
void SystemClock_Config(void)
{
  RCC_OscInitTypeDef RCC_OscInitStruct = {0};
  RCC_ClkInitTypeDef RCC_ClkInitStruct = {0};

  /** Initializes the RCC Oscillators according to the specified parameters
  * in the RCC_OscInitTypeDef structure.
  */
  RCC_OscInitStruct.OscillatorType = RCC_OSCILLATORTYPE_HSE;
  RCC_OscInitStruct.HSEState = RCC_HSE_ON;
  RCC_OscInitStruct.PLL.PLLState = RCC_PLL_ON;
  RCC_OscInitStruct.PLL.PLLSource = RCC_PLLSOURCE_HSE;
  RCC_OscInitStruct.PLL.PLLM = 1;
  RCC_OscInitStruct.PLL.PLLN = 8;
  RCC_OscInitStruct.PLL.PLLP = RCC_PLLP_DIV7;
  RCC_OscInitStruct.PLL.PLLQ = RCC_PLLQ_DIV2;
  RCC_OscInitStruct.PLL.PLLR = RCC_PLLR_DIV2;
  if (HAL_RCC_OscConfig(&RCC_OscInitStruct) != HAL_OK)
  {
    Error_Handler();
  }
  /** Initializes the CPU, AHB and APB buses clocks
  */
  RCC_ClkInitStruct.ClockType = RCC_CLOCKTYPE_HCLK|RCC_CLOCKTYPE_SYSCLK
                              |RCC_CLOCKTYPE_PCLK1|RCC_CLOCKTYPE_PCLK2;
  RCC_ClkInitStruct.SYSCLKSource = RCC_SYSCLKSOURCE_PLLCLK;
  RCC_ClkInitStruct.AHBCLKDivider = RCC_SYSCLK_DIV1;
  RCC_ClkInitStruct.APB1CLKDivider = RCC_HCLK_DIV1;
  RCC_ClkInitStruct.APB2CLKDivider = RCC_HCLK_DIV1;

  if (HAL_RCC_ClockConfig(&RCC_ClkInitStruct, FLASH_LATENCY_1) != HAL_OK)
  {
    Error_Handler();
  }
  /** Configure the main internal regulator output voltage
  */
  if (HAL_PWREx_ControlVoltageScaling(PWR_REGULATOR_VOLTAGE_SCALE1) != HAL_OK)
  {
    Error_Handler();
  }
}

/* USER CODE BEGIN 4 */

/* USER CODE END 4 */

/**
  * @brief  This function is executed in case of error occurrence.
  * @retval None
  */
void Error_Handler(void)
{
  /* USER CODE BEGIN Error_Handler_Debug */
  /* User can add his own implementation to report the HAL error return state */
  __disable_irq();
  while (1)
  {
  }
  /* USER CODE END Error_Handler_Debug */
}

#ifdef  USE_FULL_ASSERT
/**
  * @brief  Reports the name of the source file and the source line number
  *         where the assert_param error has occurred.
  * @param  file: pointer to the source file name
  * @param  line: assert_param error line source number
  * @retval None
  */
void assert_failed(uint8_t *file, uint32_t line)
{
  /* USER CODE BEGIN 6 */
  /* User can add his own implementation to report the file name and line number,
     ex: printf("Wrong parameters value: file %s on line %d\r\n", file, line) */
  /* USER CODE END 6 */
}
#endif /* USE_FULL_ASSERT */

/************************ (C) COPYRIGHT STMicroelectronics *****END OF FILE****/
