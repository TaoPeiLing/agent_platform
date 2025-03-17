from setuptools import setup, find_packages

setup(
    name="sss_agent_platform",
    version="0.1",
    packages=find_packages(),
    install_requires=[
        # 核心依赖项
        "openai-agents>=0.0.4",
        "openai>=1.0.0"
        
        # web 框架
        "fastapi>=0.104.1",
        "uvicorn>=0.23.2",
        "websockets>=11.0.3",
        "pydantic>=2.4.2",

        # 异步支持
        "httpx>=0.24.0",
        "asyncio>=3.4.3",

        # 数据库连接器
        "psycopg2-binary>=2.9.9",
        "pymongo>=4.6.0",
        "redis>=5.0.1",

        # 环境配置
        "python-dotenv>=1.0.0",

        # 数据处理
        "pydantic>=2.0.0",
        "pydantic-settings>=2.0.0",

        # 工具支持库
        "cryptography>=41.0.0",
        "requests>=2.28.0"
        
        # 监控日志
        "prometheus-client>=0.17.1",
        "opentelemetry-api>=1.19.0",
        "opentelemetry-sdk>=1.19.0",

        # 日志和调试
        "colorlog>=5.0.1",

        # 安全与认证
        "python-jose>=3.3.0",
        "passlib>=1.7.4",
        "bcrypt>=4.0.1",
        "python-dotenv>=1.0.0",


        # 开发和测试相关
        "pytest>=7.4.3",
        "pytest-asyncio>=0.21.1",
        "pytest-cov>=4.1.0",
        "black>=23.3.0",
        "nest-asyncio>=1.60"
        "pylint>=2.17.4",
        "isort>=5.12.0 "
    ],
)