# backend/services/listing_diff_service.py
# Purpose: Pure diff logic — compares two listing snapshots and returns field-level changes
# NOT for: DB operations, network calls, or alert triggering

from typing import Any


def compare_listing_snapshots(old: dict, new: dict) -> list[dict]:
    """Compare two snapshot dicts and return list of changes.

    WHY pure function: Testable without DB/network. Scheduler calls this
    then persists results separately.

    Returns: [{change_type, field_name, old_value, new_value}, ...]
    """
    changes: list[dict] = []

    # Title — exact match
    old_title = old.get("title") or ""
    new_title = new.get("title") or ""
    if old_title and new_title and old_title != new_title:
        changes.append({
            "change_type": "title",
            "field_name": None,
            "old_value": old_title,
            "new_value": new_title,
        })

    # Bullets — per-index comparison
    changes.extend(_diff_bullets(old.get("bullets", []), new.get("bullets", [])))

    # Description — exact match
    old_desc = old.get("description") or ""
    new_desc = new.get("description") or ""
    if old_desc and new_desc and old_desc != new_desc:
        changes.append({
            "change_type": "description",
            "field_name": None,
            "old_value": old_desc,
            "new_value": new_desc,
        })

    # Images — URL list diff
    changes.extend(_diff_images(old.get("images", []), new.get("images", [])))

    # Price — numeric comparison with % in field_name
    changes.extend(_diff_price(old.get("price"), new.get("price")))

    # Brand — exact match
    old_brand = old.get("brand") or ""
    new_brand = new.get("brand") or ""
    if old_brand and new_brand and old_brand != new_brand:
        changes.append({
            "change_type": "brand",
            "field_name": None,
            "old_value": old_brand,
            "new_value": new_brand,
        })

    return changes


def _diff_bullets(old_bullets: list, new_bullets: list) -> list[dict]:
    """Compare bullet points per-index. Detects added, removed, changed."""
    changes: list[dict] = []
    max_len = max(len(old_bullets), len(new_bullets))

    for i in range(max_len):
        old_val = old_bullets[i] if i < len(old_bullets) else None
        new_val = new_bullets[i] if i < len(new_bullets) else None

        if old_val == new_val:
            continue

        if old_val is None:
            changes.append({
                "change_type": "bullets",
                "field_name": f"bullet_{i}_added",
                "old_value": None,
                "new_value": new_val,
            })
        elif new_val is None:
            changes.append({
                "change_type": "bullets",
                "field_name": f"bullet_{i}_removed",
                "old_value": old_val,
                "new_value": None,
            })
        else:
            changes.append({
                "change_type": "bullets",
                "field_name": f"bullet_{i}",
                "old_value": old_val,
                "new_value": new_val,
            })

    return changes


def _diff_images(old_images: list, new_images: list) -> list[dict]:
    """Compare image URL lists. Detects main image change, added, removed."""
    changes: list[dict] = []

    if not old_images and not new_images:
        return changes

    # Main image change (first URL)
    old_main = old_images[0] if old_images else None
    new_main = new_images[0] if new_images else None
    if old_main and new_main and old_main != new_main:
        changes.append({
            "change_type": "images",
            "field_name": "image_main",
            "old_value": old_main,
            "new_value": new_main,
        })

    old_set = set(old_images)
    new_set = set(new_images)

    for url in sorted(new_set - old_set):
        # WHY skip main: Already reported above if main changed
        if url == new_main and old_main and old_main != new_main:
            continue
        changes.append({
            "change_type": "images",
            "field_name": "image_added",
            "old_value": None,
            "new_value": url,
        })

    for url in sorted(old_set - new_set):
        if url == old_main and old_main and old_main != new_main:
            continue
        changes.append({
            "change_type": "images",
            "field_name": "image_removed",
            "old_value": url,
            "new_value": None,
        })

    return changes


def _diff_price(old_price: Any, new_price: Any) -> list[dict]:
    """Compare prices. Returns change with % difference in field_name."""
    if old_price is None or new_price is None:
        return []

    try:
        old_f = float(old_price)
        new_f = float(new_price)
    except (ValueError, TypeError):
        return []

    if old_f == new_f or old_f == 0:
        return []

    pct = round(((new_f - old_f) / old_f) * 100, 1)
    return [{
        "change_type": "price",
        "field_name": f"{pct:+.1f}%",
        "old_value": str(old_f),
        "new_value": str(new_f),
    }]
