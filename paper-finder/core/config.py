#!/usr/bin/env python3
"""
配置管理模块
"""

import os
import yaml
from pathlib import Path
from typing import Any, Dict, Optional


class Config:
    """配置管理类"""

    def __init__(self, config_path: Optional[str] = None):
        """
        初始化配置

        Args:
            config_path: 配置文件路径
        """
        self._config: Dict[str, Any] = {}
        self._config_path = config_path

        # 加载默认配置
        self._load_defaults()

        # 加载配置文件
        if config_path:
            self._load_from_file(config_path)

        # 从环境变量加载
        self._load_from_env()

    def _load_defaults(self):
        """加载默认配置"""
        self._config = {
            'search': {
                'default_sources': ['openalex', 'arxiv'],
                'openalex': {
                    'api_key': None,
                    'email': None,
                    'max_results': 1000,
                    'sort_by': 'cited_by_count:desc',
                    'request_delay': 0.1,
                },
                'arxiv': {
                    'max_results': 100,
                    'default_categories': [],
                    'sort_by': 'submittedDate',
                    'sort_order': 'descending',
                    'request_delay': 0.5,
                },
                'semantic_scholar': {
                    'api_key': None,
                    'max_results': 100,
                    'request_delay': 0.3,
                },
                'filters': {
                    'year_min': None,
                    'year_max': None,
                    'min_citations': 0,
                    'open_access_only': False,
                    'document_types': ['article'],
                    'languages': [],
                },
            },
            'download': {
                'output_dir': './output/papers',
                'sources_priority': [
                    'direct_url',
                    'unpaywall',
                    'semantic_scholar',
                    'arxiv',
                    'pmc',
                    'scihub',
                ],
                'unpaywall': {
                    'email': None,
                },
                'scihub': {
                    'domains': [
                        'https://sci-hub.se/',
                        'https://sci-hub.st/',
                        'https://sci-hub.ru/',
                        'https://sci-hub.ren/',
                    ],
                    'enabled': True,
                },
                'settings': {
                    'max_workers': 5,
                    'timeout': 60,
                    'max_retries': 3,
                    'skip_existing': True,
                    'save_failed': True,
                    'strict_pdf_check': False,
                },
            },
            'output': {
                'search_results': {
                    'dir': './output/search_results',
                    'formats': ['xlsx', 'json'],
                    'filename_template': 'search_results_{timestamp}',
                },
                'download_log': {
                    'dir': './logs',
                    'level': 'INFO',
                    'save_to_file': True,
                },
            },
            'advanced': {
                'proxy': {
                    'enabled': False,
                    'http': None,
                    'https': None,
                },
                'cache': {
                    'enabled': True,
                    'dir': './cache',
                    'expire_hours': 24,
                },
                'deduplication': {
                    'enabled': True,
                    'keys': ['doi', 'title'],
                },
            },
        }

    def _load_from_file(self, config_path: str):
        """从文件加载配置"""
        path = Path(config_path)
        if not path.exists():
            return

        with open(path, 'r', encoding='utf-8') as f:
            file_config = yaml.safe_load(f)

        if file_config:
            self._merge_config(self._config, file_config)

    def _load_from_env(self):
        """从环境变量加载配置"""
        # OpenAlex API key
        if os.environ.get('OPENALEX_API_KEY'):
            self._config['search']['openalex']['api_key'] = os.environ['OPENALEX_API_KEY']

        # Semantic Scholar API key
        if os.environ.get('SEMANTIC_SCHOLAR_API_KEY'):
            self._config['search']['semantic_scholar']['api_key'] = os.environ['SEMANTIC_SCHOLAR_API_KEY']

    def _merge_config(self, base: Dict, override: Dict):
        """合并配置"""
        for key, value in override.items():
            if key in base and isinstance(base[key], dict) and isinstance(value, dict):
                self._merge_config(base[key], value)
            else:
                base[key] = value

    def get(self, key: str, default: Any = None) -> Any:
        """
        获取配置值

        Args:
            key: 配置键（支持点分隔，如 'search.openalex.max_results'）
            default: 默认值

        Returns:
            配置值
        """
        keys = key.split('.')
        value = self._config

        for k in keys:
            if isinstance(value, dict) and k in value:
                value = value[k]
            else:
                return default

        return value

    def set(self, key: str, value: Any):
        """
        设置配置值

        Args:
            key: 配置键
            value: 配置值
        """
        keys = key.split('.')
        config = self._config

        for k in keys[:-1]:
            if k not in config:
                config[k] = {}
            config = config[k]

        config[keys[-1]] = value

    def save(self, path: Optional[str] = None):
        """
        保存配置到文件

        Args:
            path: 文件路径
        """
        save_path = path or self._config_path
        if not save_path:
            return

        with open(save_path, 'w', encoding='utf-8') as f:
            yaml.dump(self._config, f, default_flow_style=False, allow_unicode=True)

    def get_download_config(self) -> Dict[str, Any]:
        """获取下载配置"""
        return {
            'output_dir': self.get('download.output_dir', './output/papers'),
            'sources_priority': self.get('download.sources_priority', []),
            'unpaywall_email': self.get('download.unpaywall.email'),
            'scihub_domains': self.get('download.scihub.domains', []),
            'scihub_enabled': self.get('download.scihub.enabled', True),
            'max_workers': self.get('download.settings.max_workers', 5),
            'timeout': self.get('download.settings.timeout', 60),
            'max_retries': self.get('download.settings.max_retries', 3),
            'skip_existing': self.get('download.settings.skip_existing', True),
            'save_failed': self.get('download.settings.save_failed', True),
            'strict_pdf_check': self.get('download.settings.strict_pdf_check', False),
            'proxy': self.get('advanced.proxy') if self.get('advanced.proxy.enabled') else None,
        }


# 全局配置实例
_config_instance: Optional[Config] = None


def get_config(config_path: Optional[str] = None) -> Config:
    """
    获取配置实例

    Args:
        config_path: 配置文件路径

    Returns:
        Config 实例
    """
    global _config_instance

    if _config_instance is None or config_path:
        _config_instance = Config(config_path)

    return _config_instance


def reload_config(config_path: Optional[str] = None) -> Config:
    """
    重新加载配置

    Args:
        config_path: 配置文件路径

    Returns:
        Config 实例
    """
    global _config_instance
    _config_instance = None
    return get_config(config_path)
