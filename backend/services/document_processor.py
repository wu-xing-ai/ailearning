"""
文档处理服务 - 提取各类文件内容
"""
import io
from typing import Tuple


class DocumentProcessor:
    """文档内容提取器"""

    SUPPORTED_TYPES = {
        'pdf': ['application/pdf'],
        'docx': ['application/vnd.openxmlformats-officedocument.wordprocessingml.document'],
        'txt': ['text/plain'],
        'md': ['text/markdown', 'text/plain'],
        'xlsx': ['application/vnd.openxmlformats-officedocument.spreadsheetml.sheet']
    }

    @classmethod
    def get_file_type(cls, filename: str) -> str:
        """根据文件名获取文件类型"""
        ext = filename.lower().split('.')[-1] if '.' in filename else ''
        return ext if ext in cls.SUPPORTED_TYPES else 'unknown'

    @classmethod
    def extract_content(cls, file_content: bytes, file_type: str, filename: str) -> Tuple[str, str]:
        """
        提取文件内容

        Args:
            file_content: 文件二进制内容
            file_type: 文件类型 (pdf/docx/txt/md/xlsx)
            filename: 文件名

        Returns:
            Tuple[str, str]: (提取的文本内容, 文件类型名称)
        """
        extractors = {
            'pdf': cls._extract_pdf,
            'docx': cls._extract_docx,
            'txt': cls._extract_txt,
            'md': cls._extract_txt,  # md文件用txt方式处理
            'xlsx': cls._extract_xlsx
        }

        extractor = extractors.get(file_type)
        if not extractor:
            raise ValueError(f"不支持的文件类型: {file_type}")

        content = extractor(file_content)
        type_names = {
            'pdf': 'PDF',
            'docx': 'DOCX',
            'txt': 'TXT',
            'md': 'MD',
            'xlsx': 'XLSX'
        }
        return content, type_names.get(file_type, file_type.upper())

    @staticmethod
    def _extract_pdf(content: bytes) -> str:
        """提取PDF内容"""
        import pdfplumber

        text_parts = []
        with pdfplumber.open(io.BytesIO(content)) as pdf:
            for page in pdf.pages:
                text = page.extract_text()
                if text:
                    text_parts.append(text)
        return '\n\n'.join(text_parts)

    @staticmethod
    def _extract_docx(content: bytes) -> str:
        """提取DOCX内容"""
        from docx import Document

        doc = Document(io.BytesIO(content))
        return '\n'.join([para.text for para in doc.paragraphs if para.text])

    @staticmethod
    def _extract_txt(content: bytes) -> str:
        """提取TXT/MD内容"""
        # 尝试多种编码
        for encoding in ['utf-8', 'gbk', 'gb2312']:
            try:
                return content.decode(encoding)
            except UnicodeDecodeError:
                continue
        return content.decode('utf-8', errors='ignore')

    @staticmethod
    def _extract_xlsx(content: bytes) -> str:
        """提取XLSX内容"""
        import pandas as pd

        df_dict = pd.read_excel(io.BytesIO(content), sheet_name=None)
        text_parts = []
        for sheet_name, sheet_df in df_dict.items():
            text_parts.append(f"=== 工作表: {sheet_name} ===")
            text_parts.append(sheet_df.to_string())
        return '\n\n'.join(text_parts)
