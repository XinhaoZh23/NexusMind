# NEXUSMIND 故障排查日志

本文档用于记录和系统性地排查在开发和测试过程中遇到的问题。
 
---

## 2025-07-03: CI `ModuleNotFoundError`

**问题描述:**
CI/CD 流水线中的 `pytest` 步骤失败，报告 `ModuleNotFoundError: No module named 'core.nexusmind.storage.s3_storage'`。此问题在本地环境中可能因不健壮的 `sys.path.insert` 路径修改而未被发现。

**根本原因分析:**
项目采用了非标准的 `core/` 目录结构，依赖于不稳定的路径修改技巧来工作，导致在不同环境（本地 vs CI）下的行为不一致。

**解决方案:**
采纳 Python 社区的最佳实践，将项目重构为标准的 `src` 布局，从根本上解决路径发现问题。

### **执行计划**

#### **第一步：创建 `src` 目录并移动源代码**

**操作:**
将 `core/nexusmind` 源代码目录移动到新的 `src/nexusmind` 位置，并清理旧的目录结构。这被视为重构的第一阶段。

**反馈:**
* **2025-07-03**: 已执行。源代码已移动到 `src/` 目录下。

#### **第二步：更新 `pyproject.toml` 以识别新布局**

**操作:**
修改 `pyproject.toml`，告知 Poetry 新的 `src` 布局。

**反馈:**
* **2025-07-03**: 已执行。`poetry check` 通过。

#### **第三步：移除所有测试文件中的路径修改代码 (关键步骤)**

**操作:**
遍历所有测试文件，删除不健壮的 `sys.path.insert()` 路径修改代码。

**反馈:**
* **2025-07-03**: 待执行。

#### **第四步：修正 `src/nexusmind/` 目录内部所有文件之间的相互导入语句**

**操作:**
由于 `sys.path` 已被移除，现在需要修正 `src/nexusmind/` 目录内部所有文件之间的相互导入语句，将所有 `from core.nexusmind...` 替换为正确的相对或绝对导入。

**反馈:**
* **2025-07-03**: 已修复 `src/nexusmind/celery_app.py`。`pytest` 错误链深入一层，暴露了 `src/nexusmind/config.py` 中的新导入问题。
* **2025-07-03**: 已修复 `src/nexusmind/config.py` 的相对导入路径。新暴露的问题是 `ImportError`，表明 `base_config.py` 文件中缺少 `MinioConfig` 等类的定义。
* **2025-07-03**: 已在 `src/nexusmind/base_config.py` 中添加缺失的配置类。新的导入瓶颈转移到了项目根目录的 `main.py` 文件。
* **2025-07-03**: 已修复 `main.py` 中的所有导入语句。`pytest` 错误链继续深入，暴露出 `src/nexusmind/brain/brain.py` 的导入问题。
* **2025-07-03**: 已修复 `brain.py` 中对 `llm_endpoint` 的导入。下一个待修复的导入在同一个文件内：`logger`。
* **2025-07-03**: 已修复 `brain.py` 中对 `logger` 的相对路径导入。新暴露的问题是 `ImportError`，表明 `logger.py` 文件中缺少 `get_logger` 函数的定义。
* **2025-07-03**: 已在 `logger.py` 中添加 `get_logger` 函数。`pytest` 错误链继续深入，暴露了 `storage/faiss_vector_store.py` 中的导入问题。
* **2025-07-03**: 已修复 `faiss_vector_store.py` 的导入。新的 `ModuleNotFoundError` 暴露在其基类 `vector_store_base.py` 中。
* **2025-07-03**: 已修复 `vector_store_base.py` 的导入。错误链回跳，暴露出 `brain.py` 中存在一个遗漏的、未被修复的旧式导入。
* **2025-07-03**: 已彻底修复 `brain.py` 的所有导入。`test_api.py` 的 `ModuleNotFoundError` 已解决，新问题为 `ImportError`，因 `config.py` 缺少 `get_core_config` 函数。
* **2025-07-03**: 已修复 `config.py` 中 `get_core_config` 函数缺失的问题。
* **2025-07-03**: 已修复 `tests/test_brain.py` 中的 `IndentationError`。
* **2025-07-03**: 已修复 `tests/test_nexus_file.py` 的导入问题并移除空测试。
* **2025-07-03**: 已修复 `tests/test_config.py` 的 `NameError: name 'os' is not defined` 问题。
* **2025-07-03**: 已修复 `src/nexusmind/database.py` 的导入问题。
* **2025-07-03**: 已修复 `src/nexusmind/processor/implementations/simple_txt_processor.py` 的导入问题。
* **2025-07-03**: 已修复 `src/nexusmind/processor/processor_base.py` 的导入问题，此举暴露了 `registry.py` 的导入错误。
* **2025-07-03**: 已修复 `src/nexusmind/processor/registry.py` 的导入。`tests/processor/test_registry.py` 的错误类型转变为 `ImportError`，因缺少 `get_processor_registry` 函数。同时，`test_api.py` 的错误链指向 `nexus_rag.py`。
* **2025-07-03**: 已在 `registry.py` 中添加 `get_processor_registry` 函数。`test_registry.py` 的错误转移为 `ImportError`，因其试图导入一个不存在的 `register_processor` 函数。
* **2025-07-03**: 已修复 `tests/processor/test_registry.py` 的导入逻辑错误。`pytest` 错误总数减少至 6 个。
* **2025-07-03**: 已修复 `src/nexusmind/rag/nexus_rag.py` 的导入问题。`test_api.py` 的错误链深入，暴露出 `s3_storage.py` 模块丢失的问题。
* **2025-07-03**: 已重新创建并补全 `src/nexusmind/storage/s3_storage.py` 文件。
* **2025-07-03**: 已修复 `src/nexusmind/tasks.py` 的导入问题。`test_api.py` 的错误类型转变为 `ImportError`，因 `main.py` 试图导入一个不存在的 `process_file_task` 函数。
* **2025-07-03**: 已修复 `main.py` 中的导入命名错误。`tests/test_api.py` 的收集时错误已完全解决，`pytest` 错误总数减少至 5 个。
* **2025-07-03**: 已修复 `src/nexusmind/brain/serialization.py` 的导入问题。此举并未完全解决 `brain` 相关的错误，`test_brain.py` 的错误转移为 `ImportError`，因缺少 `BrainVector` 定义。
* **2025-07-03**: 经调查 `06_BRAIN.md`，确认 `BrainVector` 和 `serialize_brain` 并非原始设计的一部分，根源是 `tests/test_brain.py` 的导入和逻辑与实现脱节。
* **2025-07-03**: 已彻底修正 `tests/test_brain.py` 的导入和内部逻辑，并清除了 `serialization.py` 中冗余的代码。`pytest` 错误总数减少至 4 个。
* **2025-07-03**: 已修复 `tests/test_nexus_rag.py` 的导入问题，`pytest` 错误总数减少至 3 个。
* **2025-07-03**: 已修复 `src/nexusmind/storage/local_storage.py` 的导入问题。`test_storage.py` 的收集错误已解决，`pytest` 错误总数减少至 2 个。
* **2025-07-03**: 已修复 `tests/test_vector_store.py` 的导入问题。`pytest` 错误总数减少至 1 个。

