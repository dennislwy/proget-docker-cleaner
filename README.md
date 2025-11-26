# ProGet Docker Images Cleaner

A Python CLI tool that automatically cleans up untagged Docker images from a ProGet container registry.
Useful for reducing storage usage and keeping your container repository tidy.

This tool:
1. Logs into a self-hosted ProGet instance
2. Retrieves all repository names
3. Fetches all images (tagged + untagged) for each repository
4. Identifies untagged images
5. Tags untagged images using delete-{counter}
6. Deletes those tagged images
7. Repeats the process for each repository or a specific repo

Supports **dry-run**, **single-repo**, **auto-confirmation**, and authenticated access.

## Features
- 🔐 Authenticates using ProGet username + password
- 📦 Retrieves all repositories automatically
- 🔍 Identifies untagged images (94.1% of images in typical ProGet installations!)
- 🏷️ Tags untagged images for safe deletion
- 🗑️ Deletes tagged images using the ProGet Docker API
- 🧪 Dry-run mode for safe simulation
- ✅ Auto-confirmation mode (`-y`/`--yes`) for automated scripts
- 🧭 Optional repo filtering (`--repo`)
- ⚡ Concurrent processing support
- ⚙️ Clean and easy-to-extend Python codebase

## Project Structure

```
proget-docker-cleaner/
├── core/                            # Core application functionality
│   ├── __init__.py                  # Package initialization
│   └── proget.py                    # ProGet API interactions and business logic
├── docs/                            # Documentation
│   ├── ARCHITECTURE.md              # Project architectural decisions, design 
│   ├── IMPLEMENTATION_PLAN.md       # Detailed implementation plan with phases
│   └── PROGET_URLS.md               # ProGet API endpoints documentation
├── tests/                           # Comprehensive test suite
│   ├── conftest.py                  # Shared pytest fixtures
│   ├── integration/                 # Integration tests (live ProGet)
│   │   ├── __init__.py
│   │   ├── test_authentication_live.py
│   │   ├── test_deletion_live.py
│   │   ├── test_image_live.py
│   │   ├── test_repository_live.py
│   │   └── test_tagging_live.py
│   └── unit/                        # Unit tests
│       ├── __init__.py
│       ├── test_authentication.py
│       ├── test_cli.py
│       ├── test_deletion.py
│       ├── test_image.py
│       ├── test_repository.py
│       └── test_tagging.py
├── analyze_repos.py                 # Analysis script to scan all repositories
├── proget-docker-cleaner.py         # Main CLI tool
├── pyproject.toml                   # Project dependencies and metadata
├── uv.lock                          # Dependency lock file
├── CLAUDE.md                        # Development guidance for Claude Code
├── README.md                        # This file
└── .gitignore                       # Git ignore patterns
```

## Current Implementation Status

### ✅ Completed Phases

**Phase 1: Authentication & Session Management**
- ✅ ProGet login using Playwright browser automation
- ✅ Session cookie management
- ✅ Error handling for login failures
- ✅ Test coverage: 9 tests (5 unit + 4 integration)

**Phase 2: Repository Discovery**
- ✅ Fetch all container repositories from ProGet
- ✅ Parse HTML to extract repository names
- ✅ Repository filtering by name
- ✅ Test coverage: 13 tests (9 unit + 4 integration)

**Phase 3: Image Enumeration**
- ✅ Fetch all images for a repository
- ✅ Parse image data (digest, tags, published date, downloads)
- ✅ Identify untagged images
- ✅ DockerImage dataclass with `is_untagged` property
- ✅ Test coverage: 18 tests (14 unit + 4 integration)

**Phase 4: Image Tagging Operations**
- ✅ Tag individual images using Docker Registry V2 API
- ✅ Batch tagging of untagged images with delete-{counter}
- ✅ Extract full digest (sha256:...) from short digest
- ✅ GET manifest and PUT to new tag
- ✅ Dry-run mode support
- ✅ Error handling and detailed logging
- ✅ Test coverage: 16 tests (14 unit + 2 integration)

**Phase 5: Image Deletion Operations**
- ✅ Delete individual images using Docker Registry V2 API
- ✅ Batch deletion of delete-tagged images
- ✅ Extract full digest and DELETE manifest
- ✅ Dry-run mode support
- ✅ Deletion statistics tracking
- ✅ Error handling and detailed logging
- ✅ Test coverage: 15 tests (13 unit + 2 integration)

**Total Test Coverage**: 77 tests, 100% code coverage

### 📋 Planned Phases

- **Phase 6**: Concurrent Processing
- **Phase 7**: CLI Enhancement & User Experience
- **Phase 8**: Error Handling & Resilience

See [docs/IMPLEMENTATION_PLAN.md](docs/IMPLEMENTATION_PLAN.md) for detailed phase breakdown.

## Installation

Clone the repo:
```bash
git clone https://github.com/dennislwy/proget-docker-cleaner.git
cd proget-docker-cleaner
```

