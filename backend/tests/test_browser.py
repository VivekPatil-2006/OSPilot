import pytest
from app.services.browser_automation_service import browser_automation
from app.services.browser_agent import browser_agent


def test_open_website():
    res = browser_automation.open_website("example.com", browser="chromium", headless=True)
    assert res["status"] == "success"
    assert "Example Domain" in res["title"] or "example" in res["url"].lower()
    assert res["screenshot_preview"].startswith("data:image/png;base64,")


def test_google_search():
    res = browser_automation.search_google("FastAPI Python", browser="chromium", headless=True)
    assert res["action"] == "search_google"
    assert len(res["results"]) > 0
    first_res = res["results"][0]
    assert "title" in first_res and "url" in first_res


def test_youtube_search():
    res = browser_automation.search_youtube("Python Programming", browser="chromium", headless=True)
    assert res["action"] == "search_youtube"
    assert len(res["videos"]) > 0
    first_vid = res["videos"][0]
    assert "title" in first_vid and "url" in first_vid


def test_open_github_and_linkedin():
    gh_res = browser_automation.open_github("fastapi/fastapi", browser="chromium", headless=True)
    assert gh_res["status"] == "success"
    assert "github.com/fastapi/fastapi" in gh_res["url"].lower()

    li_res = browser_automation.open_linkedin(browser="chromium", headless=True)
    assert li_res["status"] == "success"
    assert "linkedin.com" in li_res["url"].lower()


def test_browser_agent():
    res = browser_agent.execute_task("Search Google for Python Playwright", browser="chromium", headless=True)
    assert res["status"] == "success"
    assert len(res["summary"]) > 0
    assert len(res["data"]) > 0
