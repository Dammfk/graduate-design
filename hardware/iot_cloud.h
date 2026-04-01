/*
 * iot_cloud.h
 * NB-IoT 和云平台通信模块
 */

#ifndef IOT_CLOUD_H
#define IOT_CLOUD_H

#include "sensor_driver.h"

/* ===== NB-IoT 模块相关 ===== */

typedef enum {
    IOT_CONNECTED,
    IOT_CONNECTING,
    IOT_DISCONNECTED,
    IOT_ERROR
} iot_status_t;

typedef struct {
    const char *cloud_host;
    uint16_t cloud_port;
    const char *device_id;
    const char *device_key;
} iot_config_t;

/* ===== 函数声明 ===== */

/**
 * 初始化 NB-IoT 模块
 * @param config: 配置参数
 * @return: 0 成功，-1 失败
 */
int iot_init(const iot_config_t *config);

/**
 * 连接到 IoT 云平台
 * @return: 0 成功，-1 失败
 */
int iot_connect();

/**
 * 断开 IoT 连接
 */
void iot_disconnect();

/**
 * 获取 IoT 连接状态
 * @return: iot_status_t 当前状态
 */
iot_status_t iot_get_status();

/**
 * 发送遥测数据到云平台
 * @param reading: 传感器数据
 * @return: 0 成功，-1 失败
 */
int iot_send_telemetry(const sensor_reading_t *reading);

/**
 * 接收来自云平台的命令
 * @param buffer: 接收缓冲区
 * @param len: 缓冲区大小
 * @return: 实际接收的字节数，0 表示无数据，-1 表示错误
 */
int iot_recv_command(uint8_t *buffer, uint32_t len);

/**
 * 向云平台发送心跳（keepalive）
 * @return: 0 成功，-1 失败
 */
int iot_send_heartbeat();

#endif // IOT_CLOUD_H
