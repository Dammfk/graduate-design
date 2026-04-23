#include "usart.h"

#include <string.h>

UART_HandleTypeDef huart1;
UART_HandleTypeDef huart3;

static uint8_t uart_rx_byte = 0U;
static char uart_line_buffer[128];
static volatile uint16_t uart_line_length = 0U;
static volatile uint8_t uart_line_ready = 0U;

void MX_USART1_UART_Init(void)
{
  huart1.Instance = USART1;
  huart1.Init.BaudRate = 115200;
  huart1.Init.WordLength = UART_WORDLENGTH_8B;
  huart1.Init.StopBits = UART_STOPBITS_1;
  huart1.Init.Parity = UART_PARITY_NONE;
  huart1.Init.Mode = UART_MODE_TX_RX;
  huart1.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart1.Init.OverSampling = UART_OVERSAMPLING_16;
  huart1.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart1.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;

  if (HAL_UART_Init(&huart1) != HAL_OK)
  {
    Error_Handler();
  }
}

void MX_USART3_UART_Init(void)
{
  huart3.Instance = USART3;
  huart3.Init.BaudRate = 9600;
  huart3.Init.WordLength = UART_WORDLENGTH_8B;
  huart3.Init.StopBits = UART_STOPBITS_1;
  huart3.Init.Parity = UART_PARITY_NONE;
  huart3.Init.Mode = UART_MODE_TX_RX;
  huart3.Init.HwFlowCtl = UART_HWCONTROL_NONE;
  huart3.Init.OverSampling = UART_OVERSAMPLING_16;
  huart3.Init.OneBitSampling = UART_ONE_BIT_SAMPLE_DISABLE;
  huart3.AdvancedInit.AdvFeatureInit = UART_ADVFEATURE_NO_INIT;

  if (HAL_UART_Init(&huart3) != HAL_OK)
  {
    Error_Handler();
  }
}

void APP_UART_StartReceiveIT(void)
{
  uart_line_length = 0U;
  uart_line_ready = 0U;
  HAL_UART_Receive_IT(&huart1, &uart_rx_byte, 1U);
}

uint8_t APP_UART_GetLine(char *buffer, uint16_t buffer_size)
{
  uint16_t copy_length = 0U;

  if ((buffer == NULL) || (buffer_size == 0U) || (uart_line_ready == 0U))
  {
    return 0U;
  }

  __disable_irq();
  copy_length = uart_line_length;
  if (copy_length >= buffer_size)
  {
    copy_length = (uint16_t)(buffer_size - 1U);
  }

  memcpy(buffer, uart_line_buffer, copy_length);
  buffer[copy_length] = '\0';
  uart_line_length = 0U;
  uart_line_ready = 0U;
  __enable_irq();

  return 1U;
}

HAL_StatusTypeDef APP_UART_SendText(const char *text)
{
  if (text == NULL)
  {
    return HAL_ERROR;
  }

  return HAL_UART_Transmit(&huart1, (uint8_t *)text, (uint16_t)strlen(text), 100U);
}

HAL_StatusTypeDef APP_NB_UART_SendText(const char *text)
{
  if (text == NULL)
  {
    return HAL_ERROR;
  }

  return HAL_UART_Transmit(&huart3, (uint8_t *)text, (uint16_t)strlen(text), 1000U);
}

HAL_StatusTypeDef APP_NB_UART_ReadByte(uint8_t *value, uint32_t timeout_ms)
{
  if (value == NULL)
  {
    return HAL_ERROR;
  }

  return HAL_UART_Receive(&huart3, value, 1U, timeout_ms);
}

void HAL_UART_RxCpltCallback(UART_HandleTypeDef *huart)
{
  if (huart->Instance == USART1)
  {
    if ((uart_rx_byte == '\r') || (uart_rx_byte == '\n'))
    {
      if (uart_line_length > 0U)
      {
        uart_line_buffer[uart_line_length] = '\0';
        uart_line_ready = 1U;
      }
    }
    else if (uart_line_ready == 0U)
    {
      if (uart_line_length < (sizeof(uart_line_buffer) - 1U))
      {
        uart_line_buffer[uart_line_length++] = (char)uart_rx_byte;
      }
      else
      {
        uart_line_length = 0U;
      }
    }

    HAL_UART_Receive_IT(&huart1, &uart_rx_byte, 1U);
  }
}
