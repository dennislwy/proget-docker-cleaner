# ProGet Docker Images Cleaner

A Python CLI tool that automatically cleans up Docker images from a ProGet container registry —
untagged images, images with tags matching a prefix list (e.g. `mr-`, `test-`), or both.
Useful for reducing storage usage and keeping your container repository tidy.

This tool:
1. Logs into a self-hosted ProGet instance
2. Retrieves all repository names
3. Fetches all images (tagged + untagged) for each repository
4. Identifies images matching your chosen criteria (untagged and/or tag-prefix)
5. Creates temporary tags for matched images to obtain their full SHA256 digests
6. Deletes images using Docker Registry V2 API with full digests
7. Repeats the process for each repository or a specific repo

Supports **dry-run**, **single-repo**, **auto-confirmation**, and authenticated access.

## Features
- 🔐 Authenticates using ProGet username + password
- 📦 Retrieves all repositories automatically
- 🔍 Identifies untagged images and/or images with tags matching a prefix list (untagged images made up 94.1% of images in one typical ProGet installation!)
- 🏷️ Smart tagging approach to obtain full SHA256 digests from short digests
- 🗑️ Deletes untagged images (`-iu`/`--include-untagged`) and/or images with tags matching a prefix list (`-ip`/`--include-prefix`) using Docker Registry V2 API
- 🧪 Dry-run mode for safe simulation
- ✅ Auto-confirmation mode (`-y`/`--yes`) for automated scripts
- 🧭 Optional repo filtering (`--repo`)
- ⚡ Concurrent processing support (planned)
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
│   │   └── test_repository_live.py
│   └── unit/                        # Unit tests
│       ├── __init__.py
│       ├── test_authentication.py
│       ├── test_cli.py
│       ├── test_deletion.py
│       ├── test_image.py
│       └── test_repository.py
├── analyze_repos.py                 # Analysis script to scan all repositories
├── proget-docker-cleaner.py         # Main CLI tool
├── pyproject.toml                   # Project dependencies and metadata
├── uv.lock                          # Dependency lock file
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
- ✅ Identify untagged images and images with tags matching a prefix list
- ✅ DockerImage dataclass with `is_untagged` property and `matches_tag_prefix()` method
- ✅ Test coverage: unit tests in `tests/unit/test_image.py` + 4 integration tests

**Phase 4: Image Deletion Operations**
- ✅ Delete individual images using Docker Registry V2 API
- ✅ Batch deletion of images matching the selected criteria (`--include-untagged`/`--include-prefix`)
- ✅ Tag-then-delete approach: temporary tagging via Playwright form automation
- ✅ Extract full SHA256 digest from tag manifests
- ✅ DELETE manifest by full digest using Docker Registry V2 API
- ✅ Dry-run mode support
- ✅ Deletion statistics tracking
- ✅ Error handling and detailed logging
- ✅ Production-tested: Successfully deleted 142/142 images in 3min 35sec

**Total Test Coverage**: 87 tests across unit and integration suites

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

### Basic usage (clean untagged images)
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password yourpassword \
  --include-untagged
```

### Clean only a specific repository
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --repo payment-service \
  --include-untagged
```

### 🧪 Dry run (no deletions, only print actions)
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --include-untagged \
  --dry-run
```

### ✅ Auto-confirm deletion (for automation/scripts)
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --include-untagged \
  --yes

# Or use short form
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --include-untagged \
  -y
```

