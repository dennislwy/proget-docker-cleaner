"""ProGet API interaction module.

This module handles all interactions with ProGet including authentication,
repository discovery, image enumeration, and cleanup operations.
"""

import re
from dataclasses import dataclass
from playwright.async_api import Page, async_playwright


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
