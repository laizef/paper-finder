#!/usr/bin/env python3
"""
Paper Finder - 通用文献检索与下载工具
命令行接口
"""

import argparse
import sys
from pathlib import Path
import json
import pandas as pd
from datetime import datetime

# 添加项目根目录到路径
sys.path.insert(0, str(Path(__file__).parent))

from core.config import get_config, reload_config
from searchers import SearchManager
from downloaders import MultiSourceDownloader


def search_command(args):
    """搜索命令"""
    print("=" * 70)
    print("Paper Search")
    print("=" * 70)

    # 加载配置
    config = get_config(args.config)

    # 创建搜索管理器
    manager = SearchManager(config)

    # 解析搜索源
    sources = args.sources.split(',') if args.sources else None

    # 解析过滤条件
    filters = {}
    if args.year:
        if '-' in args.year:
            year_min, year_max = args.year.split('-')
            filters['from_publication_date'] = f"{year_min}-01-01"
            filters['to_publication_date'] = f"{year_max}-12-31"
        else:
            filters['publication_year'] = args.year

    if args.min_citations:
        filters['cited_by_count'] = f">{args.min_citations}"

    if args.open_access:
        filters['is_oa'] = 'true'

    # 执行搜索
    if args.queries_file:
        # 从文件读取查询列表
        with open(args.queries_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]

        papers = manager.search_multiple_queries(
            queries=queries,
            sources=sources,
            max_per_query=args.max_results,
            max_total=args.max_total,
            filters=filters if filters else None
        )
    else:
        # 单个查询
        papers = manager.search(
            query=args.query,
            sources=sources,
            max_results=args.max_results,
            filters=filters if filters else None
        )

    if not papers:
        print("\n⚠️  未找到任何文献")
        return

    # 生成文件名
    timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
    base_filename = args.output or f"search_results_{timestamp}"

    # 输出目录
    output_dir = Path(config.get('output.search_results.dir', './output/search_results'))
    output_dir.mkdir(parents=True, exist_ok=True)

    # 保存结果
    output_files = []

    # 保存为 Excel
    if args.format in ['all', 'xlsx']:
        df = pd.DataFrame(papers)
        # 添加文件名列
        df['filename'] = df.apply(_generate_filename, axis=1)

        # 排序
        if 'citations' in df.columns:
            df = df.sort_values('citations', ascending=False)

        excel_file = output_dir / f"{base_filename}.xlsx"
        df.to_excel(excel_file, index=False, engine='openpyxl')
        output_files.append(str(excel_file))

    # 保存为 JSON
    if args.format in ['all', 'json']:
        json_file = output_dir / f"{base_filename}.json"
        with open(json_file, 'w', encoding='utf-8') as f:
            json.dump(papers, f, ensure_ascii=False, indent=2)
        output_files.append(str(json_file))

    # 保存为 CSV
    if args.format in ['all', 'csv']:
        df = pd.DataFrame(papers)
        csv_file = output_dir / f"{base_filename}.csv"
        df.to_csv(csv_file, index=False, encoding='utf-8-sig')
        output_files.append(str(csv_file))

    # 显示统计
    print("\n" + "=" * 70)
    print("Search Results Statistics:")
    print(f"  Total: {len(papers)} papers")

    if papers:
        # 按来源统计
        sources_count = {}
        for paper in papers:
            source = paper.get('source', 'Unknown')
            sources_count[source] = sources_count.get(source, 0) + 1

        print("\nBy Source:")
        for source, count in sorted(sources_count.items()):
            print(f"  {source}: {count} papers")

        # 年份统计
        years = [p.get('year') for p in papers if p.get('year')]
        if years:
            print(f"\nYear Range: {min(years)} - {max(years)}")

        # 开放获取统计
        oa_count = sum(1 for p in papers if p.get('is_oa'))
        print(f"Open Access: {oa_count} papers ({oa_count/len(papers)*100:.1f}%)")

    print("\nOutput Files:")
    for file in output_files:
        print(f"  {file}")

    print("=" * 70)