---

## 2025-07-05: 从干净状态恢复

### **执行计划**

#### **第一步：修复 `ModuleNotFoundError: No module named 'nexusmind.storage.s3_storage'`**

**问题描述:**
在将代码库重置到一个干净的基线后，`pytest` 报告了 2 个收集时错误。两个错误均由 `ModuleNotFoundError: No module named 'nexusmind.storage.s3_storage'` 引发。

**根本原因分析:**
`git reset` 操作将项目恢复到了一个 `src/nexusmind/storage/s3_storage.py` 文件还未被创建的时间点。由于 `main.py` 和 `tests/test_storage.py` 都依赖于导入这个文件，因此文件的缺失导致了致命的 `ModuleNotFoundError`，中断了测试的收集过程。

**解决方案:**
重新创建 `src/nexusmind/storage/s3_storage.py` 文件，并根据项目的设计文档（`docs/11_PROD_DATA_STORE.md`）为其添加必要的 `S3Storage` 类和 `get_s3_storage` 函数的骨架。

**反馈:**
* **2025-07-05**: 已修复。此举成功解决了所有 `pytest` 收集时错误，使我们能够进入运行时错误的修复阶段。

#### **第二步：修复 `tests/test_llm_endpoint.py` 中的 `NameError`**

**问题描述:**
`pytest` 报告在 `tests/test_llm_endpoint.py` 中有 3 个测试在设置阶段就因 `NameError: name 'CoreConfig' is not defined` 而失败。

**根本原因分析:**
该测试文件中的 `core_config` fixture 直接使用了 `CoreConfig` 类来创建一个实例，但文件顶部忘记了从 `nexusmind.config` 中导入这个类。

**解决方案:**
在 `tests/test_llm_endpoint.py` 文件顶部添加 `from nexusmind.config import CoreConfig`。

**反馈:**
* **2025-07-05**: 已修复。此举成功解决了 `tests/test_llm_endpoint.py` 中的 3 个 `ERROR`，`pytest` 的失败总数减少至 5 个。

#### **第三步：修复 `mock.patch` 中的 `ModuleNotFoundError`**

**问题描述:**
`tests/test_api.py` 中的 `test_async_upload_and_chat` 测试因 `ModuleNotFoundError: No module named 'core'` 而失败。

