#ifndef __USART_H__
#define __USART_H__

#ifdef __cplusplus
extern "C" {
#endif

#include "main.h"

extern UART_HandleTypeDef huart1;

void MX_USART1_UART_Init(void);
void APP_UART_StartReceiveIT(void);
uint8_t APP_UART_GetLine(char *buffer, uint16_t buffer_size);
HAL_StatusTypeDef APP_UART_SendText(const char *text);

#ifdef __cplusplus
}
#endif

#endif /* __USART_H__ */
