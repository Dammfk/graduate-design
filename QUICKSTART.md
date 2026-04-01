# 物联网养殖大棚监控系统 - 快速入门

## ✅ 项目完成情况

### 1️⃣ 后端开发（FastAPI + SQLAlchemy + Redis） ✓ 完成

**已实现：**
- ✅ 完整的数据库模型（User, Device, EnvironmentData, LivestockArchive, AlarmInfo）
- ✅ 异步 REST API 接口
  - `POST /api/v1/telemetry/` - 接收遥测数据
  - `GET /api/v1/telemetry/latest/{device_id}` - 获取最新数据
  - `GET /api/v1/telemetry/history/{device_id}` - 获取历史数据
- ✅ 告警管理系统
  - 自动告警创建（温度、湿度、CO2、氨气）
  - 告警确认和解决流程
- ✅ Redis 缓存集成（每小时缓存设备最新数据）
- ✅ 设备管理 API
- ✅ 智能自动化控制逻辑（5条内置规则）
- ✅ 节能优化计算

**项目结构：**
```
backend/
├── main.py (FastAPI 应用入口)
├── requirements.txt (依赖列表)
├── .env (环境配置)
└── app/
    ├── core/ (配置和数据库)
    ├── models/ (SQLAlchemy 模型)
    ├── schemas/ (Pydantic 验证)
    ├── api/ (路由接口)
    └── services/ (业务逻辑)
```

---

### 2️⃣ 前端开发（Vue 3 + ECharts） ✓ 完成

**已实现：**
- ✅ 三分屏监控大屏设计
  - 左屏：4个实时仪表盘（温度、湿度、CO2、氨气）
  - 中屏：24小时数据趋势折线图（可切换指标）
  - 右屏：实时告警列表（分级显示与操作）
- ✅ 响应式设计和现代 UI
- ✅ 实时数据自动刷新（10秒间隔）
- ✅ **氨气告警闪烁效果**（NH3 > 20ppm 时红色闪烁）
- ✅ Pinia 状态管理
- ✅ API 客户端集成

**项目结构：**
```
frontend/
├── package.json (依赖)
├── vite.config.js (Vite 配置)
├── index.html
└── src/
    ├── App.vue (主应用)
    ├── main.js (入口)
    ├── api/ (API 调用)
    ├── stores/ (Pinia 状态)
    └── components/ (Vue 组件)
```

---

### 3️⃣ 硬件开发（C 语言 + LiteOS） ✓ 完成

**已实现：**
- ✅ 传感器驱动程序
  - I2C 接口驱动（DHT22 温湿度传感器）
  - ADC 接口驱动（CO2 和氨气模拟传感器）
- ✅ NB-IoT 通信模块
  - AT 指令支持
  - JSON 数据包封装
  - 云平台连接和数据上传
- ✅ 继电器控制模块（GPIO）
  - 排风扇控制
  - 水泵控制
- ✅ 智能主循环程序
  - 传感器采集（10秒周期）
  - 数据上传（30秒周期）
  - 心跳维持（60秒周期）
  - 云端命令接收和执行

**项目结构：**
```
hardware/
├── main.c (主程序)
├── sensor_driver.h/c (传感器驱动)
├── iot_cloud.h/c (NB-IoT 通信)
├── relay_control.h/c (继电器控制)
└── CMakeLists.txt (编译配置)
```

---

### 4️⃣ 自动化控制逻辑（Python） ✓ 完成

**已实现：**
- ✅ 智能控制器框架
  - 5条内置规则（温度控制、氨气告警、CO2控制、湿度控制）
  - 优先级系统（高优先级规则优先执行）
- ✅ 条件评估引擎
  - 支持 >, <, >=, <=, == 比较运算符
- ✅ 节能优化模块
  - 温度优化（目标温度范围内省电 15%）
  - 时间段优化（夜间额外省电 20%）
- ✅ 能耗跟踪和报告
  - 运行时统计
  - CO2 排放当量计算
- ✅ 可自定义规则系统

