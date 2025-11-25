"""Unit tests for image enumeration module."""

import pytest
from core.proget import DockerImage, parse_images_html, identify_untagged_images


def test_docker_image_dataclass():
    """Test DockerImage dataclass creation and properties."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["v1.0"],
        published_date="06/07/2024 10:13:35",
        downloads="4 (last 06/10/2024)",
    )

    assert img.digest == "a3b8c21afe97"
    assert img.tags == ["v1.0"]
    assert img.published_date == "06/07/2024 10:13:35"
    assert img.downloads == "4 (last 06/10/2024)"
    assert img.is_untagged == False


def test_docker_image_is_untagged_no_tags():
    """Test that image with no tags is considered untagged."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=[],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.is_untagged == True


def test_docker_image_is_untagged_with_delete_tag():
    """Test that image with only delete- tags is considered untagged."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["delete-1"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.is_untagged == True


def test_docker_image_is_untagged_with_proper_tag():
    """Test that image with proper tag is not considered untagged."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["latest"],
        published_date="06/07/2024 10:13:35",
        downloads="10",
    )

    assert img.is_untagged == False


def test_docker_image_is_untagged_mixed_tags():
    """Test that image with mix of delete and proper tags is not untagged."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["delete-1", "v1.0"],
        published_date="06/07/2024 10:13:35",
        downloads="5",
    )

    assert img.is_untagged == False


def test_parse_images_html_with_untagged_image():
    """Test parsing HTML with untagged image."""
    html_content = """
    <tr>
      <td>a3b8c21afe97</td>
      <td><span class="info-block warning" title="this may be automatically deleted">untagged</span></td>
      <td>06/07/2024 10:13:35</td>
      <td class="vulnerabilities"><span class="info-block warning">Not scanned</span></td>
      <td>4 (last 06/10/2024)</td>
    </tr>
    """

    images = parse_images_html(html_content)

    assert len(images) == 1
    assert images[0].digest == "a3b8c21afe97"
    assert images[0].tags == []
    assert images[0].published_date == "06/07/2024 10:13:35"
    assert images[0].is_untagged == True


def test_parse_images_html_with_tagged_image():
    """Test parsing HTML with tagged image."""
    html_content = """
    <tr>
      <td>6f984419c786</td>
      <td><a href="/containers/tags/gsf/gsf-aspnetcore-authentication/1.1.2408.3012/overview">1.1.2408.3012</a></td>
      <td>09/03/2024 04:35:37</td>
      <td class="vulnerabilities"><span class="info-block warning">Not scanned</span></td>
      <td>229 (last 11/13/2024)</td>
    </tr>
    """

    images = parse_images_html(html_content)

    assert len(images) == 1
    assert images[0].digest == "6f984419c786"
    assert images[0].tags == ["1.1.2408.3012"]
    assert images[0].published_date == "09/03/2024 04:35:37"
    assert images[0].is_untagged == False


def test_parse_images_html_with_multiple_images():
    """Test parsing HTML with multiple images (both tagged and untagged)."""
    html_content = """
    <tr>
      <td>a3b8c21afe97</td>
      <td><span class="info-block warning">untagged</span></td>
      <td>06/07/2024 10:13:35</td>
      <td class="vulnerabilities"><span class="info-block warning">Not scanned</span></td>
      <td>4 (last 06/10/2024)</td>
    </tr>
    <tr>
      <td>6f984419c786</td>
      <td><a href="/containers/tags/gsf/repo/1.1.2408.3012/overview">1.1.2408.3012</a></td>
      <td>09/03/2024 04:35:37</td>
      <td class="vulnerabilities"><span class="info-block warning">Not scanned</span></td>
      <td>229 (last 11/13/2024)</td>
    </tr>
    <tr>
      <td>08dd5912e0a9</td>
      <td><span class="info-block warning">untagged</span></td>
      <td>06/12/2024 08:35:35</td>
      <td class="vulnerabilities"><span class="info-block warning">Not scanned</span></td>
      <td>0</td>
    </tr>
    """

    images = parse_images_html(html_content)

    assert len(images) == 3
    assert images[0].digest == "a3b8c21afe97"
    assert images[0].is_untagged == True
    assert images[1].digest == "6f984419c786"
    assert images[1].is_untagged == False
    assert images[2].digest == "08dd5912e0a9"
    assert images[2].is_untagged == True


def test_parse_images_html_empty():
    """Test parsing HTML with no images."""
    html_content = """
    <html>
    <body>
        <table>
            <thead><tr><th>Digest</th><th>Tag</th></tr></thead>
            <tbody></tbody>
        </table>
    </body>
    </html>
    """

    images = parse_images_html(html_content)

    assert len(images) == 0


def test_parse_images_html_with_dev_tag():
    """Test parsing HTML with dev tag."""
    html_content = """
    <tr>
      <td>e3891d70edd1</td>
      <td><a href="/containers/tags/gsf/gsf-aspnetcore-authentication/dev/overview">dev</a></td>
      <td>06/18/2025 05:00:28</td>
      <td class="vulnerabilities"><span class="info-block warning">Not scanned</span></td>
      <td>397 (last 04:17)</td>
    </tr>
    """

    images = parse_images_html(html_content)

    assert len(images) == 1
    assert images[0].digest == "e3891d70edd1"
    assert images[0].tags == ["dev"]
    assert images[0].is_untagged == False


def test_identify_untagged_images_filters_correctly():
    """Test that identify_untagged_images filters correctly."""
    images = [
        DockerImage(
            digest="a3b8c21afe97",
            tags=[],
            published_date="06/07/2024 10:13:35",
            downloads="0",
        ),
        DockerImage(
            digest="6f984419c786",
            tags=["1.1.2408.3012"],
            published_date="09/03/2024 04:35:37",
            downloads="229",
        ),
        DockerImage(
            digest="08dd5912e0a9",
            tags=["delete-1"],
            published_date="06/12/2024 08:35:35",
            downloads="0",
        ),
        DockerImage(
            digest="e3891d70edd1",
            tags=["dev"],
            published_date="06/18/2025 05:00:28",
            downloads="397",
        ),
    ]

    untagged = identify_untagged_images(images)

    assert len(untagged) == 2
    assert untagged[0].digest == "a3b8c21afe97"
    assert untagged[1].digest == "08dd5912e0a9"


def test_identify_untagged_images_empty_list():
    """Test identify_untagged_images with empty list."""
    images = []

    untagged = identify_untagged_images(images)

    assert len(untagged) == 0


def test_identify_untagged_images_all_tagged():
    """Test identify_untagged_images when all images are tagged."""
    images = [
        DockerImage(
            digest="6f984419c786",
            tags=["1.1.2408.3012"],
            published_date="09/03/2024 04:35:37",
            downloads="229",
        ),
        DockerImage(
            digest="e3891d70edd1",
            tags=["dev"],
            published_date="06/18/2025 05:00:28",
            downloads="397",
        ),
    ]

    untagged = identify_untagged_images(images)

    assert len(untagged) == 0


def test_identify_untagged_images_all_untagged():
    """Test identify_untagged_images when all images are untagged."""
    images = [
        DockerImage(
            digest="a3b8c21afe97",
            tags=[],
            published_date="06/07/2024 10:13:35",
            downloads="0",
        ),
        DockerImage(
            digest="08dd5912e0a9",
            tags=["delete-1"],
            published_date="06/12/2024 08:35:35",
            downloads="0",
        ),
    ]

    untagged = identify_untagged_images(images)

    assert len(untagged) == 2
