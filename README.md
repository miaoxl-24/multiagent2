# 多智能体助手系统

基于 LangGraph 的多智能体对话服务，集成旅行规划、笑话生成、对联创作等功能。

## ✨ 功能特性

- 🗺️ **旅行规划** - 调用高德地图 MCP 进行路线规划
- 😄 **笑话生成** - 生成幽默笑话
- 📜 **对联创作** - 根据上联智能生成下联（基于 RAG 检索增强）
- 💬 **多轮对话** - 支持上下文保持的多轮对话
- 🎨 **精美界面** - 现代化的 Web 前端界面

## 🛠️ 技术栈

- **框架**: LangGraph, LangChain
- **语言模型**: 阿里云通义千问 (Qwen)
- **地图服务**: 高德地图 MCP
- **数据库**: Redis (存储对联数据集)
- **后端**: FastAPI
- **前端**: HTML5 + CSS3 + JavaScript

## 📦 安装步骤

### 1. 克隆项目

```bash
git clone https://github.com/yourusername/your-repo-name.git
cd your-repo-name
```

### 2. 安装依赖

```bash
pip install -r requirements.txt
```

### 3. 配置 API 密钥

创建 `config/Keys.json` 文件：

```json
{
    "BAILIAN_API_KEY": "your-dashscope-api-key"
}
```

### 4. 启动 Redis

```bash
# Windows
redis-server.exe

# Linux/Mac
redis-server
```

### 5. 导入数据集

```bash
python poi_loader.py
```

### 6. 启动服务

```bash
python main.py
```

### 7. 访问服务

打开浏览器访问: http://localhost:8000

## 🔧 使用方法

### API 接口

**POST /chat** - 同步聊天接口

```bash
curl -X POST http://localhost:8000/chat \
  -H "Content-Type: application/json" \
  -d '{"message": "帮我规划从长沙溁湾镇到梅溪湖的路线"}'
```

**POST /chat/stream** - 流式聊天接口

```bash
curl -X POST http://localhost:8000/chat/stream \
  -H "Content-Type: application/json" \
  -d '{"message": "给我讲个笑话"}'
```

### 测试示例

```python
from Director import invoke_graph

# 旅行规划
result = invoke_graph("帮我规划从北京到上海的路线")
print(result)

# 笑话生成
result = invoke_graph("给我讲个程序员笑话")
print(result)

# 对联创作
result = invoke_graph("帮我对个对联，上联是：瑞雪兆丰年")
print(result)
```

## 📁 项目结构

```
├── Director.py          # 多智能体核心模块
├── main.py              # FastAPI 后端服务
├── 多智能体.py          # 原始框架（开发调试用）
├── poi_loader.py        # 数据加载器
├── redis_query.py       # Redis 查询工具
├── 文件说明.txt         # 中文文件说明
├── config/
│   ├── __init__.py
│   ├── load_key.py      # 密钥加载模块
│   └── Keys.json        # API 密钥配置
├── static/
│   └── index.html       # 前端聊天界面
└── requirements.txt     # 依赖列表
```

## 🧠 智能体架构

```
用户请求 → Supervisor → 智能体选择 → 执行 → 返回结果
                              ↓
              ┌──────────────┴──────────────┐
              ▼                            ▼
         Travel Agent                  Joke Agent
              │                            │
              ▼                            ▼
         高德MCP服务                    LLM生成
              │                            │
              └──────────────┬──────────────┘
                             ▼
                       Couplet Agent
                             │
                             ▼
                       Redis检索
```

## 📊 数据集

- **来源**: couplet_samll 数据集
- **规模**: 约 294,072 条对联数据
- **存储**: Redis Hash (poi_data)

## 📝 License

MIT License

## 🤝 贡献

欢迎提交 Issue 和 Pull Request！

## 📞 联系方式

如有问题，请联系: your@email.com
