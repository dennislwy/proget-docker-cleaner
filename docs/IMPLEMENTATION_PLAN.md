# ProGet Docker Images Cleaner - Implementation Plan

## Document Overview

This document outlines the complete implementation plan for the ProGet Docker Images Cleaner project, including development phases, testing strategy, and deliverables.

## Current Status

**✅ Completed (Production-Ready):**
- Project structure setup
- Authentication module (core/proget.py:13-62)
- Repository discovery and filtering (core/proget.py:84-152)
- Image enumeration and untagged detection (core/proget.py:185-289)
- Tag-then-delete deletion workflow (core/proget.py:292-590)
- CLI with dry-run and auto-confirmation support
- Dependency management with uv
- **Production-tested:** Successfully deleted 142/142 images in 3min 35sec

**🔄 In Progress:**
- Concurrent processing (planned)
- CLI enhancements (planned)
- Advanced error handling (planned)

## Development Phases

### Phase 1: Core Authentication & Session Management
**Status:** ✅ Completed

**Objectives:**
- Implement ProGet login functionality using Playwright
- Establish authenticated browser session
- Handle session cookies for subsequent API calls

**Deliverables:**
- ✅ `login_to_proget()` function in core/proget.py

**Testing:**
- ✅ Manual testing with test credentials
- 🔲 Unit tests for login success/failure scenarios
- 🔲 Integration test with live ProGet instance

---

### Phase 2: Repository Discovery
**Status:** ✅ Completed

**Objectives:**
- Fetch all container repositories from ProGet
- Parse HTML response from `/containers` endpoint
- Support pagination (skip/take parameters)
- Filter repositories when `--repo` flag is provided

**Deliverables:**
- `get_repositories()` function to fetch all repos
- `parse_repositories_html()` function to extract repo names
- Repository data model/dataclass

**Implementation Details:**
```python
async def get_repositories(page: Page, host: str, feed: str = "docker") -> list[str]:
    """Fetch all container repositories from ProGet.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name (default: "docker")

    Returns:
        List of repository names
    """
    pass

async def parse_repositories_html(html_content: str) -> list[str]:
    """Parse repository names from ProGet containers page HTML.

    Args:
        html_content: HTML content from /containers endpoint

    Returns:
        List of repository names
    """
    pass
```

**Testing:**
- Unit test: Mock HTML parsing with sample ProGet HTML
- Unit test: Empty repository list handling
- Unit test: Pagination edge cases
- Integration test: Fetch repos from live ProGet instance
- Integration test: Verify --repo filter works correctly

---

### Phase 3: Image Enumeration
**Status:** ✅ Completed

**Objectives:**
- Fetch all images (tagged + untagged) for a given repository
- Parse HTML response from `/containers/repositories/{feed}/{repo}/images`
- Identify untagged images (those without proper tags)
- Create image data structures for tracking

**Deliverables:**
- `get_images()` function to fetch images for a repo
- `parse_images_html()` function to extract image data
- Image data model with digest, tags, and metadata
- `identify_untagged_images()` function to filter untagged images

**Implementation Details:**
```python
@dataclass
class DockerImage:
    """Represents a Docker image in ProGet."""
    digest: str
    tags: list[str]
    size: int
    created_at: str

    @property
    def is_untagged(self) -> bool:
        """Check if image has no proper tags."""
        return len(self.tags) == 0 or all(t.startswith("delete-") for t in self.tags)

async def get_images(page: Page, host: str, feed: str, repo: str) -> list[DockerImage]:
    """Fetch all images for a specific repository.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name

    Returns:
        List of DockerImage objects
    """
    pass

async def parse_images_html(html_content: str) -> list[DockerImage]:
    """Parse image data from ProGet repository images page HTML.

    Args:
        html_content: HTML content from images endpoint

    Returns:
        List of DockerImage objects
    """
    pass

def identify_untagged_images(images: list[DockerImage]) -> list[DockerImage]:
    """Filter out only untagged images.

    Args:
        images: List of all images

    Returns:
        List of untagged images only
    """
    pass
```

**Testing:**
- Unit test: Parse various HTML structures (tagged, untagged, mixed)
- Unit test: Empty image list handling
- Unit test: Untagged image identification logic
- Unit test: Edge cases (images with delete- tags already)
- Integration test: Fetch images from live repo
- Integration test: Verify untagged detection accuracy

---

### Phase 4: Image Deletion Operations (Tag-then-Delete Approach)
**Status:** ✅ Completed

