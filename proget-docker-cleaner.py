import argparse
import asyncio
import time

from core.proget import (
    login_to_proget,
    get_repositories,
    get_images,
    delete_untagged_images,
)


async def main():
    parser = argparse.ArgumentParser(
        description="Clean up untagged Docker images from ProGet registry"
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
    parser.add_argument("-dr",
        "--dry-run", action="store_true", help="Run without making actual deletions"
    )
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically confirm deletion without prompting (default: False)",
    )

    args = parser.parse_args()

    # Start timing
    start_time = time.time()

    try:
        print("=" * 80)
        print("ProGet Docker Images Cleaner")
        print("=" * 80)
        if args.dry_run:
            print("[DRY RUN MODE] No actual changes will be made")
            print("=" * 80)

        # Phase 1: Authentication
        print("\n[Phase 1/4] Authenticating to ProGet...")
        page = await login_to_proget(args.host, args.username, args.password)

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
            await page.close()
            return

        print(f"Found {len(repositories)} repository(ies) to process")

        # Statistics
        total_stats = {
            "repos_processed": 0,
            "total_images": 0,
            "untagged_images": 0,
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

            # Count untagged images
            untagged_count = sum(1 for img in images if img.is_untagged)
            total_stats["untagged_images"] += untagged_count

            print(f"Found {len(images)} total images ({untagged_count} untagged)")

            if untagged_count == 0:
                print(f"No untagged images in {repo.full_name} - skipping")
                total_stats["repos_processed"] += 1
                continue

            # Confirmation prompt (unless --yes flag is set or dry-run)
            if not args.yes and not args.dry_run:
                response = input(
                    f"\nDelete {untagged_count} untagged images in {repo.full_name}? [y/N]: "
                )
                if response.lower() != "y":
                    print("Skipped by user")
                    continue

            # Phase 4: Image Deletion (directly delete untagged images)
            print(f"\n[Phase 4/4] Deleting {untagged_count} untagged images...")
            delete_stats = await delete_untagged_images(
                page=page,
                host=args.host,
                feed=repo.feed,
                repo=repo.name,
                images=images,
                dry_run=args.dry_run,
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
        print(f"Untagged images found:    {total_stats['untagged_images']}")
        print(f"Images deleted:           {total_stats['deleted_images']}")
        if total_stats["failed_deletes"] > 0:
            print(f"Failed to delete:         {total_stats['failed_deletes']}")

        if args.dry_run:
            print("\n[DRY RUN] No actual changes were made")

        # Calculate and display elapsed time
        elapsed_time = time.time() - start_time
        minutes = int(elapsed_time // 60)
        seconds = int(elapsed_time % 60)

        if minutes > 0:
            print(f"\nTotal elapsed time:       {minutes}min {seconds}sec")
        else:
            print(f"\nTotal elapsed time:       {seconds}sec")

        print("=" * 80)

        # Clean up
        await page.close()

    except KeyboardInterrupt:
        print("\n\nOperation cancelled by user")
    except Exception as e:
        print(f"\nError: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
