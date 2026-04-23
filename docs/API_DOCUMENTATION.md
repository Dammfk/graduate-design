# 数字化养殖大棚监控系统接口文档

本文档整理当前项目后端 FastAPI 已实现的主要接口。接口基础地址默认为：

```text
http://127.0.0.1:8000
```

业务接口统一前缀为：

```text
/api/v1
```

接口返回通常采用如下结构：

```json
{
  "status": "success",
  "message": "操作说明",
  "data": {}
}
```

当请求参数错误、资源不存在或服务端处理异常时，接口会返回 FastAPI 默认错误格式：

```json
{
  "detail": "错误原因"
}
```

## 1. 基础接口

### 1.1 系统根接口

请求方式：GET

接口地址：

```text
/
```

接口说明：用于检查后端服务是否启动，并返回应用名称和版本信息。

响应示例：

```json
{
  "status": "running",
  "app_name": "IoT Greenhouse Monitoring System",
  "version": "v1"
}
```

### 1.2 健康检查接口

请求方式：GET

接口地址：

```text
/health
```

接口说明：用于检查后端服务运行状态。

响应示例：

```json
{
  "status": "healthy",
  "debug": true
}
```

## 2. 环境监测接口

环境监测接口主要用于接收 STM32 或串口桥接程序上传的环境数据，并向前端提供最新数据、历史数据和监测总览。

接口前缀：

```text
/api/v1/telemetry
```

### 2.1 上报环境数据

请求方式：POST

接口地址：

```text
/api/v1/telemetry/
```

接口说明：接收设备上报的温度、湿度、二氧化碳浓度和氨气浓度。当前项目中，tools/serial_bridge.py 会读取 STM32 串口 JSON 数据，并转发到该接口。

请求体：

