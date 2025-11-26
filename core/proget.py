"""ProGet API interaction module.

This module handles all interactions with ProGet including authentication,
repository discovery, image enumeration, and cleanup operations.
"""

import re
from dataclasses import dataclass
from playwright.async_api import Page, async_playwright
import aiohttp


async def login_to_proget(host: str, username: str, password: str) -> Page:
    """Login to ProGet using Playwright browser automation.

    Args:
        host: ProGet host URL (e.g., https://proget.mysite.com)
        username: ProGet username
        password: ProGet password

    Returns:
        Page: Authenticated Playwright page with session cookies

    Raises:
        Exception: If login fails
    """
    # Remove trailing slash from host if present
    host = host.rstrip("/")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=False)
    context = await browser.new_context()
    page = await context.new_page()

    # Navigate to ProGet login page
    login_url = f"{host}/log-in"
    print(f"Navigating to {login_url}")
    await page.goto(login_url)

    # Wait for login form to be visible
    await page.wait_for_selector("#proget-login-user", timeout=10000)

    # Fill in login credentials
    print(f"Logging in as {username}")
    await page.fill("#proget-login-user", username)
    await page.fill("#proget-login-password", password)

    # Submit the form
    await page.click("#proget-login-button")

    # Wait for navigation after login
    await page.wait_for_load_state("networkidle")

    # Verify login success by checking if we're redirected away from login page
    current_url = page.url
    if "/log-in" in current_url:
        raise Exception("Login failed - still on login page")

    print(f"Successfully logged in to ProGet at {host}")
    print(f"Current URL: {current_url}")

    return page


@dataclass
class Repository:
    """Represents a container repository in ProGet.

    Attributes:
        feed: Container feed name (e.g., "docker")
        name: Repository name (e.g., "payment-service")
        full_name: Full repository path (e.g., "docker/payment-service")
    """

    feed: str
    name: str

    @property
    def full_name(self) -> str:
        """Get full repository path."""
        return f"{self.feed}/{self.name}"


async def get_repositories(
    page: Page, host: str, feed: str = "docker", repo_filter: str | None = None
) -> list[Repository]:
    """Fetch all container repositories from ProGet.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name (default: "docker")
        repo_filter: Optional repository name filter

    Returns:
        List of Repository objects

    Raises:
        Exception: If fetching repositories fails
    """
    # Remove trailing slash from host if present
    host = host.rstrip("/")

    # Navigate to containers page
    containers_url = f"{host}/containers?skip=0&take=1000"
    print(f"Fetching repositories from {containers_url}")
    await page.goto(containers_url)
    await page.wait_for_load_state("networkidle")

    # Get page content
    content = await page.content()

    # Parse repositories from HTML
    repositories = parse_repositories_html(content, feed)

    # Filter if repo_filter is provided
    if repo_filter:
        repositories = [r for r in repositories if r.name == repo_filter]

    print(f"Found {len(repositories)} repositories")
    return repositories


def parse_repositories_html(html_content: str, feed: str = "docker") -> list[Repository]:
    """Parse repository names from ProGet containers page HTML.

    The ProGet containers page contains links to tagged images in the format:
    /containers/tags/{feed}/{repository}/{tag}/overview

    Args:
        html_content: HTML content from /containers endpoint
        feed: Container feed name to filter by

    Returns:
        List of Repository objects
    """
    # Pattern to match container tag links
    # Example: /containers/tags/gsf/my-repo/latest/overview
    # We want to extract the repository name (group 1)
    pattern = rf'/containers/tags/{re.escape(feed)}/([^/"]+)/[^/"]+/overview'

    # Find all matches
    matches = re.findall(pattern, html_content)

    # Remove duplicates and create Repository objects
    unique_repos = list(set(matches))
    repositories = [Repository(feed=feed, name=repo) for repo in unique_repos]

    # Sort by name for consistent ordering
    repositories.sort(key=lambda r: r.name)

    return repositories


@dataclass
class DockerImage:
    """Represents a Docker image in ProGet.

    Attributes:
        digest: Image digest (short form, 12 chars, e.g., "a3b8c21afe97")
        tags: List of tags for this image
        published_date: Published date string
        downloads: Number of downloads
    """

    digest: str
    tags: list[str]
    published_date: str
    downloads: str

    @property
    def is_untagged(self) -> bool:
        """Check if image has no proper tags.

        An image is considered untagged if:
        - It has no tags at all
        - All its tags start with "delete-" (temporary cleanup tags)

        Returns:
            True if image is untagged, False otherwise
        """
        return len(self.tags) == 0 or all(t.startswith("delete-") for t in self.tags)


async def get_images(
    page: Page, host: str, feed: str, repo: str
) -> list[DockerImage]:
    """Fetch all images for a specific repository.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name

    Returns:
        List of DockerImage objects

    Raises:
        Exception: If fetching images fails
    """
    # Remove trailing slash from host if present
    host = host.rstrip("/")

    # Navigate to repository images page
    images_url = f"{host}/containers/repositories/{feed}/{repo}/images"
    print(f"Fetching images from {images_url}")
    await page.goto(images_url)
    await page.wait_for_load_state("networkidle")

    # Get page content
    content = await page.content()

    # Parse images from HTML
    images = parse_images_html(content)

    print(f"Found {len(images)} images in {feed}/{repo}")
    return images


