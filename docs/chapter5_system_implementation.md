5 数字化养殖大棚监控系统实现

本章结合本系统已经完成的软硬件功能，对数字化养殖大棚监控系统的具体实现进行说明。本系统由硬件采集端、串口桥接程序、FastAPI 后端服务和 Vue 前端页面共同组成。硬件端负责采集温湿度等环境数据并执行继电器控制；桥接程序负责连接 STM32 串口与后端接口；后端负责数据入库、告警判断、自动控制命令生成和业务接口提供；前端负责环境监测、设备控制、告警管理和档案管理等功能展示。系统整体实现重点是打通“采集、上传、处理、展示、控制、反馈”的业务闭环。

5.1 硬件系统实现

本系统硬件部分以 STM32 控制板为核心，结合温湿度采集、OLED 显示、继电器控制和串口通信实现现场监测与控制。硬件工程主要位于 hardware 目录，其中 main.c 为硬件端主程序，sensor_driver.c 和 sensor_driver.h 用于传感器采集，relay_control.c 和 relay_control.h 用于继电器控制，iot_cloud.c 和 iot_cloud.h 用于通信数据组织和发送。当前演示主工程位于 hardware/demo 目录，主要用于 STM32 本地采集、OLED 显示、继电器动作和串口 JSON 数据上报。

在硬件实现中，控制板承担两类任务：一类是周期性采集养殖大棚环境参数，另一类是根据本地阈值或后端下发命令控制执行设备。系统中涉及的执行设备主要包括排风风机、水帘降温设备和补光灯等，其中当前硬件演示重点验证继电器控制和风机联动。硬件端通过串口输出遥测 JSON 数据，后续由桥接程序上传至 FastAPI 后端。

5.1.1 数据采集实现

数据采集模块主要实现温度、湿度、二氧化碳浓度和氨气浓度等环境参数采集。根据项目代码，传感器驱动模块通过 I2C 和 ADC 两类接口获取数据。温湿度采集通过 I2C 接口完成，程序先发送测量触发指令，再读取传感器返回的数据，并将原始值换算为温度和湿度。二氧化碳和氨气浓度通过 ADC 通道读取模拟电压，再根据传感器量程关系换算为 ppm 浓度值。

在 sensor_driver.c 中，read_all_sensors 函数负责完成一次完整采集过程。该函数依次调用温湿度读取函数、二氧化碳读取函数和氨气读取函数，并将结果保存到统一的 sensor_reading_t 结构中。采集结果包括 dht.temperature、dht.humidity、gas.co2_ppm、gas.ammonia_ppm 和 timestamp 等字段。这样可以保证硬件端后续进行本地控制判断和通信上报时使用同一份环境数据。

气体浓度采集过程中，程序先读取 ADC 原始值，再按照 3.3V 参考电压将其换算为实际电压。二氧化碳浓度根据电压与浓度的线性关系换算，程序中将结果限制在 0 至 5000 ppm 范围内；氨气浓度同样通过电压换算获得，并将结果限制在 0 至 100 ppm 范围内。范围限制可以避免采样噪声或异常电压导致数据明显失真。

硬件主程序中设置了采集周期，SENSOR_READ_INTERVAL 为 10 秒，即每 10 秒执行一次传感器读取。采集完成后，硬件端会执行本地控制逻辑。当前本地控制规则为：当温度高于 30°C 或氨气浓度高于 25 ppm 时开启排风风机；当温度降低到 25°C 及以下时关闭排风风机。该逻辑通过 relay_fan_on 和 relay_fan_off 控制继电器状态，能够在没有前端人工干预时实现基础自动调节。

除数据采集外，硬件端还保留了能耗统计思路。程序在风机处于开启状态时累计运行时间，并根据假定风机功率估算能耗。该部分虽然不是系统核心业务，但可以为后续扩展设备能耗统计、维护提醒和运行分析提供基础。

5.1.2 通信模块实现

本项目通信链路分为硬件端通信和上位机桥接两部分。硬件端负责组织并输出 JSON 数据，桥接程序负责把串口数据转发到后端接口。这样设计可以降低 STM32 端直接接入 HTTP 服务的复杂度，也便于在毕业设计演示时通过本地电脑完成串口调试和后端联调。

硬件通信模块在 iot_cloud.c 中实现了设备初始化、连接管理、遥测数据发送、命令接收和心跳发送等功能。遥测数据发送时，程序将设备编号、温度、湿度、二氧化碳浓度、氨气浓度和时间戳组装为 JSON 字符串。字段名称与后端 TelemetryData 数据结构保持一致，包括 device_id、temperature、humidity、co2_concentration、ammonia_concentration 和 timestamp。通过统一字段名称，后端能够直接完成数据解析和入库。

