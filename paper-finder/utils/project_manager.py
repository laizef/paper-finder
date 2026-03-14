#!/usr/bin/env python3
"""
项目管理器
"""

import re
from pathlib import Path
from datetime import datetime
from typing import Dict, Any, Optional


class ProjectManager:
    """项目管理器"""

    def __init__(self, project_name: str, base_dir: str = "./output"):
        """
        初始化项目管理器

        Args:
            project_name: 项目名称
            base_dir: 基础目录
        """
        self.project_name = project_name
        self.base_dir = Path(base_dir)
        self.project_dir = self.base_dir / project_name
        self.papers_dir = self.project_dir / "papers"
        self.analysis_dir = self.project_dir

        # 创建目录
        self.project_dir.mkdir(parents=True, exist_ok=True)
        self.papers_dir.mkdir(parents=True, exist_ok=True)

    def get_search_results_path(self, format: str = 'xlsx') -> Path:
        """获取搜索结果文件路径"""
        return self.project_dir / f"search_results.{format}"

    def get_papers_dir(self) -> Path:
        """获取论文目录"""
        return self.papers_dir

    def get_analysis_dir(self) -> Path:
        """获取分析目录"""
        return self.analysis_dir

    def generate_paper_filename(self, paper: Dict[str, Any]) -> str:
        """
        生成论文文件名

        格式: year_journal_title.pdf

        Args:
            paper: 论文信息

        Returns:
            文件名（不含扩展名）
        """
        year = paper.get('year', 'unknown')
        if year is None:
            year = 'unknown'

        journal = paper.get('journal', 'unknown') or 'unknown'
        journal = self._clean_name(str(journal))[:30]

        title = paper.get('title', 'untitled') or 'untitled'
        title = self._clean_name(str(title))[:50]

        return f"{year}_{journal}_{title}"

    def _clean_name(self, name: str) -> str:
        """清理文件名"""
        # 移除非法字符
        name = re.sub(r'[\\/:*?"<>|]', '_', name)
        # 移除多余空格
        name = re.sub(r'\s+', '_', name)
        # 移除开头结尾的空格和下划线
        name = name.strip('_ ')
        return name

    def print_project_info(self):
        """打印项目信息"""
        print(f"\nProject: {self.project_name}")
        print(f"Directory: {self.project_dir}")
        print(f"Papers: {self.papers_dir}")


def create_project(project_name: str, base_dir: str = "./output") -> ProjectManager:
    """
    创建项目

    Args:
        project_name: 项目名称
        base_dir: 基础目录

    Returns:
        ProjectManager 实例
    """
    return ProjectManager(project_name, base_dir)
