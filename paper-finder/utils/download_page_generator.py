#!/usr/bin/env python3
"""
生成手动下载HTML页面
"""

import pandas as pd
from pathlib import Path
from datetime import datetime


def generate_download_page(excel_file: str, output_file: str = None):
    """
    生成包含所有论文下载链接的HTML页面

    Args:
        excel_file: 搜索结果Excel文件
        output_file: 输出HTML文件路径
    """

    # 读取搜索结果
    df = pd.read_excel(excel_file)

    if output_file is None:
        output_file = Path(excel_file).parent / "manual_download.html"

    # 按引用次数排序
    if 'citations' in df.columns:
        df = df.sort_values('citations', ascending=False)

    # 生成HTML
    html = f"""<!DOCTYPE html>
<html lang="zh-CN">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Paper Download Page</title>
    <style>
        body {{
            font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
            line-height: 1.6;
            max-width: 1400px;
            margin: 0 auto;
            padding: 20px;
            background-color: #f5f5f5;
        }}
        .header {{
            background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
            color: white;
            padding: 30px;
            border-radius: 10px;
            margin-bottom: 30px;
            box-shadow: 0 4px 6px rgba(0,0,0,0.1);
        }}
        .header h1 {{
            margin: 0 0 10px 0;
        }}
        .stats {{
            background: white;
            padding: 20px;
            border-radius: 8px;
            margin-bottom: 20px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
        }}
        .paper-card {{
            background: white;
            border-radius: 8px;
            padding: 20px;
            margin-bottom: 15px;
            box-shadow: 0 2px 4px rgba(0,0,0,0.1);
            transition: transform 0.2s;
        }}
        .paper-card:hover {{
            transform: translateY(-2px);
            box-shadow: 0 4px 8px rgba(0,0,0,0.15);
        }}
        .paper-title {{
            font-size: 18px;
            font-weight: bold;
            color: #2c3e50;
            margin-bottom: 10px;
        }}
        .paper-meta {{
            color: #7f8c8d;
            font-size: 14px;
            margin-bottom: 10px;
        }}
        .paper-abstract {{
            color: #34495e;
            font-size: 14px;
            line-height: 1.6;
            margin-bottom: 15px;
            padding: 10px;
            background-color: #f9f9f9;
            border-left: 3px solid #667eea;
        }}
        .buttons {{
            display: flex;
            gap: 10px;
            flex-wrap: wrap;
        }}
        .btn {{
            display: inline-block;
            padding: 8px 16px;
            border: none;
            border-radius: 5px;
            cursor: pointer;
            text-decoration: none;
            font-size: 14px;
            transition: background-color 0.3s;
        }}
        .btn-primary {{
            background-color: #667eea;
            color: white;
        }}
        .btn-primary:hover {{
            background-color: #5568d3;
        }}
        .btn-secondary {{
            background-color: #95a5a6;
            color: white;
        }}
        .btn-secondary:hover {{
            background-color: #7f8c8d;
        }}
        .badge {{
            display: inline-block;
            padding: 3px 8px;
            border-radius: 12px;
            font-size: 12px;
            font-weight: bold;
            margin-right: 5px;
        }}
        .badge-oa {{
            background-color: #27ae60;
            color: white;
        }}
        .badge-citations {{
            background-color: #f39c12;
            color: white;
        }}
        .badge-year {{
            background-color: #3498db;
            color: white;
        }}
        .instructions {{
            background: #fff3cd;
            border: 1px solid #ffc107;
            padding: 15px;
            border-radius: 5px;
            margin-bottom: 20px;
        }}
        .instructions h3 {{
            margin-top: 0;
            color: #856404;
        }}
    </style>
</head>
<body>
    <div class="header">
        <h1>Paper Download Page</h1>
        <p>Generated: {datetime.now().strftime('%Y-%m-%d %H:%M:%S')}</p>
        <p>Total Papers: {len(df)}</p>
    </div>

    <div class="instructions">
        <h3>Instructions</h3>
        <ol>
            <li>Click <strong>"Download PDF"</strong> to download directly</li>
            <li>If download fails, click <strong>"DOI Link"</strong> to download manually</li>
            <li>Use Ctrl+F to search for keywords</li>
        </ol>
    </div>

    <div class="stats">
        <h3>Statistics</h3>
        <ul>
            <li>Total Papers: {len(df)}</li>
            <li>With PDF URL: {df['pdf_url'].notna().sum() if 'pdf_url' in df.columns else 0}</li>
            <li>With DOI: {df['doi'].notna().sum() if 'doi' in df.columns else 0}</li>
            <li>Open Access: {df['is_oa'].sum() if 'is_oa' in df.columns else 0}</li>
        </ul>
    </div>
"""

    # 添加论文卡片
    for idx, row in df.iterrows():
        title = row.get('title', 'Unknown Title')
        authors = row.get('authors', 'Unknown Authors')
        year = row.get('year', 'Unknown Year')
        journal = row.get('journal', 'Unknown Journal')
        citations = row.get('citations', 0)
        doi = row.get('doi', '')
        pdf_url = row.get('pdf_url', '')
        abstract = row.get('abstract', '')
        is_oa = row.get('is_oa', False)

        # 处理摘要
        abstract = str(abstract) if pd.notna(abstract) else ''
        abstract_short = abstract[:300] + "..." if len(abstract) > 300 else abstract

        html += f"""
    <div class="paper-card">
        <div class="paper-title">{idx + 1}. {title}</div>
        <div class="paper-meta">
            <span class="badge badge-year">{year}</span>
            <span class="badge badge-citations">Citations: {citations}</span>
            {'<span class="badge badge-oa">Open Access</span>' if is_oa else ''}
            <br>
            <strong>Authors:</strong> {str(authors)[:100]}{'...' if len(str(authors)) > 100 else ''}<br>
            <strong>Journal:</strong> {journal}
        </div>
        {f'<div class="paper-abstract">{abstract_short}</div>' if abstract_short else ''}
        <div class="buttons">
            {f'<a href="{pdf_url}" class="btn btn-primary" target="_blank">Download PDF</a>' if pdf_url else ''}
            {f'<a href="https://doi.org/{doi}" class="btn btn-secondary" target="_blank">DOI Link</a>' if doi else ''}
            <a href="https://scholar.google.com/scholar?q={str(title).replace(' ', '+')}" class="btn btn-secondary" target="_blank">Google Scholar</a>
        </div>
    </div>
"""

    html += """
    <div style="text-align: center; margin-top: 40px; color: #7f8c8d;">
        <p>Generated by Paper Finder</p>
    </div>
</body>
</html>
"""

    # 保存HTML文件
    with open(output_file, 'w', encoding='utf-8') as f:
        f.write(html)

    print(f"Download page generated: {output_file}")
    print(f"Total papers: {len(df)}")

    return output_file
