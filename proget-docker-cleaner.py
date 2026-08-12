import argparse
import asyncio
import time

from core.proget import (
    login_to_proget,
    get_repositories,
    get_images,
    delete_images,
    identify_images_to_delete,
)


async def main():
    parser = argparse.ArgumentParser(
        description="Clean up Docker images from a ProGet registry by untagged and/or tag-prefix criteria"
    )
    parser.add_argument(
        "-s", "--host", required=True, help="ProGet host URL (e.g., https://proget.mysite.com)"
    )
    parser.add_argument("-u", "--username", required=True, help="ProGet username")
    parser.add_argument("-p", "--password", required=True, help="ProGet password")
    parser.add_argument("-f",
        "--feed", default="docker", help="Container feed name (default: docker)"
    )
    parser.add_argument("-r",
        "--repo", help="Optional: specific repository to clean (default: all repositories)"
    )
    parser.add_argument(
        "-iu",
        "--include-untagged",
        action="store_true",
        help="Include untagged images in cleanup (default: False)",
    )
    parser.add_argument(
        "-ip",
        "--include-prefix",
        help="Include images with any tag matching a comma-separated list of prefixes (e.g. 'mr-,test')",
    )
    parser.add_argument("-dr",
        "--dry-run", action="store_true", help="Run without making actual deletions"
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically confirm deletion without prompting (default: False)",
    )
    parser.add_argument(
        "-d",
        "--debug",
        action="store_true",
        help="Show browser window for debugging (default: headless mode)",
    )

    args = parser.parse_args()

    # Parse comma-separated tag prefixes into a list
    tag_prefixes = (
        [p.strip() for p in args.include_prefix.split(",") if p.strip()]
        if args.include_prefix
        else []
    )

    if not args.include_untagged and not tag_prefixes:
        parser.error(
            "At least one of --include-untagged or --include-prefix must be specified"
        )

    # Start timing
    start_time = time.time()

    # Initialize these outside try block so they're available in finally
    page = None
    browser = None
    playwright = None

    try:
        print("=" * 80)
        print("ProGet Docker Images Cleaner")
        print("=" * 80)
        if args.dry_run:
            print("[DRY RUN MODE] No actual changes will be made")
            print("=" * 80)

        # Phase 1: Authentication
        print("\n[Phase 1/4] Authenticating to ProGet...")
        page, browser, playwright = await login_to_proget(
            args.host,
            args.username,
            args.password,
            headless=not args.debug
        )

        # Phase 2: Repository Discovery
        print("\n[Phase 2/4] Discovering repositories...")
        repositories = await get_repositories(
            page=page,
            host=args.host,
            feed=args.feed,
            repo_filter=args.repo,
        )

        if not repositories:
            print(f"No repositories found with filter: {args.repo}")
            return

        print(f"Found {len(repositories)} repository(ies) to process")

        # Statistics
        total_stats = {
            "repos_processed": 0,
            "total_images": 0,
            "untagged_images": 0,
            "prefix_matched_images": 0,
            "images_to_delete": 0,
            "deleted_images": 0,
            "failed_deletes": 0,
        }

        # Process each repository
        for idx, repo in enumerate(repositories, start=1):
            print("\n" + "=" * 80)
            print(f"Processing repository {idx}/{len(repositories)}: {repo.full_name}")
            print("=" * 80)

            # Phase 3: Image Enumeration
            print(f"\n[Phase 3/4] Fetching images from {repo.full_name}...")
            images = await get_images(
                page=page,
                host=args.host,
                feed=repo.feed,
                repo=repo.name,
            )

            total_stats["total_images"] += len(images)

            # Identify images matching the selected cleanup criteria
            to_delete = identify_images_to_delete(
                images, tag_prefixes=tag_prefixes, include_untagged=args.include_untagged
            )
            untagged_count = (
                len([img for img in to_delete if img.is_untagged])
                if args.include_untagged else 0
            )
            prefix_matched_count = (
                len([img for img in to_delete if img.matches_tag_prefix(tag_prefixes)])
                if tag_prefixes
                else 0
            )
            total_stats["untagged_images"] += untagged_count
            total_stats["prefix_matched_images"] += prefix_matched_count
            total_stats["images_to_delete"] += len(to_delete)

            print(f"Found {len(images)} total images ({len(to_delete)} to delete)")

            if not to_delete:
                print(f"No images to delete in {repo.full_name} - skipping")
                total_stats["repos_processed"] += 1
                continue

            # Confirmation prompt (unless --yes flag is set or dry-run)
            if not args.yes and not args.dry_run:
                response = input(
                    f"\nDelete {len(to_delete)} images in {repo.full_name}? [y/N]: "
                )
                if response.lower() != "y":
                    print("Skipped by user")
                    continue

            # Phase 4: Image Deletion
            print(f"\n[Phase 4/4] Deleting {len(to_delete)} images...")
            delete_stats = await delete_images(
                page=page,
                host=args.host,
                feed=repo.feed,
                repo=repo.name,
                images=images,
                dry_run=args.dry_run,
                images_to_delete=to_delete,
            )

            total_stats["deleted_images"] += delete_stats["deleted"]
            total_stats["failed_deletes"] += delete_stats["failed"]
            total_stats["repos_processed"] += 1

        # Final summary
        print("\n" + "=" * 80)
        print("FINAL SUMMARY")
        print("=" * 80)
        print(f"Repositories processed:   {total_stats['repos_processed']}/{len(repositories)}")
        print(f"Total images scanned:     {total_stats['total_images']}")
        if args.include_untagged:
            print(f"Untagged images found:    {total_stats['untagged_images']}")
        if tag_prefixes:
            print(f"Prefix-matched images:    {total_stats['prefix_matched_images']}")
        print(f"Images to delete:         {total_stats['images_to_delete']}")
        print(f"Images deleted:           {total_stats['deleted_images']}")
        if total_stats["failed_deletes"] > 0:
            print(f"Failed to delete:         {total_stats['failed_deletes']}")

        # Calculate and display elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        if minutes > 0:
            print(f"\nTotal elapsed time:       {minutes}min {seconds}sec")
        else:
            print(f"\nTotal elapsed time:       {seconds}sec")

        if args.dry_run:
            print("\n[DRY RUN] No actual changes were made")

        print("=" * 80)

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise
    finally:
        # Properly clean up Playwright resources to avoid asyncio warnings
        if page:
            await page.close()
        if browser:
            await browser.close()
        if playwright:
            await playwright.stop()


if __name__ == "__main__":
    asyncio.run(main())