**核心功能：**
```python
# 规则自动执行流程
1. 读取环境数据
2. 评估所有规则条件
3. 排序匹配的规则（按优先级）
4. 执行对应的控制动作
5. 记录能耗数据
```

---

## 🚀 快速开始指南

### 前置条件

```bash
# 检查依赖
python --version         # Python 3.8+
mysql --version         # MySQL 5.7+
redis-cli --version     # Redis 6.0+
node --version          # Node.js 16+
```

### 第 1 步：启动后端服务

```bash
# 进入后端目录
cd backend

# 安装依赖
pip install -r requirements.txt

# 配置环境变量
# 编辑 .env 文件，设置数据库和 Redis 连接信息

# 启动服务
python main.py
# 或使用 uvicorn
uvicorn main:app --host 0.0.0.0 --port 8000 --reload
```

**预期输出：**
```
INFO:     Uvicorn running on http://0.0.0.0:8000
```

### 第 2 步：启动前端应用

```bash
# 新开一个终端，进入前端目录
cd frontend

# 安装依赖
npm install

# 启动开发服务器
npm run dev
```

**预期输出：**
```
  ➜  Local:   http://localhost:5173/
```

### 第 3 步：测试系统

#### 使用 cURL 发送测试数据

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

# 预期响应
{
  "status": "success",
  "message": "Telemetry data received and processed",
  "data": {
    "data_id": 1,
    "device_id": "DEVICE_001",
    "alarms_created": 0,
    "commands_generated": 1,
    "timestamp": "2024-03-18T10:30:00Z"
  }
}
```

#### 氨气告警测试

```bash
# 发送高氨气浓度数据（触发告警闪烁）
curl -X POST http://localhost:8000/api/v1/telemetry/ \
  -H "Content-Type: application/json" \
  -d '{
    "device_id": "DEVICE_001",
    "temperature": 28.5,
    "humidity": 65.0,
    "co2_concentration": 1200.0,
    "ammonia_concentration": 28.0
  }'
```

在浏览器中访问 `http://localhost:5173`，你应该看到：
- 右侧告警列表中出现新的告警
- 页面出现红色闪烁效果

#### 获取最新数据

```bash
curl http://localhost:8000/api/v1/telemetry/latest/DEVICE_001
```

#### 获取历史数据

```bash
curl "http://localhost:8000/api/v1/telemetry/history/DEVICE_001?hours=24"
```

---

## 📊 数据库初始化

系统会在启动时自动创建所有表。如果需要手动创建，可以使用：

```python
from app.core.database import Base, engine
Base.metadata.create_all(bind=engine)
```

---

## 🎮 自动化控制演示

### 触发温度控制规则

```python
# 将以下代码添加到测试环境

from app.services.automation_service import smart_controller, process_environment_data

# 场景1：高温触发排风扇
data1 = {
    "temperature": 31.5,
    "humidity": 65.0,
    "co2_concentration": 1200.0,
    "ammonia_concentration": 15.0
}
result = process_environment_data(data1)
print(result["actions"])
# 输出：[{'action': 'FAN_ON', 'rule': 'Temperature High Control', ...}]

# 场景2：氨气过高（最高优先级）
data2 = {
    "temperature": 28.0,
    "humidity": 65.0,
    "co2_concentration": 1200.0,
    "ammonia_concentration": 28.0
}
result = process_environment_data(data2)
print(result["actions"])
# 输出：[{'action': 'FAN_ON', ...}, {'action': 'ALERT', ...}]

# 场景3：获取节能建议
print(result["energy_optimization"])
```

---

## 📈 系统架构图