def parse_images_html(html_content: str) -> list[DockerImage]:
    """Parse image data from ProGet repository images page HTML.

    The ProGet images page contains a table with rows for each image.
    Each row has: digest, tag, published date, vulnerabilities, downloads

    Args:
        html_content: HTML content from repository images page

    Returns:
        List of DockerImage objects
    """
    images = []

    # Pattern to match table rows with image data
    # Each row structure:
    # <tr>
    #   <td>digest</td>
    #   <td>tag or "untagged"</td>
    #   <td>published_date</td>
    #   <td>vulnerabilities</td>
    #   <td>downloads</td>
    # </tr>

    # Find all table rows (skip header)
    # Match each tr block individually
    row_pattern = r'<tr>\s*<td>([a-f0-9]{12})</td>\s*<td>(.*?)</td>\s*<td>([^<]+)</td>\s*<td[^>]*>.*?</td>\s*<td>([^<]*(?:\([^)]*\))?)</td>\s*</tr>'

    matches = re.findall(row_pattern, html_content, re.DOTALL)

    for match in matches:
        digest = match[0]
        tag_html = match[1]
        published_date = match[2].strip()
        downloads = match[3].strip()

        # Parse tags from tag_html
        tags = []
        if 'untagged' in tag_html:
            # This is an untagged image
            tags = []
        else:
            # Extract tag from link: <a href="/containers/tags/.../TAG/overview">TAG</a>
            tag_match = re.search(r'>([^<]+)</a>', tag_html)
            if tag_match:
                tags = [tag_match.group(1)]

        images.append(
            DockerImage(
                digest=digest,
                tags=tags,
                published_date=published_date,
                downloads=downloads,
            )
        )

    return images


def identify_untagged_images(images: list[DockerImage]) -> list[DockerImage]:
    """Filter out only untagged images.

    Args:
        images: List of all images

    Returns:
        List of untagged images only
    """
    return [img for img in images if img.is_untagged]


async def delete_image(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    digest: str,
    dry_run: bool = False,
) -> bool:
    """Delete an image using Docker Registry V2 API.

    Args:
        page: Authenticated Playwright page (for session cookies)
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name
        digest: Image digest (short form, 12 chars)
        dry_run: If True, simulate deletion without making actual API calls

    Returns:
        True if deletion succeeded, False otherwise

    Raises:
        Exception: If deletion fails
    """
    # Remove trailing slash from host if present
    host = host.rstrip("/")

    if dry_run:
        print(f"[DRY RUN] Would delete {feed}/{repo}@{digest}")
        return True

    try:
        # Get cookies from Playwright page for authentication
        cookies = await page.context.cookies()
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

        async with aiohttp.ClientSession(cookies=cookie_dict) as session:
            # Step 1: Get the full digest (sha256:...) from the short digest
            image_url = f"{host}/containers/images/{feed}/{repo}?digest={digest}"
            async with session.get(image_url) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to get image details: HTTP {response.status}"
                    )
                content = await response.text()

                # Extract full digest from page
                # Pattern: sha256:[64-char hex]
                full_digest_match = re.search(r"sha256:[a-f0-9]{64}", content)
                if not full_digest_match:
                    raise Exception(f"Could not find full digest for {digest}")
                full_digest = full_digest_match.group(0)

            # Step 2: Delete the image using the full digest
            # Docker Registry V2 API: DELETE /v2/{name}/manifests/{reference}
            delete_url = f"{host}/v2/{feed}/{repo}/manifests/{full_digest}"
            async with session.delete(delete_url) as response:
                if response.status not in (200, 202):
                    raise Exception(
                        f"Failed to delete image: HTTP {response.status}"
                    )

            print(f"Successfully deleted {feed}/{repo}@{digest}")
            return True

    except Exception as e:
        print(f"Error deleting image {feed}/{repo}@{digest}: {e}")
        return False


async def delete_untagged_images(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    images: list[DockerImage],
    dry_run: bool = False,
) -> dict[str, int]:
    """Delete all untagged images in a repository.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name
        images: List of all images in the repository
        dry_run: If True, simulate deletion without making actual API calls

    Returns:
        Dictionary with statistics:
        - total: Total number of untagged images to delete
        - deleted: Number of images successfully deleted
        - failed: Number of images that failed to delete
    """
    # Identify untagged images
    untagged = identify_untagged_images(images)

    stats = {"total": len(untagged), "deleted": 0, "failed": 0}

    if not untagged:
        print(f"No untagged images found in {feed}/{repo}")
        return stats

    print(f"Found {len(untagged)} untagged images in {feed}/{repo}")

    # Delete each untagged image directly by digest
    for image in untagged:
        success = await delete_image(
            page=page,
            host=host,
            feed=feed,
            repo=repo,
            digest=image.digest,
            dry_run=dry_run,
        )

        if success:
            stats["deleted"] += 1
        else:
            stats["failed"] += 1

    print(
        f"Deleted {stats['deleted']}/{stats['total']} untagged images in {feed}/{repo}"
    )
    if stats["failed"] > 0:
        print(f"Failed to delete {stats['failed']} images")

    return stats
