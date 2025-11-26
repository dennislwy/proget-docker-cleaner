"""Unit tests for image tagging operations."""

import pytest
from unittest.mock import AsyncMock, MagicMock, patch
from core.proget import tag_image, tag_untagged_images, DockerImage


@pytest.mark.asyncio
async def test_tag_image_dry_run():
    """Test tag_image in dry-run mode."""
    page = MagicMock()

    result = await tag_image(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        digest="a3b8c21afe97",
        tag="delete-1",
        dry_run=True,
    )

    assert result is True


@pytest.mark.asyncio
async def test_tag_image_success():
    """Test successful image tagging."""
    # Mock Playwright page
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    # Mock aiohttp responses
    with patch("aiohttp.ClientSession") as mock_session:
        # Mock the context manager
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        # Mock GET image details response
        mock_get_details = AsyncMock()
        mock_get_details.status = 200
        mock_get_details.text = AsyncMock(
            return_value="<html>sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef</html>"
        )
        mock_get_details.__aenter__.return_value = mock_get_details

        # Mock GET manifest response
        mock_get_manifest = AsyncMock()
        mock_get_manifest.status = 200
        mock_get_manifest.read = AsyncMock(return_value=b'{"manifest": "data"}')
        mock_get_manifest.headers = {"Content-Type": "application/vnd.docker.distribution.manifest.v2+json"}
        mock_get_manifest.__aenter__.return_value = mock_get_manifest

        # Mock PUT tag response
        mock_put = AsyncMock()
        mock_put.status = 201
        mock_put.__aenter__.return_value = mock_put

        # Set up the mock to return different responses for each call
        mock_ctx.get = MagicMock(side_effect=[mock_get_details, mock_get_manifest])
        mock_ctx.put = MagicMock(return_value=mock_put)

        result = await tag_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            tag="delete-1",
            dry_run=False,
        )

        assert result is True


@pytest.mark.asyncio
async def test_tag_image_failure_get_details():
    """Test tag_image failure when getting image details."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        # Mock failed GET response
        mock_get = AsyncMock()
        mock_get.status = 404
        mock_get.__aenter__.return_value = mock_get
        mock_ctx.get = MagicMock(return_value=mock_get)

        result = await tag_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            tag="delete-1",
            dry_run=False,
        )

        assert result is False


@pytest.mark.asyncio
async def test_tag_image_failure_no_full_digest():
    """Test tag_image failure when full digest is not found."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        # Mock GET response with no digest
        mock_get = AsyncMock()
        mock_get.status = 200
        mock_get.text = AsyncMock(return_value="<html>No digest here</html>")
        mock_get.__aenter__.return_value = mock_get
        mock_ctx.get = MagicMock(return_value=mock_get)

        result = await tag_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            tag="delete-1",
            dry_run=False,
        )

        assert result is False


@pytest.mark.asyncio
async def test_tag_image_failure_get_manifest():
    """Test tag_image failure when getting manifest."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        # Mock successful GET details
        mock_get_details = AsyncMock()
        mock_get_details.status = 200
        mock_get_details.text = AsyncMock(
            return_value="<html>sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef</html>"
        )
        mock_get_details.__aenter__.return_value = mock_get_details

        # Mock failed GET manifest
        mock_get_manifest = AsyncMock()
        mock_get_manifest.status = 404
        mock_get_manifest.__aenter__.return_value = mock_get_manifest

        mock_ctx.get = MagicMock(side_effect=[mock_get_details, mock_get_manifest])

        result = await tag_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            tag="delete-1",
            dry_run=False,
        )

        assert result is False


@pytest.mark.asyncio
async def test_tag_image_failure_put_tag():
    """Test tag_image failure when putting tag."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        # Mock successful GET details
        mock_get_details = AsyncMock()
        mock_get_details.status = 200
        mock_get_details.text = AsyncMock(
            return_value="<html>sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef</html>"
        )
        mock_get_details.__aenter__.return_value = mock_get_details

        # Mock successful GET manifest
        mock_get_manifest = AsyncMock()
        mock_get_manifest.status = 200
        mock_get_manifest.read = AsyncMock(return_value=b'{"manifest": "data"}')
        mock_get_manifest.headers = {"Content-Type": "application/vnd.docker.distribution.manifest.v2+json"}
        mock_get_manifest.__aenter__.return_value = mock_get_manifest

        # Mock failed PUT
        mock_put = AsyncMock()
        mock_put.status = 500
        mock_put.__aenter__.return_value = mock_put

        mock_ctx.get = MagicMock(side_effect=[mock_get_details, mock_get_manifest])
        mock_ctx.put = MagicMock(return_value=mock_put)

        result = await tag_image(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            tag="delete-1",
            dry_run=False,
        )

        assert result is False


