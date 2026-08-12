"""ProGet API interaction module.

This module handles all interactions with ProGet including authentication,
repository discovery, image enumeration, and cleanup operations.
"""

import re
from dataclasses import dataclass
from playwright.async_api import Page, Browser, Playwright, async_playwright
import aiohttp


async def login_to_proget(host: str, username: str, password: str, headless: bool = True) -> tuple[Page, Browser, Playwright]:
    """Login to ProGet using Playwright browser automation.

    Args:
        host: ProGet host URL (e.g., https://proget.mysite.com)
        username: ProGet username
        password: ProGet password
        headless: Whether to run browser in headless mode (default: True)

    Returns:
        Tuple of (Page, Browser, Playwright): Authenticated page, browser, and playwright instances
            These must be properly closed after use to avoid resource leaks

    Raises:
        Exception: If login fails
    """
    # Remove trailing slash from host if present
    host = host.rstrip("/")

    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=headless)
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

    return page, browser, playwright


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
    # Example: /containers/tags/feed123/my-repo/latest/overview
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

    def matches_tag_prefix(self, prefixes: list[str]) -> bool:
        """Check if any tag starts with any of the given prefixes.

        Args:
            prefixes: List of tag prefixes to match against

        Returns:
            True if at least one tag starts with at least one prefix, False otherwise
        """
        return any(tag.startswith(prefix) for tag in self.tags for prefix in prefixes)


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


def identify_prefix_matched_images(
    images: list[DockerImage], prefixes: list[str]
) -> list[DockerImage]:
    """Filter images whose tags match any of the given prefixes.

    Args:
        images: List of all images
        prefixes: List of tag prefixes to match against

    Returns:
        List of images with at least one tag matching at least one prefix
    """
    return [img for img in images if img.matches_tag_prefix(prefixes)]


def identify_images_to_delete(
    images: list[DockerImage],
    tag_prefixes: list[str] | None = None,
    include_untagged: bool = False,
) -> list[DockerImage]:
    """Identify images to delete based on the selected cleanup criteria.

    Args:
        images: List of all images
        tag_prefixes: Optional list of tag prefixes; images with a matching tag are included
        include_untagged: If True, untagged images are included

    Returns:
        List of images to delete, deduplicated by digest (untagged images first,
        then prefix-matched images not already included)
    """
    to_delete: list[DockerImage] = []
    seen_digests: set[str] = set()

    if include_untagged:
        for img in identify_untagged_images(images):
            if img.digest not in seen_digests:
                to_delete.append(img)
                seen_digests.add(img.digest)

    if tag_prefixes:
        for img in identify_prefix_matched_images(images, tag_prefixes):
            if img.digest not in seen_digests:
                to_delete.append(img)
                seen_digests.add(img.digest)

    return to_delete


