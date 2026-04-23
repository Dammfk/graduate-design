# 快速启动与联调说明

更新时间：2026-04-20

## 当前状态

当前项目不是最终完成版，而是联调完善版。

已经稳定可用的是：

- STM32 温湿度采集
- OLED 本地显示
- STM32 telemetry 上报
- Python 桥接脚本读取串口
- FastAPI 接收并保存 telemetry
- 前端显示数据

仍需继续完善的是：

- 前端人工控制板子动作稳定性
- 继电器真实状态上报
- CO2、氨气真实传感器接入
- 自动规则业务化
- 数据库迁移和正式部署流程

---

## 一键启动

推荐在 VS Code 中运行：

```text
Tasks: Run Task -> app: dev
```

该任务会启动：

- 后端：`http://127.0.0.1:8000`
- 前端：通常是 `http://127.0.0.1:5173`
- 桥接脚本：默认连接 `COM5`

---

## 手动启动

### 1. 启动后端

```powershell
cd "E:\fastapi\graduate design\backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

检查：

```text
http://127.0.0.1:8000/health
```

### 2. 启动前端

```powershell
cd "E:\fastapi\graduate design\frontend"
npm run dev
```

### 3. 启动桥接脚本

```powershell
cd "E:\fastapi\graduate design\tools"
python serial_bridge.py --port COM5 --baudrate 115200 --base-url http://127.0.0.1:8000 --device-id DEVICE_001
```

---

## 验证 telemetry 上报

看到以下日志说明上报链路正常：

```text
[Bridge] 串口已打开: COM5 @ 115200
[串口接收] {"device_id":"DEVICE_001","temperature":28.4,"humidity":54.9,"co2_concentration":null,"ammonia_concentration":null}
[HTTP 上报] telemetry 已上传: DEVICE_001
```

前端页面应能看到温度和湿度变化。

---

## 验证人工控制

当前人工控制是重点待完善项。

理想日志：

```text
[串口发送] {"command_id":38,"target":"fan","command":"ON"}
[串口接收] {"device_id":"DEVICE_001","type":"ack","command_id":38,"status":"ok"}
[Bridge] 命令回执已更新: command_id=38, status=success
```

如果只有 `[串口发送]`，但没有 ACK，说明：

- 前端和后端命令已经生成
- 桥接脚本已经尝试下发
- 问题大概率在 PC 到 STM32 的下行串口链路

---

## 常见问题

### 找不到 COM5

处理方式：

- 打开 Windows 设备管理器
- 查看 `端口 (COM 和 LPT)`
- 把任务或命令里的 `COM5` 改成实际串口号

### COM5 被占用

处理方式：

- 关闭串口助手
- 停掉旧的 `serial_bridge.py`
- 停掉占用串口的调试工具
- 拔插 USB 串口后重试

### 后端 Redis 报错

当前 Redis 是可选缓存。  
如果看到 Redis 连接失败，但后端仍正常启动，可以先忽略。

### 前端有数据但控制不动板子

这是当前已知未完善问题。  
优先检查 `COM5 -> STM32` 下行是否稳定，必要时使用外接 USB-TTL 模块。

---

## 下一步

1. 先确认 telemetry 持续稳定上报。
2. 再验证人工控制命令能否稳定收到 ACK。
3. 给 STM32 telemetry 增加继电器真实状态。
4. 梳理风机、水帘、补光灯和继电器的业务映射。
5. 完善毕业设计演示流程。