@pytest.mark.asyncio
async def test_tag_image_with_trailing_slash():
    """Test tag_image handles trailing slash in host."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    with patch("aiohttp.ClientSession") as mock_session:
        mock_ctx = AsyncMock()
        mock_session.return_value.__aenter__.return_value = mock_ctx

        # Mock responses
        mock_get_details = AsyncMock()
        mock_get_details.status = 200
        mock_get_details.text = AsyncMock(
            return_value="<html>sha256:1234567890abcdef1234567890abcdef1234567890abcdef1234567890abcdef</html>"
        )
        mock_get_details.__aenter__.return_value = mock_get_details

        mock_get_manifest = AsyncMock()
        mock_get_manifest.status = 200
        mock_get_manifest.read = AsyncMock(return_value=b'{"manifest": "data"}')
        mock_get_manifest.headers = {"Content-Type": "application/vnd.docker.distribution.manifest.v2+json"}
        mock_get_manifest.__aenter__.return_value = mock_get_manifest

        mock_put = AsyncMock()
        mock_put.status = 201
        mock_put.__aenter__.return_value = mock_put

        mock_ctx.get = MagicMock(side_effect=[mock_get_details, mock_get_manifest])
        mock_ctx.put = MagicMock(return_value=mock_put)

        result = await tag_image(
            page=page,
            host="https://proget.test.com/",  # Trailing slash
            feed="docker",
            repo="test-repo",
            digest="a3b8c21afe97",
            tag="delete-1",
            dry_run=False,
        )

        assert result is True


@pytest.mark.asyncio
async def test_tag_untagged_images_no_untagged():
    """Test tag_untagged_images with no untagged images."""
    page = MagicMock()

    images = [
        DockerImage(digest="abc123", tags=["v1.0"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["v2.0"], published_date="2024-01-02", downloads="5"),
    ]

    stats = await tag_untagged_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=False,
    )

    assert stats["total"] == 0
    assert stats["tagged"] == 0
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_tag_untagged_images_dry_run():
    """Test tag_untagged_images in dry-run mode."""
    page = MagicMock()

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=["v1.0"], published_date="2024-01-03", downloads="15"),
    ]

    stats = await tag_untagged_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
    )

    assert stats["total"] == 2
    assert stats["tagged"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_tag_untagged_images_success():
    """Test successful tagging of untagged images."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
    ]

    with patch("core.proget.tag_image", new=AsyncMock(return_value=True)):
        stats = await tag_untagged_images(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            images=images,
            dry_run=False,
        )

    assert stats["total"] == 2
    assert stats["tagged"] == 2
    assert stats["failed"] == 0


@pytest.mark.asyncio
async def test_tag_untagged_images_partial_failure():
    """Test tag_untagged_images with some failures."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=[], published_date="2024-01-03", downloads="7"),
    ]

    # Mock tag_image to return True, False, True
    with patch("core.proget.tag_image", new=AsyncMock(side_effect=[True, False, True])):
        stats = await tag_untagged_images(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            images=images,
            dry_run=False,
        )

    assert stats["total"] == 3
    assert stats["tagged"] == 2
    assert stats["failed"] == 1


@pytest.mark.asyncio
async def test_tag_untagged_images_counter_starts_at_one():
    """Test that tag counter starts at 1 (delete-1, delete-2, etc)."""
    page = MagicMock()
    page.context.cookies = AsyncMock(
        return_value=[{"name": "session", "value": "test123"}]
    )

    images = [
        DockerImage(digest="abc123", tags=[], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=[], published_date="2024-01-02", downloads="5"),
    ]

    tag_calls = []

    async def mock_tag_image(**kwargs):
        tag_calls.append(kwargs["tag"])
        return True

    with patch("core.proget.tag_image", new=mock_tag_image):
        await tag_untagged_images(
            page=page,
            host="https://proget.test.com",
            feed="docker",
            repo="test-repo",
            images=images,
            dry_run=False,
        )

    assert tag_calls == ["delete-1", "delete-2"]


@pytest.mark.asyncio
async def test_tag_untagged_images_with_delete_prefix_tags():
    """Test that images with delete- prefix tags are treated as untagged."""
    page = MagicMock()

    images = [
        DockerImage(digest="abc123", tags=["delete-1"], published_date="2024-01-01", downloads="10"),
        DockerImage(digest="def456", tags=["delete-2", "delete-3"], published_date="2024-01-02", downloads="5"),
        DockerImage(digest="ghi789", tags=["v1.0"], published_date="2024-01-03", downloads="15"),
    ]

    stats = await tag_untagged_images(
        page=page,
        host="https://proget.test.com",
        feed="docker",
        repo="test-repo",
        images=images,
        dry_run=True,
    )

    # First two images should be treated as untagged
    assert stats["total"] == 2
    assert stats["tagged"] == 2
    assert stats["failed"] == 0
