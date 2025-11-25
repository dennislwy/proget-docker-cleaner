import argparse
import asyncio

from core.proget import login_to_proget


async def main():
    parser = argparse.ArgumentParser(
        description="Clean up untagged Docker images from ProGet registry"
    )
    parser.add_argument(
        "--host", required=True, help="ProGet host URL (e.g., https://proget.mysite.com)"
    )
    parser.add_argument("--username", required=True, help="ProGet username")
    parser.add_argument("--password", required=True, help="ProGet password")
    parser.add_argument(
        "--dry-run", action="store_true", help="Run without making actual deletions"
    )

    args = parser.parse_args()

    try:
        # Test login
        page = await login_to_proget(args.host, args.username, args.password)

        # Keep browser open for inspection
        print("\nLogin successful! Browser will remain open for inspection.")
        print("Press Ctrl+C to close...")
        await asyncio.sleep(3600)  # Keep alive for 1 hour

    except Exception as e:
        print(f"Error: {e}")
        raise


if __name__ == "__main__":
    asyncio.run(main())