项目中的实际桥接程序为 tools/serial_bridge.py。该脚本使用 pyserial 打开 STM32 串口，默认波特率为 115200，并通过 requests 调用后端服务。桥接程序启动时可以指定串口号、后端地址、轮询间隔和设备编号，例如演示时可连接 COM5 并访问本机 8000 端口的 FastAPI 服务。程序运行后会持续读取串口中的每一行数据，并尝试按 JSON 解析。

当桥接程序收到普通遥测 JSON 数据时，会检查其中是否存在 device_id。若存在设备编号，则将该设备加入 known_devices 集合，并通过 POST 请求转发到后端 /api/v1/telemetry/ 接口。后端成功接收后，桥接程序在控制台输出 telemetry 已上传的提示。若串口收到的内容不是 JSON，桥接程序会忽略该内容，避免调试日志影响数据上报。

下行控制命令通过轮询方式实现。桥接程序每隔 poll_interval 秒访问 /api/v1/control/devices/{device_id}/commands/pending 接口，查询指定设备是否存在待执行命令。如果存在命令，则将后端命令转换为硬件端可识别的紧凑 JSON 格式，内容包括 command_id、target 和 command，然后写入串口。写入成功后，桥接程序会调用命令状态接口将命令状态更新为 sent。

硬件端执行命令后，可以通过串口回传 ACK 数据。桥接程序识别 type 为 ack 的 JSON 后，会读取 command_id 和 status，并将 ok 转换为 success，将 fail 转换为 failed，然后调用 /api/v1/control/commands/{command_id}/status 接口回写命令执行结果。通过该机制，本项目实现了从前端下发命令到硬件执行、再到后端状态更新的控制闭环。

5.2 后端系统实现

后端系统基于 FastAPI 实现，代码主要位于 backend/app 目录。系统采用“接口层、服务层、模型层、数据库层”的结构组织。api 目录负责定义 HTTP 接口，services 目录负责业务逻辑处理，models 目录负责 SQLAlchemy 数据模型，core 目录负责数据库和配置管理。当前系统使用 SQLite 数据库存储主要业务数据，同时保留 Redis 缓存最新环境数据的能力。

后端已实现的主要业务模块包括 telemetry、devices、control、alarms、archives、operations 和 system。其中 telemetry 模块负责环境数据上报和查询；control 模块负责设备控制和自动化规则；alarms 模块负责告警记录和风险面板；archives 模块负责养殖批次和个体档案；operations 模块负责生产任务、库存和设备资产；system 模块负责系统管理数据。第 5 章重点说明环境监测、控制和前端展示相关实现。

5.2.1 数据处理模块

后端数据处理的核心入口是 /api/v1/telemetry/ 接口。硬件桥接程序将 STM32 上报的 JSON 数据转发到该接口后，后端首先检查时间戳。如果请求中没有 timestamp，系统会使用当前时间补全。随后接口调用 TelemetryService.save_environment_data 保存环境数据。

TelemetryService 在保存数据时首先根据 device_id 查询设备表。如果设备已经存在，则直接使用该设备的数据库 id；如果设备不存在，系统会自动注册设备。自动注册设备时，系统会先查找默认管理用户 auto_device_owner，若不存在则使用已有管理员或创建自动用户，然后创建设备记录。自动生成的设备名称为“自动注册设备 + 设备编号”，设备类型为 stm32_controller，默认位置为“未分配”。这一实现使新硬件首次上报数据时不需要手动建档，适合演示和多设备扩展。

设备匹配完成后，系统将 temperature、humidity、co2_concentration、ammonia_concentration 和 recorded_at 写入 environment_data 表。写入成功后，系统同步更新 devices 表中的 latest_data_timestamp，用于前端判断设备最近上报时间。随后，系统把最新数据写入 Redis 缓存，缓存键格式为 device:{device_id}:latest，过期时间为 1 小时。当前项目即使 Redis 不可用，也会捕获异常并继续使用数据库，因此不会影响主流程入库。

环境数据保存完成后，后端继续执行告警判断。AlarmService 中定义了 ALARM_CONFIG，当前主要阈值包括：温度高于 30°C 生成 temperature_high 告警，温度低于 5°C 生成 temperature_low 告警，湿度高于 90% 生成 humidity_high 告警，湿度低于 20% 生成 humidity_low 告警，二氧化碳浓度高于 2000 ppm 生成 co2_high 告警，氨气浓度高于 20 ppm 生成 ammonia_high 告警。其中氨气超标告警等级为 critical，其余常见异常为 warning。告警记录保存到 alarm_info 表，状态默认为 pending。

