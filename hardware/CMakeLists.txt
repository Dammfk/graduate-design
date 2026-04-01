/*
 * CMakeLists.txt
 * BearPi 固件编译配置
 */

cmake_minimum_required(VERSION 3.10)
project(greenhouse_monitor_firmware C)

# 设置 C 标准
set(CMAKE_C_STANDARD 99)
set(CMAKE_C_STANDARD_REQUIRED ON)

# 添加源文件
set(SOURCES
    main.c
    sensor_driver.c
    iot_cloud.c
    relay_control.c
)

# 添加头文件目录
include_directories(${CMAKE_CURRENT_SOURCE_DIR})

# 创建可执行文件
add_executable(greenhouse_firmware ${SOURCES})

# 编译选项
target_compile_options(greenhouse_firmware PRIVATE
    -Wall
    -Wextra
    -O2
)

# 链接选项
target_link_options(greenhouse_firmware PRIVATE
    -lm
)

# 模拟编译（如果需要真实的 LiteOS 构建，需要替换为实际的 LiteOS 工具链）
# set(CMAKE_C_COMPILER arm-none-eabi-gcc)
# add_compile_definitions(LITEOS)
