# SSS Agent Platform

基于OpenAI Agents SDK的代理平台，支持多代理模板、工具扩展和延迟加载机制。

## 项目特点

- **模板化代理**: 支持从配置文件创建和管理不同类型的代理模板
- **灵活的工具扩展**: 易于注册和管理自定义工具
- **权限管理系统**: 为不同角色和用户提供不同级别的工具访问权限
- **延迟加载机制**: 按需加载代理模板，提高系统性能
- **诊断与自愈功能**: 自动检测和修复系统配置问题
- **多轮对话支持**: 通过上下文管理维持多轮对话的连续性
- **丰富的工具集**: 提供文件、音频、网络等多种工具，支持代理能力扩展

## 系统结构

```
sss_agent_platform/
├── agent_configs/      # 代理配置目录
│   └── agents/         # 代理模板配置(JSON)
├── agent_cores/        # 核心功能
│   ├── core/           # 核心组件
│   │   ├── factory.py  # 代理工厂
│   │   ├── runtime.py  # 运行时服务
│   │   └── template_manager.py # 模板管理器
│   ├── models/         # 数据模型
│   ├── tools/          # 工具集合
│   │   ├── calculator.py  # 计算器工具
│   │   ├── weather.py     # 天气查询工具
│   │   ├── diagnostics.py # 系统诊断工具
│   │   ├── file.py        # 文件操作工具
│   │   ├── audio.py       # 音频处理工具
│   │   ├── network.py     # 网络请求工具
│   │   ├── math.py        # 数学计算工具
│   │   ├── database.py    # 数据库操作工具
│   │   └── rbac_tools.py  # 权限控制工具
│   └── examples/       # 示例代码
│       ├── agent_templates.py  # 模板注册示例
│       ├── use_agent_templates.py # 使用模板示例
│       ├── use_tool_examples.py   # 工具使用示例
│       └── system_check.py  # 系统检查工具
├── workspace/          # 工作目录，用于存储文件和音频
└── README.md           # 项目说明
```

## 主要组件

### 模板管理系统

模板管理系统允许你定义、加载和使用不同的代理模板：

- `template_manager`: 全局模板管理器实例，提供模板的加载和获取功能
- 延迟加载机制：模板会在首次被请求时才加载到内存中
- 自动发现：系统会自动搜索`agent_configs/agents`目录下的JSON文件作为模板
- 容错处理：即使部分模板加载失败，也不会影响其他模板的使用

### 工具管理系统

工具管理系统用于注册和管理各种工具：

- `tool_manager`: 全局工具管理器实例，管理所有注册的工具
- 分类与权限：工具可以按分类组织，并设置不同的权限级别
- 自动注册：系统启动时会自动注册预定义的工具

### 运行时服务

运行时服务负责创建和运行代理：

- `runtime_service`: 全局运行时服务实例，处理代理的创建和执行
- 支持从模板创建代理或直接使用配置创建代理
- 支持流式输出和异步执行

### 工具系统

平台提供多种工具，扩展代理的能力：

- **文件工具**：提供文件读写、列出文件等功能
- **音频工具**：提供文本转语音、语音转文本、音频播放等功能
- **网络工具**：提供HTTP请求、文件下载、URL检查、网络测试等功能
- **数学工具**：提供基本计算和科学计算功能
- **数据库工具**：提供数据库查询、增删改查等功能
- **天气工具**：提供天气查询功能
- **计算器工具**：提供计算表达式和单位转换功能
- **诊断工具**：提供系统诊断和修复功能

### 诊断系统

诊断系统用于检测和修复系统配置问题：

- `diagnostics`: 全局诊断工具实例，提供系统检查和修复功能
- 模板诊断：检查模板配置是否正确，必要时创建默认模板
- SSL诊断：检查SSL配置是否正常，尝试修复证书问题
- API连接诊断：检查API密钥配置和连接是否正常

## 使用示例

### 创建并运行代理

```python
from agent_cores.core import runtime_service, template_manager

# 获取模板
template = template_manager.get_template("assistant_agent")

# 运行代理
response = runtime_service.run_agent(
    template_or_agent=template,
    message="你好，请介绍一下自己",
    user_id="user_123",
    session_id="session_123",
    stream=False
)

print(response)
```

### 使用文件工具

```python
from agent_cores.tools import FileManager

# 创建文件管理器
file_manager = FileManager()

# 写入文件
result = file_manager.write_file("example.txt", "这是示例内容")

# 读取文件
content = file_manager.read_file("example.txt")

# 列出文件
files = file_manager.list_files()
```

### 使用音频工具

```python
from agent_cores.tools import text_to_speech, speech_to_text

# 文本转语音
tts_result = text_to_speech("这是要转换为语音的文本")
audio_file = tts_result.get("file_path")

# 语音转文本
stt_result = speech_to_text(audio_file)
text = stt_result.get("text")
```

### 使用网络工具

```python
from agent_cores.tools import http_request, download_file, check_url, ping

# 发送HTTP请求
response = http_request("https://api.example.com/data", method="GET")

# 下载文件
download_result = download_file("https://example.com/file.pdf", "local_file.pdf")

# 检查URL可用性
check_result = check_url("https://example.com")

# Ping测试
ping_result = ping("example.com")
```

### 使用系统诊断

```python
from agent_cores.tools.example.diagnostics import diagnostics

# 运行完整诊断
report = diagnostics.run_all_diagnostics()

# 只诊断模板配置
template_report = diagnostics.diagnose_templates()

# 检查SSL配置
ssl_report = diagnostics.diagnose_ssl()

# 检查API连接
api_report = diagnostics.diagnose_api_connection()
```

### 使用系统检查工具

你可以使用提供的命令行工具检查系统状态：

```bash
# 检查整个系统
python agent_cores/examples/system_check.py

# 只检查模板配置
python agent_cores/examples/system_check.py --templates

# 检查SSL配置，不自动修复问题
python agent_cores/examples/system_check.py --ssl --no-fix

# 检查API连接，显示详细信息
python agent_cores/examples/system_check.py --api --verbose

# 检查模板配置并创建默认模板
python agent_cores/examples/system_check.py --templates --create-default
```

### 工具使用示例

```bash
# 运行工具使用示例
python agent_cores/examples/use_tool_examples.py
```

## 更多示例

完整示例代码可以在`agent_cores/examples`目录下找到：

- `agent_templates.py`: 展示如何注册代理模板
- `use_agent_templates.py`: 展示如何使用代理模板
- `use_tool_examples.py`: 展示如何使用各种工具
- `system_check.py`: 系统检查与诊断工具

运行示例：

```bash
# 运行所有示例
python agent_cores/examples/use_agent_templates.py

# 运行特定编号的示例
python agent_cores/examples/use_agent_templates.py 1

# 运行工具使用示例
python agent_cores/examples/use_tool_examples.py
```