控制命令生成由 ControlService 完成。系统内置了默认自动化规则，包括高温启动风机、温度持续偏高联动水帘、氨气超标启动风机、温度恢复关闭风机和夜间补光示意规则。其中风机组件 key 为 fan，水帘组件 key 为 cooling_pad，补光灯组件 key 为 fill_light。系统根据最新环境数据和启用的自动化规则判断是否需要生成控制命令，并写入 control_command_logs 表。为了避免重复下发相同命令，ControlService 会检查同一设备、同一组件、同一命令是否已有 pending、sent 或 success 状态的命令。

通过上述处理，后端在一次 telemetry 上报中完成了设备自动注册、环境数据入库、最新数据缓存、告警生成和控制命令生成。接口返回结果中包含 data_id、device_id、alarms_created、commands_generated 和 timestamp，便于桥接程序或调试人员判断本次数据处理结果。

5.2.2 接口实现

本项目后端接口按照业务模块划分，并统一使用 /api/v1 作为接口前缀。环境监测接口位于 backend/app/api/telemetry.py，主要包括 POST /api/v1/telemetry/、GET /api/v1/telemetry/overview、GET /api/v1/telemetry/latest/{device_id}、GET /api/v1/telemetry/history/{device_id} 和 GET /api/v1/telemetry/zones/{zone_name}/history。

POST /api/v1/telemetry/ 用于接收桥接程序上传的环境数据，是硬件数据进入系统的入口。GET /api/v1/telemetry/latest/{device_id} 用于查询单台设备最新数据，接口优先读取 Redis 缓存，缓存不存在时再查询数据库。GET /api/v1/telemetry/history/{device_id} 用于查询某设备指定小时数内的历史数据，hours 参数范围限制为 1 至 720 小时，返回结果包含时间戳和四类环境指标。GET /api/v1/telemetry/overview 用于前端首页和监测页获取分区、设备和平均环境指标。

设备控制接口位于 backend/app/api/control.py。GET /api/v1/control/dashboard 用于前端控制页面获取设备控制面板、自动化规则和最近命令记录；POST /api/v1/control/devices/{device_id}/commands 用于前端人工下发控制命令；GET /api/v1/control/devices/{device_id}/commands/pending 用于串口桥接程序轮询待执行命令；PUT /api/v1/control/commands/{command_id}/status 用于桥接程序回写命令发送或执行状态；PUT /api/v1/control/rules/{rule_id} 用于启用或关闭自动化规则。

告警接口位于 backend/app/api/alarms.py，主要提供待处理告警查询、设备告警查询、告警确认、告警解决和风险面板等能力。前端通过 getPending 获取待处理告警，通过 acknowledge 将告警状态更新为 acknowledged，通过 resolve 将告警状态更新为 resolved 并写入 resolved_time。风险面板接口会统计最近 24 小时不同等级、不同类型和不同区域的告警分布，并结合养殖档案健康状态形成辅助风险信息。

养殖档案接口位于 backend/app/api/archives.py，用于支撑前端档案页面。系统支持批次档案的创建、更新和删除，也支持个体档案的创建、更新和删除。批次档案字段包括 batch_number、species、quantity、check_in_date、expected_checkout_date、immunization_records、average_weight、feed_consumption 和 health_status 等；个体档案字段包括 animal_code、breed、gender、birth_date、ear_tag、source、weight 和 immunization_note 等。该模块使系统不仅能监测环境，也能记录养殖对象的生产管理信息。

5.3 前端系统实现

前端系统基于 Vue 3 实现，代码主要位于 frontend/src 目录。main.js 为前端入口，App.vue 负责整体页面框架，views 目录存放业务页面，components 目录存放可复用组件，stores/monitoring.js 负责统一管理页面状态和接口调用结果，api/client.js 对 Axios 请求进行封装。

api/client.js 中将后端接口按业务模块封装为 telemetryAPI、alarmAPI、deviceAPI、controlAPI、archiveAPI、operationsAPI 和 systemAPI。前端页面不直接拼接复杂请求逻辑，而是调用这些 API 方法获取数据。例如，环境监测页面调用 telemetryAPI.getOverview、telemetryAPI.getLatest 和 telemetryAPI.getHistory；控制页面调用 controlAPI.getDashboard 和 controlAPI.executeCommand；档案页面调用 archiveAPI.getDashboard、createArchive、updateArchive 和 createAnimal 等方法。

5.3.1 页面设计

本项目前端不是单一监控大屏，而是按照实际养殖管理业务划分为多个页面，包括首页概览、环境监测、设备控制、告警管理、养殖档案、生产任务和系统管理。页面路由和模块切换由 App.vue 与各 view 组件共同实现，用户可以在不同模块之间切换，完成监测、控制、档案和告警处理。

