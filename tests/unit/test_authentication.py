"""Unit tests for authentication module."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.proget import login_to_proget


@pytest.mark.asyncio
async def test_login_navigates_to_correct_url():
    """Test that login navigates to the correct ProGet login URL."""
    mock_page = AsyncMock()
    mock_page.url = "https://proget.example.com/"
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("core.proget.async_playwright") as mock_async_playwright:
        mock_async_playwright.return_value.start = AsyncMock(
            return_value=mock_playwright
        )

        try:
            await login_to_proget(
                host="https://proget.example.com",
                username="testuser",
                password="testpass",
            )
        except Exception:
            pass  # We're just testing the navigation call

        mock_page.goto.assert_called_once_with("https://proget.example.com/log-in")


@pytest.mark.asyncio
async def test_login_fills_credentials():
    """Test that login fills in the username and password fields."""
    mock_page = AsyncMock()
    mock_page.url = "https://proget.example.com/"
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("core.proget.async_playwright") as mock_async_playwright:
        mock_async_playwright.return_value.start = AsyncMock(
            return_value=mock_playwright
        )

        try:
            await login_to_proget(
                host="https://proget.example.com",
                username="testuser",
                password="testpass",
            )
        except Exception:
            pass

        # Verify credentials were filled
        assert mock_page.fill.call_count == 2
        mock_page.fill.assert_any_call("#proget-login-user", "testuser")
        mock_page.fill.assert_any_call("#proget-login-password", "testpass")


@pytest.mark.asyncio
async def test_login_clicks_submit_button():
    """Test that login clicks the submit button."""
    mock_page = AsyncMock()
    mock_page.url = "https://proget.example.com/"
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("core.proget.async_playwright") as mock_async_playwright:
        mock_async_playwright.return_value.start = AsyncMock(
            return_value=mock_playwright
        )

        try:
            await login_to_proget(
                host="https://proget.example.com",
                username="testuser",
                password="testpass",
            )
        except Exception:
            pass

        mock_page.click.assert_called_once_with("#proget-login-button")


@pytest.mark.asyncio
async def test_login_failure_raises_exception():
    """Test that login failure raises an exception when still on login page."""
    mock_page = AsyncMock()
    mock_page.url = "https://proget.example.com/log-in"  # Still on login page
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("core.proget.async_playwright") as mock_async_playwright:
        mock_async_playwright.return_value.start = AsyncMock(
            return_value=mock_playwright
        )

        with pytest.raises(Exception, match="Login failed - still on login page"):
            await login_to_proget(
                host="https://proget.example.com",
                username="baduser",
                password="badpass",
            )


@pytest.mark.asyncio
async def test_login_success_returns_page():
    """Test that successful login returns the authenticated page."""
    mock_page = AsyncMock()
    mock_page.url = "https://proget.example.com/"  # Redirected away from login
    mock_page.goto = AsyncMock()
    mock_page.wait_for_selector = AsyncMock()
    mock_page.fill = AsyncMock()
    mock_page.click = AsyncMock()
    mock_page.wait_for_load_state = AsyncMock()

    mock_context = AsyncMock()
    mock_context.new_page = AsyncMock(return_value=mock_page)

    mock_browser = AsyncMock()
    mock_browser.new_context = AsyncMock(return_value=mock_context)

    mock_playwright = MagicMock()
    mock_playwright.chromium.launch = AsyncMock(return_value=mock_browser)

    with patch("core.proget.async_playwright") as mock_async_playwright:
        mock_async_playwright.return_value.start = AsyncMock(
            return_value=mock_playwright
        )

        page, browser, playwright = await login_to_proget(
            host="https://proget.example.com",
            username="testuser",
            password="testpass",
        )

        assert page == mock_page
        assert browser == mock_browser
        assert playwright == mock_playwright
