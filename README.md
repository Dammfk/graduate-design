# 物联网养殖大棚监控系统 - 完整解决方案

## 📋 项目概述

这是一个基于物联网的数字化养殖大棚监控系统，包含以下四个核心模块：

1. **后端模型与 API** (FastAPI + SQLAlchemy + Redis)
2. **前端监控大屏** (Vue 3 + ECharts)
3. **硬件传感器采集** (C 语言 + LiteOS)
4. **自动化控制逻辑** (Python)

---

## 🏗️ 项目结构

```
graduate design/
├── backend/                          # 后端项目
│   ├── main.py                      # 应用入口
│   ├── requirements.txt             # 项目依赖
│   ├── .env                         # 环境配置
│   └── app/
│       ├── __init__.py
│       ├── core/                    # 核心配置
│       │   ├── config.py           # 配置管理
│       │   └── database.py         # 数据库和 Redis 连接
│       ├── models/                  # SQLAlchemy 数据库模型
│       │   └── __init__.py         # User, Device, EnvironmentData 等
│       ├── schemas/                 # Pydantic 数据验证模型
│       │   └── __init__.py
│       ├── api/                     # API 路由
│       │   ├── __init__.py
│       │   ├── telemetry.py        # 遥测数据接口
│       │   ├── devices.py          # 设备管理接口
│       │   └── alarms.py           # 告警管理接口
│       └── services/                # 业务逻辑服务
│           ├── telemetry_service.py    # 遥测数据处理
│           ├── alarm_service.py        # 告警处理
│           ├── control_service.py      # 设备控制
│           └── automation_service.py   # 智能控制逻辑
│
├── frontend/                         # 前端项目
│   ├── package.json
│   ├── vite.config.js
│   ├── index.html
│   └── src/
│       ├── App.vue                 # 主应用
│       ├── main.js                # 应用入口
│       ├── api/
│       │   └── client.js          # API 客户端
│       ├── stores/
│       │   └── monitoring.js      # Pinia 状态管理
│       └── components/
│           ├── MonitoringDashboard.vue      # 主监控大屏
│           ├── EnvironmentDashboard.vue     # 实时仪表盘
│           ├── TrendChart.vue               # 趋势图表
│           └── AlarmList.vue                # 告警列表
│
├── hardware/                         # 硬件端代码
│   ├── main.c                      # 主程序
│   ├── sensor_driver.h/c           # 传感器驱动
│   ├── iot_cloud.h/c              # NB-IoT 通信
│   ├── relay_control.h/c          # 继电器控制
│   └── CMakeLists.txt
│
└── docs/                            # 项目文档
    ├── API_DOCUMENTATION.md        # API 文档
    └── DEPLOYMENT.md              # 部署指南
```

---

## 🔧 后端快速开始

### 环境要求

- Python 3.8+
- MySQL 5.7+
- Redis 6.0+

### 安装依赖

```bash
cd backend
pip install -r requirements.txt
```

### 配置环境变量

编辑 `.env` 文件，配置数据库和 Redis：

```env
MYSQL_HOST=127.0.0.1
MYSQL_PORT=3306
MYSQL_USER=root
MYSQL_PASSWORD=your_password
MYSQL_DB=greenhouse_db

REDIS_HOST=127.0.0.1
REDIS_PORT=6379
REDIS_PASSWORD=
REDIS_DB=0

DEBUG=True
```

### 运行服务

```bash
# 方法1：直接运行
python main.py

# 方法2：使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

应用将在 `http://localhost:8000` 启动

---

## 📡 后端 API 端点

### 遥测数据接口

#### 接收 IoT 数据
```
POST /api/v1/telemetry/
Content-Type: application/json

{
  "device_id": "DEVICE_001",
  "temperature": 28.5,
  "humidity": 65.0,
  "co2_concentration": 1200.0,
  "ammonia_concentration": 15.5,
  "timestamp": "2024-03-18T10:30:00Z"
}

响应 (200):
{
  "status": "success",
  "data": {
    "data_id": 1234,
    "device_id": "DEVICE_001",
    "alarms_created": 0,
    "commands_generated": 1,
    "timestamp": "2024-03-18T10:30:00Z"
  }
}
```

#### 获取最新数据
```
GET /api/v1/telemetry/latest/DEVICE_001

响应 (200):
{
  "status": "success",
  "source": "cache",
  "data": {
    "id": 1234,
    "temperature": 28.5,
    "humidity": 65.0,
    "co2_concentration": 1200.0,
    "ammonia_concentration": 15.5,
    "recorded_at": "2024-03-18T10:30:00Z"
  }
}
```

#### 获取历史数据（24小时）
```
GET /api/v1/telemetry/history/DEVICE_001?hours=24

响应 (200):
{
  "status": "success",
  "device_id": "DEVICE_001",
  "hours": 24,
  "count": 288,
  "data": [
    {
      "timestamp": "2024-03-17T10:00:00Z",
      "temperature": 25.0,
      "humidity": 60.0,
      ...
    },
    ...
  ]
}
```

