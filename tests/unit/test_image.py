"""Unit tests for image enumeration module."""

import pytest
from core.proget import (
    DockerImage,
    parse_images_html,
    identify_untagged_images,
    identify_prefix_matched_images,
    identify_images_to_delete,
)


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


def test_matches_tag_prefix_single_match():
    """Test that an image with a tag matching a single prefix returns True."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["mr-123"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix(["mr-"]) == True


def test_matches_tag_prefix_matches_any_of_multiple_prefixes():
    """Test that a tag matching any one of several prefixes returns True."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["test-build-1"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix(["mr-", "test-"]) == True


def test_matches_tag_prefix_any_tag_matches():
    """Test that only one of several tags needs to match a prefix."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["mr-123", "latest"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix(["mr-"]) == True


def test_matches_tag_prefix_no_match():
    """Test that an image with no tag matching any prefix returns False."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["latest", "v1.0"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix(["mr-", "test-"]) == False


def test_matches_tag_prefix_empty_tags():
    """Test that an image with no tags never matches a prefix."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=[],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix(["mr-"]) == False


def test_matches_tag_prefix_empty_prefix_list():
    """Test that an empty prefix list never matches."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["mr-123"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix([]) == False


def test_matches_tag_prefix_case_sensitive():
    """Test that prefix matching is case-sensitive."""
    img = DockerImage(
        digest="a3b8c21afe97",
        tags=["MR-123"],
        published_date="06/07/2024 10:13:35",
        downloads="0",
    )

    assert img.matches_tag_prefix(["mr-"]) == False


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


def test_identify_prefix_matched_images_filters_correctly():
    """Test that identify_prefix_matched_images filters correctly."""
    images = [
        DockerImage(digest="a1", tags=["mr-100"], published_date="d", downloads="0"),
        DockerImage(digest="a2", tags=["latest"], published_date="d", downloads="0"),
        DockerImage(digest="a3", tags=["test-42"], published_date="d", downloads="0"),
        DockerImage(digest="a4", tags=[], published_date="d", downloads="0"),
    ]

    matched = identify_prefix_matched_images(images, ["mr-", "test-"])

    assert len(matched) == 2
    assert matched[0].digest == "a1"
    assert matched[1].digest == "a3"


def test_identify_prefix_matched_images_empty_list():
    """Test identify_prefix_matched_images with empty image list."""
    assert identify_prefix_matched_images([], ["mr-"]) == []


def test_identify_prefix_matched_images_no_matches():
    """Test identify_prefix_matched_images when nothing matches."""
    images = [
        DockerImage(digest="a1", tags=["latest"], published_date="d", downloads="0"),
    ]

    assert identify_prefix_matched_images(images, ["mr-"]) == []


def test_identify_images_to_delete_neither_criteria():
    """Test that no criteria selected returns an empty list."""
    images = [
        DockerImage(digest="a1", tags=[], published_date="d", downloads="0"),
        DockerImage(digest="a2", tags=["mr-1"], published_date="d", downloads="0"),
    ]

    result = identify_images_to_delete(images)

    assert result == []


def test_identify_images_to_delete_untagged_only():
    """Test that only untagged images are selected when include_untagged=True and no prefixes."""
    images = [
        DockerImage(digest="a1", tags=[], published_date="d", downloads="0"),
        DockerImage(digest="a2", tags=["mr-1"], published_date="d", downloads="0"),
        DockerImage(digest="a3", tags=["latest"], published_date="d", downloads="0"),
    ]

    result = identify_images_to_delete(images, include_untagged=True)

    assert [img.digest for img in result] == ["a1"]


def test_identify_images_to_delete_prefix_only():
    """Test that only prefix-matched images are selected when tag_prefixes given and include_untagged=False."""
    images = [
        DockerImage(digest="a1", tags=[], published_date="d", downloads="0"),
        DockerImage(digest="a2", tags=["mr-1"], published_date="d", downloads="0"),
        DockerImage(digest="a3", tags=["latest"], published_date="d", downloads="0"),
    ]

    result = identify_images_to_delete(images, tag_prefixes=["mr-"])

    assert [img.digest for img in result] == ["a2"]


def test_identify_images_to_delete_both_criteria_union_untagged_first():
    """Test that both criteria combine as a union, with untagged images first."""
    images = [
        DockerImage(digest="a1", tags=[], published_date="d", downloads="0"),
        DockerImage(digest="a2", tags=["mr-1"], published_date="d", downloads="0"),
        DockerImage(digest="a3", tags=["latest"], published_date="d", downloads="0"),
        DockerImage(digest="a4", tags=["delete-1"], published_date="d", downloads="0"),
    ]

    result = identify_images_to_delete(images, tag_prefixes=["mr-"], include_untagged=True)

    assert [img.digest for img in result] == ["a1", "a4", "a2"]


def test_identify_images_to_delete_dedupes_by_digest():
    """Test that an image matching both criteria appears only once."""
    # An untagged image (empty tags) can never also match a prefix, so build the
    # overlap case using a delete- tag that also happens to match the prefix list.
    images = [
        DockerImage(digest="a1", tags=["delete-1"], published_date="d", downloads="0"),
    ]

    result = identify_images_to_delete(images, tag_prefixes=["delete-"], include_untagged=True)

    assert [img.digest for img in result] == ["a1"]
    assert len(result) == 1
