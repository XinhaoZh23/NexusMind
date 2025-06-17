import os
import logging
from typing import List, Optional, Dict, Any
from pathlib import Path

from langchain.text_splitter import RecursiveCharacterTextSplitter
from langchain_core.documents import Document

from .models import ChunkingSettings, ProcessedDocument, ParserType, ChunkingStrategy

logger = logging.getLogger(__name__)

class FileParser:
    """文件解析器，负责读取和分块不同类型的文件"""
    
    def __init__(self, chunking_settings: Optional[ChunkingSettings] = None):
        """
        初始化文件解析器
        
        Args:
            chunking_settings: 分块设置，如果为None则使用默认设置
        """
        self.chunking_settings = chunking_settings or ChunkingSettings()
        
        # 初始化文本分割器
        self.text_splitter = RecursiveCharacterTextSplitter(
            chunk_size=self.chunking_settings.chunk_size,
            chunk_overlap=self.chunking_settings.chunk_overlap,
            separators=[self.chunking_settings.separator, "\n\n", "\n", " ", ""]
        )
        
        # 文件类型处理器映射
        self._parser_handlers = {
            ParserType.UNSTRUCTURED: self._parse_unstructured,
            ParserType.LLAMA_PARSER: self._parse_llama,
            ParserType.MEGAPARSE_VISION: self._parse_vision
        }

    def parse_file(self, file_path: str) -> ProcessedDocument:
        """
        解析文件并返回处理后的文档
        
        Args:
            file_path: 文件路径
            
        Returns:
            ProcessedDocument: 包含分块和元数据的处理文档
        """
        if not os.path.exists(file_path):
            raise FileNotFoundError(f"文件未找到: {file_path}")
            
        file_path = Path(file_path)
        file_extension = file_path.suffix.lower()
        
        # 获取对应的解析器处理函数
        parser_handler = self._parser_handlers.get(
            self.chunking_settings.parser_type,
            self._parse_unstructured
        )
        
        # 解析文件内容
        content = parser_handler(file_path)
        
        # 根据策略进行分块
        if self.chunking_settings.strategy == ChunkingStrategy.FAST:
            chunks = self._fast_chunking(content)
        elif self.chunking_settings.strategy == ChunkingStrategy.HI_RES:
            chunks = self._hi_res_chunking(content)
        else:  # AUTO
            chunks = self._auto_chunking(content)
            
        # 创建处理后的文档
        return ProcessedDocument(
            chunks=chunks,
            metadata=self._get_file_metadata(file_path),
            original_filename=file_path.name,
            file_extension=file_extension
        )

    def _parse_unstructured(self, file_path: Path) -> str:
        """使用非结构化方式解析文件"""
        try:
            with open(file_path, 'r', encoding='utf-8') as f:
                return f.read()
        except UnicodeDecodeError:
            # 如果UTF-8解码失败，尝试其他编码
            with open(file_path, 'r', encoding='latin-1') as f:
                return f.read()

    def _parse_llama(self, file_path: Path) -> str:
        """使用Llama解析器解析文件"""
        # TODO: 实现Llama解析器
        return self._parse_unstructured(file_path)

    def _parse_vision(self, file_path: Path) -> str:
        """使用视觉解析器解析文件"""
        # TODO: 实现视觉解析器
        return self._parse_unstructured(file_path)

    def _fast_chunking(self, content: str) -> List[Document]:
        """快速分块策略"""
        chunks = self.text_splitter.split_text(content)
        return [Document(page_content=chunk) for chunk in chunks]

    def _hi_res_chunking(self, content: str) -> List[Document]:
        """高精度分块策略
        通过以下方式实现高精度：
        1. 使用更细粒度的分隔符
        2. 增加重叠比例
        3. 保持合理的块大小以维持语义完整性
        """
        # 使用更细粒度的分隔符，按优先级排序
        separators = [
            "\n\n",     # 段落分隔（最高优先级）
            "。\n",     # 中文句号+换行
            "！\n",     # 中文感叹号+换行
            "？\n",     # 中文问号+换行
            "；\n",     # 中文分号+换行
            ".\n",      # 英文句号+换行
            "!\n",      # 英文感叹号+换行
            "?\n",      # 英文问号+换行
            ";\n",      # 英文分号+换行
            "。",       # 中文句号
            "！",       # 中文感叹号
            "？",       # 中文问号
            "；",       # 中文分号
            ". ",       # 英文句号+空格
            "! ",       # 英文感叹号+空格
            "? ",       # 英文问号+空格
            "; ",       # 英文分号+空格
            "\n",       # 换行
            " ",        # 空格
            ""          # 字符（最低优先级）
        ]
        
        # 计算重叠大小，确保不超过块大小的30%
        chunk_size = self.chunking_settings.chunk_size
        max_overlap = int(chunk_size * 0.3)  # 降低最大重叠比例到30%
        chunk_overlap = min(
            self.chunking_settings.chunk_overlap * 2,
            max_overlap
        )
        
        # 创建高精度分块器
        splitter = RecursiveCharacterTextSplitter(
            chunk_size=chunk_size,
            chunk_overlap=chunk_overlap,
            separators=separators,
            length_function=len,
            is_separator_regex=False
        )
        
        # 执行分块
        chunks = splitter.split_text(content)
        
        # 后处理：清理和优化分块
        processed_chunks = []
        for i, chunk in enumerate(chunks):
            # 清理空白字符
            chunk = chunk.strip()
            
            # 移除开头的标点符号
            while chunk and chunk[0] in "。！？；.!?;":
                chunk = chunk[1:].strip()
            
            # 移除结尾的标点符号
            while chunk and chunk[-1] in "。！？；.!?;":
                chunk = chunk[:-1].strip()
            
            # 如果不是最后一个块，确保以句号结尾
            if i < len(chunks) - 1 and chunk and not chunk.endswith("。"):
                chunk += "。"
            
            # 移除重复的内容（如果当前块的开头与上一个块的结尾相同）
            if processed_chunks and chunk:
                last_chunk = processed_chunks[-1].page_content
                if chunk.startswith(last_chunk.split("。")[-1].strip()):
                    chunk = chunk[len(last_chunk.split("。")[-1].strip()):].strip()
            
            if chunk:  # 只保留非空块
                processed_chunks.append(Document(page_content=chunk))
        
        return processed_chunks

    def _auto_chunking(self, content: str) -> List[Document]:
        """自动分块策略"""
        # 根据内容长度自动选择分块策略
        if len(content) > 100000:  # 如果内容很长，使用快速分块
            return self._fast_chunking(content)
        return self._hi_res_chunking(content)

    def _get_file_metadata(self, file_path: Path) -> Dict[str, Any]:
        """获取文件元数据"""
        return {
            "file_size": os.path.getsize(file_path),
            "created_time": os.path.getctime(file_path),
            "modified_time": os.path.getmtime(file_path),
            "parser_type": self.chunking_settings.parser_type.value,
            "chunking_strategy": self.chunking_settings.strategy.value
        } 