def download_command(args):
    """下载命令"""
    print("=" * 70)
    print("Paper Download")
    print("=" * 70)

    # 加载配置
    config = get_config(args.config)

    # 读取文献列表
    if args.input.endswith('.xlsx'):
        df = pd.read_excel(args.input)
        papers = df.to_dict('records')
    elif args.input.endswith('.json'):
        with open(args.input, 'r', encoding='utf-8') as f:
            papers = json.load(f)
    elif args.input.endswith('.csv'):
        df = pd.read_csv(args.input)
        papers = df.to_dict('records')
    else:
        print(f"⚠️  不支持的文件格式: {args.input}")
        return

    print(f"\nLoaded {len(papers)} papers")

    # 过滤（如果需要）
    if args.max_papers:
        papers = papers[:args.max_papers]
        print(f"   Will download first {args.max_papers} papers")

    # 创建下载器
    download_config = config.get_download_config()

    # 覆盖输出目录（如果指定）
    if args.output_dir:
        download_config['output_dir'] = args.output_dir

    downloader = MultiSourceDownloader(download_config)

    # 批量下载
    stats = downloader.download_batch(
        papers,
        max_workers=args.workers
    )

    # 保存下载日志
    if args.save_log:
        log_dir = Path(config.get('output.download_log.dir', './logs'))
        log_dir.mkdir(parents=True, exist_ok=True)

        timestamp = datetime.now().strftime("%Y%m%d_%H%M%S")
        log_file = log_dir / f"download_log_{timestamp}.json"

        with open(log_file, 'w', encoding='utf-8') as f:
            json.dump(stats, f, ensure_ascii=False, indent=2)

        print(f"\nDownload log saved: {log_file}")


def config_command(args):
    """配置命令"""
    config = get_config(args.config)

    if args.show:
        print("=" * 70)
        print("Current Configuration")
        print("=" * 70)

        import yaml
        print(yaml.dump(config._config, default_flow_style=False, allow_unicode=True))

    elif args.set:
        # 设置配置值
        key, value = args.set.split('=')

        # 尝试解析为 JSON
        try:
            import json
            value = json.loads(value)
        except:
            pass

        config.set(key, value)
        print(f"✓ 已设置 {key} = {value}")

        if args.save:
            config.save()
            print(f"✓ 配置已保存")


def analyze_command(args):
    """分析命令"""
    from utils.analyzer import analyze_papers

    print("=" * 70)
    print("Paper Analysis")
    print("=" * 70)

    # 执行分析
    output_dir = args.output or "./output/analysis"
    stats = analyze_papers(args.input, output_dir)


