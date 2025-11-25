"""Integration tests for authentication against live ProGet instance."""

import pytest
from core.proget import login_to_proget


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_with_valid_credentials(proget_test_credentials):
    """Test login with valid credentials against live ProGet instance.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Verify we're logged in by checking URL is not the login page
    assert "/log-in" not in page.url

    # Verify we can access the page
    assert page is not None

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_with_invalid_credentials(proget_test_credentials):
    """Test login with invalid credentials fails appropriately.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    with pytest.raises(Exception, match="Login failed"):
        page = await login_to_proget(
            host=proget_test_credentials["host"],
            username="invalid_user",
            password="invalid_password",
        )
        # Clean up if somehow login succeeded
        if page:
            await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_maintains_session(proget_test_credentials):
    """Test that logged-in session is maintained across page navigations.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Navigate to containers page (requires authentication)
    containers_url = f"{proget_test_credentials['host']}/containers"
    await page.goto(containers_url)
    await page.wait_for_load_state("networkidle")

    # Verify we're not redirected to login
    assert "/log-in" not in page.url
    assert "containers" in page.url

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_login_with_trailing_slash_in_host(proget_test_credentials):
    """Test login works with trailing slash in host URL.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    host_with_slash = proget_test_credentials["host"] + "/"

    page = await login_to_proget(
        host=host_with_slash,
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Verify login succeeded
    assert "/log-in" not in page.url

    # Clean up
    await page.close()
