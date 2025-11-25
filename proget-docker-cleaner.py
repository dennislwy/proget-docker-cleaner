import argparse
import asyncio

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