### 🏷️ Clean images by tag prefix (e.g. merge-request or test builds)
```bash
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --include-prefix "mr-,test"

# Combine with untagged cleanup
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --include-untagged \
  --include-prefix "mr-,test"
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

| Flag                      | Short | Required | Description                                                         |
| ------------------------- | ----- | -------- | ------------------------------------------------------------------- |
| `--host <url>`            | `-s`  | Yes      | Base ProGet URL, e.g. `https://proget.mysite.com`                   |
| `--username <user>`       | `-u`  | Yes      | ProGet username                                                     |
| `--password <pass>`       | `-p`  | Yes      | ProGet password                                                     |
| `--feed <name>`           | `-f`  | No       | Container feed name (default: docker)                               |
| `--dry-run`               | `-dr` | No       | Simulate actions without deletion                                   |
| `--yes`                   | `-y`  | No       | Auto-confirm deletion without prompting (default: False)            |
| `--repo <name>`           | `-r`  | No       | Only clean one specific repository                                  |
| `--include-untagged`      | `-iu` | No\*     | Include untagged images in cleanup (default: False)                 |
| `--include-prefix <list>` | `-ip` | No\*     | Comma-separated tag prefixes to include in cleanup, e.g. `mr-,test` |
| `--debug`                 | `-d`  | No       | Show browser window for debugging (default: headless)               |
| `--concurrency <n>`       | `-c`  | No       | Clean multiple repos concurrently (default: 1)                      |

\* At least one of `--include-untagged` or `--include-prefix` must be specified, or the tool exits with an error.

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

1. **Authentication Module** (`core/proget.py`): Handles login and session management
2. **Repository Discovery** (`core/proget.py`): Fetches and parses repository list
3. **Image Enumeration** (`core/proget.py`): Identifies tagged and untagged images
4. **Image Deletion** (`core/proget.py`): Tag-then-delete approach for untagged images
   - Creates temporary tags via Playwright form automation
   - Queries Docker Registry V2 API for full SHA256 digests
   - Deletes images by full digest
5. **Data Models**:
   - `Repository` dataclass for repository metadata
   - `DockerImage` dataclass for image data with `is_untagged` property

### Deletion Process Flow

The deletion process works around ProGet's limitation of only exposing short 12-character digests in the UI:

1. **Tag Creation**: Use Playwright to fill ProGet's "Create Tag" form with:
   - Tag name: `delete-{short_digest}` (temporary tag)
   - Image: `{short_digest}` (12-char digest from HTML)
2. **Digest Retrieval**: Query the tag's manifest via `HEAD /v2/{feed}/{repo}/manifests/delete-{short_digest}`
   - Extract full SHA256 digest from `Docker-Content-Digest` header
3. **Image Deletion**: Delete using `DELETE /v2/{feed}/{repo}/manifests/{full_sha256_digest}`
   - This automatically removes the image and all its tags (including the temporary tag)

## Safety Notes

- ⚠️ Always run with `--dry-run` before real deletion
- ⚠️ Review the list of images to be deleted
- ⚠️ Use `--yes` flag carefully - it skips confirmation prompts
- ⚠️ Avoid using high concurrency if your ProGet server is small
- ⚠️ The tool only deletes images matching the criteria you specify via `--include-untagged`/`--include-prefix` - all other images are safe
- ⚠️ Images with `delete-` prefix tags are considered untagged and to be deleted

### Running in Development

```bash
# For development/testing, use the test ProGet instance
python proget-docker-cleaner.py \
  --host https://proget.mysite.com \
  --username test \
  --password test123 \
  --include-untagged \
  --dry-run
```

## 🤝 Contributing

1. Fork the repository
2. Create a feature branch: `git checkout -b feature/amazing-feature`
3. Make your changes with tests
4. Ensure all tests pass: `uv run pytest tests/`
5. Maintain 100% code coverage
6. Submit a pull request

## 🙏 Sponsor

Like this project? **Leave a star**! ⭐⭐⭐⭐⭐

You love what I do? <a href="https://www.buymeacoffee.com/dennislwy" target="_blank"><img src="https://cdn.buymeacoffee.com/buttons/default-orange.png" alt="Buy Me A Coffee" height="41" width="174"></a>

Recognized my open-source contributions? [Nominate me](https://stars.github.com/nominate) as GitHub Star! 💫

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