```
┌─────────────────────────────────────────────────────────────┐
│                    IoT Greenhouse Monitoring System         │
└─────────────────────────────────────────────────────────────┘

硬件层 (BearPi + LiteOS)
┌─────────────────────────────────────────┐
│ 传感器 → DHT22, ADC → NB-IoT 模块 → 继电器 │
└──────────────────┬──────────────────────┘
                   │ JSON 数据包
                   ▼
后端 API 层 (FastAPI on Port 8000)
┌─────────────────────────────────────────┐
│  POST /api/v1/telemetry/  ← 接收数据    │
│  └─▶ 保存到 MySQL                       │
│  └─▶ 缓存到 Redis                       │
│  └─▶ 检查告警                           │
│  └─▶ 执行自动化控制                      │
│                                         │
│  GET /api/v1/telemetry/latest           │
│  GET /api/v1/alarms/pending             │
│  PUT /api/v1/alarms/{id}/acknowledge    │
└──────────────────┬──────────────────────┘
                   │ REST API
                   ▼
前端展示层 (Vue 3 + ECharts on Port 5173)
┌─────────────────────────────────────────┐
│     监控大屏                             │
│  ┌──────────┬──────────┬──────────┐    │
│  │ 仪表盘   │ 趋势图   │ 告警列表  │    │
│  │ (4个)   │ (可切换) │ (可操作) │    │
│  └──────────┴──────────┴──────────┘    │
└─────────────────────────────────────────┘

数据存储
┌──────────────────────────┐
│ MySQL (实时数据+历史)    │
│ Redis (缓存+消息队列)    │
└──────────────────────────┘
```

---

## 🔄 数据流示例

```
1. 硬件采集
   DHT22(温度✅ 湿度✅) + ADC(CO2✅ NH3✅)
   
2. 数据编码
   JSON: {"device_id": "DEVICE_001", ...}
   
3. NB-IoT 上传
   AT+NSOST 指令发送到云平台
   
4. FastAPI 接收
   POST /api/v1/telemetry/ 
   ├─ 验证数据 (Pydantic)
   ├─ 储存数据库 (SQLAlchemy)
   ├─ 缓存 Redis (1小时过期)
   └─ 触发规则 (Automation Service)
   
5. 智能控制
   评估条件 → 排序优先级 → 执行动作 → 记录能耗
   
6. 告警处理
   温度告警 → 告警表 → 前端显示 → 用户确认
   
7. 前端展示
   自动刷新 → ECharts → 用户交互
```

---

## 🎯 关键功能清单

### 后端功能
- [x] MySQL 数据库设计（5个核心表）
- [x] 异步 REST API（12个端点）
- [x] Redis 缓存整合
- [x] 自动告警系统
- [x] 智能控制引擎
- [x] 节能优化模块
- [x] CORS 支持

### 前端功能
- [x] 响应式三分屏布局
- [x] ECharts 4个仪表盘
- [x] 24小时趋势图（4种指标）
- [x] 告警列表（可交互）
- [x] **氨气红色闪烁告警**
- [x] 设备切换
- [x] 自动数据刷新
- [x] Pinia 状态管理

### 硬件功能
- [x] I2C 传感器驱动
- [x] ADC 采样驱动
- [x] NB-IoT 通信模块
- [x] GPIO 继电器控制
- [x] JSON 数据打包
- [x] 命令接收执行
- [x] AT 指令支持

### 自动化功能
- [x] 5条智能规则
- [x] 优先级评估
- [x] 节能计算
- [x] 能耗统计
- [x] CO2 排放计算
- [x] 可自定义规则

---

## 📝 下一步建议

### 缺失的功能（可选）

1. **用户认证与授权**
   - JWT Token 认证
   - 基于角色的权限控制

2. **数据持久化增强**
   - 数据导出功能
   - 数据分析报表
   - 日志审计

3. **通知系统**
   - 邮件告警
   - 短信告警
   - 移动端推送

4. **硬件完善**
   - 真实传感器集成测试
   - 固件升级机制
   - 远程诊断

5. **性能优化**
   - API 请求限流
   - 数据库分表分库
   - 消息队列（RabbitMQ）

---

## 📞 支持和反馈

如有问题或建议，请：
1. 检查日志文件
2. 参考项目文档
3. 运行测试脚本
4. 提交 Issue

---

**项目完成日期：** 2024年3月18日
**所有核心功能已实现 ✓**