**根本原因分析:**
该测试内部使用了 `mock.patch('core.nexusmind.llm.llm_endpoint.litellm')`。`mock.patch` 使用的是字符串形式的路径，它不会被开发工具自动重构。在我们将 `core/` 目录重命名为 `src/` 后，这个硬编码的字符串路径没有被更新，导致了错误。

**解决方案:**
将 `mock.patch` 的字符串参数从 `core.nexusmind...` 修改为 `nexusmind...`。

**反馈:**
* **2025-07-05**: 已修复。此举成功解决了 `test_api.py` 中的 `ModuleNotFoundError`，并将故障点推进到了 `main.py` 中的依赖注入环节。

#### **第四步：修复 `S3Storage` 初始化时的 `TypeError`**

**问题描述:**
`tests/test_api.py` 的失败原因转变为 `TypeError: S3Storage.__init__() missing 1 required positional argument: 'config'`。

**根本原因分析:**
错误发生在 FastAPI 的依赖注入环节。`main.py` 中的 `get_s3_storage` 依赖提供者在调用 `S3Storage()` 时没有传递所需的 `config` 参数。

**解决方案:**
重构 `main.py` 中的 `get_s3_storage` 函数，让它依赖于 `get_core_config` 来获取配置实例，并将其作为参数传递给 `S3Storage` 的构造函数。

**反馈:**
* **2025-07-05**: 已修复。此举暴露了更深层次的问题：`TypeError: unhashable type: 'CoreConfig'`。原因是 `@lru_cache` 无法缓存以可变对象（如 Pydantic 模型）为参数的函数。

---

## 2025-07-05: 修复运行时 (Runtime) 错误 (续)

### **执行计划**

#### **第七步：修复 `test_config.py` 中的 `AssertionError`**

**问题描述:**
`tests/test_config.py` 中的 `test_init_without_override` 测试失败，断言 `'gpt-4' == 'gpt-4o'`。

**根本原因分析:**
`src/nexusmind/base_config.py` 中 `CoreConfig` 的默认模型 `llm_model_name` 被硬编码为 "gpt-4"，而测试用例期望的默认值是 "gpt-4o"。这是代码实现与测试期望之间的直接冲突。

**解决方案:**
以测试为准，将 `src/nexusmind/config.py` 中的默认模型修改为 `gpt-4o`，并将默认 `temperature` 修改为 `0.7` 以匹配测试期望。

**反馈:**
* **2025-07-05**: 已修复 `llm_model_name` 的断言错误，但新暴露出 `temperature` 的断言错误 (`assert 0.5 == 0.7`)。修复仍在进行中。

#### **第八步：移除不当的缓存**

