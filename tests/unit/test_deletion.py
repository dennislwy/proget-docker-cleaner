"""Unit tests for image deletion operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.proget import delete_image, delete_images, DockerImage


@pytest.mark.asyncio
async def test_delete_image_dry_run():
    """Test delete_image in dry-run mode."""
    page = MagicMock()

    result = await delete_image(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        digest="a3b8c21afe97",
        dry_run=True,
    )

    assert result is True


@pytest.mark.asyncio
async def test_delete_image_success():
    """Test successful image deletion."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(
        return_value='<html>repositoryId=123 name="AHAntiCsrfToken" value="csrf-token-123"</html>'
    )
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        mock_post = AsyncMock()
        mock_post.status = 200
        mock_post.__aenter__.return_value = mock_post
        mock_ctx.post = MagicMock(return_value=mock_post)

        mock_head = AsyncMock()
        mock_head.status = 200
        mock_head.headers = {"Docker-Content-Digest": "sha256:abc123def456"}
        mock_head.__aenter__.return_value = mock_head
        mock_ctx.head = MagicMock(return_value=mock_head)

        mock_delete = AsyncMock()
        mock_delete.status = 202
        mock_delete.__aenter__.return_value = mock_delete
        mock_ctx.delete = MagicMock(return_value=mock_delete)

        result = await delete_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            dry_run=False,
        )

        assert result is True


@pytest.mark.asyncio
async def test_delete_image_failure_get_details():
    """Test delete_image failure when repository ID is not found in page HTML."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>No repository ID here</html>")
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    result = await delete_image(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        digest="a3b8c21afe97",
        dry_run=False,
    )

    assert result is False


@pytest.mark.asyncio
async def test_delete_image_failure_no_full_digest():
    """Test delete_image failure when Docker-Content-Digest header is missing."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(
        return_value='<html>repositoryId=123 name="AHAntiCsrfToken" value="csrf-token-123"</html>'
    )
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        mock_post = AsyncMock()
        mock_post.status = 200
        mock_post.__aenter__.return_value = mock_post
        mock_ctx.post = MagicMock(return_value=mock_post)

        mock_head = AsyncMock()
        mock_head.status = 200
        mock_head.headers = {}  # No Docker-Content-Digest
        mock_head.__aenter__.return_value = mock_head
        mock_ctx.head = MagicMock(return_value=mock_head)

        result = await delete_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            dry_run=False,
        )

        assert result is False


@pytest.mark.asyncio
async def test_delete_image_failure_delete_request():
    """Test delete_image failure when DELETE request fails."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(
        return_value='<html>repositoryId=123 name="AHAntiCsrfToken" value="csrf-token-123"</html>'
    )
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        mock_post = AsyncMock()
        mock_post.status = 200
        mock_post.__aenter__.return_value = mock_post
        mock_ctx.post = MagicMock(return_value=mock_post)

        mock_head = AsyncMock()
        mock_head.status = 200
        mock_head.headers = {"Docker-Content-Digest": "sha256:abc123def456"}
        mock_head.__aenter__.return_value = mock_head
        mock_ctx.head = MagicMock(return_value=mock_head)

        # DELETE fails for both the temp-tag cleanup and the image deletion
        mock_delete = AsyncMock()
        mock_delete.status = 500
        mock_delete.__aenter__.return_value = mock_delete
        mock_ctx.delete = MagicMock(return_value=mock_delete)

        result = await delete_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            dry_run=False,
        )

        assert result is False


@pytest.mark.asyncio
async def test_delete_image_with_trailing_slash():
    """Test delete_image handles trailing slash in host."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(
        return_value='<html>repositoryId=123 name="AHAntiCsrfToken" value="csrf-token-123"</html>'
    )
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        mock_post = AsyncMock()
        mock_post.status = 200
        mock_post.__aenter__.return_value = mock_post
        mock_ctx.post = MagicMock(return_value=mock_post)

        mock_head = AsyncMock()
        mock_head.status = 200
        mock_head.headers = {"Docker-Content-Digest": "sha256:abc123def456"}
        mock_head.__aenter__.return_value = mock_head
        mock_ctx.head = MagicMock(return_value=mock_head)

        mock_delete = AsyncMock()
        mock_delete.status = 202
        mock_delete.__aenter__.return_value = mock_delete
        mock_ctx.delete = MagicMock(return_value=mock_delete)

        result = await delete_image(
            page=page,
            host="https://proget.test.com/",  # Trailing slash
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            dry_run=False,
        )

        assert result is True


