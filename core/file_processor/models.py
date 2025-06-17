from dataclasses import dataclass
from typing import List, Optional, Dict, Any
from enum import Enum
from langchain_core.documents import Document

class ParserType(str, Enum):
    """解析器类型枚举"""
    UNSTRUCTURED = "unstructured"  # 非结构化解析
    LLAMA_PARSER = "llama_parser"  # Llama解析器
    MEGAPARSE_VISION = "megaparse_vision"  # 视觉解析器

class ChunkingStrategy(str, Enum):
    """分块策略枚举"""
    FAST = "fast"  # 快速分块
    AUTO = "auto"  # 自动分块
    HI_RES = "hi_res"  # 高精度分块

@dataclass
class ChunkingSettings:
    """配置文档分块的设置"""
    chunk_size: int = 1000  # 每个块的大小
    chunk_overlap: int = 200  # 块之间的重叠大小
    separator: str = "\n"  # 用于分割文本的分隔符
    parser_type: ParserType = ParserType.UNSTRUCTURED  # 解析器类型
    strategy: ChunkingStrategy = ChunkingStrategy.AUTO  # 分块策略
    check_table: bool = False  # 是否检查表格
    parsing_instruction: Optional[str] = None  # 解析指令
    model_name: str = "gpt-4"  # 使用的模型名称

@dataclass
class ProcessedDocument:
    """处理后的文档，包含分块和元数据"""
    chunks: List[Document]  # 文档分块列表
    metadata: Dict[str, Any]  # 文档元数据
    original_filename: str  # 原始文件名
    file_extension: str  # 文件扩展名
    
    def __post_init__(self):
        # 为每个块添加元数据
        for idx, chunk in enumerate(self.chunks, start=1):
            chunk.metadata.update({
                "chunk_index": idx,
                "original_filename": self.original_filename,
                "file_extension": self.file_extension,
                **self.metadata
            })
