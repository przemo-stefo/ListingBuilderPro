# backend/tests/test_listing_diff.py
# Purpose: Unit tests for listing_diff_service — pure function, no DB needed
# NOT for: Integration tests with scheduler or API

import pytest
from services.listing_diff_service import compare_listing_snapshots


class TestTitleDiff:
    def test_title_changed(self):
        old = {"title": "Old Title", "bullets": [], "description": "", "images": [], "brand": ""}
        new = {"title": "New Title", "bullets": [], "description": "", "images": [], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["change_type"] == "title"
        assert diffs[0]["old_value"] == "Old Title"
        assert diffs[0]["new_value"] == "New Title"

    def test_title_unchanged(self):
        old = {"title": "Same", "bullets": [], "description": "", "images": [], "brand": ""}
        new = {"title": "Same", "bullets": [], "description": "", "images": [], "brand": ""}
        assert compare_listing_snapshots(old, new) == []

    def test_title_empty_to_value_ignored(self):
        """WHY: Empty old title means first SP-API fetch — not a real change."""
        old = {"title": "", "bullets": [], "description": "", "images": [], "brand": ""}
        new = {"title": "New", "bullets": [], "description": "", "images": [], "brand": ""}
        assert compare_listing_snapshots(old, new) == []


class TestBulletsDiff:
    def test_bullet_changed(self):
        old = {"title": "", "bullets": ["A", "B"], "description": "", "images": [], "brand": ""}
        new = {"title": "", "bullets": ["A", "C"], "description": "", "images": [], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["change_type"] == "bullets"
        assert diffs[0]["field_name"] == "bullet_1"

    def test_bullet_added(self):
        old = {"title": "", "bullets": ["A"], "description": "", "images": [], "brand": ""}
        new = {"title": "", "bullets": ["A", "B"], "description": "", "images": [], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["field_name"] == "bullet_1_added"

    def test_bullet_removed(self):
        old = {"title": "", "bullets": ["A", "B"], "description": "", "images": [], "brand": ""}
        new = {"title": "", "bullets": ["A"], "description": "", "images": [], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["field_name"] == "bullet_1_removed"

    def test_multiple_bullet_changes(self):
        old = {"title": "", "bullets": ["A", "B", "C"], "description": "", "images": [], "brand": ""}
        new = {"title": "", "bullets": ["X", "B", "Z"], "description": "", "images": [], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 2
        types = {d["field_name"] for d in diffs}
        assert "bullet_0" in types
        assert "bullet_2" in types


class TestImagesDiff:
    def test_main_image_changed(self):
        old = {"title": "", "bullets": [], "description": "", "images": ["img1.jpg", "img2.jpg"], "brand": ""}
        new = {"title": "", "bullets": [], "description": "", "images": ["img3.jpg", "img2.jpg"], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        main_change = [d for d in diffs if d["field_name"] == "image_main"]
        assert len(main_change) == 1
        assert main_change[0]["old_value"] == "img1.jpg"
        assert main_change[0]["new_value"] == "img3.jpg"

    def test_image_added(self):
        old = {"title": "", "bullets": [], "description": "", "images": ["a.jpg"], "brand": ""}
        new = {"title": "", "bullets": [], "description": "", "images": ["a.jpg", "b.jpg"], "brand": ""}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["field_name"] == "image_added"

    def test_no_changes_same_images(self):
        imgs = ["a.jpg", "b.jpg"]
        old = {"title": "", "bullets": [], "description": "", "images": imgs[:], "brand": ""}
        new = {"title": "", "bullets": [], "description": "", "images": imgs[:], "brand": ""}
        assert compare_listing_snapshots(old, new) == []


class TestPriceDiff:
    def test_price_increased(self):
        old = {"title": "", "bullets": [], "description": "", "images": [], "brand": "", "price": 10.0}
        new = {"title": "", "bullets": [], "description": "", "images": [], "brand": "", "price": 12.0}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["change_type"] == "price"
        assert "+20.0%" in diffs[0]["field_name"]

    def test_price_decreased(self):
        old = {"title": "", "bullets": [], "description": "", "images": [], "brand": "", "price": 20.0}
        new = {"title": "", "bullets": [], "description": "", "images": [], "brand": "", "price": 15.0}
        diffs = compare_listing_snapshots(old, new)
        assert "-25.0%" in diffs[0]["field_name"]

    def test_price_none_ignored(self):
        old = {"title": "", "bullets": [], "description": "", "images": [], "brand": ""}
        new = {"title": "", "bullets": [], "description": "", "images": [], "brand": "", "price": 10}
        assert compare_listing_snapshots(old, new) == []


class TestBrandDiff:
    def test_brand_changed(self):
        old = {"title": "", "bullets": [], "description": "", "images": [], "brand": "OldBrand"}
        new = {"title": "", "bullets": [], "description": "", "images": [], "brand": "NewBrand"}
        diffs = compare_listing_snapshots(old, new)
        assert len(diffs) == 1
        assert diffs[0]["change_type"] == "brand"


class TestComplex:
    def test_multiple_changes(self):
        old = {"title": "Old", "bullets": ["A"], "description": "desc1", "images": ["x.jpg"], "brand": "B1", "price": 10}
        new = {"title": "New", "bullets": ["A", "B"], "description": "desc2", "images": ["x.jpg"], "brand": "B1", "price": 12}
        diffs = compare_listing_snapshots(old, new)
        types = {d["change_type"] for d in diffs}
        assert "title" in types
        assert "bullets" in types
        assert "description" in types
        assert "price" in types
        assert "brand" not in types  # brand unchanged
