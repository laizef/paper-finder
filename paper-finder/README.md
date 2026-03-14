# Paper Finder

[![Python 3.8+](https://img.shields.io/badge/python-3.8+-blue.svg)](https://www.python.org/downloads/)
[![License: MIT](https://img.shields.io/badge/License-MIT-yellow.svg)](https://opensource.org/licenses/MIT)

A powerful command-line tool for searching, downloading, and analyzing academic literature across all research domains.

## Features

- **Multi-source Search**: OpenAlex, arXiv, Semantic Scholar
- **Multi-source Download**: Unpaywall, PubMed Central, arXiv, Semantic Scholar, Sci-Hub
- **Smart File Naming**: Automatically renames PDFs as `year_journal_title.pdf`
- **Comprehensive Analysis**: 10-dimension statistics (year, citations, journals, authors, keywords)
- **Multiple Output Formats**: Excel, CSV, JSON, Markdown
- **Manual Download Page**: Auto-generated HTML for paywalled papers
- **Unified Project Management**: All outputs organized in one directory

## Installation

```bash
git clone https://github.com/yourusername/paper-finder.git
cd paper-finder
pip install -r requirements.txt
```

## Quick Start

### Complete Workflow (Recommended)

Search, download, and analyze in one command:

```bash
python paper_finder.py workflow "machine learning" \
    --project-name ml_review \
    --max-results 100 \
    --download \
    --max-download 50 \
    --analyze
```

### Search Only

```bash
python paper_finder.py search "quantum computing" \
    --max-results 100 \
    --output quantum_papers
```

### Download from Results

```bash
python paper_finder.py download search_results.xlsx \
    --output-dir ./papers \
    --workers 10
```

### Analyze Results

```bash
python paper_finder.py analyze search_results.xlsx
```

## Supported Research Domains

Paper Finder works across all academic fields:

| Domain | Example Keywords |
|--------|------------------|
| Computer Science | machine learning, computer vision, NLP |
| Physics | quantum computing, astrophysics, particle physics |
| Biology | gene editing, protein folding, microbiome |
| Chemistry | organic synthesis, catalysis, materials science |
| Medicine | cancer treatment, drug discovery, vaccine development |
| Engineering | battery technology, renewable energy, robotics |
| Economics | game theory, market analysis, behavioral economics |
| Social Sciences | social networks, political behavior, linguistics |

## Command Reference

### `workflow` - Complete Pipeline

```bash
python paper_finder.py workflow "query" [OPTIONS]

Required:
  query                       Search keywords

Options:
  --project-name NAME         Project name
  --queries-file FILE         File with keywords (one per line)
  --sources SOURCES           Search sources (comma-separated: openalex,arxiv)
  --max-results N             Max results per source (default: 100)
  --max-total N               Max total results (default: 1000)
  --year YEAR                 Year or range (e.g., 2023 or 2020-2023)
  --min-citations N           Minimum citation count
  --open-access               Open access papers only
  --output-dir DIR            Output directory
  --download                  Enable downloading
  --max-download N            Maximum downloads
  --workers N                 Concurrent downloads (default: 5)
  --analyze                   Generate analysis report
```

### `search` - Search Papers

```bash
python paper_finder.py search "query" [OPTIONS]

Options:
  --sources, -s SOURCES       Search sources
  --max-results, -n N         Maximum results (default: 100)
  --year YEAR                 Year filter
  --min-citations N           Minimum citations
  --open-access               Open access only
  --output, -o NAME           Output filename
  --format, -f FORMAT         Output format (xlsx/json/csv/all)
```

### `download` - Download PDFs

```bash
python paper_finder.py download INPUT_FILE [OPTIONS]

Options:
  --output-dir, -o DIR        Download directory
  --workers, -w N             Concurrent downloads
  --max-papers N              Maximum papers to download
```

### `analyze` - Generate Reports

```bash
python paper_finder.py analyze INPUT_FILE [OPTIONS]

Options:
  --output, -o DIR            Output directory
```

## Project Structure

```
paper-finder/
├── paper_finder.py           # Main CLI entry point
├── requirements.txt          # Python dependencies
├── config/
│   └── settings.yaml         # Configuration file
├── core/
│   └── config.py             # Configuration management
├── searchers/
│   ├── base.py               # Base searcher class
│   ├── openalex_searcher.py  # OpenAlex API
│   ├── arxiv_searcher.py     # arXiv API
│   └── manager.py            # Search orchestration
├── downloaders/
│   └── multisource_downloader.py  # Multi-source downloader
└── utils/
    ├── analyzer.py           # Literature analysis
    ├── project_manager.py    # Project management
    ├── download_page_generator.py  # HTML page generator
    └── report_generator.py   # Markdown reports
```

## Output Structure

Each project generates:

```
output/project_name/
├── search_results.xlsx       # Search results (Excel)
├── search_results.json       # Search results (JSON)
├── papers/                   # Downloaded PDFs
│   ├── 2023_Nature_Paper_Title.pdf
│   └── ...
├── analysis_report.md        # Analysis report
├── statistics.json           # Detailed statistics
├── summary_table.xlsx        # Summary table
├── detailed_table.xlsx       # Detailed table
└── manual_download.html      # Manual download page
```

## Configuration

Edit `config/settings.yaml` to customize behavior:

```yaml
search:
  default_sources:
    - openalex
    - arxiv

download:
  sources_priority:
    - direct_url
    - unpaywall
    - arxiv
    - pmc
    - scihub
  unpaywall:
    email: null  # Optional: add your email for better Unpaywall access
  settings:
    max_workers: 5
    timeout: 60
```

### API Keys (Optional)

Set environment variables for enhanced access:

```bash
export OPENALEX_API_KEY="your-key"
export SEMANTIC_SCHOLAR_API_KEY="your-key"
```

## Advanced Usage

### Multi-keyword Search

Create `queries.txt`:
```
machine learning
deep learning
neural networks
```

Run:
```bash
python paper_finder.py workflow --queries-file queries.txt --max-results 50
```

### Filter Examples

```bash
# Recent highly-cited papers
python paper_finder.py workflow "transformer" \
    --year 2022-2024 \
    --min-citations 50 \
    --open-access

# Specific time period
python paper_finder.py search "CRISPR" \
    --year 2020-2023 \
    --max-results 200
```

### Python API

```python
from searchers import SearchManager
from downloaders import MultiSourceDownloader
from utils.analyzer import PaperAnalyzer

# Search
manager = SearchManager()
papers = manager.search("your topic", max_results=100)

# Download
downloader = MultiSourceDownloader({'output_dir': './papers'})
stats = downloader.download_batch(papers)

# Analyze
analyzer = PaperAnalyzer(papers)
analyzer.generate_report('./analysis')
```

## Troubleshooting

### Download Failures

Most failures occur due to:
1. **Anti-scraping protection** (HTTP 403)
2. **Paywalls** requiring subscription
3. **Redirects** to login pages

**Solutions:**
- Use the generated `manual_download.html` page
- Connect through institutional VPN
- The tool includes Sci-Hub as a fallback source

### No Search Results

- Use more specific keywords
- Try different search sources
- Check year/citation filters
- Verify internet connection

### PDF File Issues

- Check file size (>10KB is usually valid)
- Re-download using manual download page
- Files may be corrupted during transfer

## Contributing

Contributions are welcome! Please feel free to submit a Pull Request.

1. Fork the repository
2. Create your feature branch (`git checkout -b feature/AmazingFeature`)
3. Commit your changes (`git commit -m 'Add some AmazingFeature'`)
4. Push to the branch (`git push origin feature/AmazingFeature`)
5. Open a Pull Request

## License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

## Acknowledgments

- [OpenAlex](https://openalex.org/) - Open academic catalog
- [arXiv](https://arxiv.org/) - Preprint server
- [Semantic Scholar](https://www.semanticscholar.org/) - AI-powered research tool
- [Unpaywall](https://unpaywall.org/) - Open access database
- [PubMed Central](https://www.ncbi.nlm.nih.gov/pmc/) - Free full-text archive

## Disclaimer

This tool is for academic research purposes only. Please respect copyright laws and terms of service of the data sources. Users are responsible for ensuring their use complies with applicable regulations and publisher policies.
