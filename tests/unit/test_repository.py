"""Unit tests for repository discovery module."""

import pytest
from core.proget import Repository, parse_repositories_html


def test_repository_dataclass():
    """Test Repository dataclass creation and properties."""
    repo = Repository(feed="docker", name="my-service")

    assert repo.feed == "docker"
    assert repo.name == "my-service"
    assert repo.full_name == "docker/my-service"


def test_parse_repositories_html_with_single_repo():
    """Test parsing HTML with a single repository."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/payment-service/images">payment-service</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 1
    assert repositories[0].name == "payment-service"
    assert repositories[0].feed == "docker"


def test_parse_repositories_html_with_multiple_repos():
    """Test parsing HTML with multiple repositories."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/payment-service/images">payment-service</a>
        <a href="/containers/repositories/docker/user-service/images">user-service</a>
        <a href="/containers/repositories/docker/api-gateway/images">api-gateway</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 3
    repo_names = [r.name for r in repositories]
    assert "payment-service" in repo_names
    assert "user-service" in repo_names
    assert "api-gateway" in repo_names


def test_parse_repositories_html_sorted_by_name():
    """Test that repositories are sorted alphabetically by name."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/zebra-service/images">zebra-service</a>
        <a href="/containers/repositories/docker/alpha-service/images">alpha-service</a>
        <a href="/containers/repositories/docker/beta-service/images">beta-service</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 3
    assert repositories[0].name == "alpha-service"
    assert repositories[1].name == "beta-service"
    assert repositories[2].name == "zebra-service"


def test_parse_repositories_html_with_duplicates():
    """Test that duplicate repository links are deduplicated."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/payment-service/images">payment-service</a>
        <a href="/containers/repositories/docker/payment-service/images">payment-service</a>
        <a href="/containers/repositories/docker/user-service/images">user-service</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 2
    repo_names = [r.name for r in repositories]
    assert "payment-service" in repo_names
    assert "user-service" in repo_names


def test_parse_repositories_html_empty():
    """Test parsing HTML with no repositories."""
    html_content = """
    <html>
    <body>
        <p>No repositories found</p>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 0


def test_parse_repositories_html_different_feed():
    """Test parsing HTML with different feed names."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/service1/images">service1</a>
        <a href="/containers/repositories/npm/package1/images">package1</a>
        <a href="/containers/repositories/docker/service2/images">service2</a>
    </body>
    </html>
    """

    # Should only return docker feed repositories
    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 2
    repo_names = [r.name for r in repositories]
    assert "service1" in repo_names
    assert "service2" in repo_names
    assert "package1" not in repo_names


def test_parse_repositories_html_with_special_characters():
    """Test parsing repositories with special characters in names."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/my-service-123/images">my-service-123</a>
        <a href="/containers/repositories/docker/api_gateway/images">api_gateway</a>
        <a href="/containers/repositories/docker/service.v2/images">service.v2</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 3
    repo_names = [r.name for r in repositories]
    assert "my-service-123" in repo_names
    assert "api_gateway" in repo_names
    assert "service.v2" in repo_names


def test_parse_repositories_html_ignores_non_image_links():
    """Test that non-image repository links are ignored."""
    html_content = """
    <html>
    <body>
        <a href="/containers/repositories/docker/payment-service/images">payment-service</a>
        <a href="/containers/repositories/docker/user-service">user-service</a>
        <a href="/containers/repositories/docker/api-gateway/settings">api-gateway</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    # Should only match the link ending with /images
    assert len(repositories) == 1
    assert repositories[0].name == "payment-service"
