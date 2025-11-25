"""Shared pytest fixtures and configuration."""

import pytest
from playwright.async_api import async_playwright


@pytest.fixture
async def browser():
    """Provide a Playwright browser instance.

    Yields:
        Browser instance that is automatically closed after test
    """
    playwright = await async_playwright().start()
    browser = await playwright.chromium.launch(headless=True)
    yield browser
    await browser.close()
    await playwright.stop()


@pytest.fixture
async def page(browser):
    """Provide a Playwright page instance.

    Args:
        browser: Browser fixture

    Yields:
        Page instance that is automatically closed after test
    """
    context = await browser.new_context()
    page = await context.new_page()
    yield page
    await page.close()


@pytest.fixture
def proget_test_credentials():
    """Provide test ProGet credentials.

    Returns:
        Dictionary with host, username, and password
    """
    return {
        "host": "https://proget.gsf.ai",
        "username": "test",
        "password": "test123",
    }
