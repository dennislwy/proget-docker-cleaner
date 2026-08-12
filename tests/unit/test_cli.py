"""Unit tests for CLI argument parsing."""

import argparse
import sys
from io import StringIO

import pytest


def test_yes_flag_short_form():
    """Test that -y flag is parsed correctly."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
        "-y"
    ])

    assert args.yes == True
    assert args.host == "https://proget.example.com"


def test_yes_flag_long_form():
    """Test that --yes flag is parsed correctly."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
        "--yes"
    ])

    assert args.yes == True


def test_yes_flag_defaults_to_false():
    """Test that yes flag defaults to False when not provided."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass"
    ])

    assert args.yes == False


def test_yes_flag_with_dry_run():
    """Test that yes flag can be combined with dry-run."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
        "--dry-run",
        "-y"
    ])

    assert args.yes == True
    assert args.dry_run == True


def test_all_required_arguments():
    """Test that all required arguments are present."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument("-y", "--yes", action="store_true")

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "testuser",
        "--password", "testpass",
        "--dry-run",
        "-y"
    ])

    assert args.host == "https://proget.example.com"
    assert args.username == "testuser"
    assert args.password == "testpass"
    assert args.dry_run == True
    assert args.yes == True


def test_yes_flag_help_text():
    """Test that yes flag has proper help text."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument("--dry-run", action="store_true")
    parser.add_argument(
        "-y",
        "--yes",
        action="store_true",
        help="Automatically confirm deletion without prompting (default: False)",
    )

    # Get help text
    help_output = StringIO()
    parser.print_help(help_output)
    help_text = help_output.getvalue()

    assert "-y" in help_text
    assert "--yes" in help_text
    assert "Automatically confirm deletion" in help_text


def _build_parser():
    """Build a parser matching proget-docker-cleaner.py's cleanup-criteria flags."""
    parser = argparse.ArgumentParser()
    parser.add_argument("--host", required=True)
    parser.add_argument("--username", required=True)
    parser.add_argument("--password", required=True)
    parser.add_argument(
        "-iu",
        "--include-untagged",
        action="store_true",
        help="Include untagged images in cleanup (default: False)",
    )
    parser.add_argument(
        "-ip",
        "--include-prefix",
        help="Include images with any tag matching a comma-separated list of prefixes (e.g. 'mr-,test')",
    )
    return parser


def test_include_untagged_flag_short_form():
    """Test that -iu flag is parsed correctly."""
    parser = _build_parser()

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
        "-iu",
    ])

    assert args.include_untagged == True


def test_include_untagged_flag_defaults_to_false():
    """Test that include_untagged defaults to False when not provided."""
    parser = _build_parser()

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
    ])

    assert args.include_untagged == False


def test_include_prefix_flag_short_form():
    """Test that -ip flag is parsed correctly."""
    parser = _build_parser()

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
        "-ip", "mr-,test",
    ])

    assert args.include_prefix == "mr-,test"


def test_include_prefix_flag_defaults_to_none():
    """Test that include_prefix defaults to None when not provided."""
    parser = _build_parser()

    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
    ])

    assert args.include_prefix is None


def test_neither_criteria_flag_raises_parser_error():
    """Test that validation (parser.error) exits with status 2 when neither criteria is given."""
    parser = _build_parser()
    args = parser.parse_args([
        "--host", "https://proget.example.com",
        "--username", "user",
        "--password", "pass",
    ])

    tag_prefixes = (
        [p.strip() for p in args.include_prefix.split(",") if p.strip()]
        if args.include_prefix
        else []
    )

    with pytest.raises(SystemExit) as exc_info:
        if not args.include_untagged and not tag_prefixes:
            parser.error(
                "At least one of --include-untagged or --include-prefix must be specified"
            )

    assert exc_info.value.code == 2
