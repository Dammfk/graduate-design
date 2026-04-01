/*
 * relay_control.c
 * 继电器控制实现
 */

#include "relay_control.h"
#include <stdio.h>

static relay_state_t g_relay_states[2] = { RELAY_OFF, RELAY_OFF };

int relay_init()
{
    printf("[RELAY] Initializing relay control...\n");
    
    // 初始化 GPIO 引脚
    // gpio_init(RELAY_FAN_PIN, GPIO_OUT);
    // gpio_init(RELAY_PUMP_PIN, GPIO_OUT);
    
    // 初始设置所有继电器为关闭状态
    g_relay_states[0] = RELAY_OFF;
    g_relay_states[1] = RELAY_OFF;
    
    printf("[RELAY] Relay control initialized\n");
    return 0;
}

int relay_set_state(uint8_t relay_id, relay_state_t state)
{
    if (relay_id >= 2) {
        printf("[ERROR] Invalid relay ID: %u\n", relay_id);
        return -1;
    }
    
    const char *relay_name[] = { "FAN", "PUMP" };
    const uint8_t relay_pins[] = { RELAY_FAN_PIN, RELAY_PUMP_PIN };
    
    printf("[RELAY] Setting %s relay to %s\n", 
           relay_name[relay_id], 
           state == RELAY_ON ? "ON" : "OFF");
    
    // 实际 GPIO 操作：
    // gpio_write(relay_pins[relay_id], state);
    
    g_relay_states[relay_id] = state;
    
    // 可选：记录日志
    printf("[RELAY] %s relay is now %s\n", 
           relay_name[relay_id],
           state == RELAY_ON ? "ON" : "OFF");
    
    return 0;
}

relay_state_t relay_get_state(uint8_t relay_id)
{
    if (relay_id >= 2) {
        return RELAY_OFF;
    }
    return g_relay_states[relay_id];
}

int relay_fan_on()
{
    return relay_set_state(0, RELAY_ON);
}

int relay_fan_off()
{
    return relay_set_state(0, RELAY_OFF);
}
