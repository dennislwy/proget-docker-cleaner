"""Integration tests for image deletion against live ProGet instance.

These tests are SKIPPED by default to avoid modifying live data.
Remove @pytest.mark.skip to run actual deletion tests.
"""

import pytest
from core.proget import (
    login_to_proget,
    get_repositories,
    get_images,
    delete_image,
    delete_untagged_images,
)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_image_dry_run(proget_test_credentials):
    """Test deleting a single image in dry-run mode on live ProGet.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get the test repository
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
        repo_filter="gsf-eca-service-systemactivity",
    )

    assert len(repositories) == 1, "Test repository should exist"
    repo = repositories[0]

    # Get images
    images = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Find an image with delete- tag or untagged
    test_image = None
    for img in images:
        if img.is_untagged:
            test_image = img
            break

    assert test_image is not None, "Should have at least one untagged/delete-tagged image"

    # Try to delete one image in dry-run mode
    result = await delete_image(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        digest=test_image.digest,
        dry_run=True,
    )

    assert result is True
    print(f"[DRY RUN] Deleted {repo.full_name}@{test_image.digest}")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_delete_untagged_images_dry_run(proget_test_credentials):
    """Test deleting all untagged images in dry-run mode on live ProGet.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get the test repository
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
        repo_filter="gsf-eca-service-systemactivity",
    )

    assert len(repositories) == 1, "Test repository should exist"
    repo = repositories[0]

    # Get images
    images = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Delete all untagged images in dry-run mode
    stats = await delete_untagged_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        images=images,
        dry_run=True,
    )

    # Verify statistics
    assert stats["total"] >= 0, "Should have count of untagged images"
    if stats["total"] > 0:
        assert stats["deleted"] == stats["total"], "All should be deleted (dry-run)"
        assert stats["failed"] == 0, "No failures in dry-run"

    print(f"[DRY RUN] Would delete {stats['total']} untagged images in {repo.full_name}")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Skipped by default - modifies live ProGet data")
async def test_delete_single_image_live(proget_test_credentials):
    """Test deleting a single untagged image on live ProGet.

    This test is SKIPPED by default to avoid modifying live data.
    Remove @pytest.mark.skip to run this test.

    WARNING: This will delete an untagged image.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get the test repository
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
        repo_filter="gsf-eca-service-systemactivity",
    )

    assert len(repositories) == 1, "Test repository should exist"
    repo = repositories[0]

    # Get images
    images = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Find an untagged image
    test_image = None
    for img in images:
        if img.is_untagged:
            test_image = img
            break

    if test_image is None:
        print("No untagged images found - skipping test")
        await page.close()
        return

    # Delete the untagged image
    print(f"Deleting {repo.full_name}@{test_image.digest}")
    delete_result = await delete_image(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        digest=test_image.digest,
        dry_run=False,
    )

    assert delete_result is True, "Deletion should succeed"

    # Verify the image is gone by fetching images again
    images_after = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Check that the image is no longer in the list
    deleted_image = next(
        (img for img in images_after if img.digest == test_image.digest), None
    )
    assert deleted_image is None, "Image should be deleted"

    print(f"Verified image {test_image.digest} was successfully deleted")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Skipped by default - modifies live ProGet data")
async def test_delete_multiple_images_live(proget_test_credentials):
    """Test deleting multiple untagged images on live ProGet.

    This test is SKIPPED by default to avoid modifying live data.
    Remove @pytest.mark.skip to run this test.

    WARNING: This will delete up to 3 untagged images in the repository.

    Args:
        proget_test_credentials: Fixture providing test credentials
    """
    # Login first
    page = await login_to_proget(
        host=proget_test_credentials["host"],
        username=proget_test_credentials["username"],
        password=proget_test_credentials["password"],
    )

    # Get the test repository
    repositories = await get_repositories(
        page=page,
        host=proget_test_credentials["host"],
        feed="gsf",
        repo_filter="gsf-eca-service-systemactivity",
    )

    assert len(repositories) == 1, "Test repository should exist"
    repo = repositories[0]

    # Get images
    images = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Get only first 3 untagged images to minimize impact
    untagged = [img for img in images if len(img.tags) == 0][:3]

    if len(untagged) == 0:
        print("No untagged images found - skipping test")
        await page.close()
        return

    print(f"Deleting {len(untagged)} untagged images in {repo.full_name}")

    # Delete the images
    stats = await delete_tagged_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        images=untagged,
        dry_run=False,
    )

    # Verify statistics
    assert stats["total"] == len(untagged), "Should match untagged count"
    assert stats["deleted"] > 0, "Should have deleted at least some images"
    assert stats["deleted"] + stats["failed"] == stats["total"], "Stats should add up"

    print(f"Deleted {stats['deleted']}/{stats['total']} images")
    if stats["failed"] > 0:
        print(f"Failed to delete {stats['failed']} images")

    # Verify images were deleted by fetching images again
    images_after = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Check that deleted images are no longer in the list
    deleted_digests = [img.digest for img in untagged]
    remaining_digests = [img.digest for img in images_after]

    for digest in deleted_digests:
        if digest not in remaining_digests:
            print(f"Verified image {digest} was deleted")

    # Clean up
    await page.close()
