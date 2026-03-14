#!/usr/bin/env python3
"""
搜索器基类
"""

from abc import ABC, abstractmethod
from typing import Dict, List, Optional, Any


class BaseSearcher(ABC):
    """搜索器基类"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化搜索器

        Args:
            config: 配置字典
        """
        self.config = config or {}

    @abstractmethod
    def search(
        self,
        query: str,
        max_results: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索文献

        Args:
            query: 搜索关键词
            max_results: 最大结果数
            filters: 过滤条件

        Returns:
            文献列表
        """
        pass

    @abstractmethod
    def get_source_name(self) -> str:
        """
        获取数据源名称

        Returns:
            数据源名称
        """
        pass

    def _normalize_paper(self, paper: Dict[str, Any]) -> Dict[str, Any]:
        """
        标准化文献数据

        Args:
            paper: 原始文献数据

        Returns:
            标准化后的文献数据
        """
        return {
            'title': paper.get('title', ''),
            'authors': paper.get('authors', []),
            'year': paper.get('year'),
            'journal': paper.get('journal', ''),
            'doi': paper.get('doi', ''),
            'url': paper.get('url', ''),
            'pdf_url': paper.get('pdf_url', ''),
            'abstract': paper.get('abstract', ''),
            'citations': paper.get('citations', 0),
            'keywords': paper.get('keywords', []),
            'source': self.get_source_name(),
            'is_oa': paper.get('is_oa', False),
            'oa_status': paper.get('oa_status', ''),
            'institution': paper.get('institution', ''),
            'language': paper.get('language', 'en'),
            'document_type': paper.get('document_type', 'article'),
        }