### 告警管理接口

#### 获取待处理告警
```
GET /api/v1/alarms/pending

响应 (200):
{
  "status": "success",
  "count": 3,
  "data": [
    {
      "id": 1,
      "device_id": 1,
      "alarm_type": "ammonia_high",
      "alarm_level": "critical",
      "threshold_value": 20.0,
      "actual_value": 25.5,
      "description": "氨气浓度过高",
      "alarm_time": "2024-03-18T10:25:00Z",
      "status": "pending"
    },
    ...
  ]
}
```

#### 确认告警
```
PUT /api/v1/alarms/1/acknowledge
Content-Type: application/json

{
  "user_id": 1
}
```

#### 解决告警
```
PUT /api/v1/alarms/1/resolve

响应 (200):
{
  "status": "success",
  "data": {
    "id": 1,
    "status": "resolved",
    "resolved_time": "2024-03-18T10:30:00Z"
  }
}
```

### 设备管理接口

#### 列出设备
```
GET /api/v1/devices/?owner_id=1

响应 (200):
{
  "status": "success",
  "count": 3,
  "data": [
    {
      "id": 1,
      "device_id": "DEVICE_001",
      "device_name": "大棚01 温度传感器",
      "device_type": "DHT22",
      "location": "棚1号",
      "owner_id": 1,
      "is_active": true,
      "latest_data_timestamp": "2024-03-18T10:30:00Z",
      "created_at": "2024-01-01T00:00:00Z"
    },
    ...
  ]
}
```

#### 创建设备
```
POST /api/v1/devices/?owner_id=1
Content-Type: application/json

{
  "device_id": "DEVICE_004",
  "device_name": "大棚04 气体传感器",
  "device_type": "CO2/NH3",
  "location": "棚4号"
}

响应 (201):
{
  "id": 4,
  "device_id": "DEVICE_004",
  "device_name": "大棚04 气体传感器",
  ...
}
```

---

## 🎨 前端快速开始

### 环境要求

- Node.js 16+
- npm 或 yarn

### 安装依赖

```bash
cd frontend
npm install
```

### 开发模式

```bash
npm run dev
```

访问 `http://localhost:5173` 查看应用

### 生产构建

```bash
npm run build
```

构建输出位于 `dist/` 目录

---

## 🎯 前端特性

### 监控大屏布局

**三分屏设计：**

1. **左屏 - 实时仪表盘**
   - 四个实时仪表（温度、湿度、CO2、NH3）
   - ECharts gauge 可视化
   - 实时数据展示
   - 氨气告警指示（当 > 20ppm 时红色闪烁）

2. **中屏 - 趋势图表**
   - 24小时数据趋势折线图
   - Tab 切换不同数据类型
   - 平滑曲线显示
   - 渐变填充背景

3. **右屏 - 告警列表**
   - 实时告警信息展示
   - 告警分级显示（严重、警告、信息）
   - 确认、解决操作按钮
   - 告警状态跟踪

### 关键交互

- **氨气告警效果**：当 NH3 > 20ppm 时，整个页面出现红色闪烁效果
- **自动刷新**：每 10 秒自动刷新数据
- **设备切换**：支持多个设备的切换和监控

---

## 🔌 硬件端指南

### BearPi 开发板集成

#### 传感器接线

| 传感器 | 接口 | 引脚 | 说明 |
|--------|------|------|------|
| DHT22 | I2C | 0 | 温湿度传感器 @0x40 |
| CO2 | ADC | 1-0 | 模拟 CO2 传感器 |
| NH3 | ADC | 1-1 | 模拟氨气传感器 |
| 排风扇继电器 | GPIO | 17 | 排风扇控制 |
| 水泵继电器 | GPIO | 27 | 水泵控制 |
| NB-IoT 模块 | UART | - | 物联网通信 |

#### 编译和烧录

```bash
cd hardware
mkdir build
cd build
cmake ..
make

# 烧录固件
# 使用 LiteOS 的烧录工具将生成的固件烧录到 BearPi 开发板
```

#### 主程序功能

- **传感器采集**：每 10 秒读取一次传感器数据
- **云端通信**：每 30 秒上传一次数据到 IoT 平台
- **心跳维持**：每 60 秒发送一次心跳包
- **命令执行**：实时接收并执行云端下发的控制命令

---

## 🤖 自动化控制逻辑

### 智能控制规则

系统内置5条智能控制规则（可自定义）：

| 规则 | 条件 | 动作 | 优先级 |
|------|------|------|--------|
| 高温控制 | 温度 > 30°C | 打开排风扇 | 8 |
| 氨气告警 | 氨气 > 25ppm | 打开排风扇 + 告警 | **10** |
| 温度正常 | 温度 <= 25°C AND 氨气 <= 20ppm | 关闭排风扇 | 5 |
| CO2控制 | CO2 > 2000ppm | 打开排风扇 | 7 |
| 湿度控制 | 湿度 > 90% | 打开排风扇 | 6 |

