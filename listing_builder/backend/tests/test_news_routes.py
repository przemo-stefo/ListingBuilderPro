# backend/tests/test_news_routes.py
# Purpose: News feed endpoint tests — RSS parsing, caching
# NOT for: Groq translation logic

import pytest
from unittest.mock import patch, AsyncMock
import time

from api.news_routes import _parse_rss_xml, _cache


SAMPLE_RSS = """<?xml version="1.0" encoding="UTF-8"?>
<rss version="2.0">
  <channel>
    <title>Test Feed</title>
    <item>
      <title>Article One</title>
      <link>https://example.com/1</link>
      <pubDate>Mon, 01 Jan 2026 12:00:00 GMT</pubDate>
      <description>First article description</description>
    </item>
    <item>
      <title>Article Two</title>
      <link>https://example.com/2</link>
      <pubDate>Tue, 02 Jan 2026 12:00:00 GMT</pubDate>
      <description>&lt;p&gt;HTML in description&lt;/p&gt;</description>
    </item>
  </channel>
</rss>"""

SAMPLE_ATOM = """<?xml version="1.0" encoding="UTF-8"?>
<feed xmlns="http://www.w3.org/2005/Atom">
  <title>Atom Feed</title>
  <entry>
    <title>Atom Entry</title>
    <link href="https://example.com/atom/1"/>
    <updated>2026-01-01T12:00:00Z</updated>
    <summary>Atom summary text</summary>
  </entry>
</feed>"""


class TestParseRssXml:

    def test_parse_rss_items(self):
        feed = {"source": "Test", "category": "ecommerce"}
        items = _parse_rss_xml(SAMPLE_RSS, feed)
        assert len(items) == 2
        assert items[0]["title"] == "Article One"
        assert items[0]["link"] == "https://example.com/1"
        assert items[0]["source"] == "Test"
        assert items[0]["category"] == "ecommerce"

    def test_html_stripped_from_description(self):
        feed = {"source": "Test", "category": "ecommerce"}
        items = _parse_rss_xml(SAMPLE_RSS, feed)
        desc = items[1]["description"]
        assert "<p>" not in desc

    def test_parse_atom_items(self):
        feed = {"source": "AtomSrc", "category": "amazon"}
        items = _parse_rss_xml(SAMPLE_ATOM, feed)
        assert len(items) == 1
        assert items[0]["title"] == "Atom Entry"
        assert items[0]["link"] == "https://example.com/atom/1"

    def test_max_6_items(self):
        many_items = "<rss><channel>" + "".join(
            f"<item><title>Item {i}</title><link>https://x.com/{i}</link></item>"
            for i in range(20)
        ) + "</channel></rss>"
        feed = {"source": "Big", "category": "test"}
        items = _parse_rss_xml(many_items, feed)
        assert len(items) == 6


class TestNewsFeedEndpoint:

    @patch("api.news_routes._translate_all", new_callable=AsyncMock)
    @patch("api.news_routes._resolve_thumbnails", new_callable=AsyncMock)
    @patch("api.news_routes._fetch_all_feeds", new_callable=AsyncMock)
    async def test_feed_returns_articles(self, mock_fetch, mock_thumbs, mock_translate, auth_client, test_settings):
        # Clear cache
        _cache["articles"] = []
        _cache["timestamp"] = 0

        mock_fetch.return_value = [{"title": "Test", "link": "https://x.com"}]
        mock_translate.return_value = [{"title": "Test PL", "link": "https://x.com"}]

        resp = auth_client.get(
            "/api/news/feed",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert "articles" in data

    def test_cached_feed_served(self, auth_client, test_settings):
        _cache["articles"] = [{"title": "Cached", "link": "https://x.com"}]
        _cache["timestamp"] = time.time()

        resp = auth_client.get(
            "/api/news/feed",
            headers={"X-API-Key": test_settings.api_secret_key},
        )
        assert resp.status_code == 200
        data = resp.json()
        assert data["cached"] is True
        assert data["articles"][0]["title"] == "Cached"

        # Cleanup
        _cache["articles"] = []
        _cache["timestamp"] = 0
