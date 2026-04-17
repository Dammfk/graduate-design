#ifndef __OLED_H
#define __OLED_H

#include "main.h"

void OLED_Init(void);
void OLED_Clear(void);
void OLED_ShowString(uint8_t x, uint8_t page, const char *text);

#endif
