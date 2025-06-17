import os
import logging
from pathlib import Path
from typing import List

from .parsers import FileParser
from .models import ChunkingSettings, ParserType, ChunkingStrategy

# 配置日志
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def create_test_file(file_path: str, content: str) -> None:
    """创建测试文件"""
    with open(file_path, 'w', encoding='utf-8') as f:
        f.write(content)
    logger.info(f"已创建测试文件: {file_path}")

def print_chunk_info(chunks: List[dict], chunk_index: int) -> None:
    """打印分块信息"""
    chunk = chunks[chunk_index]
    print(f"\n分块 #{chunk_index + 1}:")
    print("-" * 50)
    print(f"内容: {chunk.page_content}")
    print(f"元数据: {chunk.metadata}")
    print("-" * 50)

def run_mvp1_test():
    """运行MVP1测试：文档导入与分块"""
    logger.info("--- 开始 MVP1 测试：文档导入与分块 ---")

    # 1. 创建测试文件
    file_name = "sample.txt"
    sample_content = """
NexusMind是一个强大的知识管理系统，它利用先进的AI技术来帮助用户管理和检索信息。
这个系统支持多种文件格式，包括PDF、TXT、Markdown等。
通过智能的分块和检索机制，NexusMind能够提供精准的信息检索服务。
系统采用模块化设计，每个组件都可以独立扩展和优化。
我们正在构建这个系统，从最基础的文件处理开始。
"""
    create_test_file(file_name, sample_content)

    try:
        # 2. 配置不同的测试场景
        test_scenarios = [
            {
                "name": "默认配置测试",
                "settings": ChunkingSettings()
            },
            {
                "name": "快速分块测试",
                "settings": ChunkingSettings(
                    chunk_size=100,
                    chunk_overlap=20,
                    strategy=ChunkingStrategy.FAST
                )
            },
            {
                "name": "高精度分块测试",
                "settings": ChunkingSettings(
                    chunk_size=100,
                    chunk_overlap=30,
                    strategy=ChunkingStrategy.HI_RES
                )
            }
        ]

        # 3. 运行每个测试场景
        for scenario in test_scenarios:
            logger.info(f"\n执行测试场景: {scenario['name']}")
            
            # 初始化解析器
            parser = FileParser(chunking_settings=scenario['settings'])
            
            # 解析文件
            processed_doc = parser.parse_file(file_name)
            
            # 打印结果
            logger.info(f"文件解析成功！总共获得 {len(processed_doc.chunks)} 个分块。")
            
            # 打印每个分块的信息
            for i in range(len(processed_doc.chunks)):
                print_chunk_info(processed_doc.chunks, i)

    except Exception as e:
        logger.error(f"测试过程中出现错误: {e}")

    finally:
        # 4. 清理测试文件
        if os.path.exists(file_name):
            os.remove(file_name)
            logger.info(f"已清理测试文件: {file_name}")

if __name__ == "__main__":
    run_mvp1_test() 