#!/usr/bin/env python3
"""
arXiv 搜索器
"""

import time
import urllib.parse
import xml.etree.ElementTree as ET
import requests
from typing import Dict, List, Optional, Any
from .base import BaseSearcher


class ArxivSearcher(BaseSearcher):
    """arXiv 搜索器"""

    BASE_URL = "http://export.arxiv.org/api/query"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.max_results = self.config.get('max_results', 100)
        self.sort_by = self.config.get('sort_by', 'submittedDate')
        self.sort_order = self.config.get('sort_order', 'descending')
        self.request_delay = self.config.get('request_delay', 0.5)

    def get_source_name(self) -> str:
        return "arXiv"

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
        papers = []
        start = 0
        batch_size = min(100, max_results)

        # 映射排序字段
        sort_map = {
            'submittedDate': 'submittedDate',
            'updatedDate': 'lastUpdatedDate',
            'relevance': 'relevance',
        }
        sort_by = sort_map.get(self.sort_by, 'relevance')

        while len(papers) < max_results:
            # 构建查询
            search_query = f"all:{urllib.parse.quote(query)}"

            params = {
                'search_query': search_query,
                'start': start,
                'max_results': batch_size,
                'sortBy': sort_by,
                'sortOrder': self.sort_order,
            }

            try:
                response = requests.get(
                    self.BASE_URL,
                    params=params,
                    timeout=30
                )
                response.raise_for_status()

                # 解析 XML
                root = ET.fromstring(response.content)

                # 定义命名空间
                ns = {
                    'atom': 'http://www.w3.org/2005/Atom',
                    'arxiv': 'http://arxiv.org/schemas/atom',
                }

                entries = root.findall('atom:entry', ns)
                if not entries:
                    break

                for entry in entries:
                    if len(papers) >= max_results:
                        break

                    paper = self._parse_entry(entry, ns)
                    papers.append(paper)

                if len(entries) < batch_size:
                    break

                start += batch_size
                time.sleep(self.request_delay)

            except Exception as e:
                print(f"arXiv search error: {e}")
                break

        return papers

    def _parse_entry(self, entry, ns: Dict[str, str]) -> Dict[str, Any]:
        """解析 arXiv entry"""
        # 提取标题
        title_elem = entry.find('atom:title', ns)
        title = title_elem.text.strip() if title_elem is not None and title_elem.text else ''

        # 提取作者
        authors = []
        for author in entry.findall('atom:author', ns):
            name_elem = author.find('atom:name', ns)
            if name_elem is not None and name_elem.text:
                authors.append(name_elem.text)

        # 提取摘要
        summary_elem = entry.find('atom:summary', ns)
        abstract = summary_elem.text.strip() if summary_elem is not None and summary_elem.text else ''

        # 提取发布日期
        published_elem = entry.find('atom:published', ns)
        year = None
        if published_elem is not None and published_elem.text:
            year = int(published_elem.text[:4])

        # 提取 arXiv ID
        id_elem = entry.find('atom:id', ns)
        arxiv_id = ''
        if id_elem is not None and id_elem.text:
            arxiv_id = id_elem.text.split('/')[-1]

        # 提取 PDF 链接
        pdf_url = ''
        for link in entry.findall('atom:link', ns):
            if link.get('title') == 'pdf':
                pdf_url = link.get('href', '')
                break

        if not pdf_url and arxiv_id:
            pdf_url = f"https://arxiv.org/pdf/{arxiv_id}.pdf"

        # 提取 DOI
        doi = ''
        doi_elem = entry.find('arxiv:doi', ns)
        if doi_elem is not None and doi_elem.text:
            doi = doi_elem.text

        # 提取分类/关键词
        keywords = []
        for category in entry.findall('atom:category', ns):
            term = category.get('term', '')
            if term:
                keywords.append(term)

        return self._normalize_paper({
            'title': title,
            'authors': '; '.join(authors[:10]),
            'year': year,
            'journal': 'arXiv',
            'doi': doi,
            'url': f"https://arxiv.org/abs/{arxiv_id}" if arxiv_id else '',
            'pdf_url': pdf_url,
            'abstract': abstract,
            'citations': 0,  # arXiv 没有引用数据
            'keywords': '; '.join(keywords),
            'is_oa': True,
            'oa_status': 'green',
            'institution': '',
            'language': 'en',
            'document_type': 'preprint',
        })
