#!/usr/bin/env python3
"""
多源下载器
"""

import os
import re
import time
import requests
from pathlib import Path
from typing import Dict, List, Optional, Any, Callable
from concurrent.futures import ThreadPoolExecutor, as_completed
from bs4 import BeautifulSoup


class MultiSourceDownloader:
    """多源下载器"""

    def __init__(
        self,
        config: Optional[Dict[str, Any]] = None,
        filename_generator: Optional[Callable] = None
    ):
        """
        初始化下载器

        Args:
            config: 配置字典
            filename_generator: 文件名生成函数
        """
        self.config = config or {}
        self.filename_generator = filename_generator

        # 配置
        self.output_dir = Path(self.config.get('output_dir', './output/papers'))
        self.output_dir.mkdir(parents=True, exist_ok=True)

        self.sources_priority = self.config.get('sources_priority', [
            'direct_url', 'unpaywall', 'semantic_scholar', 'arxiv', 'pmc', 'scihub'
        ])

        self.unpaywall_email = self.config.get('unpaywall_email')
        self.scihub_domains = self.config.get('scihub_domains', ['https://sci-hub.se/'])
        self.scihub_enabled = self.config.get('scihub_enabled', True)

        self.max_workers = self.config.get('max_workers', 5)
        self.timeout = self.config.get('timeout', 60)
        self.max_retries = self.config.get('max_retries', 3)
        self.skip_existing = self.config.get('skip_existing', True)
        self.save_failed = self.config.get('save_failed', True)
        self.strict_pdf_check = self.config.get('strict_pdf_check', False)

        # 代理
        proxy_config = self.config.get('proxy')
        self.proxies = None
        if proxy_config and proxy_config.get('enabled'):
            self.proxies = {
                'http': proxy_config.get('http'),
                'https': proxy_config.get('https'),
            }

        # 请求头
        self.headers = {
            'User-Agent': 'Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/120.0.0.0 Safari/537.36',
            'Accept': 'application/pdf,text/html,*/*',
        }

    def download_batch(
        self,
        papers: List[Dict[str, Any]],
        max_workers: Optional[int] = None
    ) -> Dict[str, Any]:
        """
        批量下载

        Args:
            papers: 文献列表
            max_workers: 并发数

        Returns:
            下载统计
        """
        workers = max_workers or self.max_workers

        stats = {
            'total': len(papers),
            'success': 0,
            'failed': 0,
            'skipped': 0,
            'results': []
        }

        print(f"\nStarting download of {len(papers)} papers...")
        print(f"Workers: {workers}, Timeout: {self.timeout}s")

        with ThreadPoolExecutor(max_workers=workers) as executor:
            futures = {}

            for i, paper in enumerate(papers):
                future = executor.submit(
                    self._download_paper_with_retry,
                    paper,
                    i + 1,
                    len(papers)
                )
                futures[future] = paper

            for future in as_completed(futures):
                paper = futures[future]
                try:
                    result = future.result()
                    stats['results'].append(result)

                    if result['status'] == 'success':
                        stats['success'] += 1
                    elif result['status'] == 'skipped':
                        stats['skipped'] += 1
                    else:
                        stats['failed'] += 1

                except Exception as e:
                    stats['failed'] += 1
                    stats['results'].append({
                        'title': paper.get('title', ''),
                        'status': 'error',
                        'error': str(e)
                    })

        self._print_stats(stats)
        return stats

    def _download_paper_with_retry(
        self,
        paper: Dict[str, Any],
        index: int,
        total: int
    ) -> Dict[str, Any]:
        """带重试的下载"""
        title = paper.get('title', 'Unknown')[:50]

        # 生成文件名
        if self.filename_generator:
            filename = self.filename_generator(paper)
        else:
            filename = self._generate_filename(paper)

        filepath = self.output_dir / f"{filename}.pdf"

        # 检查是否已存在
        if self.skip_existing and filepath.exists():
            return {
                'title': paper.get('title', ''),
                'filename': filename,
                'status': 'skipped',
                'reason': 'File already exists'
            }

        # 尝试下载
        for attempt in range(self.max_retries):
            result = self._try_download_from_sources(paper, filepath)

            if result['status'] == 'success':
                print(f"[{index}/{total}] [OK] {title}")
                return result

            time.sleep(1)

        print(f"[{index}/{total}] [FAIL] {title}")
        return result

    def _try_download_from_sources(
        self,
        paper: Dict[str, Any],
        filepath: Path
    ) -> Dict[str, Any]:
        """从多个源尝试下载"""
        doi = paper.get('doi', '')
        pdf_url = paper.get('pdf_url', '')
        title = paper.get('title', '')

        for source in self.sources_priority:
            try:
                if source == 'direct_url' and pdf_url:
                    result = self._download_from_url(pdf_url, filepath)
                    if result:
                        return {'title': title, 'filename': filepath.stem, 'status': 'success', 'source': 'direct_url'}

                elif source == 'unpaywall' and doi:
                    result = self._download_from_unpaywall(doi, filepath)
                    if result:
                        return {'title': title, 'filename': filepath.stem, 'status': 'success', 'source': 'unpaywall'}

                elif source == 'arxiv' and 'arxiv' in paper.get('source', '').lower():
                    result = self._download_from_arxiv(doi or title, filepath)
                    if result:
                        return {'title': title, 'filename': filepath.stem, 'status': 'success', 'source': 'arxiv'}

                elif source == 'pmc' and doi:
                    result = self._download_from_pmc(doi, filepath)
                    if result:
                        return {'title': title, 'filename': filepath.stem, 'status': 'success', 'source': 'pmc'}

                elif source == 'scihub' and self.scihub_enabled and doi:
                    result = self._download_from_scihub(doi, filepath)
                    if result:
                        return {'title': title, 'filename': filepath.stem, 'status': 'success', 'source': 'scihub'}

            except Exception as e:
                continue

        return {'title': title, 'filename': filepath.stem, 'status': 'failed', 'error': 'All sources failed'}

    def _download_from_url(self, url: str, filepath: Path) -> bool:
        """从 URL 下载"""
        try:
            response = requests.get(
                url,
                headers=self.headers,
                timeout=self.timeout,
                proxies=self.proxies,
                stream=True
            )

            if response.status_code == 200:
                content_type = response.headers.get('Content-Type', '')
                if 'pdf' in content_type.lower() or not self.strict_pdf_check:
                    with open(filepath, 'wb') as f:
                        for chunk in response.iter_content(chunk_size=8192):
                            f.write(chunk)

                    if self._is_valid_pdf(filepath):
                        return True
                    else:
                        filepath.unlink(missing_ok=True)

        except Exception:
            pass

        return False

    def _download_from_unpaywall(self, doi: str, filepath: Path) -> bool:
        """从 Unpaywall 下载"""
        if not self.unpaywall_email:
            return False

        try:
            url = f"https://api.unpaywall.org/v2/{doi}?email={self.unpaywall_email}"
            response = requests.get(url, timeout=30)

            if response.status_code == 200:
                data = response.json()
                oa_url = data.get('best_oa_location', {}).get('url_for_pdf')
                if oa_url:
                    return self._download_from_url(oa_url, filepath)

        except Exception:
            pass

        return False

    def _download_from_arxiv(self, identifier: str, filepath: Path) -> bool:
        """从 arXiv 下载"""
        try:
            # 提取 arXiv ID
            if 'arxiv' in identifier.lower():
                arxiv_id = re.search(r'(\d{4}\.\d{4,5})', identifier)
                if arxiv_id:
                    pdf_url = f"https://arxiv.org/pdf/{arxiv_id.group(1)}.pdf"
                    return self._download_from_url(pdf_url, filepath)

        except Exception:
            pass

        return False

    def _download_from_pmc(self, doi: str, filepath: Path) -> bool:
        """从 PMC 下载"""
        try:
            # 查找 PMC ID
            search_url = f"https://www.ncbi.nlm.nih.gov/pmc/utils/oa/oa.fcgi?doi={doi}"
            response = requests.get(search_url, timeout=30)

            if response.status_code == 200:
                # 解析 XML 找到 PDF 链接
                soup = BeautifulSoup(response.content, 'xml')
                link = soup.find('link', {'format': 'pdf'})
                if link:
                    pdf_url = link.get('href', '')
                    if pdf_url:
                        return self._download_from_url(pdf_url, filepath)

        except Exception:
            pass

        return False

    def _download_from_scihub(self, doi: str, filepath: Path) -> bool:
        """从 Sci-Hub 下载"""
        if not self.scihub_enabled:
            return False

        for domain in self.scihub_domains:
            try:
                url = f"{domain.rstrip('/')}/{doi}"
                response = requests.get(
                    url,
                    headers=self.headers,
                    timeout=self.timeout,
                    proxies=self.proxies
                )

                if response.status_code == 200:
                    soup = BeautifulSoup(response.content, 'html.parser')

                    # 查找 PDF 链接
                    for embed in soup.find_all(['embed', 'iframe']):
                        src = embed.get('src', '')
                        if src and '.pdf' in src:
                            if not src.startswith('http'):
                                src = f"https:{src}" if src.startswith('//') else f"{domain.rstrip('/')}/{src}"

                            if self._download_from_url(src, filepath):
                                return True

            except Exception:
                continue

        return False

    def _is_valid_pdf(self, filepath: Path) -> bool:
        """验证 PDF 文件"""
        if not filepath.exists():
            return False

        # 检查文件大小
        if filepath.stat().st_size < 10240:  # 10KB
            return False

        if self.strict_pdf_check:
            # 检查 PDF 头
            with open(filepath, 'rb') as f:
                header = f.read(5)
                return header == b'%PDF-'

        return True

    def _generate_filename(self, paper: Dict[str, Any]) -> str:
        """生成文件名"""
        year = paper.get('year', 'unknown')
        journal = paper.get('journal', 'unknown')
        title = paper.get('title', 'untitled')

        # 清理
        journal = re.sub(r'[\\/:*?"<>|]', '_', str(journal))[:30]
        title = re.sub(r'[\\/:*?"<>|]', '_', str(title))[:50]

        return f"{year}_{journal}_{title}"

    def _print_stats(self, stats: Dict[str, Any]):
        """打印统计信息"""
        print("\n" + "=" * 50)
        print("Download Statistics")
        print("=" * 50)
        print(f"Total:    {stats['total']}")
        print(f"Success:  {stats['success']}")
        print(f"Failed:   {stats['failed']}")
        print(f"Skipped:  {stats['skipped']}")
        print(f"Success Rate: {stats['success']/max(stats['total'], 1)*100:.1f}%")
        print("=" * 50)