async def delete_image(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    digest: str,
    dry_run: bool = False,
) -> bool:
    """Delete an image using Docker Registry V2 API.

    The deletion process:
    1. Create a temporary tag for the image using its short digest
    2. Get the full SHA256 digest from the tag's manifest
    3. Delete the temporary tag
    4. Delete the image using the full digest

    Args:
        page: Authenticated Playwright page (for session cookies and UI interaction)
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

        temp_tag = f"delete-{digest}"

        async with aiohttp.ClientSession(cookies=cookie_dict) as session:
            # Step 1: Create a temporary tag for this image using ProGet UI
            # We need to get the repository ID first from the page
            # Navigate to the repository to get the repositoryId
            repo_url = f"{host}/containers/repositories/{feed}/{repo}/images"
            await page.goto(repo_url)
            await page.wait_for_load_state("networkidle")

            # Extract repositoryId from the page
            content = await page.content()
            repo_id_match = re.search(r'repositoryId=(\d+)', content)
            if not repo_id_match:
                raise Exception(f"Could not find repository ID for {feed}/{repo}")
            repo_id = repo_id_match.group(1)

            # Create tag via ProGet UI form POST
            create_tag_url = f"{host}/docker-pages/tags/create?repositoryId={repo_id}"

            # Get CSRF token from page
            csrf_match = re.search(r'name="AHAntiCsrfToken" value="([^"]+)"', content)
            if not csrf_match:
                raise Exception("Could not find CSRF token")
            csrf_token = csrf_match.group(1)

            # POST to create the tag
            form_data = {
                'AHAntiCsrfToken': csrf_token,
                'ah0~ah4~ah0': temp_tag,  # Tag name
                'ah0~ah5~ah0': digest,     # Image (short digest)
                'ah0~ah7~ah0': 'Create Tag'  # Submit button
            }

            async with session.post(create_tag_url, data=form_data) as response:
                if response.status not in (200, 302):
                    raise Exception(
                        f"Failed to create temporary tag: HTTP {response.status}"
                    )

            # Step 2: Get the full digest from the temporary tag's manifest
            manifest_url = f"{host}/v2/{feed}/{repo}/manifests/{temp_tag}"
            headers = {
                'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
            }

            async with session.head(manifest_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to get manifest for temp tag: HTTP {response.status}"
                    )

                if 'Docker-Content-Digest' not in response.headers:
                    raise Exception("No Docker-Content-Digest header in response")

                full_digest = response.headers['Docker-Content-Digest']

            # Step 3: Delete the temporary tag
            delete_tag_url = f"{host}/v2/{feed}/{repo}/manifests/{temp_tag}"
            async with session.delete(delete_tag_url) as response:
                # Ignore errors here - the tag might not exist or might be auto-deleted
                pass

            # Step 4: Delete the image using the full digest
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


async def delete_images(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    images: list[DockerImage],
    dry_run: bool = False,
    tag_prefixes: list[str] | None = None,
    include_untagged: bool = False,
) -> dict[str, int]:
    """Delete images matching the selected cleanup criteria.

    Args:
        page: Authenticated Playwright page
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name
        images: List of all images in the repository
        dry_run: If True, simulate deletion without making actual API calls
        tag_prefixes: Optional list of tag prefixes; images with a matching tag are included
        include_untagged: If True, untagged images are included

    Returns:
        Dictionary with statistics:
        - total: Total number of images to delete
        - deleted: Number of images successfully deleted
        - failed: Number of images that failed to delete
    """
    # Identify images matching the selected criteria
    to_delete = identify_images_to_delete(images, tag_prefixes, include_untagged)

    stats = {"total": len(to_delete), "deleted": 0, "failed": 0}

    if not to_delete:
        print(f"No images to delete in {feed}/{repo}")
        return stats

    print(f"Found {len(to_delete)} images to delete in {feed}/{repo}")

    # Optimize: Get repository ID and CSRF token once for all deletions
    host = host.rstrip("/")
    repo_url = f"{host}/containers/repositories/{feed}/{repo}/images"
    await page.goto(repo_url)
    await page.wait_for_load_state("networkidle")

    content = await page.content()
    repo_id_match = re.search(r'repositoryId=(\d+)', content)
    if not repo_id_match:
        print(f"Error: Could not find repository ID for {feed}/{repo}")
        stats["failed"] = stats["total"]
        return stats

    repo_id = repo_id_match.group(1)

    # Delete each image
    for idx, image in enumerate(to_delete, start=1):
        print(f"[{idx}/{len(to_delete)}] Deleting {image.digest}...")

        success = await delete_image_optimized(
            page=page,
            host=host,
            feed=feed,
            repo=repo,
            repo_id=repo_id,
            digest=image.digest,
            dry_run=dry_run,
        )

        if success:
            stats["deleted"] += 1
        else:
            stats["failed"] += 1

    print(
        f"Deleted {stats['deleted']}/{stats['total']} images in {feed}/{repo}"
    )
    if stats["failed"] > 0:
        print(f"Failed to delete {stats['failed']} images")

    return stats


async def delete_image_optimized(
    page: Page,
    host: str,
    feed: str,
    repo: str,
    repo_id: str,
    digest: str,
    dry_run: bool = False,
) -> bool:
    """Delete an image using Docker Registry V2 API (optimized version).

    This is an optimized version that doesn't need to fetch the repo ID on each call.

    The deletion process:
    1. Create a temporary tag for the image using its short digest (via Playwright form interaction)
    2. Get the full SHA256 digest from the tag's manifest
    3. Delete the image using the full digest (tag gets deleted automatically)

    Args:
        page: Authenticated Playwright page (for browser automation and cookies)
        host: ProGet host URL
        feed: Container feed name
        repo: Repository name
        repo_id: Repository ID (fetched once for the whole batch)
        digest: Image digest (short form, 12 chars)
        dry_run: If True, simulate deletion without making actual API calls

    Returns:
        True if deletion succeeded, False otherwise
    """
    if dry_run:
        print(f"[DRY RUN] Would delete {feed}/{repo}@{digest}")
        return True

    try:
        temp_tag = f"delete-{digest}"

        # Step 1: Create a temporary tag using Playwright form interaction
        # Navigate to the tag creation page
        create_tag_url = f"{host}/docker-pages/tags/create?repositoryId={repo_id}"
        await page.goto(create_tag_url)
        await page.wait_for_load_state("networkidle")

        # Fill the form
        await page.fill('#ah0_ah4_ah0', temp_tag)  # Tag name field
        await page.fill('#ah0_ah5_ah0', digest)     # Image field (short digest)

        # Click the Create Tag button
        await page.click('a[name="ah0~ah7~ah0"]')

        # Wait for the form submission to complete
        await page.wait_for_load_state("networkidle")

        # Step 2: Get the full digest from the temporary tag's manifest
        cookies = await page.context.cookies()
        cookie_dict = {cookie["name"]: cookie["value"] for cookie in cookies}

        async with aiohttp.ClientSession(cookies=cookie_dict) as session:
            manifest_url = f"{host}/v2/{feed}/{repo}/manifests/{temp_tag}"
            headers = {
                'Accept': 'application/vnd.docker.distribution.manifest.v2+json'
            }

            async with session.head(manifest_url, headers=headers) as response:
                if response.status != 200:
                    raise Exception(
                        f"Failed to get manifest for temp tag: HTTP {response.status}"
                    )

                if 'Docker-Content-Digest' not in response.headers:
                    raise Exception("No Docker-Content-Digest header in response")

                full_digest = response.headers['Docker-Content-Digest']

            # Step 3: Delete the image using the full digest
            # Note: Deleting the image will also delete all its tags including our temp tag
            delete_url = f"{host}/v2/{feed}/{repo}/manifests/{full_digest}"
            async with session.delete(delete_url) as response:
                if response.status not in (200, 202):
                    raise Exception(
                        f"Failed to delete image: HTTP {response.status}"
                    )

        return True

    except Exception as e:
        print(f"Error deleting {digest}: {e}")
        return False
