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
        <a href="/containers/tags/docker/payment-service/latest/overview">payment-service:latest</a>
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
        <a href="/containers/tags/docker/payment-service/latest/overview">payment-service:latest</a>
        <a href="/containers/tags/docker/user-service/v1.0/overview">user-service:v1.0</a>
        <a href="/containers/tags/docker/api-gateway/dev/overview">api-gateway:dev</a>
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
        <a href="/containers/tags/docker/zebra-service/latest/overview">zebra-service:latest</a>
        <a href="/containers/tags/docker/alpha-service/v1/overview">alpha-service:v1</a>
        <a href="/containers/tags/docker/beta-service/dev/overview">beta-service:dev</a>
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
        <a href="/containers/tags/docker/payment-service/latest/overview">payment-service:latest</a>
        <a href="/containers/tags/docker/payment-service/v1.0/overview">payment-service:v1.0</a>
        <a href="/containers/tags/docker/user-service/latest/overview">user-service:latest</a>
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
        <a href="/containers/tags/docker/service1/latest/overview">service1:latest</a>
        <a href="/containers/tags/npm/package1/v1/overview">package1:v1</a>
        <a href="/containers/tags/docker/service2/dev/overview">service2:dev</a>
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
        <a href="/containers/tags/docker/my-service-123/latest/overview">my-service-123:latest</a>
        <a href="/containers/tags/docker/api_gateway/v1/overview">api_gateway:v1</a>
        <a href="/containers/tags/docker/service.v2/dev/overview">service.v2:dev</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    assert len(repositories) == 3
    repo_names = [r.name for r in repositories]
    assert "my-service-123" in repo_names
    assert "api_gateway" in repo_names
    assert "service.v2" in repo_names


def test_parse_repositories_html_ignores_non_overview_links():
    """Test that non-overview repository links are ignored."""
    html_content = """
    <html>
    <body>
        <a href="/containers/tags/docker/payment-service/latest/overview">payment-service:latest</a>
        <a href="/containers/tags/docker/user-service/v1/settings">user-service:v1</a>
        <a href="/containers/registry?feedId=docker">registry</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="docker")

    # Should only match the link ending with /overview
    assert len(repositories) == 1
    assert repositories[0].name == "payment-service"


def test_parse_repositories_html_with_gsf_feed():
    """Test parsing repositories from gsf feed (real ProGet format)."""
    html_content = """
    <html>
    <body>
        <a href="/containers/tags/gsf/gsf-aspnetcore-authentication/1.1.2408.3012/overview">gsf-aspnetcore-authentication:1.1.2408.3012</a>
        <a href="/containers/tags/gsf/gsf-aspnetcore-authentication/latest/overview">gsf-aspnetcore-authentication:latest</a>
        <a href="/containers/tags/gsf/gsf-central-core/dev/overview">gsf-central-core:dev</a>
        <a href="/containers/tags/gsf/gsf-central-core/latest/overview">gsf-central-core:latest</a>
    </body>
    </html>
    """

    repositories = parse_repositories_html(html_content, feed="gsf")

    assert len(repositories) == 2
    repo_names = [r.name for r in repositories]
    assert "gsf-aspnetcore-authentication" in repo_names
    assert "gsf-central-core" in repo_names