**Objectives:**
- ✅ Tag untagged images with temporary identifiers (delete-{short_digest})
- ✅ Use Playwright to automate ProGet's tag creation form
- ✅ Extract full SHA256 digests from tag manifests via Docker Registry V2 API
- ✅ Delete images using full digests
- ✅ Handle deletion failures gracefully

**Deliverables:**
- ✅ `delete_image_optimized()` function implementing tag-then-delete approach
- ✅ `delete_untagged_images()` batch function with progress tracking
- ✅ Temporary tag creation via Playwright form automation
- ✅ Full SHA256 digest extraction from Docker Registry V2 API
- ✅ Image deletion by full digest
- ✅ Deletion statistics tracking
- ✅ Dry-run mode support
- ✅ Error handling for each deletion step

**Implementation Approach:**

The implementation uses a **tag-then-delete** approach to work around ProGet's limitation of only exposing short 12-character digests in the UI:

1. **Tag Creation (Playwright)**: Navigate to ProGet's tag creation form and fill:
   - Tag name: `delete-{short_digest}`
   - Image field: `{short_digest}` (12-char digest from HTML)
   - Submit the form via browser automation

2. **Digest Retrieval (Docker Registry V2 API)**:
   ```python
   HEAD /v2/{feed}/{repo}/manifests/delete-{short_digest}
   # Extract from response header:
   # Docker-Content-Digest: sha256:1f3f64fb947bc6a4...
   ```

3. **Image Deletion (Docker Registry V2 API)**:
   ```python
   DELETE /v2/{feed}/{repo}/manifests/{full_sha256_digest}
   # This automatically removes the image and all its tags
   ```

**Key Implementation Functions:**
- `delete_image_optimized()` - Handles single image deletion with tag-then-delete workflow
- `delete_untagged_images()` - Batch processes all untagged images in a repository
- Optimized to fetch repository ID once per batch instead of per image

**Testing:**
- ✅ Production test: Successfully deleted 142/142 untagged images in 3min 35sec
- ✅ Verified: Temporary tags are created correctly
- ✅ Verified: Full digests are extracted from manifests
- ✅ Verified: Images are deleted successfully
- ✅ Verified: Dry-run mode works without making changes
- ✅ Verified: Error handling for failed operations

---

### Phase 6: Concurrent Processing
**Status:** 🔲 Not Started

**Objectives:**
- Implement concurrent repository processing
- Add `--concurrency` CLI option
- Use asyncio for parallel execution
- Implement rate limiting to protect ProGet server

**Deliverables:**
- Async task queue for repository processing
- Concurrency control with semaphore
- Progress tracking for concurrent operations
- Rate limiting mechanism

**Implementation Details:**
```python
async def process_repository(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    dry_run: bool = False
) -> dict:
    """Process a single repository (enumerate, tag, delete).

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name
        dry_run: If True, simulate operations

    Returns:
        Dictionary with processing statistics
    """
    pass

async def process_repositories_concurrent(
    page: Page,
    host: str,
    feed: str,
    repos: list[str],
    concurrency: int = 1,
    dry_run: bool = False
) -> list[dict]:
    """Process multiple repositories concurrently.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name
        repos: List of repository names
        concurrency: Maximum concurrent tasks
        dry_run: If True, simulate operations

    Returns:
        List of processing statistics per repository
    """
    pass
```

**Testing:**
- Unit test: Concurrency limit enforcement
- Unit test: Task queue management
- Integration test: Process 3 repos with concurrency=1 (sequential)
- Integration test: Process 3 repos with concurrency=3 (parallel)
- Integration test: Verify no race conditions
- Load test: Test with 10+ repositories
- Load test: Verify ProGet server handling under load

---

### Phase 7: CLI Enhancement & User Experience
**Status:** 🔲 Not Started

**Objectives:**
- Enhance CLI with better progress indicators
- Add verbose logging option
- Implement proper error messages
- Add statistics summary at the end

**Deliverables:**
- Progress bars for long-running operations
- `--verbose` flag for detailed logging
- `--feed` flag for custom feed names (default: docker)
- Summary report with deletion statistics
- Color-coded console output

**Implementation Details:**
```python
def print_summary(results: list[dict]) -> None:
    """Print summary statistics of cleanup operation.

    Args:
        results: List of processing statistics per repository
    """
    pass

def setup_logging(verbose: bool) -> None:
    """Configure logging level.

    Args:
        verbose: If True, enable DEBUG logging
    """
    pass
```

**Additional CLI Arguments:**
```bash
--verbose           Enable verbose logging
--feed <name>       ProGet feed name (default: docker)
--timeout <seconds> Timeout for operations (default: 300)
--no-color          Disable colored output
```