### 节能优化

- **温度优化**：当温度在目标范围内（25-29°C）时，预计节能 15%
- **时间段优化**：夜间（23点-次日6点）温度较低时，预计节能 20%
- **能耗跟踪**：记录排风扇运行时间，计算总能耗和 CO2 排放当量

### 示例：自定义规则

```python
from app.services.automation_service import smart_controller, ControlRule, ControlAction

# 创建新规则：湿度过低时打开加湿设备
rule = ControlRule(
    name="Humidity Low Control",
    conditions={
        "humidity": {"operator": "<", "value": 40}
    },
    actions=[ControlAction.PUMP_ON],
    priority=6,
    enabled=True
)

smart_controller.add_rule(rule)
```

---

## 📊 数据库架构

### 核心表结构

**users** - 用户表
- id, username, email, password_hash, role, is_active, created_at, updated_at

**devices** - 设备表
- id, device_id, device_name, device_type, location, owner_id, is_active, latest_data_timestamp, created_at, updated_at

**environment_data** - 环境数据表
- id, device_id, temperature, humidity, co2_concentration, ammonia_concentration, recorded_at, created_at

**livestock_archive** - 入栏及免疫记录表
- id, batch_number, species, quantity, check_in_date, expected_checkout_date, immunization_records, notes, is_active, created_at, updated_at

**alarm_info** - 告警信息表
- id, device_id, alarm_type, alarm_level, threshold_value, actual_value, description, user_id, status, alarm_time, resolved_time, created_at

### Redis 缓存

**Key 设计：**
- `device:{device_id}:latest` - 设备最新数据（过期时间：1小时）
- `alarm:{device_id}:pending` - 待处理告警（过期时间：无）
- `control:command:{device_id}` - 待执行的控制命令

---

## 🔐 安全性考虑

### 已实现

- CORS 跨域资源共享配置
- 数据库参数化查询（SQLAlchemy ORM 自动处理）
- 异步数据库操作
- Redis 连接池管理

### 建议补充

- JWT 用户认证和授权
- HTTPS/TLS 加密
- API 请求限流
- 敏感数据加密
- 审计日志

---

## 📈 性能考虑

### 优化策略

1. **Redis 缓存**：最新数据缓存，减少数据库查询
2. **数据库索引**：device_id, recorded_at 等常用查询字段已添加索引
3. **连接池**：SQLAlchemy 连接池大小设置为 20
4. **异步 I/O**：FastAPI 原生支持异步处理

### 可扩展性

- 支持多设备并发数据接收
- Redis 可用于分布式缓存和消息队列
- 数据库可进行分表分库优化

---

## 🚀 部署建议

### Docker 容器化

创建 `backend/Dockerfile`：

```dockerfile
FROM python:3.9-slim

WORKDIR /app

COPY requirements.txt .
RUN pip install -r requirements.txt

COPY . .

CMD ["uvicorn", "main:app", "--host", "0.0.0.0", "--port", "8000"]
```

### Docker Compose

```yaml
version: '3.8'

services:
  mysql:
    image: mysql:5.7
    environment:
      MYSQL_ROOT_PASSWORD: password
      MYSQL_DATABASE: greenhouse_db
    ports:
      - "3306:3306"

  redis:
    image: redis:6-alpine
    ports:
      - "6379:6379"

  backend:
    build: ./backend
    ports:
      - "8000:8000"
    depends_on:
      - mysql
      - redis
    environment:
      MYSQL_HOST: mysql
      REDIS_HOST: redis

  frontend:
    build: ./frontend
    ports:
      - "5173:5173"
    depends_on:
      - backend
```

---

## 📝 API 测试

### 使用 cURL 测试

```bash
# 发送遥测数据
curl -X POST http://localhost:8000/api/v1/telemetry/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEVICE_001",
    "temperature": 28.5,
    "humidity": 65.0,
    "co2_concentration": 1200.0,
    "ammonia_concentration": 15.5
  }'

# 获取最新数据
curl http://localhost:8000/api/v1/telemetry/latest/DEVICE_001

# 获取待处理告警
curl http://localhost:8000/api/v1/alarms/pending
```

---

## 🐛 故障排除

### 常见问题

**Q: 数据库连接失败**
A: 检查 `.env` 文件中的数据库配置，确保 MySQL 服务正在运行

**Q: Redis 连接失败**
A: 确保 Redis 服务已启动，端口 6379 可访问

**Q: 前端无法连接后端**
A: 检查 `vite.config.js` 中的 proxy 配置，确保后端服务地址正确

---

## 📚 相关文档

- [详细 API 文档](./docs/API_DOCUMENTATION.md)
- [部署指南](./docs/DEPLOYMENT.md)
- [开发指南](./docs/DEVELOPMENT.md)

---

## 📄 许可证

MIT License

---

## 👨‍💼 作者

IoT 智能农业团队

**最后更新:** 2024年3月18日