def workflow_command(args):
    """完整工作流命令：搜索 -> 下载 -> 分析"""
    from utils.project_manager import create_project
    from searchers import SearchManager
    from downloaders import MultiSourceDownloader
    from utils.analyzer import PaperAnalyzer

    print("=" * 70)
    print("Complete Workflow: Search -> Download -> Analyze")
    print("=" * 70)

    # 1. 创建项目
    project_name = args.project_name or f"paper_project_{datetime.now().strftime('%Y%m%d_%H%M%S')}"
    project = create_project(project_name, args.output_dir or "./output")
    project.print_project_info()

    # 2. 搜索文献
    print("\n" + "=" * 70)
    print("Step 1: Searching Papers")
    print("=" * 70)

    config = get_config(args.config)
    manager = SearchManager(config)

    # 解析搜索源
    sources = args.sources.split(',') if args.sources else None

    # 解析过滤条件
    filters = {}
    if args.year:
        if '-' in args.year:
            year_min, year_max = args.year.split('-')
            filters['from_publication_date'] = f"{year_min}-01-01"
            filters['to_publication_date'] = f"{year_max}-12-31"
        else:
            filters['publication_year'] = args.year

    if args.min_citations:
        filters['cited_by_count'] = f">{args.min_citations}"

    if args.open_access:
        filters['is_oa'] = 'true'

    # 执行搜索
    if args.queries_file:
        with open(args.queries_file, 'r', encoding='utf-8') as f:
            queries = [line.strip() for line in f if line.strip()]

        papers = manager.search_multiple_queries(
            queries=queries,
            sources=sources,
            max_per_query=args.max_results,
            max_total=args.max_total,
            filters=filters if filters else None
        )
    else:
        papers = manager.search(
            query=args.query,
            sources=sources,
            max_results=args.max_results,
            filters=filters if filters else None
        )

    if not papers:
        print("\nNo papers found!")
        return

    # 3. 保存搜索结果
    print("\n" + "=" * 70)
    print("Step 2: Saving Search Results")
    print("=" * 70)

    # 保存为 Excel
    df = pd.DataFrame(papers)
    df['filename'] = df.apply(lambda row: project.generate_paper_filename(row.to_dict()), axis=1)

    if 'citations' in df.columns:
        df = df.sort_values('citations', ascending=False)

    search_results_file = project.get_search_results_path('xlsx')
    df.to_excel(search_results_file, index=False, engine='openpyxl')
    print(f"Search results saved: {search_results_file}")

    # 保存为 JSON
    search_results_json = project.get_search_results_path('json')
    with open(search_results_json, 'w', encoding='utf-8') as f:
        json.dump(papers, f, ensure_ascii=False, indent=2)
    print(f"Search results saved: {search_results_json}")

    # 4. 下载文献
    if args.download:
        print("\n" + "=" * 70)
        print("Step 3: Downloading Papers")
        print("=" * 70)

        download_config = config.get_download_config()
        download_config['output_dir'] = str(project.get_papers_dir())

        # 创建下载器，使用项目文件名生成器
        downloader = MultiSourceDownloader(
            download_config,
            filename_generator=project.generate_paper_filename
        )

        # 限制下载数量
        download_papers = papers[:args.max_download] if args.max_download else papers

        stats = downloader.download_batch(
            download_papers,
            max_workers=args.workers
        )

        # 保存下载日志
        if args.save_log:
            log_file = project.project_dir / "download_log.json"
            with open(log_file, 'w', encoding='utf-8') as f:
                json.dump(stats, f, ensure_ascii=False, indent=2)
            print(f"\nDownload log saved: {log_file}")

    # 5. 生成分析报告
    if args.analyze:
        print("\n" + "=" * 70)
        print("Step 4: Generating Analysis Report")
        print("=" * 70)

        analyzer = PaperAnalyzer(papers)
        stats = analyzer.generate_report(
            str(project.get_analysis_dir()),
            use_timestamp=False
        )

    # 6. 完成
    print("\n" + "=" * 70)
    print("Workflow Completed!")
    print("=" * 70)
    print(f"Project directory: {project.project_dir}")
    print(f"Total papers found: {len(papers)}")
    if args.download:
        print(f"Papers downloaded to: {project.get_papers_dir()}")
    print("\nFiles generated:")
    print(f"  - Search results: {search_results_file}")
    if args.analyze:
        print(f"  - Analysis report: {project.project_dir / 'analysis_report.md'}")
        print(f"  - Statistics: {project.project_dir / 'statistics.json'}")
        print(f"  - Summary table: {project.project_dir / 'summary_table.xlsx'}")
        print(f"  - Detailed table: {project.project_dir / 'detailed_table.xlsx'}")
    print("=" * 70)


def _generate_filename(row) -> str:
    """生成安全的文件名"""
    import re

    if pd.notna(row.get("doi")):
        doi = str(row["doi"]).replace("https://doi.org/", "").replace("http://dx.doi.org/", "")
        filename = doi.replace("/", "_").replace(":", "_")
    else:
        title = str(row.get("title", "unknown"))
        filename = re.sub(r'[\\/:*?"<>|]', '_', title)[:50]

    return filename


