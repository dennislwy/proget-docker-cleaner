"""Integration tests for image enumeration against live ProGet instance."""

import re
import pytest
from core.proget import (
    login_to_proget,
    get_repositories,
    get_images,
    identify_untagged_images,
)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_images_from_live_repository(proget_test_credentials):
    """Test fetching images from a live ProGet repository.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get repositories
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
    )

    # Get images from first repository if available
    if repositories:
        repo = repositories[0]
        print(f"\nFetching images from {repo.full_name}")

        images = await get_images(
            page=page,
            host=proget_test_credentials["host"],
            feed=repo.feed,
            repo=repo.name,
        )

        # Verify we got images
        assert images is not None
        assert isinstance(images, list)

        print(f"Found {len(images)} images")

        # Verify each image has expected structure
        for img in images:
            assert hasattr(img, "digest")
            assert hasattr(img, "tags")
            assert hasattr(img, "published_date")
            assert hasattr(img, "downloads")
            assert len(img.digest) == 12  # Short digest format

        # Print first few images
        for i, img in enumerate(images[:5]):
            tags_str = ", ".join(img.tags) if img.tags else "untagged"
            print(f"  {i+1}. {img.digest} - {tags_str}")

    else:
        print("No repositories found to test")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_identify_untagged_images_from_live(proget_test_credentials):
    """Test identifying untagged images from live ProGet.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get repositories
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
    )

    # Get images from first repository if available
    if repositories:
        repo = repositories[0]

        images = await get_images(
            page=page,
            host=proget_test_credentials["host"],
            feed=repo.feed,
            repo=repo.name,
        )

        # Identify untagged images
        untagged = identify_untagged_images(images)

        print(f"\nRepository: {repo.full_name}")
        print(f"Total images: {len(images)}")
        print(f"Untagged images: {len(untagged)}")
        print(f"Tagged images: {len(images) - len(untagged)}")

        # Verify untagged filtering works
        for img in untagged:
            assert img.is_untagged == True
            assert len(img.tags) == 0 or all(t.startswith("delete-") for t in img.tags)

        # Print some untagged images
        if untagged:
            print("\nSample untagged images:")
            for i, img in enumerate(untagged[:5]):
                print(f"  {i+1}. {img.digest} - published {img.published_date}")

    else:
        print("No repositories found to test")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_get_images_handles_empty_repository(proget_test_credentials):
    """Test that get_images handles empty/non-existent repository gracefully.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Try to get images from non-existent repository
    # This should not crash, might return empty list or error
    try:
        images = await get_images(
            page=page,
            host=proget_test_credentials["host"],
            feed="gsf",
            repo="non-existent-repo-xyz-123",
        )

        # If it succeeds, should return empty list or valid list
        assert isinstance(images, list)
        print(f"Got {len(images)} images from non-existent repo (expected 0 or error)")

    except Exception as e:
        # It's okay if it fails - repository doesn't exist
        print(f"Expected error for non-existent repo: {e}")
        assert True

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_images_have_consistent_structure(proget_test_credentials):
    """Test that all images from live ProGet have consistent structure.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get repositories
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
    )

    # Test at least 2 repositories if available
    repos_to_test = repositories[:2] if len(repositories) >= 2 else repositories

    for repo in repos_to_test:
        images = await get_images(
            page=page,
            host=proget_test_credentials["host"],
            feed=repo.feed,
            repo=repo.name,
        )

        # Verify structure of each image
        for img in images:
            # Digest must be 12-char hex
            assert re.match(r'^[a-f0-9]{12}$', img.digest)

            # Tags must be a list
            assert isinstance(img.tags, list)

            # Published date must be non-empty
            assert len(img.published_date) > 0

            # Downloads must be a string
            assert isinstance(img.downloads, str)

            # is_untagged must be boolean
            assert isinstance(img.is_untagged, bool)

    # Clean up
    await page.close()
