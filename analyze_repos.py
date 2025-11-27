"""Analysis script to scan all ProGet repositories and generate statistics.

This script connects to ProGet, scans all repositories, and generates a report
showing statistics about tagged vs untagged images in each repository.
"""

import argparse
import asyncio
from dataclasses import dataclass

from core.proget import (
    login_to_proget,
    get_repositories,
    get_images,
    identify_untagged_images,
)


@dataclass
class RepoStats:
    """Statistics for a single repository.

    Attributes:
        name: Repository name
        total_images: Total number of images
        tagged_images: Number of tagged images
        untagged_images: Number of untagged images
        percent_untagged: Percentage of untagged images
    """

    name: str
    total_images: int
    tagged_images: int
    untagged_images: int

    @property
    def percent_untagged(self) -> float:
        """Calculate percentage of untagged images."""
        if self.total_images == 0:
            return 0.0
        return (self.untagged_images / self.total_images) * 100


async def main():
    parser = argparse.ArgumentParser(
        description="Analyze ProGet repositories for untagged images"
    )
    parser.add_argument(
        "-s",
        "--host",
        help="ProGet host URL",
    )
    parser.add_argument(
        "-u", "--username", default="test", help="ProGet username (default: test)"
    )
    parser.add_argument(
        "-p",
        "--password",
        default="test123",
        help="ProGet password (default: test123)",
    )
    parser.add_argument(
        "-f",
        "--feed",
        default="docker",
        help="Container feed name (default: docker)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show browser window for debugging (default: headless mode)",
    )

    args = parser.parse_args()

    # Initialize these outside try block so they're available in finally
    page = None
    browser = None
    playwright = None

    try:
        print("=" * 80)
        print("ProGet Untagged Images Analysis")
        print("=" * 80)

        # Phase 1: Authentication
        print("\n[Phase 1/3] Authenticating to ProGet...")
        page, browser, playwright = await login_to_proget(
            args.host, args.username, args.password, headless=not args.debug
        )

        # Phase 2: Repository Discovery
        print("\n[Phase 2/3] Discovering repositories...")
        repositories = await get_repositories(
            page=page,
            host=args.host,
            feed=args.feed,
        )

        if not repositories:
            print("No repositories found")
            return

        print(f"Found {len(repositories)} repositories")

        # Phase 3: Analyze each repository
        print("\n[Phase 3/3] Analyzing repositories...")
        repo_stats_list: list[RepoStats] = []

        for idx, repo in enumerate(repositories, start=1):
            print(f"[{idx}/{len(repositories)}] Analyzing {repo.full_name}...")

            # Fetch images for this repository
            images = await get_images(
                page=page,
                host=args.host,
                feed=repo.feed,
                repo=repo.name,
            )

            # Count tagged vs untagged
            untagged = identify_untagged_images(images)
            tagged = len(images) - len(untagged)

            stats = RepoStats(
                name=repo.name,
                total_images=len(images),
                tagged_images=tagged,
                untagged_images=len(untagged),
            )

            repo_stats_list.append(stats)

        # Generate report
        print_report(repo_stats_list)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        # Properly clean up Playwright resources
        if page:
            await page.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


def print_report(stats_list: list[RepoStats]):
    """Print the analysis report.

    Args:
        stats_list: List of repository statistics
    """
    # Sort by total images descending
    stats_list.sort(key=lambda s: s.total_images, reverse=True)

    print("\n" + "=" * 80)
    print("ProGet Untagged Images Analysis")
    print("=" * 80)
    print()

    # Print header
    print(
        f"{'Repository':<40} {'Total':<8} {'Tagged':<8} {'Untagged':<10} {'%':<6}"
    )
    print("-" * 40 + " " + "-" * 8 + " " + "-" * 8 + " " + "-" * 10 + " " + "-" * 6)

    # Print each repository
    total_images = 0
    total_tagged = 0
    total_untagged = 0

    for stats in stats_list:
        print(
            f"{stats.name:<40} {stats.total_images:<8} {stats.tagged_images:<8} "
            f"{stats.untagged_images:<10} {stats.percent_untagged:>5.1f}%"
        )

        total_images += stats.total_images
        total_tagged += stats.tagged_images
        total_untagged += stats.untagged_images

    # Print totals
    print("-" * 40 + " " + "-" * 8 + " " + "-" * 8 + " " + "-" * 10 + " " + "-" * 6)

    total_percent_untagged = (
        (total_untagged / total_images * 100) if total_images > 0 else 0.0
    )

    print(
        f"{'TOTAL':<40} {total_images:<8} {total_tagged:<8} "
        f"{total_untagged:<10} {total_percent_untagged:>5.1f}%"
    )

    print()
    print(f"Total Repositories: {len(stats_list):,}")
    print(f"Total Images: {total_images:,}")
    print(f"Total Tagged Images: {total_tagged:,}")
    print(f"Total Untagged Images: {total_untagged:,} ({total_percent_untagged:.1f}%)")

    # Estimate storage to reclaim (rough estimate: 100-500 MB per image)
    min_storage_gb = (total_untagged * 100) // 1024  # Convert MB to GB
    max_storage_gb = (total_untagged * 500) // 1024  # Convert MB to GB

    print(f"Estimated Storage to Reclaim: {min_storage_gb} GB - {max_storage_gb} GB")


if __name__ == "__main__":
    asyncio.run(main())
