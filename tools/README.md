# 工具目录说明

这个目录用于放置“软硬件连通辅助程序”。

当前工具：

- `serial_bridge.py`
  负责从 STM32 串口读取一行一条的 JSON 数据，转发给 FastAPI，并定时轮询后端待执行命令，再写回串口给设备。

## 使用方式

先安装依赖：

```bash
cd tools
pip install -r requirements.txt
```

启动桥接程序：

```bash
python serial_bridge.py --port COM5 --baudrate 115200 --base-url http://127.0.0.1:8000 --device-id DEVICE_001
```

## 常用参数

- `--port`
  串口号，例如 `COM5`
- `--baudrate`
  串口波特率，默认 `115200`
- `--base-url`
  FastAPI 地址，默认 `http://127.0.0.1:8000`
- `--poll-interval`
  轮询后端命令的时间间隔，默认 `2.0`
- `--read-timeout`
  串口读取超时，默认 `0.2`
- `--device-id`
  手动指定需要轮询命令的设备 ID，可重复传入多个

## 当前协议

STM32 上报遥测：

```json
{"device_id":"DEVICE_001","temperature":24.8,"humidity":61.3,"co2_concentration":null,"ammonia_concentration":null}
```

后端下发命令给 STM32：

```json
{"command_id":12,"target":"relay1","command":"ON"}
```

STM32 回 ACK：

```json
{"device_id":"DEVICE_001","type":"ack","command_id":12,"status":"ok"}
```

## 当前联调重点

当前已经确认：

- `COM5` 能收到 `BOOT_OK`
- `COM5` 能收到 telemetry JSON
- 桥接脚本能把 telemetry 转发到 FastAPI

接下来要继续确认：

- 后端下发的命令是否都能被 STM32 正确执行
- STM32 是否能把 ACK 正确回写给后端

## 目录边界

这个目录只放桥接和辅助脚本：

- 设备业务逻辑放在 `hardware/demo`
- 平台业务逻辑放在 `backend`
- 页面展示逻辑放在 `frontend`
