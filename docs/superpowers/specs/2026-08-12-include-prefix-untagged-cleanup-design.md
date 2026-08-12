# Design: `--include-untagged` and `--include-prefix` cleanup criteria

## Summary

Today the tool always deletes untagged images with no flag needed. This change makes cleanup criteria explicit and opt-in, and adds a second criterion: deleting images whose tags match a user-supplied prefix list (e.g. `mr-`, `test`).

## CLI Arguments

Added to `proget-docker-cleaner.py`:

- `-iu`, `--include-untagged` — `action="store_true"`, default `False`. Include untagged images in cleanup.
- `-ip`, `--include-prefix` — string, default `None`. Comma-separated list of tag prefixes (e.g. `-ip "mr-,test"`). Parsed into a trimmed, non-empty list of prefixes once, before the repo loop.

**Validation:** Immediately after `parser.parse_args()`, if neither `args.include_untagged` is `True` nor `args.include_prefix` yields a non-empty prefix list, call `parser.error("At least one of --include-untagged or --include-prefix must be specified")`. This exits with a usage message and non-zero code before any browser/login work starts.

This is a breaking change to default behavior: running the tool with no flags now selects nothing (and in fact errors out immediately, per the validation above) rather than deleting all untagged images as before.

## Matching Semantics

An image is selected for deletion if:
- `--include-untagged` is set AND the image is untagged (existing `DockerImage.is_untagged` logic, unchanged), OR
- `--include-prefix` is set AND at least one of the image's tags starts with at least one of the given prefixes (case-sensitive `str.startswith`).

An image needs to satisfy only one of the two active criteria to be included (OR, not AND, across criteria). Within `--include-prefix`, a single prefix match on a single tag is sufficient — an image with tags `["mr-123", "latest"]` matches `-ip "mr-"` even though `latest` doesn't match.

## Core Changes (`core/proget.py`)

1. **`DockerImage.matches_tag_prefix(prefixes: list[str]) -> bool`** (new method)
   Returns `True` if any tag in `self.tags` starts with any prefix in `prefixes`.

2. **`identify_prefix_matched_images(images, prefixes) -> list[DockerImage]`** (new function)
   Filters `images` to those where `matches_tag_prefix(prefixes)` is `True`.

3. **`identify_images_to_delete(images, tag_prefixes=None, include_untagged=False) -> list[DockerImage]`** (new function)
   Replaces `identify_untagged_images` as the selection entrypoint used by the deletion flow:
   - If `include_untagged`: add all untagged images (via existing `identify_untagged_images`).
   - If `tag_prefixes`: add all prefix-matched images (via `identify_prefix_matched_images`).
   - Dedupe by `digest`, preserving order (untagged images first, then prefix-matched images not already included).
   - `identify_untagged_images` is left unchanged and still used internally / available for standalone use.

4. **Rename `delete_untagged_images` → `delete_images`**, adding parameters:
   - `tag_prefixes: list[str] | None = None`
   - `include_untagged: bool = False`

   Internally, replace the call to `identify_untagged_images(images)` with `identify_images_to_delete(images, tag_prefixes, include_untagged)`. The rest of the function (repo-id lookup, per-image deletion loop via `delete_image_optimized`, stats dict shape `{total, deleted, failed}`) is unchanged.

## Main Flow Changes (`proget-docker-cleaner.py`)

- Parse `--include-prefix` into `tag_prefixes: list[str]` once, before the repo loop (split on `,`, strip whitespace, drop empty entries).
- Per repo, replace the inline `is_untagged` count with:
  ```python
  to_delete = identify_images_to_delete(images, tag_prefixes, args.include_untagged)
  ```
  Its length drives the "Found N images to delete" message and the confirmation prompt.
- `total_stats` changes:
  - `untagged_images` → still tracked for the breakdown line, computed from `identify_untagged_images` count (only meaningful/shown when `--include-untagged` is set).
  - New `prefix_matched_images` counter (only meaningful/shown when `--include-prefix` is set), computed from `identify_prefix_matched_images` count.
  - New `images_to_delete` counter (replaces old bare `untagged_images` usage as the deletion-driving total) = `len(to_delete)` summed across repos.
- Call site updates from `delete_untagged_images(...)` to `delete_images(..., tag_prefixes=tag_prefixes, include_untagged=args.include_untagged)`.
- Final summary prints the breakdown counts conditionally based on which criteria were active.

## Out of Scope

- No change to the actual deletion mechanics (`delete_image_optimized`), temp-tag creation, or Docker Registry V2 API calls.
- No change to case-sensitivity behavior (case-sensitive matching, per prior decision).
- No new confirmation-prompt UX beyond reflecting the combined `to_delete` count.