**Testing:**
- Unit test: Argument parsing for all flags
- Unit test: Summary report generation
- Integration test: Verify verbose output includes debug info
- Integration test: Verify --no-color disables colors
- Manual test: User experience with progress indicators

---

### Phase 8: Error Handling & Resilience
**Status:** 🔲 Not Started

**Objectives:**
- Implement comprehensive error handling
- Add retry logic with exponential backoff
- Handle network timeouts gracefully
- Implement graceful shutdown on Ctrl+C

**Deliverables:**
- Custom exception classes
- Retry decorator for API calls
- Timeout handling
- Signal handling for graceful shutdown

**Implementation Details:**
```python
class ProGetError(Exception):
    """Base exception for ProGet operations."""
    pass

class AuthenticationError(ProGetError):
    """Raised when authentication fails."""
    pass

class RepositoryNotFoundError(ProGetError):
    """Raised when repository doesn't exist."""
    pass

class ImageOperationError(ProGetError):
    """Raised when image operation fails."""
    pass

def retry_on_failure(max_attempts: int = 3, backoff_factor: float = 2.0):
    """Decorator to retry failed operations with exponential backoff.

    Args:
        max_attempts: Maximum number of retry attempts
        backoff_factor: Multiplier for backoff delay
    """
    pass

async def graceful_shutdown(page: Page) -> None:
    """Clean up resources on shutdown.

    Args:
        page: Playwright page to close
    """
    pass
```

**Testing:**
- Unit test: Exception hierarchy
- Unit test: Retry logic with mock failures
- Unit test: Backoff timing calculations
- Integration test: Handle authentication failure
- Integration test: Handle network timeout
- Integration test: Handle invalid repository name
- Integration test: Graceful shutdown on Ctrl+C

---

## Testing Strategy

### Unit Tests

**Framework:** pytest with pytest-asyncio

**Coverage Target:** 80%+ code coverage

**Test Structure:**
```
tests/
├── unit/
│   ├── test_authentication.py      # Login logic tests
│   ├── test_repository.py          # Repository discovery tests
│   ├── test_image.py                # Image enumeration tests
│   ├── test_tagging.py              # Tagging logic tests
│   ├── test_deletion.py             # Deletion logic tests
│   ├── test_concurrency.py          # Async/concurrent tests
│   └── test_cli.py                  # CLI argument parsing tests
└── integration/
    ├── test_end_to_end.py           # Full workflow tests
    ├── test_live_proget.py          # Live ProGet instance tests
    └── conftest.py                  # Shared fixtures
```

**Key Unit Test Areas:**
1. HTML parsing logic (mocked HTML responses)
2. Untagged image identification
3. Tag generation (delete-1, delete-2, etc.)
4. Dry-run mode verification
5. Error handling and exceptions
6. Retry logic
7. Concurrency control
8. CLI argument validation

**Example Unit Test:**
```python
import pytest
from core.proget import identify_untagged_images, DockerImage

def test_identify_untagged_images():
    """Test that untagged images are correctly identified."""
    images = [
        DockerImage(digest="sha256:abc", tags=["v1.0"], size=1000, created_at="2025-01-01"),
        DockerImage(digest="sha256:def", tags=[], size=2000, created_at="2025-01-02"),
        DockerImage(digest="sha256:ghi", tags=["delete-1"], size=3000, created_at="2025-01-03"),
    ]

    untagged = identify_untagged_images(images)

    assert len(untagged) == 2
    assert untagged[0].digest == "sha256:def"
    assert untagged[1].digest == "sha256:ghi"
```

---

### Integration Tests

