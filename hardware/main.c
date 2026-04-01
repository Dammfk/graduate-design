/*
 * main.c
 * BearPi 主程序
 * 物联网养殖大棚监控系统硬件端
 */

#include <stdio.h>
#include <unistd.h>
#include <time.h>
#include "sensor_driver.h"
#include "iot_cloud.h"
#include "relay_control.h"

/* ===== 配置常量 ===== */
#define SENSOR_READ_INTERVAL    10      // 10 秒读取一次传感器
#define IOT_SEND_INTERVAL       30      // 30 秒发送一次数据
#define HEARTBEAT_INTERVAL      60      // 60 秒发送一次心跳

/* ===== 全局变量 ===== */
static uint32_t g_sensor_counter = 0;
static uint32_t g_send_counter = 0;
static uint32_t g_heartbeat_counter = 0;

int main(void)
{
    printf("=====================================\n");
    printf("IoT Greenhouse Monitoring System\n");
    printf("BearPi Hardware Firmware v1.0\n");
    printf("=====================================\n\n");
    
    // 初始化硬件
    printf("[INIT] Initializing hardware...\n");
    
    if (sensor_i2c_init(0, 400000) != 0) {
        printf("[ERROR] Failed to initialize I2C\n");
        return -1;
    }
    
    if (sensor_adc_init(1, 0) != 0 || sensor_adc_init(1, 1) != 0) {
        printf("[ERROR] Failed to initialize ADC\n");
        return -1;
    }
    
    if (relay_init() != 0) {
        printf("[ERROR] Failed to initialize relay\n");
        return -1;
    }
    
    printf("[INIT] Hardware initialization completed\n\n");
    
    // 初始化 IoT 连接
    printf("[INIT] Initializing IoT connection...\n");
    
    iot_config_t iot_config = {
        .cloud_host = "iot.example.com",
        .cloud_port = 5684,
        .device_id = "DEVICE_001",
        .device_key = "your_device_key_here"
    };
    
    if (iot_init(&iot_config) != 0) {
        printf("[ERROR] Failed to initialize IoT\n");
        return -1;
    }
    
    if (iot_connect() != 0) {
        printf("[ERROR] Failed to connect to IoT\n");
        return -1;
    }
    
    printf("[INIT] IoT connection completed\n\n");
    printf("[SYSTEM] Starting main loop...\n");
    printf("=====================================\n\n");
    
    // 主循环
    while (1) {
        // 读取传感器数据
        if (g_sensor_counter >= SENSOR_READ_INTERVAL) {
            sensor_reading_t reading = {0};
            
            if (read_all_sensors(&reading) == 0) {
                // 应用智能控制逻辑
                if (process_control_logic(&reading) != 0) {
                    printf("[WARN] Error processing control logic\n");
                }
            }
            
            g_sensor_counter = 0;
        }
        
        // 发送数据到云平台
        if (g_send_counter >= IOT_SEND_INTERVAL) {
            sensor_reading_t reading = {0};
            
            if (read_all_sensors(&reading) == 0) {
                if (iot_send_telemetry(&reading) != 0) {
                    printf("[WARN] Failed to send telemetry\n");
                }
            }
            
            g_send_counter = 0;
        }
        
        // 发送心跳
        if (g_heartbeat_counter >= HEARTBEAT_INTERVAL) {
            if (iot_send_heartbeat() != 0) {
                printf("[WARN] Failed to send heartbeat\n");
            }
            g_heartbeat_counter = 0;
        }
        
        // 接收云平台命令
        uint8_t cmd_buffer[256];
        int cmd_len = iot_recv_command(cmd_buffer, sizeof(cmd_buffer));
        if (cmd_len > 0) {
            process_cloud_command(cmd_buffer, cmd_len);
        }
        
        // 睡眠 1 秒
        sleep(1);
        g_sensor_counter++;
        g_send_counter++;
        g_heartbeat_counter++;
    }
    
    iot_disconnect();
    return 0;
}

/**
 * 处理控制逻辑
 * 根据环境数据自动控制硬件
 */
static int process_control_logic(const sensor_reading_t *reading)
{
    if (reading == NULL) {
        return -1;
    }
    
    // 控制阈值
    const float TEMP_ON = 30.0f;      // 温度 > 30°C 时打开排风扇
    const float AMMONIA_ON = 25.0f;   // 氨气 > 25ppm 时打开排风扇
    const float TEMP_OFF = 25.0f;     // 温度 <= 25°C 时关闭排风扇
    
    printf("[CONTROL] Processing control logic...\n");
    printf("  Temperature: %.1f°C\n", reading->dht.temperature);
    printf("  Ammonia: %.1f ppm\n", reading->gas.ammonia_ppm);
    
    // 温度控制逻辑
    if (reading->dht.temperature > TEMP_ON ||
        reading->gas.ammonia_ppm > AMMONIA_ON) {
        
        if (relay_get_state(0) != RELAY_ON) {
            printf("[CONTROL] Turning on FAN (温度或氨气过高)\n");
            relay_fan_on();
        }
    } else if (reading->dht.temperature <= TEMP_OFF) {
        
        if (relay_get_state(0) != RELAY_OFF) {
            printf("[CONTROL] Turning off FAN (温度降低)\n");
            relay_fan_off();
        }
    }
    
    // 节能计算
    static int fan_on_time = 0;
    if (relay_get_state(0) == RELAY_ON) {
        fan_on_time++;
    }
    
    if (fan_on_time % 60 == 0) {
        float energy_consumption = (fan_on_time / 3600.0f) * 100;  // 假设排风扇功率 100W
        printf("[ENERGY] Total FAN runtime: %d seconds, Energy: %.2f Wh\n", 
               fan_on_time, energy_consumption / 1000);
    }
    
    printf("[CONTROL] Control logic processed\n\n");
    return 0;
}

/**
 * 处理来自云平台的命令
 */
static int process_cloud_command(const uint8_t *cmd_data, uint32_t len)
{
    if (cmd_data == NULL || len == 0) {
        return -1;
    }
    
    printf("[CLOUD CMD] Processing command from cloud...\n");
    printf("  Data: %s\n", cmd_data);
    
    // 解析命令（简化的字符串匹配）
    if (strstr((const char *)cmd_data, "FAN_ON") != NULL) {
        printf("[CLOUD CMD] Turn FAN ON\n");
        relay_fan_on();
    } else if (strstr((const char *)cmd_data, "FAN_OFF") != NULL) {
        printf("[CLOUD CMD] Turn FAN OFF\n");
        relay_fan_off();
    }
    
    printf("[CLOUD CMD] Command processed\n\n");
    return 0;
}