```json
{
  "device_id": "DEVICE_001",
  "temperature": 28.5,
  "humidity": 65.0,
  "co2_concentration": 1200.0,
  "ammonia_concentration": 15.5,
  "timestamp": "2026-04-21T20:30:00"
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| device_id | string | 是 | 设备唯一编号 |
| temperature | number | 否 | 温度，单位 °C |
| humidity | number | 否 | 湿度，单位 % |
| co2_concentration | number | 否 | 二氧化碳浓度，单位 ppm |
| ammonia_concentration | number | 否 | 氨气浓度，单位 ppm |
| timestamp | string | 否 | 采集时间，不传时后端自动补当前时间 |

响应示例：

```json
{
  "status": "success",
  "message": "Telemetry data received and processed",
  "data": {
    "data_id": 1,
    "device_id": "DEVICE_001",
    "alarms_created": 0,
    "commands_generated": 1,
    "timestamp": "2026-04-21T20:30:00+08:00"
  }
}
```

### 2.2 获取监测总览

请求方式：GET

接口地址：

```text
/api/v1/telemetry/overview
```

接口说明：获取棚区、设备、在线状态和环境均值等监测总览数据，前端首页和监测页会使用该接口。

响应示例：

```json
{
  "status": "success",
  "data": {
    "summary": {
      "device_count": 1,
      "zone_count": 1,
      "online_count": 1,
      "offline_count": 0,
      "avg_temperature": 28.5,
      "avg_humidity": 65.0
    },
    "zones": [],
    "devices": []
  }
}
```

### 2.3 获取指定设备最新数据

请求方式：GET

接口地址：

```text
/api/v1/telemetry/latest/{device_id}
```

路径参数：

| 参数名 | 类型 | 说明 |
| --- | --- | --- |
| device_id | string | 设备编号，例如 DEVICE_001 |

接口说明：查询指定设备最新环境数据。后端优先读取 Redis 缓存，缓存不存在时查询数据库。

响应示例：

```json
{
  "status": "success",
  "source": "cache",
  "data": {
    "id": 1,
    "temperature": 28.5,
    "humidity": 65.0,
    "co2_concentration": 1200.0,
    "ammonia_concentration": 15.5,
    "recorded_at": "2026-04-21T20:30:00+08:00"
  }
}
```

### 2.4 获取指定设备历史数据

请求方式：GET

接口地址：

```text
/api/v1/telemetry/history/{device_id}
```

查询参数：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| hours | integer | 否 | 24 | 查询最近多少小时，范围 1 至 720 |

请求示例：

```text
GET /api/v1/telemetry/history/DEVICE_001?hours=24
```

响应示例：

```json
{
  "status": "success",
  "device_id": "DEVICE_001",
  "hours": 24,
  "count": 2,
  "data": [
    {
      "timestamp": "2026-04-21T20:00:00+08:00",
      "temperature": 28.1,
      "humidity": 64.0,
      "co2_concentration": 1180.0,
      "ammonia_concentration": 14.2
    }
  ]
}
```

### 2.5 获取指定棚区历史数据

请求方式：GET

接口地址：

```text
/api/v1/telemetry/zones/{zone_name}/history
```

查询参数：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| hours | integer | 否 | 24 | 查询最近多少小时，范围 1 至 720 |

接口说明：按棚区名称查询历史环境数据。

## 3. 设备管理接口

设备管理接口用于维护设备台账，包括设备创建、查询、更新和删除。

接口前缀：

```text
/api/v1/devices
```

### 3.1 创建设备

请求方式：POST

接口地址：

```text
/api/v1/devices/?owner_id=1
```

查询参数：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| owner_id | integer | 是 | 设备所属用户 ID |

请求体：

```json
{
  "device_id": "DEVICE_001",
  "device_name": "一号棚控制器",
  "device_type": "stm32_controller",
  "location": "一号棚 东侧"
}
```

响应说明：成功后返回设备对象。

### 3.2 获取设备详情

请求方式：GET

接口地址：

```text
/api/v1/devices/{device_id}
```

接口说明：根据设备编号查询设备详情。

### 3.3 获取设备列表

请求方式：GET

接口地址：

```text
/api/v1/devices/
```

查询参数：

| 参数名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| owner_id | integer | 否 | 按用户 ID 过滤设备 |

响应示例：

```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "id": 1,
      "device_id": "DEVICE_001",
      "device_name": "一号棚控制器",
      "device_type": "stm32_controller",
      "location": "一号棚 东侧",
      "owner_id": 1,
      "is_active": true,
      "latest_data_timestamp": "2026-04-21T20:30:00",
      "created_at": "2026-04-21T20:00:00"
    }
  ]
}
```

### 3.4 更新设备信息

请求方式：PUT

接口地址：

```text
/api/v1/devices/{device_id}
```

请求体：

```json
{
  "device_name": "一号棚主控制器",
  "location": "一号棚 西侧",
  "is_active": true
}
```

### 3.5 删除设备

请求方式：DELETE

接口地址：

```text
/api/v1/devices/{device_id}
```

响应示例：

```json
{
  "status": "success",
  "message": "Device DEVICE_001 deleted"
}
```

## 4. 设备控制接口

设备控制接口用于前端控制面板、自动化规则展示、串口桥接程序轮询命令和命令状态回写。

接口前缀：

```text
/api/v1/control
```

### 4.1 获取控制面板数据

请求方式：GET

接口地址：

```text
/api/v1/control/dashboard
```

接口说明：返回设备控制面板、可控组件、自动化规则和最近命令记录。

响应数据主要包含：

| 字段名 | 说明 |
| --- | --- |
| components_catalog | 系统可控组件目录，例如 fan、cooling_pad、fill_light |
| devices | 设备控制面板数据 |
| automation_rules | 自动化规则 |
| recent_commands | 最近控制命令 |

### 4.2 下发人工控制命令

请求方式：POST

接口地址：

```text
/api/v1/control/devices/{device_id}/commands
```

请求体：

```json
{
  "target_component": "fan",
  "command_type": "ON",
  "execution_mode": "manual",
  "reason": "人工开启通风",
  "operator_user_id": 1
}
```

字段说明：

| 字段名 | 类型 | 必填 | 说明 |
| --- | --- | --- | --- |
| target_component | string | 是 | 控制组件，如 fan、cooling_pad、fill_light |
| command_type | string | 是 | 命令类型，如 ON、OFF |
| execution_mode | string | 否 | 执行模式，默认 manual |
| reason | string | 否 | 控制原因 |
| operator_user_id | integer | 否 | 操作用户 ID |

响应示例：

```json
{
  "status": "success",
  "message": "Command executed",
  "data": {
    "id": 12,
    "device_id": "DEVICE_001",
    "target_component": "fan",
    "command_type": "ON",
    "status": "pending"
  }
}
```

### 4.3 获取待执行命令

请求方式：GET

接口地址：

```text
/api/v1/control/devices/{device_id}/commands/pending
```

查询参数：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| limit | integer | 否 | 10 | 返回命令数量，范围 1 至 100 |

接口说明：供 tools/serial_bridge.py 轮询。桥接程序获取命令后写入 STM32 串口。

响应示例：

```json
{
  "status": "success",
  "device_id": "DEVICE_001",
  "count": 1,
  "data": [
    {
      "id": 12,
      "target_component": "fan",
      "command_type": "ON",
      "execution_mode": "manual",
      "status": "pending"
    }
  ]
}
```

### 4.4 更新命令状态

请求方式：PUT

接口地址：

```text
/api/v1/control/commands/{command_id}/status
```

请求体：

```json
{
  "status": "success"
}
```

状态说明：

| 状态 | 说明 |
| --- | --- |
| pending | 待执行 |
| sent | 已发送到硬件 |
| success | 硬件执行成功 |
| failed | 硬件执行失败 |

### 4.5 更新自动化规则状态

请求方式：PUT

接口地址：

```text
/api/v1/control/rules/{rule_id}
```

请求体：

```json
{
  "is_enabled": true
}
```

接口说明：启用或关闭指定自动化规则。

## 5. 告警管理接口

告警管理接口用于查询告警、确认告警、解决告警和查看风险面板。

接口前缀：

```text
/api/v1/alarms
```

### 5.1 获取待处理告警

请求方式：GET

接口地址：

```text
/api/v1/alarms/pending
```

响应示例：

```json
{
  "status": "success",
  "count": 1,
  "data": [
    {
      "id": 1,
      "device_id": 1,
      "alarm_type": "ammonia_high",
      "alarm_level": "critical",
      "threshold_value": 20.0,
      "actual_value": 25.5,
      "description": "氨气超标，实际值 25.5",
      "alarm_time": "2026-04-21T20:30:00",
      "status": "pending",
      "resolved_time": null,
      "user_id": null
    }
  ]
}
```

### 5.2 获取风险面板

请求方式：GET

接口地址：

```text
/api/v1/alarms/risk-dashboard
```

接口说明：统计告警总数、待处理告警、24 小时严重告警、最高风险区域、告警分布和档案风险信息。

### 5.3 获取指定设备告警

请求方式：GET

接口地址：

```text
/api/v1/alarms/device/{device_id}
```

查询参数：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| limit | integer | 否 | 20 | 返回最近告警数量 |

注意：此处 device_id 为数据库中的设备数字 ID，不是设备字符串编号 DEVICE_001。

### 5.4 确认告警

请求方式：PUT

接口地址：

```text
/api/v1/alarms/{alarm_id}/acknowledge
```

请求体：

```json
{
  "user_id": 1
}
```

响应示例：

```json
{
  "status": "success",
  "message": "Alarm acknowledged",
  "data": {
    "id": 1,
    "status": "acknowledged"
  }
}
```

### 5.5 解决告警

请求方式：PUT

接口地址：

```text
/api/v1/alarms/{alarm_id}/resolve
```

响应示例：

```json
{
  "status": "success",
  "message": "Alarm resolved",
  "data": {
    "id": 1,
    "status": "resolved",
    "resolved_time": "2026-04-21T21:00:00"
  }
}
```

### 5.6 获取告警详情

请求方式：GET

接口地址：

```text
/api/v1/alarms/{alarm_id}
```

## 6. 养殖档案接口

养殖档案接口用于维护批次档案和个体档案。

接口前缀：

```text
/api/v1/archives
```

### 6.1 获取档案面板

请求方式：GET

接口地址：

```text
/api/v1/archives/dashboard
```

接口说明：返回批次档案、个体档案和统计摘要。

### 6.2 创建批次档案

请求方式：POST

接口地址：

```text
/api/v1/archives/
```

请求体：

```json
{
  "batch_number": "BATCH-20260421-001",
  "species": "肉牛",
  "quantity": 20,
  "check_in_date": "2026-04-21T08:00:00",
  "expected_checkout_date": "2026-10-21T08:00:00",
  "immunization_records": "已完成基础免疫",
  "notes": "状态稳定",
  "average_weight": 280.5,
  "feed_consumption": 120.0,
  "health_status": "stable"
}
```

### 6.3 更新批次档案

请求方式：PUT

接口地址：

```text
/api/v1/archives/{archive_id}
```

请求体说明：字段均可选，支持更新 batch_number、species、quantity、expected_checkout_date、immunization_records、notes、average_weight、feed_consumption、health_status 和 is_active。

### 6.4 删除批次档案

请求方式：DELETE

接口地址：

```text
/api/v1/archives/{archive_id}
```

接口说明：删除或停用指定批次档案，具体行为由 ArchiveService 实现。

### 6.5 创建个体档案

请求方式：POST

接口地址：

```text
/api/v1/archives/animals
```

请求体：

```json
{
  "archive_id": 1,
  "animal_code": "ANIMAL-001",
  "species": "肉牛",
  "breed": "西门塔尔",
  "gender": "male",
  "birth_date": "2025-06-01T00:00:00",
  "check_in_date": "2026-04-21T08:00:00",
  "weight": 280.5,
  "health_status": "stable",
  "ear_tag": "ET-001",
  "source": "本地采购",
  "immunization_note": "已免疫",
  "notes": "无异常"
}
```

### 6.6 更新个体档案

请求方式：PUT

接口地址：

```text
/api/v1/archives/animals/{animal_id}
```

请求体说明：字段均可选，支持更新 animal_code、species、breed、gender、birth_date、check_in_date、weight、health_status、ear_tag、source、immunization_note、notes 和 is_active。

### 6.7 删除个体档案

请求方式：DELETE

接口地址：

```text
/api/v1/archives/animals/{animal_id}
```

## 7. 生产运营接口

生产运营接口用于管理生产任务、日常任务、库存物资和设备资产。

接口前缀：

```text
/api/v1/operations
```

### 7.1 获取运营面板

请求方式：GET

接口地址：

```text
/api/v1/operations/dashboard
```

### 7.2 生产任务接口

| 功能 | 方法 | 地址 |
| --- | --- | --- |
| 创建生产任务 | POST | /api/v1/operations/tasks |
| 更新生产任务 | PUT | /api/v1/operations/tasks/{task_id} |
| 更新任务状态 | PUT | /api/v1/operations/tasks/{task_id}/status |
| 删除生产任务 | DELETE | /api/v1/operations/tasks/{task_id} |

创建生产任务请求体：

```json
{
  "title": "检查一号棚通风",
  "category": "巡检",
  "priority": "medium",
  "status": "pending",
  "zone_name": "一号棚",
  "archive_id": 1,
  "assignee_user_id": 1,
  "due_at": "2026-04-22T08:00:00",
  "description": "检查风机和水帘运行状态"
}
```

更新任务状态请求体：

```json
{
  "status": "completed"
}
```

### 7.3 日常任务接口

| 功能 | 方法 | 地址 |
| --- | --- | --- |
| 创建日常任务 | POST | /api/v1/operations/daily-tasks |
| 更新日常任务 | PUT | /api/v1/operations/daily-tasks/{task_id} |
| 删除日常任务 | DELETE | /api/v1/operations/daily-tasks/{task_id} |

### 7.4 库存接口

| 功能 | 方法 | 地址 |
| --- | --- | --- |
| 创建库存物资 | POST | /api/v1/operations/inventory |
| 更新库存物资 | PUT | /api/v1/operations/inventory/{item_id} |
| 删除库存物资 | DELETE | /api/v1/operations/inventory/{item_id} |

创建库存物资请求体：

```json
{
  "item_name": "玉米饲料",
  "category": "饲料",
  "unit": "kg",
  "current_stock": 500,
  "safety_stock": 100,
  "location": "仓库 A",
  "supplier": "本地供应商",
  "last_restocked_at": "2026-04-21T09:00:00",
  "notes": "常用饲料"
}
```

### 7.5 设备资产接口

| 功能 | 方法 | 地址 |
| --- | --- | --- |
| 创建设备资产 | POST | /api/v1/operations/assets |
| 更新设备资产 | PUT | /api/v1/operations/assets/{asset_id} |
| 删除设备资产 | DELETE | /api/v1/operations/assets/{asset_id} |

创建设备资产请求体：

```json
{
  "asset_code": "ASSET-001",
  "asset_name": "一号棚排风风机",
  "asset_type": "fan",
  "zone_name": "一号棚",
  "linked_device_id": 1,
  "status": "online",
  "installed_at": "2026-04-21T09:00:00",
  "last_maintenance_at": "2026-04-21T09:00:00",
  "next_maintenance_at": "2026-05-21T09:00:00",
  "notes": "运行正常"
}
```

## 8. 系统管理接口

系统管理接口用于查看系统面板、用户操作日志和更新用户状态。

接口前缀：

```text
/api/v1/system
```

### 8.1 获取系统面板

请求方式：GET

接口地址：

```text
/api/v1/system/dashboard
```

### 8.2 获取用户操作日志

请求方式：GET

接口地址：

```text
/api/v1/system/users/{user_id}/logs
```

查询参数：

| 参数名 | 类型 | 必填 | 默认值 | 说明 |
| --- | --- | --- | --- | --- |
| limit | integer | 否 | 20 | 返回日志数量 |

### 8.3 更新用户状态

请求方式：PUT

接口地址：

```text
/api/v1/system/users/{user_id}
```

请求体：

```json
{
  "role": "manager",
  "is_active": true
}
```

## 9. 串口桥接相关说明

项目中的 tools/serial_bridge.py 会使用本接口文档中的部分接口完成硬件联调。

主要流程如下：

1. 从 STM32 串口读取 JSON 遥测数据。
2. 调用 POST /api/v1/telemetry/ 上传环境数据。
3. 定时调用 GET /api/v1/control/devices/{device_id}/commands/pending 轮询待执行命令。
4. 将命令写入串口，发送给 STM32。
5. 收到 STM32 ACK 后，调用 PUT /api/v1/control/commands/{command_id}/status 回写命令状态。

桥接程序发送给 STM32 的命令格式示例：

```json
{
  "command_id": 12,
  "target": "fan",
  "command": "ON"
}
```

STM32 回传 ACK 格式示例：

```json
{
  "type": "ack",
  "command_id": 12,
  "status": "ok"
}
```

## 10. 常见状态码

| 状态码 | 说明 |
| --- | --- |
| 200 | 请求成功 |
| 400 | 请求参数错误 |
| 404 | 资源不存在 |
| 500 | 服务端处理异常 |

## 11. 前端接口调用对应关系

前端接口封装文件位于 frontend/src/api/client.js。

| 前端 API 模块 | 后端接口模块 | 说明 |
| --- | --- | --- |
| telemetryAPI | /api/v1/telemetry | 环境监测、历史趋势、监测总览 |
| alarmAPI | /api/v1/alarms | 告警列表、风险面板、告警处理 |
| deviceAPI | /api/v1/devices | 设备台账 |
| controlAPI | /api/v1/control | 控制面板、人工命令、自动规则 |
| archiveAPI | /api/v1/archives | 批次档案、个体档案 |
| operationsAPI | /api/v1/operations | 生产任务、库存、设备资产 |
| systemAPI | /api/v1/system | 系统面板、用户日志、用户状态 |
