#!/usr/bin/env python3
"""
搜索管理器
"""

from typing import Dict, List, Optional, Any
from .openalex_searcher import OpenAlexSearcher
from .arxiv_searcher import ArxivSearcher


class SearchManager:
    """搜索管理器"""

    def __init__(self, config: Optional[Dict[str, Any]] = None):
        """
        初始化搜索管理器

        Args:
            config: 配置字典
        """
        self.config = config or {}
        self._searchers = {}

        # 注册搜索器
        self._register_searchers()

    def _register_searchers(self):
        """注册搜索器"""
        search_config = self.config.get('search', {})

        # OpenAlex
        if 'openalex' in search_config or True:
            self._searchers['openalex'] = OpenAlexSearcher(
                search_config.get('openalex', {})
            )

        # arXiv
        if 'arxiv' in search_config or True:
            self._searchers['arxiv'] = ArxivSearcher(
                search_config.get('arxiv', {})
            )

    def search(
        self,
        query: str,
        sources: Optional[List[str]] = None,
        max_results: int = 100,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        搜索文献

        Args:
            query: 搜索关键词
            sources: 搜索源列表
            max_results: 每个源的最大结果数
            filters: 过滤条件

        Returns:
            文献列表
        """
        if sources is None:
            sources = self.config.get('search', {}).get('default_sources', ['openalex', 'arxiv'])

        all_papers = []
        seen_dois = set()
        seen_titles = set()

        for source in sources:
            if source not in self._searchers:
                print(f"Unknown source: {source}")
                continue

            searcher = self._searchers[source]
            print(f"Searching {searcher.get_source_name()}...")

            try:
                papers = searcher.search(query, max_results, filters)

                # 去重
                for paper in papers:
                    doi = paper.get('doi', '')
                    title = paper.get('title', '').lower().strip()

                    # 基于 DOI 去重
                    if doi and doi in seen_dois:
                        continue

                    # 基于标题去重
                    if title and title in seen_titles:
                        continue

                    if doi:
                        seen_dois.add(doi)
                    if title:
                        seen_titles.add(title)

                    all_papers.append(paper)

                print(f"  Found {len(papers)} papers from {searcher.get_source_name()}")

            except Exception as e:
                print(f"Error searching {source}: {e}")

        print(f"\nTotal unique papers: {len(all_papers)}")
        return all_papers

    def search_multiple_queries(
        self,
        queries: List[str],
        sources: Optional[List[str]] = None,
        max_per_query: int = 100,
        max_total: int = 1000,
        filters: Optional[Dict[str, Any]] = None
    ) -> List[Dict[str, Any]]:
        """
        多关键词搜索

        Args:
            queries: 关键词列表
            sources: 搜索源列表
            max_per_query: 每个关键词的最大结果数
            max_total: 最大总结果数
            filters: 过滤条件

        Returns:
            文献列表
        """
        all_papers = []
        seen_dois = set()
        seen_titles = set()

        for i, query in enumerate(queries):
            print(f"\n[{i+1}/{len(queries)}] Searching: {query}")

            papers = self.search(query, sources, max_per_query, filters)

            # 去重
            for paper in papers:
                doi = paper.get('doi', '')
                title = paper.get('title', '').lower().strip()

                if doi and doi in seen_dois:
                    continue
                if title and title in seen_titles:
                    continue

                if doi:
                    seen_dois.add(doi)
                if title:
                    seen_titles.add(title)

                all_papers.append(paper)

            if len(all_papers) >= max_total:
                break

        return all_papers[:max_total]
