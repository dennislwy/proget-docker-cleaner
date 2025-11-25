"""Integration tests for repository discovery against live ProGet instance."""

import pytest
from core.proget import login_to_proget, get_repositories


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_repositories_from_live_proget(proget_test_credentials):
    """Test fetching repositories from live ProGet instance.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Fetch repositories (using "gsf" feed for test instance)
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
    )

    # Verify we got some repositories
    assert repositories is not None
    assert isinstance(repositories, list)

    # Verify each repository has expected structure
    for repo in repositories:
        assert hasattr(repo, "feed")
        assert hasattr(repo, "name")
        assert repo.feed == "gsf"
        assert len(repo.name) > 0

    print(f"Found {len(repositories)} repositories")
    for repo in repositories:
        print(f"  - {repo.full_name}")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_repositories_with_filter(proget_test_credentials):
    """Test fetching repositories with filter.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get all repositories first (using "gsf" feed for test instance)
    all_repos = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
    )

    # If there are repositories, test filtering
    if all_repos:
        # Get first repository name
        first_repo_name = all_repos[0].name

        # Fetch with filter
        filtered_repos = await get_repositories(
            page=page,
            host=proget_test_credentials["host"],
            feed="gsf",
            repo_filter=first_repo_name,
        )

        # Verify filter worked
        assert len(filtered_repos) == 1
        assert filtered_repos[0].name == first_repo_name

        print(f"Filtered for repository: {first_repo_name}")
    else:
        print("No repositories found to test filtering")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_repositories_returns_sorted_list(proget_test_credentials):
    """Test that repositories are returned in sorted order.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Fetch repositories (using "gsf" feed for test instance)
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
    )

    # Verify repositories are sorted
    if len(repositories) > 1:
        repo_names = [r.name for r in repositories]
        sorted_names = sorted(repo_names)
        assert repo_names == sorted_names, "Repositories should be sorted alphabetically"

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_repositories_with_nonexistent_filter(proget_test_credentials):
    """Test fetching repositories with non-existent filter returns empty list.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Fetch with non-existent filter (using "gsf" feed for test instance)
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
        repo_filter="non-existent-repo-xyz-123",
    )

    # Should return empty list
    assert len(repositories) == 0

    # Clean up
    await page.close()
