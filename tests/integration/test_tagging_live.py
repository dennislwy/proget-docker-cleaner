"""Integration tests for image tagging against live ProGet instance.

These tests use the gsf-eca-service-systemactivity repository which has
142 untagged images (99.3% untagged) to minimize impact footprint.
"""

import pytest
from core.proget import (
    login_to_proget,
    get_repositories,
    get_images,
    tag_image,
    tag_untagged_images,
    identify_untagged_images,
)


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tag_image_live_dry_run(proget_test_credentials):
    """Test tagging a single image in dry-run mode on live ProGet.

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
    untagged = identify_untagged_images(images)
    assert len(untagged) > 0, "Should have untagged images"

    # Try to tag one image in dry-run mode
    test_image = untagged[0]
    result = await tag_image(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        digest=test_image.digest,
        tag="delete-test-1",
        dry_run=True,
    )

    assert result is True
    print(f"[DRY RUN] Tagged {repo.full_name}@{test_image.digest}")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
async def test_tag_untagged_images_live_dry_run(proget_test_credentials):
    """Test tagging all untagged images in dry-run mode on live ProGet.

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

    # Tag all untagged images in dry-run mode
    stats = await tag_untagged_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        images=images,
        dry_run=True,
    )

    # Verify statistics
    assert stats["total"] > 0, "Should have untagged images"
    assert stats["tagged"] == stats["total"], "All should be tagged (dry-run)"
    assert stats["failed"] == 0, "No failures in dry-run"

    print(f"[DRY RUN] Would tag {stats['total']} untagged images in {repo.full_name}")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Skipped by default - modifies live ProGet data")
async def test_tag_single_image_live(proget_test_credentials):
    """Test actually tagging a single image on live ProGet.

    This test is SKIPPED by default to avoid modifying live data.
    Remove @pytest.mark.skip to run this test.

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
    untagged = identify_untagged_images(images)
    assert len(untagged) > 0, "Should have untagged images"

    # Tag one image
    test_image = untagged[0]
    result = await tag_image(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        digest=test_image.digest,
        tag="delete-test-single",
        dry_run=False,
    )

    assert result is True
    print(f"Tagged {repo.full_name}@{test_image.digest} as delete-test-single")

    # Verify the tag was created by fetching images again
    images_after = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Find the image we just tagged
    tagged_image = next(
        (img for img in images_after if img.digest == test_image.digest), None
    )
    assert tagged_image is not None, "Should find the tagged image"
    assert "delete-test-single" in tagged_image.tags, "Should have the new tag"

    print(f"Verified tag created: {tagged_image.tags}")

    # Clean up
    await page.close()


@pytest.mark.asyncio
@pytest.mark.integration
@pytest.mark.skip(reason="Skipped by default - modifies live ProGet data")
async def test_tag_multiple_images_live(proget_test_credentials):
    """Test tagging multiple untagged images on live ProGet.

    This test is SKIPPED by default to avoid modifying live data.
    Remove @pytest.mark.skip to run this test.

    WARNING: This will tag the first 5 untagged images in the repository.

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

    # Get only first 5 untagged images to minimize impact
    untagged = identify_untagged_images(images)[:5]
    assert len(untagged) > 0, "Should have untagged images"

    print(f"Tagging {len(untagged)} untagged images in {repo.full_name}")

    # Tag the images
    stats = await tag_untagged_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
        images=untagged,
        dry_run=False,
    )

    # Verify statistics
    assert stats["total"] == len(untagged), "Should match untagged count"
    assert stats["tagged"] > 0, "Should have tagged at least some images"
    assert stats["tagged"] + stats["failed"] == stats["total"], "Stats should add up"

    print(f"Tagged {stats['tagged']}/{stats['total']} images")
    if stats["failed"] > 0:
        print(f"Failed to tag {stats['failed']} images")

    # Verify tags were created by fetching images again
    images_after = await get_images(
        page=page,
        host=proget_test_credentials["host"],
        feed=repo.feed,
        repo=repo.name,
    )

    # Check that at least some images now have delete- tags
    delete_tagged = [
        img for img in images_after if any(t.startswith("delete-") for t in img.tags)
    ]
    assert len(delete_tagged) >= stats["tagged"], "Should have delete- tagged images"

    print(f"Verified {len(delete_tagged)} images with delete- tags")

    # Clean up
    await page.close()
