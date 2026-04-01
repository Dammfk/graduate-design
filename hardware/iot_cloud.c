/*
 * iot_cloud.c
 * NB-IoT 和云平台通信实现
 */

#include "iot_cloud.h"
#include <stdio.h>
#include <string.h>
#include <unistd.h>
#include <json.h>  // 需要 JSON 库支持

static iot_config_t g_iot_config = {0};
static iot_status_t g_iot_status = IOT_DISCONNECTED;

/* ===== AT 指令操作 ===== */

/**
 * 发送 AT 指令到 NB-IoT 模块
 * @param cmd: 指令字符串
 * @param response: 响应缓冲区
 * @param resp_len: 响应缓冲区大小
 * @return: 0 成功，-1 失败
 */
static int send_at_command(const char *cmd, char *response, uint32_t resp_len)
{
    printf("[AT CMD] > %s\n", cmd);
    
    // 实际实现：
    // 1. 打开 UART 串口
    // 2. 发送命令
    // 3. 读取响应
    // 4. 检查响应状态
    
    // 模拟响应
    if (strstr(cmd, "AT+CSCON?") != NULL) {
        snprintf(response, resp_len, "+CSCON: 1\r\nOK");
    } else if (strstr(cmd, "AT+NCONFIG?") != NULL) {
        snprintf(response, resp_len, "+NCONFIG: AUTOCONNECT,TRUE\r\nOK");
    } else {
        snprintf(response, resp_len, "OK");
    }
    
    printf("[AT RSP] < %s\n", response);
    return 0;
}

/* ===== NB-IoT 初始化 ===== */

int iot_init(const iot_config_t *config)
{
    if (config == NULL) {
        printf("[ERROR] Invalid config\n");
        return -1;
    }
    
    memcpy(&g_iot_config, config, sizeof(iot_config_t));
    g_iot_status = IOT_DISCONNECTED;
    
    printf("[IOT] Initializing NB-IoT module...\n");
    printf("[IOT] Cloud Host: %s:%u\n", config->cloud_host, config->cloud_port);
    printf("[IOT] Device ID: %s\n", config->device_id);
    
    // 初始化 UART 串口通信
    // uart_init(UART_NB_IOT_ID, 9600);
    
    char response[256];
    
    // 发送初始化指令序列
    send_at_command("AT", response, sizeof(response));
    usleep(100000);
    
    send_at_command("AT+NRB", response, sizeof(response));  // 重启模块
    usleep(500000);
    
    send_at_command("AT+CFUN=1", response, sizeof(response));  // 启用全功能
    usleep(200000);
    
    send_at_command("AT+NCONFIG=AUTOCONNECT,TRUE", response, sizeof(response));  // 自动连接
    
    printf("[IOT] NB-IoT module initialized\n");
    return 0;
}

/* ===== 连接管理 ===== */

int iot_connect()
{
    if (g_iot_status != IOT_DISCONNECTED) {
        printf("[INFO] Already connected or connecting\n");
        return 0;
    }
    
    printf("[IOT] Connecting to cloud platform...\n");
    g_iot_status = IOT_CONNECTING;
    
    char response[256];
    
    // 检查网络连接
    send_at_command("AT+CEREG?", response, sizeof(response));
    usleep(100000);
    
    // 建立 TCP 连接
    char cmd[128];
    snprintf(cmd, sizeof(cmd), "AT+NSOCR=STREAM,6,%u,1\r\n", g_iot_config.cloud_port);
    send_at_command(cmd, response, sizeof(response));
    
    // 模拟连接成功
    g_iot_status = IOT_CONNECTED;
    printf("[IOT] Connected successfully\n");
    
    return 0;
}

void iot_disconnect()
{
    printf("[IOT] Disconnecting...\n");
    
    char response[256];
    send_at_command("AT+NSOCL=0", response, sizeof(response));  // 关闭 socket
    
    g_iot_status = IOT_DISCONNECTED;
    printf("[IOT] Disconnected\n");
}

iot_status_t iot_get_status()
{
    return g_iot_status;
}

/* ===== 数据传输 ===== */

int iot_send_telemetry(const sensor_reading_t *reading)
{
    if (reading == NULL) {
        return -1;
    }
    
    if (g_iot_status != IOT_CONNECTED) {
        printf("[ERROR] Not connected to IoT platform\n");
        return -1;
    }
    
    // 构建 JSON 数据包
    char json_data[256];
    snprintf(json_data, sizeof(json_data),
        "{"
            "\"device_id\":\"%s\","
            "\"temperature\":%.1f,"
            "\"humidity\":%.1f,"
            "\"co2_concentration\":%.0f,"
            "\"ammonia_concentration\":%.1f,"
            "\"timestamp\":%u"
        "}",
        g_iot_config.device_id,
        reading->dht.temperature,
        reading->dht.humidity,
        reading->gas.co2_ppm,
        reading->gas.ammonia_ppm,
        reading->timestamp
    );
    
    printf("[IOT] Sending telemetry data:\n");
    printf("%s\n", json_data);
    
    // 通过 NB-IoT 发送数据
    char cmd[512];
    snprintf(cmd, sizeof(cmd), "AT+NSOST=0,%s,%u,%u,%s\r\n",
        g_iot_config.cloud_host, g_iot_config.cloud_port, 
        strlen(json_data), json_data);
    
    char response[256];
    send_at_command(cmd, response, sizeof(response));
    
    printf("[IOT] Telemetry sent successfully\n");
    return 0;
}

int iot_recv_command(uint8_t *buffer, uint32_t len)
{
    if (buffer == NULL || len == 0) {
        return -1;
    }
    
    if (g_iot_status != IOT_CONNECTED) {
        return 0;  // 无数据
    }
    
    // 从 NB-IoT 模块接收数据
    char response[256];
    send_at_command("AT+NSORF=0,256\r\n", response, sizeof(response));
    
    // 模拟接收命令（FAN_ON）
    snprintf((char *)buffer, len, "{\"command\":\"FAN_ON\",\"priority\":\"high\"}");
    
    printf("[IOT] Received command from cloud: %s\n", buffer);
    return strlen((const char *)buffer);
}

int iot_send_heartbeat()
{
    if (g_iot_status != IOT_CONNECTED) {
        return -1;
    }
    
    printf("[IOT] Sending heartbeat...\n");
    
    char response[256];
    send_at_command("AT+NPING=1.1.1.1\r\n", response, sizeof(response));
    
    return 0;
}
