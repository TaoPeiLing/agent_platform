# 工具系统架构说明

## 核心概念

工具系统是一个为Agent提供能力扩展的框架，它允许Agent调用各种工具来完成特定任务。工具系统的核心包括：

1. **工具函数**: 实现具体功能的函数，如计算器、单位转换器等
2. **工具管理器**: 负责工具的注册、发现和执行
3. **工具注册机制**: 提供简单的方式来注册新工具

## 系统层次结构

工具系统采用清晰的层次结构：

1. **底层**: 工具函数实现 (calculator.py, converter.py, example_tool.py等)
2. **中间层**: 工具管理和注册 (tool_manager.py, tool_registry.py)
3. **应用层**: Agent与工具的交互示例 (tool_example.py)

## 主要组件

### 工具管理器 (ToolManager)

工具管理器是整个系统的核心，负责:

- 注册和管理工具
- 工具发现和过滤
- 工具权限检查
- 执行工具

关键方法:
- `register_tool()`: 注册一个工具
- `get_tool()`: 获取指定名称的工具
- `find_tools()`: 根据条件查找工具
- `get_original_function()`: 获取工具的原始函数
- `execute_tool()`: 执行指定的工具

### 工具注册模块

提供装饰器和函数来简化工具注册过程:

- `@register_tool`: 装饰器，用于注册工具函数
- `register_function_dynamically()`: 动态注册任意函数为工具
- `discover_tools()`: 自动发现和注册工具模块中的工具

### 上下文工具

提供与Agent上下文交互的工具:

- 获取用户信息
- 检查权限
- 获取对话历史

## 使用方法

### 1. 基本工具创建和注册

使用装饰器注册工具:

class Dict:
pass

```python
from agent_cores.tools.core.tool_registry import register_tool

@register_tool(
    name="calculator_tool",
    description="执行数学计算",
    category="math",
    tags=["calculation"]
)
def calculator_tool(expression: str) -> Dict[str, Any]:
    """
    执行数学计算
    
    Args:
        expression: 要计算的表达式
        
    Returns:
        计算结果
    """
    try:
        # 计算逻辑
        result = eval(expression)
        return {
            "success": True,
            "result": result
        }
    except Exception as e:
        return {
            "success": False,
            "message": f"计算错误: {str(e)}"
        }
```

### 2. 动态注册类方法

```python
from agent_cores.tools.core.tool_registry import register_function_dynamically

# 假设有一个数据库管理器类
class DatabaseManager:
    def query(self, sql: str) -> List[Dict]:
        # 查询实现...
        pass

# 创建实例
db_manager = DatabaseManager()

# 动态注册类方法为工具
register_function_dynamically(
    db_manager.query,
    name="database_query",
    description="执行SQL查询",
    category="database",
    permission_level="advanced"
)
```

### 3. 通过工具管理器执行工具

```python
from agent_cores.tools.core.tool_manager import tool_manager

# 执行工具
result = tool_manager.execute_tool("calculator_tool", "2 + 2 * 3")
print(result)  # 输出: {'success': True, 'result': 8}

# 获取原始函数并调用
calc_func = tool_manager.get_original_function("calculator_tool")
if calc_func:
    result = calc_func("10 / 2")
    print(result)  # 输出: {'success': True, 'result': 5.0}
```

### 4. 在Agent系统中集成工具

```python
# 1. 在Agent初始化时注册所有工具
from agent_cores.tools.register_tools import register_all_tools
from agent_cores.tools.core.tool_manager import tool_manager
register_all_tools()

# 2. 获取工具列表供Agent使用
available_tools = list(tool_manager.tools.values())

# 3. Agent根据用户输入选择合适的工具
user_input = "帮我计算2+2"
selected_tool = "calculator_tool"  # 根据输入选择工具

# 4. 执行工具并处理结果
result = tool_manager.execute_tool(selected_tool, "2+2")
if result.get("success", False):
    response = f"计算结果是: {result.get('result')}"
else:
    response = f"计算失败: {result.get('message')}"
```

## 注意事项

1. 工具函数应返回标准化的结果结构，通常包含:
   - `success`: 布尔值，表示操作是否成功
   - `result`: 操作结果(如果成功)
   - `message`: 错误信息(如果失败)

2. 使用原始函数引用时要注意:
   - 通过 `get_original_function()` 获取原始函数
   - 原始函数已被包装，包含错误处理

3. 工具权限管理:
   - 设置适当的权限级别 (`basic`, `advanced`, `admin`)
   - 在执行前检查用户是否有权限使用工具

4. 工具分类和标签:
   - 合理设置分类和标签，便于Agent选择合适的工具
   - 可以通过分类和标签筛选工具 

## 工具目录架构
agent_cores/
└── tools/
    ├── __init__.py
    ├── README.md
    ├── core/                  # 基础设施
    │   ├── __init__.py
    │   ├── tool_manager.py
    │   ├── tool_registry.py
    │   └── tool_utils.py
    ├── register_tools.py      # 注册入口点
    ├── system/                # 系统工具
    │   ├── __init__.py
    │   ├── context_tools.py
    │   └── rbac_tools.py
    ├── data/                  # 数据处理工具
    │   ├── __init__.py
    │   ├── database.py
    │   └── file.py
    ├── math/                  # 数学相关工具
    │   ├── __init__.py
    │   ├── calculator.py
    │   └── math.py
    ├── media/                 # 媒体工具
    │   ├── __init__.py
    │   └── audio.py
    ├── web/                   # 网络工具
    │   ├── __init__.py
    │   ├── network.py
    │   └── weather.py
    └── examples/              # 示例工具
        ├── __init__.py
        ├── example_tool.py
        └── diagnostics.py