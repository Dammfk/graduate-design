# 软硬件联调指南

更新时间：2026-04-20

## 1. 当前联调目标

本指南描述当前项目真实可用的软硬件联调方式。  
当前最稳定的链路是 telemetry 上报：

```text
STM32 -> USART1 -> COM5 -> serial_bridge.py -> FastAPI -> frontend
```

控制下发链路已经具备代码基础，但仍需继续验证硬件下行串口稳定性：

```text
frontend -> FastAPI -> serial_bridge.py -> COM5 -> STM32
```

---

## 2. 启动前检查

### 硬件

- STM32 已烧录当前 `hardware/demo` 固件
- 板子上电正常
- OLED 能显示温湿度
- Windows 设备管理器能看到串口，例如 `COM5`

### 软件

- Python 依赖已安装
- 前端依赖已安装
- 后端可启动
- `tools/serial_bridge.py` 可运行

---

## 3. 推荐启动方式

在 VS Code 中运行：

```text
Tasks: Run Task -> app: dev
```

该任务会启动：

- `backend: dev`
- `frontend: dev`
- `bridge: dev`

---

## 4. 手动启动方式

### 后端

```powershell
cd "E:\fastapi\graduate design\backend"
python -m uvicorn main:app --host 127.0.0.1 --port 8000
```

验证：

```text
http://127.0.0.1:8000/health
```

### 前端

```powershell
cd "E:\fastapi\graduate design\frontend"
npm run dev
```

默认访问：

```text
http://127.0.0.1:5173
```

### 桥接

```powershell
cd "E:\fastapi\graduate design\tools"
python serial_bridge.py --port COM5 --baudrate 115200 --base-url http://127.0.0.1:8000 --device-id DEVICE_001
```

---

## 5. telemetry 验证

桥接脚本出现以下日志，说明上报链路正常：

```text
[Bridge] 串口已打开: COM5 @ 115200
[串口接收] {"device_id":"DEVICE_001","temperature":28.4,"humidity":54.9,"co2_concentration":null,"ammonia_concentration":null}
[HTTP 上报] telemetry 已上传: DEVICE_001
```

如果没有 `[串口接收]`：

- 检查串口号是否变化
- 检查板子是否正在运行最新固件
- 检查是否有串口助手或其他进程占用串口
- 检查是否仍使用 `COM5`

---

## 6. 控制下发验证

前端手动点击风机或水帘按钮后，理想日志应包含：

```text
[串口发送] {"command_id":38,"target":"fan","command":"ON"}
[串口接收] {"device_id":"DEVICE_001","type":"ack","command_id":38,"status":"ok"}
[Bridge] 命令回执已更新: command_id=38, status=success
```

如果只有 `[串口发送]`，没有 ACK：

- 说明后端和桥接已经下发命令
- 问题大概率在 `COM5 -> STM32` 下行串口
- 需要继续查板载串口路由，或改用外接 USB-TTL 模块验证

---

## 7. 当前协议

### STM32 上报 telemetry

```json
{"device_id":"DEVICE_001","temperature":28.4,"humidity":54.9,"co2_concentration":null,"ammonia_concentration":null}
```

### 后端下发命令

```json
{"command_id":38,"target":"fan","command":"ON"}
```

注意：桥接脚本下发给 STM32 的 JSON 必须是紧凑格式，不要带多余空格。

### STM32 回 ACK

```json
{"device_id":"DEVICE_001","type":"ack","command_id":38,"status":"ok"}
```

---

## 8. 已知限制

- 当前只上报温湿度，CO2 和氨气为 `null`
- 当前未上报继电器真实状态
- 人工控制板子动作不稳定，需要优先解决下行串口链路
- 自动规则仍为演示规则，需要结合实际养殖场景重新整理
- SQLite 适合当前开发联调，正式部署前应考虑迁移方案

---

## 9. 下一步联调建议

1. 先保证 telemetry 持续稳定上报。
2. 单独验证 `COM5 -> STM32` 是否能稳定收命令。
3. 给 STM32 收到命令后增加 OLED 临时提示，方便肉眼判断。
4. 若仍无 ACK，使用外接 USB-TTL 模块接 MCU 的 TX/RX/GND。
5. 等人工控制稳定后，再整理规则、状态上报和前端展示。

