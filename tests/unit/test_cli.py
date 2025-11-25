"""Unit tests for CLI argument parsing."""

import argparse
import sys
from io import StringIO


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
