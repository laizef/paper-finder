#!/usr/bin/env python3
"""
OpenAlex 搜索器
"""

import time
import requests
from typing import Dict, List, Optional, Any
from .base import BaseSearcher


class OpenAlexSearcher(BaseSearcher):
    """OpenAlex 搜索器"""

    BASE_URL = "https://api.openalex.org"

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        super().__init__(config)
        self.api_key = self.config.get('api_key')
        self.email = self.config.get('email')
        self.max_results = self.config.get('max_results', 1000)
        self.sort_by = self.config.get('sort_by', 'cited_by_count:desc')
        self.request_delay = self.config.get('request_delay', 0.1)

    def get_source_name(self) -> str:
        return "OpenAlex"

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
        cursor = '*'
        per_page = min(200, max_results)

        headers = {}
        if self.api_key:
            headers['Authorization'] = f'Bearer {self.api_key}'
        if self.email:
            headers['mailto'] = self.email

        while len(papers) < max_results:
            # 构建查询参数
            params = {
                'search': query,
                'per_page': per_page,
                'cursor': cursor,
                'sort': self.sort_by,
            }

            # 添加过滤条件
            filter_parts = []
            if filters:
                if 'from_publication_date' in filters:
                    filter_parts.append(f"from_publication_date:{filters['from_publication_date']}")
                if 'to_publication_date' in filters:
                    filter_parts.append(f"to_publication_date:{filters['to_publication_date']}")
                if 'publication_year' in filters:
                    filter_parts.append(f"publication_year:{filters['publication_year']}")
                if 'cited_by_count' in filters:
                    filter_parts.append(f"cited_by_count:{filters['cited_by_count']}")
                if 'is_oa' in filters:
                    filter_parts.append(f"is_oa:{filters['is_oa']}")

            if filter_parts:
                params['filter'] = ','.join(filter_parts)

            try:
                response = requests.get(
                    f"{self.BASE_URL}/works",
                    params=params,
                    headers=headers,
                    timeout=30
                )
                response.raise_for_status()
                data = response.json()

                results = data.get('results', [])
                if not results:
                    break

                for work in results:
                    if len(papers) >= max_results:
                        break

                    paper = self._parse_work(work)
                    papers.append(paper)

                # 获取下一页游标
                next_cursor = data.get('meta', {}).get('next_cursor')
                if not next_cursor:
                    break
                cursor = next_cursor

                # 延迟
                time.sleep(self.request_delay)

            except Exception as e:
                print(f"OpenAlex search error: {e}")
                break

        return papers

    def _parse_work(self, work: Dict[str, Any]) -> Dict[str, Any]:
        """解析 OpenAlex work 数据"""
        # 提取作者
        authors = []
        for authorship in work.get('authorships', []):
            author = authorship.get('author', {})
            authors.append(author.get('display_name', ''))

        # 提取期刊
        source = work.get('primary_location', {}) or {}
        source_info = source.get('source', {}) or {}
        journal = source_info.get('display_name', '')

        # 提取 DOI
        doi = work.get('doi', '') or ''
        if doi:
            doi = doi.replace('https://doi.org/', '')

        # 提取 PDF URL
        pdf_url = ''
        oa = work.get('open_access', {}) or {}
        if oa.get('is_oa'):
            pdf_url = oa.get('oa_url', '')

        # 提取机构
        institutions = set()
        for authorship in work.get('authorships', []):
            for inst in authorship.get('institutions', []):
                if inst:
                    institutions.add(inst.get('display_name', ''))
        institution = '; '.join(list(institutions)[:3])

        # 提取关键词
        keywords = []
        for concept in work.get('concepts', [])[:5]:
            if concept.get('score', 0) > 0.3:
                keywords.append(concept.get('display_name', ''))

        return self._normalize_paper({
            'title': work.get('title', ''),
            'authors': '; '.join(authors[:10]),
            'year': work.get('publication_year'),
            'journal': journal,
            'doi': doi,
            'url': work.get('id', ''),
            'pdf_url': pdf_url,
            'abstract': work.get('abstract_inverted_index') or '',
            'citations': work.get('cited_by_count', 0),
            'keywords': '; '.join(keywords),
            'is_oa': oa.get('is_oa', False),
            'oa_status': oa.get('oa_status', ''),
            'institution': institution,
            'language': work.get('language', 'en'),
            'document_type': work.get('type', 'article'),
        })
