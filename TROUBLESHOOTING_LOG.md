# NEXUSMIND 故障排查日志

本文档用于记录和系统性地排查在开发和测试过程中遇到的问题。

---

## 问题 3: Pytest 收集测试时因 `ImportError` 和 `PermissionError` 失败

- **最后更新**: 2024-07-03
- **状态**: <font color="green">**原因已确认，待修复**</font>

### 现象
在尝试运行 `poetry run pytest` 以诊断 S3 配置问题时，测试在收集阶段就提前失败，未能实际运行任何测试代码。出现了两个独立的、阻塞性的错误。

#### 错误 A: `ImportError` - **[已确认]**
- **追溯**: `tests/test_api.py` -> `main.py` -> `tasks.py`
- **错误信息**: `ImportError: cannot import name 'get_db' from 'core.nexusmind.database'`
- **根本原因**: `core/nexusmind/tasks.py` 试图从 `core/nexusmind/database.py` 导入 `get_db` 函数，但后者中只存在一个名为 `get_session` 的函数。

#### 错误 B: `PermissionError` - **[已确认]**
- **错误信息**: `PermissionError: [Errno 13] Permission denied: '/home/xhz/documents/code_project/NEXUSMIND/postgres_data'`
- **根本原因**: `docker-compose up` 创建的 `postgres_data` 目录的所有者是 Docker 内部用户 (uid 999)，导致在宿主机上运行 `pytest` 的当前用户 (`xhz`) 没有权限访问该目录。

### 修复方案 (待执行)

#### 修复方案 A: 解决 `ImportError`
-   **目标**: 修正 `tasks.py` 中的错误导入。
-   **操作**:
    1.  打开 `core/nexusmind/tasks.py` 文件。
    2.  找到第 7 行: `from core.nexusmind.database import engine, get_db`
    3.  将其修改为: `from core.nexusmind.database import engine, get_session`
    4.  检查 `tasks.py` 文件中是否有任何地方使用了 `get_db()`，并将其替换为 `get_session()`。

#### 修复方案 B: 解决 `PermissionError`
-   **目标**: 修正 `postgres_data` 目录的权限。
-   **操作**: 在项目根目录的终端中，运行以下命令：
    ```bash
    sudo chown -R $(whoami):$(whoami) postgres_data
    ```

---

## 问题 2: Pytest 环境下 S3Storage 配置加载不正确

- **最后更新**: 2024-07-03
- **状态**: <font color="green">**原因已确认，待修复**</font>

### 现象
- 在 `S3Storage` 中加入诊断代码后，`pytest` 输出显示 `CoreConfig` 成功从 `.env` 文件加载了正确的配置 (`AWS_ENDPOINT_URL` 等)。
- 但 `boto3` 客户端在连接 MinIO 时，返回了 `InvalidAccessKeyId` 错误。

### 根本原因 - **[已确认]**
这是一个凭证不匹配的问题。
- **MinIO 服务端**: 根据 `docker-compose.yml` 的配置，MinIO 服务使用的凭证是 `MINIO_ROOT_USER: minioadmin` 和 `MINIO_ROOT_PASSWORD: minioadmin`。
- **boto3 客户端 (测试中)**: 根据 `tests/test_api.py` 中 `settings` fixture 的配置，传递给 `boto3` 客户端的凭证是 `AWS_ACCESS_KEY_ID="test-key"` 和 `AWS_SECRET_ACCESS_KEY="test-secret"`。

客户端使用的密钥 (`test-key`) 与服务端期望的密钥 (`minioadmin`) 不一致，导致 MinIO 拒绝了连接。

### 修复方案 (待执行)
-   **目标**: 统一测试环境中的客户端和服务端凭证。
-   **操作**: 修改 `tests/test_api.py` 中的 `settings` fixture，使其提供的 AWS 凭证与 `docker-compose.yml` 中定义的一致。

    ```python
    @pytest.fixture
    def settings(monkeypatch):
        """Fixture to set environment variables for testing."""
        monkeypatch.setenv("API_KEYS", '["test-key"]')
        monkeypatch.setenv("AWS_ACCESS_KEY_ID", "minioadmin")
        monkeypatch.setenv("AWS_SECRET_ACCESS_KEY", "minioadmin")
        monkeypatch.setenv("AWS_ENDPOINT_URL", "http://localhost:9000")
        monkeypatch.setenv("S3_BUCKET_NAME", "test-bucket")
        
        # Pydantic settings are cached, clear the cache to force reload
        get_core_config.cache_clear()
    ```