@pytest.mark.asyncio
async def test_delete_image_accepts_200_status():
    """Test delete_image accepts HTTP 200 as success."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(
        return_value='<html>repositoryId=123 name="AHAntiCsrfToken" value="csrf-token-123"</html>'
    )
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        mock_post = AsyncMock()
        mock_post.status = 200
        mock_post.__aenter__.return_value = mock_post
        mock_ctx.post = MagicMock(return_value=mock_post)

        mock_head = AsyncMock()
        mock_head.status = 200
        mock_head.headers = {"Docker-Content-Digest": "sha256:abc123def456"}
        mock_head.__aenter__.return_value = mock_head
        mock_ctx.head = MagicMock(return_value=mock_head)

        # DELETE returns 200 instead of 202
        mock_delete = AsyncMock()
        mock_delete.status = 200
        mock_delete.__aenter__.return_value = mock_delete
        mock_ctx.delete = MagicMock(return_value=mock_delete)

        result = await delete_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            dry_run=False,
        )

        assert result is True


@pytest.mark.asyncio
async def test_delete_images_no_untagged():
    """Test delete_images with no untagged images."""
    page = MagicMock()

    images = [
        DockerImage(digest="abc123", tags=["v1.0"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["v2.0"], published_date="2024-01-02", downloads="5"),
    ]

    stats = await delete_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=False,
        include_untagged=True,
    )

    assert stats["total"] == 0
    assert stats["deleted"] == 0
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_images_dry_run():
    """Test delete_images in dry-run mode."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>repositoryId=123</html>")

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["delete-1"], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=["v1.0"], published_date="2024-01-03", downloads="15"),
    ]

    stats = await delete_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
        include_untagged=True,
    )

    assert stats["total"] == 2
    assert stats["deleted"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_images_success():
    """Test successful deletion of untagged images."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>repositoryId=123</html>")

    images = [
        DockerImage(digest="abc123", tags=["delete-1"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
    ]

    with patch("core.proget.delete_image_optimized", new=AsyncMock(return_value=True)):
        stats = await delete_images(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            images=images,
            dry_run=False,
            include_untagged=True,
        )

    assert stats["total"] == 2
    assert stats["deleted"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_images_partial_failure():
    """Test delete_images with some failures."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>repositoryId=123</html>")

    images = [
        DockerImage(digest="abc123", tags=["delete-1"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=[], published_date="2024-01-03", downloads="7"),
    ]

    with patch("core.proget.delete_image_optimized", new=AsyncMock(side_effect=[True, False, True])):
        stats = await delete_images(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            images=images,
            dry_run=False,
            include_untagged=True,
        )

    assert stats["total"] == 3
    assert stats["deleted"] == 2
    assert stats["failed"] == 1


@pytest.mark.asyncio
async def test_delete_images_only_deletes_untagged_when_that_criteria_set():
    """Test that delete_images with include_untagged=True only deletes untagged images."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>repositoryId=123</html>")

    images = [
        DockerImage(digest="abc123", tags=["delete-1"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=["v1.0"], published_date="2024-01-03", downloads="15"),
        DockerImage(digest="jkl012", tags=["latest"], published_date="2024-01-04", downloads="20"),
    ]

    stats = await delete_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
        include_untagged=True,
    )

    # Should only delete the first two images (delete-1 prefix and untagged)
    assert stats["total"] == 2
    assert stats["deleted"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_images_with_multiple_delete_tags():
    """Test deleting images with multiple delete- prefix tags."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>repositoryId=123</html>")

    images = [
        DockerImage(digest="abc123", tags=["delete-1", "delete-2"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["delete-3"], published_date="2024-01-02", downloads="5"),
    ]

    stats = await delete_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
        include_untagged=True,
    )

    assert stats["total"] == 2
    assert stats["deleted"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_images_default_excludes_untagged():
    """Test that delete_images with no criteria (defaults) selects nothing."""
    page = MagicMock()

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["delete-1"], published_date="2024-01-02", downloads="5"),
    ]

    stats = await delete_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
    )

    assert stats["total"] == 0
    assert stats["deleted"] == 0
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_delete_images_with_tag_prefixes_only():
    """Test delete_images selects only prefix-matched images when include_untagged=False."""
    page = MagicMock()
    page.goto = AsyncMock()
    page.wait_for_load_state = AsyncMock()
    page.content = AsyncMock(return_value="<html>repositoryId=123</html>")

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["mr-42"], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=["latest"], published_date="2024-01-03", downloads="15"),
    ]

    stats = await delete_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
        tag_prefixes=["mr-"],
    )

    assert stats["total"] == 1
    assert stats["deleted"] == 1
    assert stats["failed"] == 0