def main():
    """主函数"""
    parser = argparse.ArgumentParser(
        description='Paper Finder - 通用文献检索与下载工具',
        formatter_class=argparse.RawDescriptionHelpFormatter,
        epilog="""
示例:
  # 搜索文献
  python paper_finder.py search "machine learning" -n 100 -o ml_papers

  # 多关键词搜索
  python paper_finder.py search --queries-file queries.txt -n 50

  # 下载文献
  python paper_finder.py download search_results.xlsx -o ./papers

  # 查看配置
  python paper_finder.py config --show
        """
    )

    # 全局参数
    parser.add_argument('--config', '-c', help='配置文件路径')

    # 子命令
    subparsers = parser.add_subparsers(dest='command', help='可用命令')

    # 搜索命令
    search_parser = subparsers.add_parser('search', help='搜索文献')
    search_parser.add_argument('query', nargs='?', help='搜索关键词')
    search_parser.add_argument('--queries-file', '-qf', help='查询关键词文件（每行一个）')
    search_parser.add_argument('--sources', '-s', help='搜索源（逗号分隔，如 openalex,arxiv）')
    search_parser.add_argument('--max-results', '-n', type=int, default=100, help='每个源的最大结果数')
    search_parser.add_argument('--max-total', type=int, default=1000, help='最大总结果数（多关键词时）')
    search_parser.add_argument('--year', help='年份或年份范围（如 2023 或 2020-2023）')
    search_parser.add_argument('--min-citations', type=int, help='最小引用次数')
    search_parser.add_argument('--open-access', action='store_true', help='只搜索开放获取')
    search_parser.add_argument('--output', '-o', help='输出文件名（不含扩展名）')
    search_parser.add_argument('--format', '-f', choices=['xlsx', 'json', 'csv', 'all'], default='xlsx',
                               help='输出格式')

    # 下载命令
    download_parser = subparsers.add_parser('download', help='下载文献')
    download_parser.add_argument('input', help='输入文件（xlsx/json/csv）')
    download_parser.add_argument('--output-dir', '-o', help='下载目录')
    download_parser.add_argument('--workers', '-w', type=int, default=5, help='并发下载数')
    download_parser.add_argument('--max-papers', type=int, help='最大下载数量')
    download_parser.add_argument('--save-log', action='store_true', help='保存下载日志')

    # 配置命令
    config_parser = subparsers.add_parser('config', help='配置管理')
    config_parser.add_argument('--show', action='store_true', help='显示当前配置')
    config_parser.add_argument('--set', help='设置配置值（格式: key=value）')
    config_parser.add_argument('--save', action='store_true', help='保存配置')

    # 分析命令
    analyze_parser = subparsers.add_parser('analyze', help='分析文献')
    analyze_parser.add_argument('input', help='输入文件（xlsx/json/csv）')
    analyze_parser.add_argument('--output', '-o', help='输出目录')

    # 工作流命令（整合搜索、下载、分析）
    workflow_parser = subparsers.add_parser('workflow', help='完整工作流：搜索->下载->分析')
    workflow_parser.add_argument('query', nargs='?', help='搜索关键词')
    workflow_parser.add_argument('--project-name', '-p', help='项目名称')
    workflow_parser.add_argument('--queries-file', '-qf', help='查询关键词文件（每行一个）')
    workflow_parser.add_argument('--sources', '-s', help='搜索源（逗号分隔）')
    workflow_parser.add_argument('--max-results', '-n', type=int, default=100, help='每个源的最大结果数')
    workflow_parser.add_argument('--max-total', type=int, default=1000, help='最大总结果数')
    workflow_parser.add_argument('--year', help='年份或年份范围')
    workflow_parser.add_argument('--min-citations', type=int, help='最小引用次数')
    workflow_parser.add_argument('--open-access', action='store_true', help='只搜索开放获取')
    workflow_parser.add_argument('--output-dir', '-o', help='项目输出目录')
    workflow_parser.add_argument('--download', action='store_true', help='下载文献')
    workflow_parser.add_argument('--max-download', type=int, help='最大下载数量')
    workflow_parser.add_argument('--workers', '-w', type=int, default=5, help='并发下载数')
    workflow_parser.add_argument('--save-log', action='store_true', help='保存下载日志')
    workflow_parser.add_argument('--analyze', action='store_true', help='生成分析报告')

    # 解析参数
    args = parser.parse_args()

    # 执行命令
    if args.command == 'search':
        if not args.query and not args.queries_file:
            search_parser.error('请提供搜索关键词或查询文件')
        search_command(args)
    elif args.command == 'download':
        download_command(args)
    elif args.command == 'config':
        config_command(args)
    elif args.command == 'analyze':
        analyze_command(args)
    elif args.command == 'workflow':
        if not args.query and not args.queries_file:
            workflow_parser.error('请提供搜索关键词或查询文件')
        workflow_command(args)
    else:
        parser.print_help()


if __name__ == "__main__":
    main()
