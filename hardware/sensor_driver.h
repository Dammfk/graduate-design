/*
 * sensor_driver.h
 * BearPi 传感器驱动程序
 * 包含 I2C、ADC 和传感器初始化
 */

#ifndef SENSOR_DRIVER_H
#define SENSOR_DRIVER_H

#include <stdint.h>

/* ===== 传感器类型定义 ===== */
typedef struct {
    float temperature;   // 温度（℃）
    float humidity;      // 湿度（%）
} dht_data_t;

typedef struct {
    float co2_ppm;       // CO2浓度（ppm）
    float ammonia_ppm;   // 氨气浓度（ppm）
} gas_sensor_data_t;

typedef struct {
    dht_data_t dht;
    gas_sensor_data_t gas;
    uint32_t timestamp;
} sensor_reading_t;

/* ===== 函数声明 ===== */

/**
 * 初始化 I2C 接口
 * @param i2c_id: I2C 端口号
 * @param freq: 时钟频率
 * @return: 0 成功，-1 失败
 */
int sensor_i2c_init(uint8_t i2c_id, uint32_t freq);

/**
 * 初始化 ADC 接口
 * @param adc_id: ADC 端口号
 * @param channel: ADC 通道
 * @return: 0 成功，-1 失败
 */
int sensor_adc_init(uint8_t adc_id, uint8_t channel);

/**
 * 读取 DHT11/DHT22 温湿度传感器
 * @param i2c_id: I2C 端口号
 * @param data: 保存读取结果的结构体指针
 * @return: 0 成功，-1 失败
 */
int read_dht_sensor(uint8_t i2c_id, dht_data_t *data);

/**
 * 通过 ADC 读取 CO2 传感器
 * @param adc_id: ADC 端口号
 * @param channel: ADC 通道
 * @return: CO2浓度（ppm），-1 表示失败
 */
float read_co2_adc(uint8_t adc_id, uint8_t channel);

/**
 * 通过 ADC 读取氨气传感器
 * @param adc_id: ADC 端口号
 * @param channel: ADC 通道
 * @return: 氨气浓度（ppm），-1 表示失败
 */
float read_ammonia_adc(uint8_t adc_id, uint8_t channel);

/**
 * 读取所有传感器数据
 * @param reading: 保存读取结果的结构体指针
 * @return: 0 成功，-1 失败
 */
int read_all_sensors(sensor_reading_t *reading);

#endif // SENSOR_DRIVER_H
