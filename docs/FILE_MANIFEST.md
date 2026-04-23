# 项目文件清单

更新时间：2026-04-20

## 说明

本文件用于记录当前项目的主要目录和文件职责。  
当前项目仍在联调完善阶段，不是最终生产版本。

---

## 根目录

```text
E:\fastapi\graduate design
├── README.md
├── TE.py
├── .vscode/
├── backend/
├── docs/
├── frontend/
├── hardware/
└── tools/
```

### 根目录文件

- `README.md`：项目总说明
- `TE.py`：历史测试文件，当前不是主流程
- `.vscode/tasks.json`：VS Code 开发任务配置

---

## 后端目录

```text
backend/
├── .env
├── greenhouse.db
├── main.py
├── requirements.txt
├── seed_data.py
└── app/
```

### 关键文件

- `backend/main.py`：FastAPI 应用入口
- `backend/requirements.txt`：Python 依赖
- `backend/greenhouse.db`：当前 SQLite 数据库
- `backend/seed_data.py`：演示数据初始化脚本
- `backend/app/core/config.py`：配置管理
- `backend/app/core/database.py`：数据库和 Redis 连接
- `backend/app/models/__init__.py`：SQLAlchemy 数据模型
- `backend/app/schemas/__init__.py`：Pydantic 请求/响应模型

### API

- `backend/app/api/telemetry.py`：环境数据上报与查询
- `backend/app/api/control.py`：设备控制与命令状态
- `backend/app/api/alarms.py`：告警接口
- `backend/app/api/devices.py`：设备管理接口
- `backend/app/api/archives.py`：养殖档案接口
- `backend/app/api/operations.py`：任务、库存、资产接口
- `backend/app/api/system.py`：用户与系统面板接口

### 服务层

- `backend/app/services/telemetry_service.py`：遥测数据、设备自动注册、监测总览
- `backend/app/services/control_service.py`：控制面板、自动规则、命令生成
- `backend/app/services/alarm_service.py`：告警生成与风险面板
- `backend/app/services/archive_service.py`：养殖档案服务
- `backend/app/services/operations_service.py`：任务、库存、资产服务
- `backend/app/services/system_service.py`：系统用户与日志服务
- `backend/app/services/automation_service.py`：早期自动化服务，需确认是否仍参与主流程

---

## 前端目录

```text
frontend/
├── index.html
├── package.json
├── vite.config.js
└── src/
```

### 关键文件

- `frontend/src/App.vue`：应用壳、路由切换、全局刷新
- `frontend/src/main.js`：Vue 应用入口
- `frontend/src/api/client.js`：Axios API 封装
- `frontend/src/stores/monitoring.js`：Pinia 状态管理

### 页面

- `frontend/src/views/OverviewHome.vue`：总览首页
- `frontend/src/views/MonitoringView.vue`：环境监测页
- `frontend/src/views/ControlView.vue`：智能控制页
- `frontend/src/views/ArchivesView.vue`：养殖档案页
- `frontend/src/views/AlarmsView.vue`：风险预警页
- `frontend/src/views/OperationsView.vue`：任务资产页
- `frontend/src/views/SystemView.vue`：系统权限页

### 组件

- `frontend/src/components/EnvironmentDashboard.vue`：实时环境仪表
- `frontend/src/components/TrendChart.vue`：历史趋势图
- `frontend/src/components/ControlPanel.vue`：设备控制面板
- `frontend/src/components/CommandHistory.vue`：控制记录
- `frontend/src/components/AutomationRules.vue`：自动规则展示与开关
- `frontend/src/components/AlarmList.vue`：告警列表
- `frontend/src/components/ArchivePanel.vue`：档案管理
- `frontend/src/components/OperationsPanel.vue`：任务、库存、资产管理
- `frontend/src/components/SystemPanel.vue`：系统管理

---

## 硬件目录

```text
hardware/
├── demo/
├── CMakeLists.txt
├── main.c
├── sensor_driver.c
├── relay_control.c
└── iot_cloud.c
```

### 当前主工程

当前 STM32 主工程是：

```text
hardware/demo/
```

重点文件：

- `hardware/demo/Core/Src/main.c`：当前主固件逻辑
- `hardware/demo/Core/Src/usart.c`：USART1 串口初始化和收发
- `hardware/demo/Core/Src/gpio.c`：GPIO 初始化
- `hardware/demo/Core/Src/oled.c`：OLED 驱动
- `hardware/demo/Core/Inc/main.h`：引脚定义

### 历史参考代码

`hardware/` 根目录下的 `main.c`、`sensor_driver.c`、`relay_control.c`、`iot_cloud.c` 更偏早期参考代码，不是当前实际烧录主线。

---

## 桥接工具目录

```text
tools/
├── README.md
├── requirements.txt
└── serial_bridge.py
```

### 关键文件

- `tools/serial_bridge.py`：串口与 FastAPI 桥接程序
- `tools/requirements.txt`：`pyserial` 和 `requests`
- `tools/README.md`：桥接工具说明

---

## 文档目录

```text
docs/
├── 2026-04-17.md
├── 2026-04-20.md
├── FILE_MANIFEST.md
├── INTEGRATION_GUIDE.md
├── PROJECT_SUMMARY.md
└── QUICKSTART.md
```

### 当前文档职责

- `docs/2026-04-17.md`：阶段进展记录
- `docs/2026-04-20.md`：当前交接文档与缺口清单
- `docs/INTEGRATION_GUIDE.md`：当前软硬件联调指南
- `docs/PROJECT_SUMMARY.md`：阶段总结
- `docs/FILE_MANIFEST.md`：本文件
- `docs/QUICKSTART.md`：快速启动说明，后续仍需按当前任务配置再更新

---

## 当前主要缺口

- 人工控制板子动作不稳定
- STM32 未上报继电器真实状态
- CO2 和氨气目前没有真实传感器数据
- 自动规则仍需贴合真实业务
- 数据库迁移方式还不正式
- 部分旧文档仍可能包含历史说法，需要继续清理

