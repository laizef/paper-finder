#!/usr/bin/env python3
"""
文献分析器
"""

import json
import numpy as np
import pandas as pd
from pathlib import Path
from typing import Dict, List, Optional, Any
from datetime import datetime
from collections import Counter


class PaperAnalyzer:
    """文献分析器"""

    def __init__(self, papers: List[Dict[str, Any]]):
        """
        初始化分析器

        Args:
            papers: 文献列表
        """
        self.papers = papers
        self.df = pd.DataFrame(papers)

    def generate_report(
        self,
        output_dir: str,
        use_timestamp: bool = True
    ) -> Dict[str, Any]:
        """
        生成分析报告

        Args:
            output_dir: 输出目录
            use_timestamp: 是否使用时间戳

        Returns:
            统计结果
        """
        output_path = Path(output_dir)
        output_path.mkdir(parents=True, exist_ok=True)

        # 生成统计
        stats = self._generate_statistics()

        # 生成文件名后缀
        suffix = f"_{datetime.now().strftime('%Y%m%d_%H%M%S')}" if use_timestamp else ""

        # 保存统计信息
        stats_file = output_path / f"statistics{suffix}.json"
        with open(stats_file, 'w', encoding='utf-8') as f:
            json.dump(self._convert_to_native_types(stats), f, ensure_ascii=False, indent=2)

        # 生成摘要表格
        self._create_summary_table(output_path / f"summary_table{suffix}.xlsx")

        # 生成详细表格
        self._create_detailed_table(output_path / f"detailed_table{suffix}.xlsx")

        # 生成 Markdown 报告
        self._create_markdown_report(output_path / f"analysis_report{suffix}.md", stats)

        print(f"\nAnalysis report generated in: {output_path}")
        return stats

    def _generate_statistics(self) -> Dict[str, Any]:
        """生成统计数据"""
        stats = {}

        # 基本统计
        stats['basic'] = {
            'total_papers': len(self.papers),
            'with_doi': self.df['doi'].notna().sum() if 'doi' in self.df.columns else 0,
            'with_abstract': self.df['abstract'].notna().sum() if 'abstract' in self.df.columns else 0,
            'with_pdf_url': self.df['pdf_url'].notna().sum() if 'pdf_url' in self.df.columns else 0,
        }

        # 年份分布
        if 'year' in self.df.columns:
            years = self.df['year'].dropna().astype(int)
            year_counts = years.value_counts().sort_index()
            stats['year_distribution'] = {
                'min_year': int(years.min()) if len(years) > 0 else None,
                'max_year': int(years.max()) if len(years) > 0 else None,
                'distribution': {str(k): int(v) for k, v in year_counts.items()}
            }

        # 来源分布
        if 'source' in self.df.columns:
            source_counts = self.df['source'].value_counts()
            stats['source_distribution'] = {str(k): int(v) for k, v in source_counts.items()}

        # 开放获取统计
        if 'is_oa' in self.df.columns:
            oa_count = self.df['is_oa'].sum()
            stats['open_access'] = {
                'total_oa': int(oa_count),
                'percentage': float(oa_count / len(self.papers) * 100) if self.papers else 0
            }

        # 引用统计
        if 'citations' in self.df.columns:
            citations = self.df['citations'].dropna()
            stats['citations'] = {
                'total': int(citations.sum()),
                'mean': float(citations.mean()) if len(citations) > 0 else 0,
                'median': float(citations.median()) if len(citations) > 0 else 0,
                'max': int(citations.max()) if len(citations) > 0 else 0,
                'min': int(citations.min()) if len(citations) > 0 else 0,
            }

        # 期刊统计
        if 'journal' in self.df.columns:
            journals = self.df['journal'].dropna()
            journal_counts = journals.value_counts().head(20)
            stats['top_journals'] = {str(k): int(v) for k, v in journal_counts.items()}

        # 作者统计
        if 'authors' in self.df.columns:
            all_authors = []
            for authors in self.df['authors'].dropna():
                all_authors.extend(str(authors).split(';'))

            author_counts = Counter([a.strip() for a in all_authors if a.strip()])
            stats['top_authors'] = {k: int(v) for k, v in author_counts.most_common(20)}

        # 关键词统计
        if 'keywords' in self.df.columns:
            all_keywords = []
            for keywords in self.df['keywords'].dropna():
                all_keywords.extend(str(keywords).split(';'))

            keyword_counts = Counter([k.strip() for k in all_keywords if k.strip()])
            stats['top_keywords'] = {k: int(v) for k, v in keyword_counts.most_common(30)}

        return stats

    def _create_summary_table(self, output_file: Path):
        """创建摘要表格"""
        summary_data = []

        # 按年份统计
        if 'year' in self.df.columns:
            year_groups = self.df.groupby('year').agg({
                'title': 'count',
                'citations': 'sum' if 'citations' in self.df.columns else 'count'
            }).reset_index()
            year_groups.columns = ['Year', 'Paper Count', 'Total Citations']
            summary_data.append(('By Year', year_groups))

        # 按来源统计
        if 'source' in self.df.columns:
            source_groups = self.df.groupby('source').agg({
                'title': 'count'
            }).reset_index()
            source_groups.columns = ['Source', 'Paper Count']
            summary_data.append(('By Source', source_groups))

        # 保存
        with pd.ExcelWriter(output_file, engine='openpyxl') as writer:
            for name, df in summary_data:
                df.to_excel(writer, sheet_name=name[:31], index=False)

    def _create_detailed_table(self, output_file: Path):
        """创建详细表格"""
        # 选择重要列
        columns = ['title', 'authors', 'year', 'journal', 'citations', 'doi', 'is_oa', 'source']
        available_columns = [c for c in columns if c in self.df.columns]

        df_detailed = self.df[available_columns].copy()

        # 排序
        if 'citations' in df_detailed.columns:
            df_detailed = df_detailed.sort_values('citations', ascending=False)

        # 保存
        df_detailed.to_excel(output_file, index=False, engine='openpyxl')

    def _create_markdown_report(self, output_file: Path, stats: Dict[str, Any]):
        """创建 Markdown 报告"""
        report = f"""# Literature Analysis Report

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

## Basic Statistics

| Metric | Value |
|--------|-------|
| Total Papers | {stats['basic']['total_papers']} |
| With DOI | {stats['basic']['with_doi']} |
| With Abstract | {stats['basic']['with_abstract']} |
| With PDF URL | {stats['basic']['with_pdf_url']} |

"""

        # 年份分布
        if 'year_distribution' in stats:
            yd = stats['year_distribution']
            report += f"""## Year Distribution

- Range: {yd['min_year']} - {yd['max_year']}

"""

        # 开放获取
        if 'open_access' in stats:
            oa = stats['open_access']
            report += f"""## Open Access

- Total OA: {oa['total_oa']} ({oa['percentage']:.1f}%)

"""

        # 引用统计
        if 'citations' in stats:
            c = stats['citations']
            report += f"""## Citation Statistics

| Metric | Value |
|--------|-------|
| Total Citations | {c['total']} |
| Mean | {c['mean']:.1f} |
| Median | {c['median']:.1f} |
| Max | {c['max']} |
| Min | {c['min']} |

"""

        # 顶级期刊
        if 'top_journals' in stats:
            report += "## Top Journals\n\n"
            for journal, count in list(stats['top_journals'].items())[:10]:
                report += f"- {journal}: {count}\n"
            report += "\n"

        # 顶级关键词
        if 'top_keywords' in stats:
            report += "## Top Keywords\n\n"
            for keyword, count in list(stats['top_keywords'].items())[:15]:
                report += f"- {keyword}: {count}\n"
            report += "\n"

        # 保存
        with open(output_file, 'w', encoding='utf-8') as f:
            f.write(report)

    def _convert_to_native_types(self, obj):
        """转换 numpy 类型为 Python 原生类型"""
        if isinstance(obj, dict):
            return {k: self._convert_to_native_types(v) for k, v in obj.items()}
        elif isinstance(obj, list):
            return [self._convert_to_native_types(v) for v in obj]
        elif isinstance(obj, (np.integer, np.int64, np.int32)):
            return int(obj)
        elif isinstance(obj, (np.floating, np.float64, np.float32)):
            return float(obj)
        elif isinstance(obj, np.ndarray):
            return obj.tolist()
        elif pd.isna(obj):
            return None
        return obj


def analyze_papers(input_file: str, output_dir: str) -> Dict[str, Any]:
    """
    分析文献

    Args:
        input_file: 输入文件
        output_dir: 输出目录

    Returns:
        统计结果
    """
    # 读取文件
    if input_file.endswith('.xlsx'):
        df = pd.read_excel(input_file)
    elif input_file.endswith('.json'):
        with open(input_file, 'r', encoding='utf-8') as f:
            papers = json.load(f)
        df = pd.DataFrame(papers)
    elif input_file.endswith('.csv'):
        df = pd.read_csv(input_file)
    else:
        raise ValueError(f"Unsupported file format: {input_file}")

    papers = df.to_dict('records')

    # 分析
    analyzer = PaperAnalyzer(papers)
    stats = analyzer.generate_report(output_dir)

    return stats