---

## 问题 1: Pytest 在收集测试用例时因 `PermissionError` 失败

- **最后更新**: 2024-07-03
- **状态**: <font color="green">**原因已确认，待修复**</font>

### 现象
运行 `poetry run pytest` 时，测试在开始执行前就立即失败。错误发生在"收集测试用例"阶段，日志明确指出 `pytest` 因为"权限被拒绝"而无法访问 `postgres_data` 目录。

### 根本原因 - **[已确认]**
1.  **权限问题**: `docker-compose up` 创建的 `postgres_data` 目录的所有者是 Docker 内部用户 (uid 999)，而运行 `pytest` 的宿主机用户没有权限读取该目录。
2.  **配置问题**: `pyproject.toml` 文件中没有为 `pytest` 配置 `norecursedirs` 选项，导致 `pytest` 默认会尝试扫描项目下的所有目录，包括它没有权限访问的 `postgres_data`。

### 修复方案 (待执行)
-   **目标**: 修正 `pytest` 的配置，使其忽略不相关的目录，从而从根源上解决问题。
-   **操作**: 在 `pyproject.toml` 文件中的 `[tool.pytest.ini_options]` 部分，添加 `norecursedirs` 配置项。

    ```toml
    [tool.pytest.ini_options]
    pythonpath = [
      "."
    ]
    norecursedirs = ["postgres_data", "minio_data", "redis_data", ".venv", "storage"]
    ```

---

## 问题 4: Celery 在 eager (同步) 测试模式下不更新任务结果

- **最后更新**: 2024-07-03
- **状态**: <font color="green">**根本原因已确认，待修复**</font>

### 现象
在 `tests/test_api.py` 中，我们通过在 fixture 中设置 `celery_app.conf.update(task_always_eager=True)`，成功地使 Celery 任务同步执行。
- **证据 A (成功)**: SQLAlchemy 的日志显示，`process_file` 任务被完整执行，并且数据库中对应 `File` 记录的状态被成功更新为 `SUCCESS`。
- **证据 B (失败)**: 当测试代码调用 `GET /upload/status/{task_id}` 时，`AsyncResult` 返回的状态**仍然是 `PENDING`**，导致断言 `assert 'PENDING' == 'SUCCESS'` 失败。

### 根本原因 - **[已确认]**
- **关键警告**: `pytest` 在运行时发出了一条明确的 `RuntimeWarning`:
  > `Results are not stored in backend and should not be retrieved when task_always_eager is enabled, unless task_store_eager_result is enabled.`
- **结论**: 这个警告直接解释了问题。当 Celery 在 `eager` (同步) 模式下运行时，为了优化，它默认**不会**将任务的最终结果（如状态 `SUCCESS` 或返回值）写回到配置的结果后端（Redis）。因此，当我们的 API 端点尝试通过 `AsyncResult` 查询结果时，它只能找到任务被创建时的初始状态，而找不到已经执行完毕的最终状态。我们修复了执行流，但忽略了结果流。

### 修复方案 (待执行)
-   **目标**: 强制 Celery 在 `eager` 模式下也将任务结果存入结果后端。
-   **操作**: 在 `tests/test_api.py` 的 `settings` fixture 中，为 Celery app 配置添加 `task_store_eager_result = True` 选项。

    ```python
    # 在 tests/test_api.py 的 settings fixture 中
    celery_app.conf.update(
        task_always_eager=True,
        task_store_eager_result=True  # 添加这一行
    )
    ```

---

## 问题 2: `tests/test_api.py` 导入了不存在的函数

- **最后更新**: 2024-07-03
- **状态**: <font color="green">**原因已确认，待修复**</font>

### 现象
在解决了 `PermissionError` 后，`pytest` 在收集 `tests/test_api.py` 时失败，并报告 `ImportError: cannot import name 'get_storage' from 'main'`。

### 根本原因 - **[已确认]**
- **函数重命名**: `tests/test_api.py` 试图从 `main.py` 导入 `get_storage` 函数。
- **验证结果**: 对 `main.py` 的检查显示，该函数实际上名为 `get_s3_storage`。这是一个典型的因代码重构而导致测试代码未同步更新的问题。

