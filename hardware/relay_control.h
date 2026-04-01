/*
 * relay_control.h
 * 继电器控制模块
 */

#ifndef RELAY_CONTROL_H
#define RELAY_CONTROL_H

#include <stdint.h>

typedef enum {
    RELAY_OFF = 0,
    RELAY_ON = 1
} relay_state_t;

/* ===== 继电器引脚定义 ===== */
#define RELAY_FAN_PIN       17  // 排风扇继电器引脚
#define RELAY_PUMP_PIN      27  // 水泵继电器引脚

/* ===== 函数声明 ===== */

/**
 * 初始化继电器控制
 * @return: 0 成功，-1 失败
 */
int relay_init();

/**
 * 设置继电器状态
 * @param relay_id: 继电器编号（0-排风扇, 1-水泵等）
 * @param state: 状态（RELAY_ON 或 RELAY_OFF）
 * @return: 0 成功，-1 失败
 */
int relay_set_state(uint8_t relay_id, relay_state_t state);

/**
 * 获取继电器当前状态
 * @param relay_id: 继电器编号
 * @return: 当前状态 (RELAY_ON 或 RELAY_OFF)
 */
relay_state_t relay_get_state(uint8_t relay_id);

/**
 * 打开排风扇
 * @return: 0 成功，-1 失败
 */
int relay_fan_on();

/**
 * 关闭排风扇
 * @return: 0 成功，-1 失败
 */
int relay_fan_off();

#endif // RELAY_CONTROL_H
