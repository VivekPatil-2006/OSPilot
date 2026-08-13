from fastapi import APIRouter, HTTPException
from app.domain.schemas import (
    BrowserNavRequest, GoogleSearchRequest, YouTubeSearchRequest, PortalRequest,
    FormFillRequest, ButtonClickRequest, DownloadFileRequest,
    BrowserAgentTaskRequest, BrowserActionResult
)
from app.services.browser_automation_service import browser_automation
from app.services.browser_agent import browser_agent

router = APIRouter(prefix="/browser", tags=["Browser Automation & Browser Agent"])


@router.post("/open", response_model=BrowserActionResult)
def open_website(req: BrowserNavRequest) -> BrowserActionResult:
    """Launches Playwright browser (Google Chrome, Microsoft Edge) and opens target website."""
    try:
        res = browser_automation.open_website(url=req.url, browser=req.browser, headless=req.headless)
        return BrowserActionResult(status=res["status"], action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/search/google", response_model=BrowserActionResult)
def search_google(req: GoogleSearchRequest) -> BrowserActionResult:
    """Performs Google search and parses top organic titles, URLs, and snippets."""
    try:
        res = browser_automation.search_google(query=req.query, browser=req.browser, headless=req.headless)
        return BrowserActionResult(status="success", action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/search/youtube", response_model=BrowserActionResult)
def search_youtube(req: YouTubeSearchRequest) -> BrowserActionResult:
    """Searches YouTube and parses video titles, channel names, and video URLs."""
    try:
        res = browser_automation.search_youtube(query=req.query, browser=req.browser, headless=req.headless)
        return BrowserActionResult(status="success", action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/github", response_model=BrowserActionResult)
def open_github(req: PortalRequest) -> BrowserActionResult:
    """Navigates to GitHub home page or specified repository/user profile."""
    try:
        res = browser_automation.open_github(repo_or_user=req.target, browser=req.browser, headless=req.headless)
        return BrowserActionResult(status=res["status"], action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/linkedin", response_model=BrowserActionResult)
def open_linkedin(req: PortalRequest) -> BrowserActionResult:
    """Navigates to LinkedIn home page or specified profile/search."""
    try:
        res = browser_automation.open_linkedin(profile_or_query=req.target, browser=req.browser, headless=req.headless)
        return BrowserActionResult(status=res["status"], action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/form/fill", response_model=BrowserActionResult)
def fill_form(req: FormFillRequest) -> BrowserActionResult:
    """Fills web form input fields and optionally submits the form."""
    try:
        res = browser_automation.fill_form(
            url=req.url,
            form_data=req.form_data,
            submit_selector=req.submit_selector,
            browser=req.browser,
            headless=req.headless
        )
        return BrowserActionResult(status=res["status"], action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/click", response_model=BrowserActionResult)
def click_button(req: ButtonClickRequest) -> BrowserActionResult:
    """Clicks a button or link matching CSS selector or visible text content."""
    try:
        res = browser_automation.click_button(
            url=req.url,
            selector_or_text=req.selector_or_text,
            browser=req.browser,
            headless=req.headless
        )
        return BrowserActionResult(status=res["status"], action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=400, detail=str(e))


@router.post("/download", response_model=BrowserActionResult)
def download_file(req: DownloadFileRequest) -> BrowserActionResult:
    """Intercepts download event and saves downloaded file to local storage."""
    try:
        res = browser_automation.download_file(
            url=req.url,
            download_selector=req.download_selector,
            save_dir=req.save_dir,
            browser=req.browser,
            headless=req.headless
        )
        return BrowserActionResult(status=res["status"], action=res["action"], data=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))


@router.post("/agent/execute", response_model=BrowserActionResult)
def execute_browser_agent(req: BrowserAgentTaskRequest) -> BrowserActionResult:
    """Executes multi-step autonomous browser tasks using BrowserAgent."""
    try:
        res = browser_agent.execute_task(
            task=req.task,
            browser=req.browser,
            headless=req.headless
        )
        return BrowserActionResult(status=res["status"], action="browser_agent_task", data=res)
    except Exception as e:
        raise HTTPException(status_code=500, detail=str(e))