环境监测页面对应 MonitoringView.vue。该页面使用 ModuleContextBar 作为顶部筛选区域，支持选择棚区和历史时间范围。页面左侧为分区概览，展示当前分区名称、在线设备数量和离线设备数量，并以设备卡片形式列出当前分区下的设备。用户点击设备卡片后，页面会更新 selectedDeviceId，并同时请求最新数据和历史数据。

环境监测页面右侧由两个核心组件组成：EnvironmentDashboard 和 TrendChart。EnvironmentDashboard 用于展示当前设备最新环境指标，包括温度、湿度、二氧化碳浓度和氨气浓度；TrendChart 用于展示所选设备的历史趋势。这样的布局既能看到当前状态，也能观察最近一段时间的变化趋势，符合养殖大棚监控的使用场景。

设备控制页面主要由 ControlPanel、AutomationRules 和 CommandHistory 等组件组成。ControlPanel 展示每台设备下的可控组件，包括排风风机、水帘降温和补光灯，并支持人工执行 ON、OFF 指令。AutomationRules 展示后端自动化规则，例如高温启动风机、氨气超标启动风机等，用户可以通过开关调整规则是否启用。CommandHistory 展示最近控制命令，便于检查人工控制或自动控制是否已生成和执行。

告警页面使用 AlarmList 和 RiskDashboard 展示异常信息。AlarmList 主要展示待处理告警、告警等级、告警类型、实际值和发生时间，并提供确认或解决操作。RiskDashboard 则对告警数量、最高风险区域、告警等级分布和近 7 天历史告警进行汇总，帮助用户快速判断当前大棚环境风险。

档案页面通过 ArchivePanel 实现养殖档案管理。该页面围绕批次档案和个体档案展开，支持维护存栏批次、数量、平均体重、饲料消耗、健康状态和免疫记录等信息。该设计使系统不仅停留在设备监测层面，也能够支撑基本养殖生产资料管理。

5.3.2 数据可视化实现

本项目的数据可视化主要体现在环境仪表、历史趋势图、告警风险面板和首页摘要。环境数据可视化的核心组件是 TrendChart.vue，该组件基于 ECharts 实现折线图。组件接收 title 和 data 两个参数，其中 data 来自后端历史数据接口，包含 timestamp、temperature、humidity、co2_concentration 和 ammonia_concentration 等字段。

TrendChart 组件提供四个指标切换按钮，分别为温度、湿度、CO2 和氨气。用户点击不同指标后，组件会更新 activeTab，并重新绘制图表。图表横轴使用 timestamp 转换后的本地时间，纵轴为当前指标的数值。折线图设置为 smooth 平滑曲线，并隐藏普通数据点符号，使趋势变化更清晰。不同指标使用不同颜色，例如温度使用偏橙色，湿度使用青绿色，CO2 使用绿色，氨气使用黄色。

图表提示框采用 axis 触发方式，用户悬停在曲线上时可以看到具体时间、指标名称、数值和单位。例如温度单位为 °C，湿度单位为 %，CO2 和氨气单位为 ppm。图表还使用面积渐变效果突出趋势区域，并监听窗口 resize 事件，在浏览器窗口变化时自动调整图表尺寸。组件卸载时会移除 resize 监听并销毁 ECharts 实例，避免资源泄漏。

EnvironmentDashboard 组件用于展示实时环境指标，数据来源于 monitoringStore.currentMetrics。该状态由前端调用 telemetryAPI.getLatest 或监测总览接口后更新。MonitoringView 中，当用户切换设备时，会同时调用 fetchLatestData 和 fetchHistoricalData，因此实时指标和趋势图能够同步变化。当用户调整历史时间范围时，页面只重新请求历史数据，不影响当前设备选择。

告警风险可视化主要依赖 alarms 模块返回的数据。RiskDashboard 会展示待处理告警数量、严重告警数量、高风险区域和告警分布情况。通过将环境监测图表、告警列表和控制面板结合起来，前端能够较完整地呈现系统运行状态：环境数据异常时，用户可以在告警页面看到风险，在控制页面看到自动命令或人工下发命令，在监测页面继续观察环境指标变化。

综上，本项目第 5 章所述实现不是独立的单点功能，而是围绕真实项目代码形成的完整链路。STM32 或硬件演示端负责采集并输出数据，serial_bridge.py 负责串口与 FastAPI 的双向转发，后端负责数据入库、告警和命令生成，前端负责分区监测、趋势可视化、设备控制和档案管理。各部分通过统一的设备编号和 JSON 数据结构连接，最终实现数字化养殖大棚监控系统的基本功能闭环。