**问题描述:**
`
---

## 2025-07-06: 修复运行时 (Runtime) 错误 (续)

**问题描述:**
在修正了 `.gitignore` 问题并能正确追踪 `s3_storage.py` 文件后，`pytest` 现在可以运行，但报告了 4 个新的运行时错误。

### **执行计划**

#### **第一步：修复 `brain.py` 中的 `ModuleNotFoundError`**
**反馈:**
* **2025-07-06**: 已修复。

#### **第二步：修复 `brain.py` 中的 `AttributeError`**
**反馈:**
* **2025-07-06**: 已修复。

#### **第三步：修复 `faiss_vector_store.py` 中的 `NameError`**
**反馈:**
* **2025-07-06**: 已修复。

#### **第四步：修复 `test_llm_endpoint.py` 中的 `NameError`**
**反馈:**
* **2025-07-06**: 已修复。

#### **第五步：修复 `test_api.py` 中的 `TypeError` (由不当缓存引起)**
**反馈:**
* **2025-07-06**: 已修复。

#### **第六步：修复 `S3Storage` 初始化时的 `AttributeError` (错误的配置对象)**
**反馈:**
* **2025-07-06**: 已修复。

#### **第七步：修复 `S3Storage` 中的属性名错误 (错误的属性名)**
**反馈:**
* **2025-07-06**: 已修复。

#### **第八步：修复 `MinioConfig` 中的密钥类型错误 (`str` vs `SecretStr`)**
**反馈:**
* **2025-07-06**: 已修复。

#### **第九步：同步 `S3Storage` 与 `MinioConfig` 的属性名**
**反馈:**
* **2025-07-06**: 已修复。

#### **第十步：修复 `main.py` 中的 `NameError`**
**反馈:**
* **2025-07-06**: 已修复。此举最终暴露出基础设施层面的配置错误。

#### **第十一步：修复数据库连接密码错误**
**反馈:**
* **2025-07-06**: 已尝试修复 `base_config.py`，但该修复并未生效，因为 `database.py` 中创建数据库引擎的代码没有使用这个更新后的配置。

#### **第十二步：使数据库引擎使用动态配置**

**问题:**
尽管 `PostgresConfig` 已被正确更新，但数据库连接依然失败，因为它仍在使用旧的 "user" 用户名。

**根本原因分析:**
问题的真正根源在 `src/nexusmind/database.py`。该文件在创建 SQLAlchemy `engine` 时，使用了一个硬编码的数据库 URL，完全忽略了我们在 `base_config.py` 中精心设置的 `PostgresConfig`。

**解决方案:**
重构 `src/nexusmind/database.py`：
1.  导入 `get_core_config`。
2.  调用 `get_core_config()` 来获取配置实例。
3.  使用 `config.postgres.get_db_url()` 方法来动态生成数据库连接字符串，并用它来创建 `engine`。

**反馈:**
* **2025-07-06**: 已修复。此举成功解决了数据库密码认证失败的问题，但暴露了新的问题：`relation "file" does not exist`。

#### **第十三步：确保测试时创建数据库表**

**问题:**
`test_api.py` 测试失败，日志显示 `sqlalchemy.exc.ProgrammingError: (psycopg2.errors.UndefinedTable) relation "file" does not exist`。

**根本原因分析:**
我们成功连接到了数据库，但数据库是空的。`main.py` 在应用启动时 (`@app.on_event("startup")`) 会调用 `create_db_and_tables`，但 `pytest` 使用的 `TestClient` 默认不会触发应用的生命周期（startup/shutdown）事件，因此该函数从未被执行。

**上次失败的尝试与教训:**
我们之前试图通过引入一个复杂的、使用独立测试数据库的 `conftest.py` fixture 来解决这个问题。这个方案过于庞大和激进，它：
1.  做出了不当的假设（如数据库密码），导致了新的连接错误。
2.  影响了所有测试，造成了大规模的失败，违反了"一次只解决一个问题"的原则。
3.  偏离了小步快跑、逐步修复的策略。
**今后的修改将严格遵循小步迭代的原则，避免进行大规模的结构性改动。**

**新的解决方案 (最小化修改):**
修改 `tests/test_api.py` 中现有的 `api_client` fixture。通过将 `TestClient` 的实例化方式从 `TestClient(app)` 改为在 `with` 语句中使用 (`with TestClient(app) as client: yield client`)，我们可以指示 `pytest` 正确地处理 FastAPI 应用的生命周期事件，从而确保 `create_db_and_tables` 在测试运行前被调用。这是一个目标明确、影响范围最小的修复方案。

**反馈:**
* **2025-07-06**: 已修复。此举成功解决了数据库密码认证失败的问题，但暴露了新的问题：`relation "file" does not exist`。

#### **第十四步：修复启动逻辑中的依赖注入错误**

**问题:**
`tests/test_api.py` 在测试设置阶段就失败了，错误是 `AttributeError: 'Depends' object has no attribute 'minio'`。

**根本原因分析:**
我们上一步的修复是正确的，`startup` 事件被成功触发。但该事件的处理函数 `on_startup` 内部直接调用了 `get_s3_storage()`。`get_s3_storage` 是一个 FastAPI 依赖项，它期望 FastAPI 框架来为其提供 `config` 参数。在 `startup` 事件这种上下文之外被直接调用时，它的 `config` 参数没有被正确注入，导致了错误。

**解决方案 (最小化修改):**
修改 `main.py` 中的 `on_startup` 函数。我们将不再直接调用依赖项 `get_s3_storage()`，而是手动执行与它相同的逻辑：
1.  调用 `get_core_config()` 来获取配置对象。
2.  使用返回的 `config.minio` 来直接实例化 `S3Storage`。
3.  调用实例上的 `_create_bucket_if_not_exists()` 方法。
这会绕过错误的依赖注入调用，同时保持原有功能不变。

**反馈:**
* **2025-07-06**: 已修复。此举成功解决了应用启动过程中的 `AttributeError`，使 `test_api.py` 中的 2 个测试转为通过，并将失败推进到了 `/upload` 端点的核心逻辑中。

#### **第十五步：在 S3Storage 中实现文件保存逻辑**

**问题:**
`test_async_upload_and_chat` 测试失败，API 返回 500 错误，日志显示 `NotNullViolation`，因为 `s3_path` 为空。

**根本原因分析:**
在 `/upload` 端点中，`storage.save(content, file.filename)` 被调用，但它返回了 `None`。这是因为 `src/nexusmind/storage/s3_storage.py` 文件中的 `save` 方法只是一个空的 `pass` 占位符，没有实际的文件上传逻辑，也没有返回值。

**解决方案 (最小化修改):**
修改 `src/nexusmind/storage/s3_storage.py` 文件中的 `save` 方法：
1.  调用 `self.s3_client.put_object()` 将 `content` 上传到 S3。
2.  使用 `self.config.bucket`作为存储桶名称，`file_path` 作为对象的键（Key）。
3.  在上传成功后，返回 `file_path`。

**反馈:**
* **2025-07-06**: 待执行。
