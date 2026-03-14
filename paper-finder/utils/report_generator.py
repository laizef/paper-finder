#!/usr/bin/env python3
"""
报告生成器
"""

import json
from pathlib import Path
from datetime import datetime
from typing import Dict, Any


def generate_markdown_report(
    stats: Dict[str, Any],
    output_file: str,
    title: str = "Literature Analysis Report"
) -> str:
    """
    生成 Markdown 报告

    Args:
        stats: 统计数据
        output_file: 输出文件
        title: 报告标题

    Returns:
        报告内容
    """
    report = f"""# {title}

Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}

"""

    # 基本统计
    if 'basic' in stats:
        basic = stats['basic']
        report += """## Basic Statistics

| Metric | Value |
|--------|-------|
"""
        report += f"| Total Papers | {basic.get('total_papers', 0)} |\n"
        report += f"| With DOI | {basic.get('with_doi', 0)} |\n"
        report += f"| With Abstract | {basic.get('with_abstract', 0)} |\n"
        report += f"| With PDF URL | {basic.get('with_pdf_url', 0)} |\n"
        report += "\n"

    # 年份分布
    if 'year_distribution' in stats:
        yd = stats['year_distribution']
        report += f"""## Year Distribution

- Range: {yd.get('min_year', 'N/A')} - {yd.get('max_year', 'N/A')}

"""

    # 开放获取
    if 'open_access' in stats:
        oa = stats['open_access']
        report += f"""## Open Access

- Total OA: {oa.get('total_oa', 0)} ({oa.get('percentage', 0):.1f}%)

"""

    # 引用统计
    if 'citations' in stats:
        c = stats['citations']
        report += """## Citation Statistics

| Metric | Value |
|--------|-------|
"""
        report += f"| Total Citations | {c.get('total', 0)} |\n"
        report += f"| Mean | {c.get('mean', 0):.1f} |\n"
        report += f"| Median | {c.get('median', 0):.1f} |\n"
        report += f"| Max | {c.get('max', 0)} |\n"
        report += f"| Min | {c.get('min', 0)} |\n"
        report += "\n"

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

    return report