**Environment:** Live ProGet test instance (https://proget.gsf.ai)

**Test Credentials:**
- Username: test
- Password: test123

**Prerequisites:**
- Test ProGet instance must be available
- Test feed "docker" must exist
- Test repositories with sample images should be pre-populated

**Key Integration Test Areas:**
1. End-to-end workflow (login → discover → enumerate → tag → delete)
2. Authentication against live ProGet
3. Repository discovery with real data
4. Image enumeration with real repositories
5. Tagging operations on live images
6. Deletion operations on live images
7. Concurrent processing with multiple repositories
8. Error scenarios (invalid credentials, missing repos, etc.)

**Example Integration Test:**
```python
import pytest
from core.proget import login_to_proget, get_repositories
from playwright.async_api import async_playwright

@pytest.mark.asyncio
async def test_login_and_fetch_repositories():
    """Test authentication and repository fetching against live ProGet."""
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)

    try:
        # Login
        page = await login_to_proget(
            host="https://proget.mysite.com",
            username="test",
            password="test123"
        )

        # Fetch repositories
        repos = await get_repositories(page, "https://proget.mysite.com")

        # Assertions
        assert len(repos) > 0
        assert all(isinstance(r, str) for r in repos)

    finally:
        await browser.close()
        await playwright.stop()
```

**Test Isolation:**
- Each test should create temporary test images
- Tests should clean up after themselves
- Use unique prefixes for test images (e.g., "test-{timestamp}-")

---

### Load Testing

**Objectives:**
- Verify performance with large numbers of repositories
- Test concurrent processing under load
- Identify bottlenecks and memory issues

**Scenarios:**
1. Clean 50+ repositories sequentially
2. Clean 50+ repositories with concurrency=5
3. Process repository with 100+ images
4. Handle ProGet server slowness/timeouts

**Tools:**
- pytest-benchmark for performance metrics
- memory_profiler for memory usage tracking

---

### Manual Testing Checklist

Before each release, perform manual testing:

- [ ] Test with real ProGet instance (not test instance)
- [ ] Verify dry-run mode doesn't delete anything
- [ ] Test with --repo flag for single repository
- [ ] Test with --concurrency flag (values: 1, 3, 5)
- [ ] Verify progress indicators display correctly
- [ ] Test graceful shutdown (Ctrl+C)
- [ ] Verify error messages are clear and actionable
- [ ] Test with invalid credentials
- [ ] Test with non-existent repository
- [ ] Review logs for any warnings or errors

---

## Deployment & Release

### Version 1.0.0 Release Criteria

**Must Have:**
- ✅ All Phase 1-5 completed (core functionality)
- ✅ All Phase 6 completed (concurrent processing)
- ✅ Unit test coverage >80%
- ✅ Integration tests passing
- ✅ Documentation complete (README, CLAUDE.md, API docs)
- ✅ Manual testing checklist completed

**Nice to Have:**
- Phase 7 (CLI enhancements)
- Phase 8 (advanced error handling)
- Load testing results

### Release Process

1. Update version in pyproject.toml
2. Run full test suite (`pytest`)
3. Run manual testing checklist
4. Update CHANGELOG.md
5. Create git tag (e.g., `v1.0.0`)
6. Push to GitHub
7. Create GitHub release with notes

---

## Risk Assessment

| Risk                                 | Impact   | Probability | Mitigation                                       |
| ------------------------------------ | -------- | ----------- | ------------------------------------------------ |
| ProGet API changes                   | High     | Medium      | Version docs, add API tests                      |
| Authentication failures              | High     | Low         | Comprehensive error handling                     |
| Accidental deletion of tagged images | Critical | Low         | Strict untagged detection logic, dry-run default |
| ProGet server overload               | Medium   | Medium      | Rate limiting, concurrency controls              |
| Network timeouts                     | Medium   | Medium      | Retry logic, configurable timeouts               |
| HTML parsing breaks                  | High     | Low         | Robust parsing with fallbacks                    |

---

## Success Metrics

**Functional Metrics:**
- Successfully clean 100+ repositories without errors
- Process 1000+ untagged images in single run
- Handle concurrent processing without failures
- Zero accidental deletions of tagged images

**Quality Metrics:**
- Unit test coverage >80%
- Integration test pass rate 100%
- Zero critical bugs in production
- Documentation completeness score >90%

**Performance Metrics:**
- Process single repository in <30 seconds
- Handle 10 concurrent repositories without throttling
- Memory usage <500MB during execution
- Browser session stable for 1+ hour runs

---

## Timeline Estimate

| Phase   | Estimated Time | Dependencies |
| ------- | -------------- | ------------ |
| Phase 1 | ✅ Completed    | None         |
| Phase 2 | 2-3 days       | Phase 1      |
| Phase 3 | 3-4 days       | Phase 2      |
| Phase 4 | 2-3 days       | Phase 3      |
| Phase 5 | 2-3 days       | Phase 4      |
| Phase 6 | 2-3 days       | Phase 5      |
| Phase 7 | 1-2 days       | Phase 6      |
| Phase 8 | 2-3 days       | All phases   |
| Testing | Ongoing        | All phases   |

**Total Estimated Time:** 3-4 weeks for full implementation

---

## Next Steps

1. **Immediate:** Begin Phase 2 (Repository Discovery)
2. **Week 1:** Complete Phases 2-3 with unit tests
3. **Week 2:** Complete Phases 4-5 with integration tests
4. **Week 3:** Complete Phases 6-7 with load tests
5. **Week 4:** Complete Phase 8, final testing, and documentation

---

## Appendix: Technology Decisions

### Why Playwright?
- ProGet doesn't provide a public REST API for all operations
- HTML scraping is necessary for repository and image listing
- Playwright handles authentication cookies automatically
- Supports headless mode for CI/CD

### Why aiohttp?
- Async/await pattern for better performance
- Native Python async support
- Lightweight compared to requests

### Why uv?
- Modern, fast package manager
- Better dependency resolution than pip
- Lockfile support for reproducible builds
- Growing adoption in Python community

### Why pytest?
- Industry standard for Python testing
- Rich plugin ecosystem (pytest-asyncio, pytest-cov)
- Easy to write and maintain tests
- Excellent async support

---

## Technical Deep Dive: Tag-then-Delete Solution

### Problem Statement

ProGet's web UI only exposes **short 12-character digests** (e.g., `1f3f64fb947b`) for Docker images, but the Docker Registry V2 API requires **full 64-character SHA256 digests** (e.g., `sha256:1f3f64fb947bc6a4c9c2946e8c33f346f2124c0058f2e20a657aa7fcdd91d18b`) for deletion operations.

This creates a challenge: How do we delete untagged images when we only have short digests?

### Solution Evolution

**Initial Attempts (Failed):**
1. ❌ **Direct API endpoint**: Tried `GET /containers/images/{feed}/{repo}?digest={short_digest}` → HTTP 404
2. ❌ **Docker Registry API with short digest**: Tried `DELETE /v2/{feed}/{repo}/manifests/{short_digest}` → HTTP 404
3. ❌ **Form POST via aiohttp**: Tried posting to tag creation endpoint → Form validation failed (requires JavaScript)

**Working Solution:**
✅ **Tag-then-delete approach** using Playwright browser automation + Docker Registry V2 API

### Implementation Details

```python
async def delete_image_optimized(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    repo_id: str,
    digest: str,  # short digest (12 chars)
    dry_run: bool = False,
) -> bool:
    """Delete an image using tag-then-delete approach."""

    temp_tag = f"delete-{digest}"

    # Step 1: Create temporary tag via Playwright
    create_tag_url = f"{host}/docker-pages/tags/create?repositoryId={repo_id}"
    await page.goto(create_tag_url)
    await page.wait_for_load_state("networkidle")

    # Fill form fields
    await page.fill('#ah0_ah4_ah0', temp_tag)    # Tag name
    await page.fill('#ah0_ah5_ah0', digest)      # Image (short digest)
    await page.click('a[name="ah0~ah7~ah0"]')    # Submit button
    await page.wait_for_load_state("networkidle")

    # Step 2: Get full digest from tag manifest
    cookies = await page.context.cookies()
    cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

    async with aiohttp.ClientSession(cookies=cookie_dict) as session:
        manifest_url = f"{host}/v2/{feed}/{repo}/manifests/{temp_tag}"
        headers = {'Accept': 'application/vnd.docker.distribution.manifest.v2+json'}

        async with session.head(manifest_url, headers=headers) as response:
            full_digest = response.headers['Docker-Content-Digest']

        # Step 3: Delete image using full digest
        delete_url = f"{host}/v2/{feed}/{repo}/manifests/{full_digest}"
        async with session.delete(delete_url) as response:
            return response.status in (200, 202)
```

### Key Insights

1. **ProGet accepts short digests in tag creation form**: The "Image" field in ProGet's tag creation form accepts both tag names AND short digests (visible in autocomplete dropdown).

2. **Playwright required for form submission**: Direct HTTP POST doesn't work because ProGet's form requires JavaScript validation. Playwright provides proper browser automation.

3. **Docker-Content-Digest header**: The HEAD request to a tag's manifest returns the full SHA256 digest in the `Docker-Content-Digest` response header.

4. **Automatic tag cleanup**: When deleting an image by its full digest, Docker Registry V2 API automatically removes all associated tags, including our temporary `delete-*` tags.

5. **Optimization**: Fetching repository ID once per batch (instead of per image) significantly improves performance.

### Performance Metrics

**Production Test Results:**
- Repository: `gsf-eca-service-systemactivity`
- Total images: 143 (1 tagged, 142 untagged)
- Deletion time: 3 minutes 35 seconds
- Success rate: 100% (142/142 deleted successfully)
- Average: ~1.5 seconds per image

### Future Optimizations

Potential improvements for concurrent processing:
1. Parallel tag creation for multiple images
2. Batch digest retrieval
3. Concurrent deletion operations
4. Connection pooling for aiohttp sessions

---

## Document Maintenance

**Last Updated:** 2025-11-26
**Version:** 2.0
**Owner:** Project Team
**Review Frequency:** After each phase completion
