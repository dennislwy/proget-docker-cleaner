# ProGet Docker Images Cleaner

A Python CLI tool that automatically cleans up untagged Docker images from a ProGet container registry.
Useful for reducing storage usage and keeping your container repository tidy.

This tool:
1. Logs into a self-hosted ProGet instance
2. Retrieves all repository names
3. Fetches all images (tagged + untagged) for each repository
4. Tags untagged images using delete-{counter}
5. Deletes those tagged images
6. Repeats the process for each repository or a specific repo

Supports **dry-run**, **single-repo**, and authenticated access.

## Features
- 🔐 Authenticates using ProGet username + password
- 📦 Retrieves all repositories automatically
- 🏷️ Identifies untagged images safely
- 🗑️ Tags + deletes old images using the ProGet Docker API
- 🧪 Dry-run mode for safe simulation
- 🧭 Optional repo filtering (--repo)
- ⚙️ Clean and easy-to-extend Python codebase

## Project Structure

```
proget-docker-cleaner/
├── docs/                            # Documentation
├── tests/                           # Test suite
├── proget-docker-cleaner.py         # Main CLI tool
├── pyproject.toml                   # Project dependencies and metadata
├── README.md                        # This file
├── uv.lock                          # Dependency lock file
└── .gitignore                       # Git ignore patterns
```

## Installation

Clone the repo:
```bash
git clone https://github.com/dennislwy/proget-docker-cleaner.git
cd proget-docker-cleaner
```

Install dependencies:
```bash
uv sync
```

## Usage
### Basic usage
```
python cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password yourpassword
```

### Clean only a specific repository
```
python cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --repo payment-service
```

### 🧪 Dry run (no deletions, only print actions)
```
python cleaner.py \
  --host https://proget.mysite.com \
  --username admin \
  --password pw123 \
  --dry-run
```

Nothing will be deleted — useful for validation.

## Command Line Arguments
| Flag                | Required | Description                                       |
| ------------------- | -------- | ------------------------------------------------- |
| `--host <url>`      | Yes      | Base ProGet URL, e.g. `https://proget.mysite.com` |
| `--username <user>` | Yes      | ProGet username                                   |
| `--password <pass>` | Yes      | ProGet password                                   |
| `--dry-run`         | No       | Simulate actions without deletion                 |
| `--repo <name>`     | No       | Only clean one specific repository                |
| `--concurrency <n>` | No       | Clean multiple repos concurrently (default: 1)    |

## Technologies Used
- Python 3.12+
- uv
- argparse
- playwright
- aiohttp

## Safety Notes
- Always run with --dry-run before real deletion
- Avoid using high concurrency if your ProGet server is small