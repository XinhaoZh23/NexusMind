# NEXUSMIND

这是一个通过 LLM 指导逐步构建的 RAG（检索增强生成）项目。它实现了一个完整的 RAG 流水线，并提供 API 接口。

## ✨ 特性

- **📝 文档处理**: 支持通过 API 异步上传文档，并自动在后台进行处理和分块。
- **🧠 RAG 问答**: 基于上传的文档内容进行问答。
- **🧩 可扩展设计**: 采用模块化和面向接口的设计，易于扩展（例如，添加新的文档处理器或存储后端）。
- **🔐 API 驱动与安全**: 所有核心功能均通过 FastAPI 提供，并由 API 密钥保护。
- **🐳 容器化**: 提供 `Dockerfile` 和 `docker-compose.yml`，一键启动整个应用。

## 🚀 安装与启动

### 环境要求

- Python 3.9+
- [Poetry](https://python-poetry.org/)
- [Docker](https://www.docker.com/) & [Docker Compose](https://docs.docker.com/compose/)

### 本地运行

1.  **克隆仓库**:
    ```bash
    git clone https://github.com/your-username/NEXUSMIND.git
    cd NEXUSMIND
    ```

2.  **安装依赖**:
    我们使用 Poetry 管理项目依赖。运行以下命令来安装：
    ```bash
    poetry install
    ```

3.  **配置环境变量**:
    复制 `.env.example` 文件（如果存在）或创建一个新的 `.env` 文件，并填入以下内容。
    ```env
    # 用于访问应用 API 的密钥，可以设置一个或多个，用逗号分隔
    API_KEYS='["your-secret-api-key"]'

    # 您使用的大语言模型提供商的 API 密钥
    OPENAI_API_KEY="sk-..." 
    ```

4.  **启动 API 服务器**:
    ```bash
    poetry run uvicorn main:app --reload
    ```
    服务器将在 `http://127.0.0.1:8000` 上运行。

### 使用 Docker 运行

1.  **克隆仓库** (如果尚未操作)。

2.  **配置环境变量**:
    在项目根目录创建一个 `.env` 文件，内容同上。

3.  **构建并启动容器**:
    ```bash
    docker-compose up --build -d
    ```
    服务将以与本地运行相同的方式在 `http://127.0.0.1:8000` 上可用。

## ⚙️ API 使用示例

以下示例假设您的 API 密钥为 `your-secret-api-key`。

### 1. 上传文件

此操作将上传一个文件进行处理。这是一个异步操作，会立即返回一个任务 ID。

```bash
curl -X POST "http://127.0.0.1:8000/upload" \
-H "X-API-Key: your-secret-api-key" \
-F "file=@/path/to/your/document.txt" \
-F "brain_id=00000000-0000-0000-0000-000000000000"
```

### 2. 查询上传状态

使用上一步返回的 `task_id` 来查询文件处理状态。

```bash
curl -X GET "http://127.0.0.1:8000/upload/status/<your_task_id>" \
-H "X-API-Key: your-secret-api-key"
```

### 3. 进行聊天

在文件处理成功后，就已上传的文档内容提问。

```bash
curl -X POST "http://127.0.0.1:8000/chat" \
-H "Content-Type: application/json" \
-H "X-API-Key: your-secret-api-key" \
-d '{
    "brain_id": "00000000-0000-0000-0000-000000000000",
    "question": "文档的主要内容是什么?"
}'
```