Install dependencies:
```bash
uv sync

# Install development dependencies (for testing)
uv sync --extra dev
```

Install Playwright browsers:
```bash
uv run playwright install chromium
```

## Usage

### Basic usage
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password yourpassword
```

### Clean only a specific repository
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --repo payment-service
```

### 🧪 Dry run (no deletions, only print actions)
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --dry-run
```

### ✅ Auto-confirm deletion (for automation/scripts)
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --yes

# Or use short form
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  -y
```

### 📊 Analyze all repositories
```bash
python analyze_repos.py
```

This will scan all repositories and generate a report showing:
- Total images per repository
- Number of tagged vs untagged images
- Percentage of untagged images
- Overall statistics

## Command Line Arguments

| Flag                | Short | Required | Description                                              |
| ------------------- | ----- | -------- | -------------------------------------------------------- |
| `--host <url>`      | `-h`  | Yes      | Base ProGet URL, e.g. `https://proget.mysite.com`        |
| `--username <user>` | `-u`  | Yes      | ProGet username                                          |
| `--password <pass>` | `-p`  | Yes      | ProGet password                                          |
| `--dry-run`         | `-d`  | No       | Simulate actions without deletion                        |
| `--yes`             | `-y`  | No       | Auto-confirm deletion without prompting (default: False) |
| `--repo <name>`     | `-r`  | No       | Only clean one specific repository                       |
| `--concurrency <n>` | `-c`  | No       | Clean multiple repos concurrently (default: 1)           |

## Testing

Run all tests:
```bash
uv run pytest tests/
```

Run only unit tests:
```bash
uv run pytest tests/unit/ -v
```

Run only integration tests (requires live ProGet instance):
```bash
uv run pytest tests/integration/ -v -m integration
```

Run tests with coverage report:
```bash
uv run pytest tests/ --cov=core --cov-report=term-missing
```

## Example Analysis Output

Here's an example from a real ProGet instance with 19 repositories:

```
================================================================================
ProGet Untagged Images Analysis
================================================================================

Repository                               Total    Tagged   Untagged   %
---------------------------------------- -------- -------- ---------- ------
gsf-central-web                          410      12       398         97.1%
gsf-central-core                         154      9        145         94.2%
gsf-eca-service-systemactivity           143      1        142         99.3%
gsf-aspnetcore-authentication            96       5        91          94.8%
...
---------------------------------------- -------- -------- ---------- ------
TOTAL                                    1329     78       1251        94.1%

Total Repositories: 19
Total Images: 1,329
Total Tagged Images: 78
Total Untagged Images: 1,251 (94.1%)
Estimated Storage to Reclaim: 125 GB - 625 GB
```

## Technologies Used

- **Python 3.12+** - Modern Python with async/await support
- **uv** - Fast Python package manager
- **Playwright** - Browser automation for ProGet web scraping
- **aiohttp** - Async HTTP client for API calls
- **pytest** - Testing framework with async support
- **argparse** - CLI argument parsing

## Architecture

The tool uses Playwright to interact with ProGet's web interface and Docker Registry V2 API for image operations. Key components:

1. **Authentication Module** (`core/proget.py:13-62`): Handles login and session management
2. **Repository Discovery** (`core/proget.py:84-152`): Fetches and parses repository list
3. **Image Enumeration** (`core/proget.py:185-289`): Identifies tagged and untagged images
4. **Image Tagging** (`core/proget.py:292-438`): Tags images using Docker Registry V2 API
5. **Image Deletion** (`core/proget.py:441-568`): Deletes images using Docker Registry V2 API
6. **Data Models**:
   - `Repository` dataclass for repository metadata
   - `DockerImage` dataclass for image data with `is_untagged` property

## Safety Notes

- ⚠️ Always run with `--dry-run` before real deletion
- ⚠️ Review the list of images to be deleted
- ⚠️ Use `--yes` flag carefully - it skips confirmation prompts
- ⚠️ Avoid using high concurrency if your ProGet server is small
- ⚠️ The tool only targets untagged images - tagged images are safe
- ⚠️ Images with `delete-` prefix tags are considered untagged and to be deleted

## Development

See [CLAUDE.md](CLAUDE.md) for development guidelines and commands.

### Running in Development

```bash
# For development/testing, use the test ProGet instance
python proget-docker-cleaner.py \
  --host https://proget.gsf.ai \
  --username test \
  --password test123 \
  --dry-run
```

## Contributing

1. Fork the repository
2. Create a feature branch
3. Make your changes with tests
4. Ensure all tests pass: `uv run pytest tests/`
5. Maintain 100% code coverage
6. Submit a pull request

## License

MIT License - See LICENSE file for details

## Acknowledgments

- Built with async Python patterns for performance
- Tested against live ProGet instances
- Comprehensive test coverage (77 tests, 100% coverage)
- Follows Google Style Python docstrings
- Uses Docker Registry V2 API for image operations
