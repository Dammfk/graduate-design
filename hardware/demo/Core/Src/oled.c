#include "oled.h"

#include <stddef.h>

#define OLED_ADDR 0x78
#define OLED_WIDTH 128U
#define OLED_PAGES 4U

typedef struct {
  char ch;
  uint8_t bitmap[5];
} OledGlyph;

static const OledGlyph kFont[] = {
    {' ', {0x00, 0x00, 0x00, 0x00, 0x00}},
    {'-', {0x08, 0x08, 0x08, 0x08, 0x08}},
    {'%', {0x63, 0x13, 0x08, 0x64, 0x63}},
    {'.', {0x00, 0x60, 0x60, 0x00, 0x00}},
    {':', {0x00, 0x36, 0x36, 0x00, 0x00}},
    {'0', {0x3E, 0x51, 0x49, 0x45, 0x3E}},
    {'1', {0x00, 0x42, 0x7F, 0x40, 0x00}},
    {'2', {0x42, 0x61, 0x51, 0x49, 0x46}},
    {'3', {0x21, 0x41, 0x45, 0x4B, 0x31}},
    {'4', {0x18, 0x14, 0x12, 0x7F, 0x10}},
    {'5', {0x27, 0x45, 0x45, 0x45, 0x39}},
    {'6', {0x3C, 0x4A, 0x49, 0x49, 0x30}},
    {'7', {0x01, 0x71, 0x09, 0x05, 0x03}},
    {'8', {0x36, 0x49, 0x49, 0x49, 0x36}},
    {'9', {0x06, 0x49, 0x49, 0x29, 0x1E}},
    {'A', {0x7E, 0x11, 0x11, 0x11, 0x7E}},
    {'C', {0x3E, 0x41, 0x41, 0x41, 0x22}},
    {'F', {0x7F, 0x09, 0x09, 0x09, 0x01}},
    {'H', {0x7F, 0x08, 0x08, 0x08, 0x7F}},
    {'I', {0x00, 0x41, 0x7F, 0x41, 0x00}},
    {'L', {0x7F, 0x40, 0x40, 0x40, 0x40}},
    {'N', {0x7F, 0x06, 0x08, 0x30, 0x7F}},
    {'O', {0x3E, 0x41, 0x41, 0x41, 0x3E}},
    {'R', {0x7F, 0x09, 0x19, 0x29, 0x46}},
    {'S', {0x26, 0x49, 0x49, 0x49, 0x32}},
    {'T', {0x01, 0x01, 0x7F, 0x01, 0x01}},
    {'W', {0x7F, 0x20, 0x18, 0x20, 0x7F}},
    {'X', {0x63, 0x14, 0x08, 0x14, 0x63}},
};

static void oled_delay(void)
{
  for (volatile uint32_t i = 0; i < 16U; ++i) {
    __NOP();
  }
}

static void oled_scl_write(GPIO_PinState state)
{
  HAL_GPIO_WritePin(OLED_SCL_GPIO_Port, OLED_SCL_Pin, state);
}

static void oled_sda_write(GPIO_PinState state)
{
  HAL_GPIO_WritePin(OLED_SDA_GPIO_Port, OLED_SDA_Pin, state);
}

static void oled_i2c_start(void)
{
  oled_sda_write(GPIO_PIN_SET);
  oled_scl_write(GPIO_PIN_SET);
  oled_delay();
  oled_sda_write(GPIO_PIN_RESET);
  oled_delay();
  oled_scl_write(GPIO_PIN_RESET);
}

static void oled_i2c_stop(void)
{
  oled_scl_write(GPIO_PIN_RESET);
  oled_sda_write(GPIO_PIN_RESET);
  oled_delay();
  oled_scl_write(GPIO_PIN_SET);
  oled_delay();
  oled_sda_write(GPIO_PIN_SET);
  oled_delay();
}

static void oled_i2c_write_byte(uint8_t value)
{
  for (uint8_t bit = 0; bit < 8U; ++bit) {
    oled_sda_write((value & 0x80U) != 0U ? GPIO_PIN_SET : GPIO_PIN_RESET);
    oled_delay();
    oled_scl_write(GPIO_PIN_SET);
    oled_delay();
    oled_scl_write(GPIO_PIN_RESET);
    value <<= 1U;
  }

  oled_sda_write(GPIO_PIN_SET);
  oled_delay();
  oled_scl_write(GPIO_PIN_SET);
  oled_delay();
  oled_scl_write(GPIO_PIN_RESET);
}

static void oled_write(uint8_t control, uint8_t value)
{
  oled_i2c_start();
  oled_i2c_write_byte(OLED_ADDR);
  oled_i2c_write_byte(control);
  oled_i2c_write_byte(value);
  oled_i2c_stop();
}

static void oled_write_command(uint8_t value)
{
  oled_write(0x00U, value);
}

static void oled_write_data(uint8_t value)
{
  oled_write(0x40U, value);
}

static void oled_set_pos(uint8_t x, uint8_t page)
{
  oled_write_command((uint8_t)(0xB0U + page));
  oled_write_command((uint8_t)(0x10U | ((x >> 4U) & 0x0FU)));
  oled_write_command((uint8_t)(x & 0x0FU));
}

static const uint8_t *oled_find_glyph(char ch)
{
  for (size_t i = 0; i < (sizeof(kFont) / sizeof(kFont[0])); ++i) {
    if (kFont[i].ch == ch) {
      return kFont[i].bitmap;
    }
  }

  return kFont[0].bitmap;
}

static void oled_show_char(uint8_t x, uint8_t page, char ch)
{
  const uint8_t *glyph = oled_find_glyph(ch);

  oled_set_pos(x, page);
  for (uint8_t i = 0; i < 5U; ++i) {
    oled_write_data(glyph[i]);
  }
  oled_write_data(0x00U);
}

void OLED_Init(void)
{
  HAL_Delay(100);
  oled_write_command(0xAEU);
  oled_write_command(0x20U);
  oled_write_command(0x10U);
  oled_write_command(0xB0U);
  oled_write_command(0xC8U);
  oled_write_command(0x00U);
  oled_write_command(0x10U);
  oled_write_command(0x40U);
  oled_write_command(0x81U);
  oled_write_command(0xFFU);
  oled_write_command(0xA1U);
  oled_write_command(0xA6U);
  oled_write_command(0xA8U);
  oled_write_command(0x1FU);
  oled_write_command(0xA4U);
  oled_write_command(0xD3U);
  oled_write_command(0x00U);
  oled_write_command(0xD5U);
  oled_write_command(0xF0U);
  oled_write_command(0xD9U);
  oled_write_command(0x22U);
  oled_write_command(0xDAU);
  oled_write_command(0x02U);
  oled_write_command(0xDBU);
  oled_write_command(0x49U);
  oled_write_command(0x8DU);
  oled_write_command(0x14U);
  oled_write_command(0xAFU);
  OLED_Clear();
}

void OLED_Clear(void)
{
  for (uint8_t page = 0; page < OLED_PAGES; ++page) {
    oled_set_pos(0U, page);
    for (uint8_t x = 0; x < OLED_WIDTH; ++x) {
      oled_write_data(0x00U);
    }
  }
}

void OLED_ShowString(uint8_t x, uint8_t page, const char *text)
{
  while ((text != NULL) && (*text != '\0') && (x <= (OLED_WIDTH - 6U))) {
    oled_show_char(x, page, *text);
    x = (uint8_t)(x + 6U);
    ++text;
  }
}