### 修复方案 (待执行)
-   **目标**: 修正 `tests/test_api.py` 中的错误导入。
-   **操作**: 在 `tests/test_api.py` 文件中，将导入语句：
    ```python
    from main import app, get_processor_registry, get_storage, get_core_config
    ```
    修改为：
    ```python
    from main import app, get_processor_registry, get_s3_storage, get_core_config
    ```

---

## 问题 3: `pytest` 运行时出现大量测试失败

- **最后更新**: 2024-07-03
- **状态**: <font color="red">**调查中 - 正在分析第一批失败**</font>

### 现象
在解决了 `pytest` 收集阶段的 `PermissionError` 和 `ImportError` 后，`pytest` 成功运行了所有测试，但报告了 11 个失败。这些失败可以归纳为几个独立的问题。

---
### 3.1 `test_api.py` S3/Boto3 凭证失败

- **测试**: `test_async_upload_and_chat`
- **错误信息**: `Failed to queue file processing for test_doc.txt: Unable to locate credentials`
- **状态**: <font color="green">**已解决**</font>

#### 根本原因 - **[已确认]**
- **验证结果**: 诊断日志显示 `CoreConfig()` 在初始化时，所有 S3 相关配置均为 `None`。
- **结论**: 依赖创建 `.env` 文件和切换工作目录的 `settings` fixture **不可靠**。
- **修复方案**: 使用 `pytest` 的 `monkeypatch` fixture 来强制设置环境变量，确保在测试运行时配置能被正确加载。

---
### 3.2 `LLMEndpoint` & `Brain` 重构不一致

- **测试**: `test_brain_initialization`, `test_save_and_load_brain`, `test_get_chat_completion`, 等。
- **错误信息**: `AttributeError: 'LLMEndpoint' object has no attribute 'config'` 和 `TypeError: LLMEndpoint.__init__() got an unexpected keyword argument 'config'`
- **状态**: <font color="green">**原因已确认，待修复**</font>

#### 根本原因 - **[已确认]**
- **接口变更**: `core/nexusmind/llm/llm_endpoint.py` 中的 `LLMEndpoint` 类已经被重构。
    -   它的 `__init__` 方法现在需要三个独立的参数 (`model_name`, `temperature`, `max_tokens`)，而不是一个 `config` 对象。
    -   它不再拥有一个 `.config` 属性；配置值被直接存储在实例上（如 `self.model_name`）。
- **测试代码未同步**: `tests/test_brain.py` 和 `tests/test_llm_endpoint.py` 仍然在使用旧的接口创建实例和访问属性，导致了 `TypeError` 和 `AttributeError`。

#### 修复方案 (待执行)
-   **目标**: 使所有相关的测试代码与 `LLMEndpoint` 的新接口保持一致。
-   **操作**:
    1.  **修改 `tests/test_llm_endpoint.py`**:
        -   在所有创建 `LLMEndpoint` 的地方，将 `LLMEndpoint(config=core_config)` 修改为 `LLMEndpoint(model_name=core_config.llm_model_name, temperature=core_config.temperature, max_tokens=core_config.max_tokens)`。
    2.  **修改 `core/nexusmind/brain/brain.py`**:
        -   检查 `Brain` 类的 `__init__` 方法。它在内部创建 `LLMEndpoint` 时，很可能也需要被修改，以正确地将 `self.llm_model_name` 等属性传递给 `LLMEndpoint` 的构造函数。
    3.  **修改 `tests/test_brain.py`**:
        -   在测试断言中，将访问 `brain.llm_endpoint.config.some_value` 修改为直接访问 `brain.some_value` 或 `brain.llm_endpoint.some_value`。例如，`brain.llm_endpoint.config.llm_model_name` 应修改为 `brain.llm_model_name`。

---
### 3.3 `CoreConfig` 默认值不匹配

- **测试**: `test_init_without_override`
- **错误信息**: `AssertionError: assert 'openai/gpt-4' == 'gpt-4o'`
- **状态**: <font color="grey">**待处理**</font>

---
### 3.4 `LocalStorage.save` 类型错误

- **测试**: `test_save_and_exists`, `test_get_content`, 等。
- **错误信息**: `TypeError: unsupported operand type(s) for /: 'PosixPath' and 'bytes'`
- **状态**: <font color="grey">**待处理**</font>