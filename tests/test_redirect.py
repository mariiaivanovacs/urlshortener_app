"""Integration tests for all API endpoints."""
from app.core.config import settings
import logging
logging.basicConfig(level=logging.INFO)

BASE = settings.base_domain


# ---------------------------------------------------------------------------
# POST /shorten
# ---------------------------------------------------------------------------

def test_shorten_returns_201(client):
    # first test function with logging
    logging.info("Testing POST /shorten with valid URL")
    resp = client.post("/shorten", json={"url": "http://testserver/long/path"})
    assert resp.status_code == 201
    body = resp.json()
    print(f"Response: {body}")

    # assert body["short_url"] == f"{BASE}/{body['short_id']}"
    # assert body["short_url"] == f"{BASE}/{body['short_id']}"
    assert body["original_url"] == "http://testserver/long/path"


def test_shorten_different_urls_different_ids(client):
    r1 = client.post("/shorten", json={"url": "http://testserver/a"})
    r2 = client.post("/shorten", json={"url": "http://testserver/b"})
    assert r1.json()["short_id"] != r2.json()["short_id"]


def test_shorten_invalid_url_returns_422(client):
    resp = client.post("/shorten", json={"url": "not-a-url"})
    assert resp.status_code == 422


# ---------------------------------------------------------------------------
# GET /{short_id}  (redirect)
# ---------------------------------------------------------------------------

def test_redirect_follows_to_original(client):
    short_id = client.post("/shorten", json={"url": "http://testserver/"}).json()["short_id"]
    resp = client.get(f"/{short_id}", follow_redirects=False)
    assert resp.status_code == 302
    assert resp.headers["location"] == "http://testserver/"


def test_redirect_increments_clicks(client):
    short_id = client.post("/shorten", json={"url": "http://testserver/click"}).json()["short_id"]
    client.get(f"/{short_id}", follow_redirects=False)
    client.get(f"/{short_id}", follow_redirects=False)
    assert client.get(f"/stats/{short_id}").json()["clicks"] == 2


def test_redirect_unknown_id_returns_404(client):
    resp = client.get("/zzzzzzzzz", follow_redirects=False)
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# GET /stats/{short_id}
# ---------------------------------------------------------------------------

def test_stats_initial_clicks_zero(client):
    body = client.post("/shorten", json={"url": "http://testserver/stats"}).json()
    resp = client.get(f"/stats/{body['short_id']}")
    assert resp.status_code == 200
    stats = resp.json()
    assert stats["clicks"] == 0
    assert stats["short_id"] == body["short_id"]
    assert stats["original_url"] == "http://testserver/stats"
    assert body["short_url"] == f"{BASE}/{body['short_id']}"


def test_stats_unknown_id_returns_404(client):
    resp = client.get("/stats/zzzzzzzzz")
    assert resp.status_code == 404


# ---------------------------------------------------------------------------
# Additional Tests: Bulk Shortening & Click Tracking
# ---------------------------------------------------------------------------

def test_shorten_10_links_and_display(client):
    """Test creating 10 shortened URLs and display their short versions"""
    logging.info("\n=== Testing 10 URL shortenings ===")

    # List of 10 different URLs to shorten
    urls_to_shorten = [
        "http://testserver/page1",
        "https://github.com/user/repo",
        "https://stackoverflow.com/questions/12345",
        "https://docs.python.org/3/library/",
        "https://www.youtube.com/watch?v=dQw4w9WgXcQ",
        "https://medium.com/article/title",
        "https://reddit.com/r/programming",
        "https://news.ycombinator.com/item?id=123",
        "https://twitter.com/user/status/456",
        "https://linkedin.com/in/profile"
    ]

    shortened_links = []

    # Create 10 shortened URLs
    for i, url in enumerate(urls_to_shorten, 1):
        resp = client.post("/shorten", json={"url": url})
        assert resp.status_code == 201, f"Failed to shorten URL {i}: {url}"

        body = resp.json()
        shortened_links.append({
            "index": i,
            "original": url,
            "short_id": body["short_id"],
            "short_url": body["short_url"]
        })

        logging.info(f"{i}. {url}")
        logging.info(f"   → {body['short_url']} (ID: {body['short_id']})")

    # Display summary
    print("\n" + "="*80)
    print("SHORTENED URLS SUMMARY")
    print("="*80)
    for link in shortened_links:
        print(f"{link['index']:2d}. Original: {link['original']}")
        print(f"    Short:    {link['short_url']}")
        print(f"    ID:       {link['short_id']}")
        print("-" * 80)

    # Verify all links are unique
    short_ids = [link["short_id"] for link in shortened_links]
    assert len(short_ids) == len(set(short_ids)), "All short IDs should be unique"

    logging.info(f"\n✅ Successfully created {len(shortened_links)} unique shortened URLs")
    print(f"\n✅ All {len(shortened_links)} URLs shortened successfully with unique IDs!\n")


def test_multiple_clicks_tracking(client):
    """Test that clicks are properly tracked after multiple redirects"""
    logging.info("\n=== Testing multiple clicks tracking ===")

    # Create a shortened URL
    original_url = "http://testserver/track-clicks"
    resp = client.post("/shorten", json={"url": original_url})
    assert resp.status_code == 201

    body = resp.json()
    short_id = body["short_id"]
    short_url = body["short_url"]

    print(f"\nCreated short URL: {short_url}")
    print(f"Original URL: {original_url}")
    print(f"Short ID: {short_id}\n")

    # Initial clicks should be 0
    stats_resp = client.get(f"/stats/{short_id}")
    assert stats_resp.status_code == 200
    initial_clicks = stats_resp.json()["clicks"]
    assert initial_clicks == 0
    print(f"Initial clicks: {initial_clicks}")

    # Simulate multiple clicks (redirects)
    num_clicks = 15
    print(f"\nSimulating {num_clicks} clicks...")

    for i in range(1, num_clicks + 1):
        # Follow the redirect
        redirect_resp = client.get(f"/{short_id}", follow_redirects=False)
        assert redirect_resp.status_code == 302
        assert redirect_resp.headers["location"] == original_url

        # Check clicks after each redirect
        stats_resp = client.get(f"/stats/{short_id}")
        current_clicks = stats_resp.json()["clicks"]

        # Verify clicks incremented correctly
        assert current_clicks == i, f"Expected {i} clicks, got {current_clicks}"

        if i % 5 == 0:  # Print every 5 clicks
            print(f"  After {i:2d} clicks: {current_clicks} total")

    # Final verification
    final_stats = client.get(f"/stats/{short_id}")
    final_body = final_stats.json()
    final_clicks = final_body["clicks"]

    print(f"\n{'='*60}")
    print(f"CLICK TRACKING RESULTS")
    print(f"{'='*60}")
    print(f"Short URL:      {short_url}")
    print(f"Original URL:   {final_body['original_url']}")
    print(f"Total Clicks:   {final_clicks}")
    print(f"Expected:       {num_clicks}")
    print(f"Match:          {'✅ YES' if final_clicks == num_clicks else '❌ NO'}")
    print(f"{'='*60}\n")

    assert final_clicks == num_clicks, f"Expected {num_clicks} clicks, got {final_clicks}"
    logging.info(f"✅ Click tracking verified: {final_clicks}/{num_clicks} clicks recorded correctly")
