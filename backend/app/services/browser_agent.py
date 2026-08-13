import time
import re
import urllib.parse
from typing import Dict, Any, Optional
from app.services.browser_automation_service import browser_automation
from app.core.logger import logger


class BrowserAgent:
    """Autonomous Browser Agent executing multi-step browser tasks using Playwright and local Ollama synthesis."""

    def _extract_query_after_keywords(self, task_str: str, keywords: list) -> Optional[str]:
        task_lower = task_str.lower()
        for kw in keywords:
            if kw in task_lower:
                idx = task_lower.find(kw)
                extracted = task_str[idx + len(kw):].strip(" ':\"")
                if extracted.startswith("and "):
                    extracted = extracted[4:].strip(" ':\"")
                if extracted.startswith("for "):
                    extracted = extracted[4:].strip(" ':\"")
                if extracted:
                    return extracted
        return None

    def execute_task(
        self,
        task: str,
        browser: str = "chrome",
        headless: bool = True
    ) -> Dict[str, Any]:
        """Parses and executes any multi-step natural language browser task autonomously."""
        start_time = time.time()
        task_str = task.strip()
        task_lower = task_str.lower()

        logger.info(f"BrowserAgent executing task: '{task_str}' on browser='{browser}'")

        try:
            # 1. YouTube Tasks
            if "youtube" in task_lower:
                query = self._extract_query_after_keywords(task_str, [
                    "search youtube for", "open youtube and search for", "youtube search for",
                    "search youtube", "find youtube video for", "find youtube videos on", "open youtube", "youtube"
                ])
                if not query or query.lower() in ["youtube", "open youtube"]:
                    query = "trending"

                res = browser_automation.search_youtube(query=query, browser=browser, headless=headless)
                agent_summary = f"### YouTube Search Agent Results for '{query}'\n"
                if res.get("videos"):
                    for idx, v in enumerate(res["videos"][:5], 1):
                        agent_summary += f"{idx}. **[{v['title']}]({v['url']})** - *Channel: {v['channel']}*\n"
                else:
                    agent_summary += f"Opened YouTube search for **[{query}](https://www.youtube.com/results?search_query={urllib.parse.quote(query)})**."

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": agent_summary,
                    "data": res.get("videos", []),
                    "execution_time_ms": elapsed_ms
                }

            # 2. LinkedIn Tasks
            elif "linkedin" in task_lower:
                query = self._extract_query_after_keywords(task_str, [
                    "open linkedin and search for", "search linkedin for", "open linkedin for",
                    "linkedin search for", "search linkedin", "open linkedin", "linkedin"
                ])
                if query and query.lower() in ["linkedin", "open linkedin"]:
                    query = None

                res = browser_automation.open_linkedin(profile_or_query=query, browser=browser, headless=headless)
                target_desc = f"searched for **'{query}'**" if query else "opened LinkedIn home page"
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": f"### LinkedIn Agent Result\nSuccessfully {target_desc} on LinkedIn.\n\n🔗 **[Open LinkedIn Target Page]({res['url']})** (Title: *{res.get('title', 'LinkedIn')}*)",
                    "data": res,
                    "execution_time_ms": elapsed_ms
                }

            # 3. GitHub Tasks
            elif "github" in task_lower:
                query = self._extract_query_after_keywords(task_str, [
                    "open github and search for", "search github for", "open github for",
                    "github search for", "search github", "open github", "github"
                ])
                if query and query.lower() in ["github", "open github"]:
                    query = None

                res = browser_automation.open_github(repo_or_user=query, browser=browser, headless=headless)
                target_desc = f"searched/opened **'{query}'**" if query else "opened GitHub home page"
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": f"### GitHub Agent Result\nSuccessfully {target_desc} on GitHub.\n\n🔗 **[Open GitHub Target Page]({res['url']})** (Title: *{res.get('title', 'GitHub')}*)",
                    "data": res,
                    "execution_time_ms": elapsed_ms
                }

            # 4. Amazon Tasks
            elif "amazon" in task_lower:
                query = self._extract_query_after_keywords(task_str, [
                    "open amazon and search for", "search amazon for", "amazon search for",
                    "search amazon", "open amazon", "amazon"
                ])
                if query and query.lower() not in ["amazon", "open amazon"]:
                    target_url = f"https://www.amazon.com/s?k={urllib.parse.quote(query)}"
                else:
                    target_url = "https://www.amazon.com"
                
                res = browser_automation.open_website(url=target_url, browser=browser, headless=headless)
                target_desc = f"searched Amazon for **'{query}'**" if query and query.lower() not in ["amazon", "open amazon"] else "opened Amazon home page"
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": f"### Amazon Agent Result\nSuccessfully {target_desc}.\n\n🔗 **[Open Amazon Target Page]({res['url']})**",
                    "data": res,
                    "execution_time_ms": elapsed_ms
                }

            # 5. Wikipedia Tasks
            elif "wikipedia" in task_lower:
                query = self._extract_query_after_keywords(task_str, [
                    "open wikipedia and search for", "search wikipedia for", "wikipedia search for",
                    "search wikipedia", "open wikipedia", "wikipedia"
                ])
                if query and query.lower() not in ["wikipedia", "open wikipedia"]:
                    target_url = f"https://en.wikipedia.org/w/index.php?search={urllib.parse.quote(query)}"
                else:
                    target_url = "https://en.wikipedia.org"

                res = browser_automation.open_website(url=target_url, browser=browser, headless=headless)
                target_desc = f"searched Wikipedia for **'{query}'**" if query and query.lower() not in ["wikipedia", "open wikipedia"] else "opened Wikipedia home page"
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": f"### Wikipedia Agent Result\nSuccessfully {target_desc}.\n\n🔗 **[Open Wikipedia Target Page]({res['url']})**",
                    "data": res,
                    "execution_time_ms": elapsed_ms
                }

            # 6. Reddit Tasks
            elif "reddit" in task_lower:
                query = self._extract_query_after_keywords(task_str, [
                    "open reddit and search for", "search reddit for", "reddit search for",
                    "search reddit", "open reddit", "reddit"
                ])
                if query and query.lower() not in ["reddit", "open reddit"]:
                    target_url = f"https://www.reddit.com/search/?q={urllib.parse.quote(query)}"
                else:
                    target_url = "https://www.reddit.com"

                res = browser_automation.open_website(url=target_url, browser=browser, headless=headless)
                target_desc = f"searched Reddit for **'{query}'**" if query and query.lower() not in ["reddit", "open reddit"] else "opened Reddit home page"
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": f"### Reddit Agent Result\nSuccessfully {target_desc}.\n\n🔗 **[Open Reddit Target Page]({res['url']})**",
                    "data": res,
                    "execution_time_ms": elapsed_ms
                }

            # 7. Direct Domain / URL Navigation (e.g. "github.com", "google.com", "http://...", "open stackoverflow.com")
            elif any(domain_ext in task_lower for domain_ext in [".com", ".org", ".net", ".io", ".dev", ".in", "http://", "https://"]):
                words = task_str.split()
                url = task_str
                for w in words:
                    if "." in w or "http" in w:
                        url = w.strip(" ':\"")
                        break

                res = browser_automation.open_website(url=url, browser=browser, headless=headless)
                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": f"### Navigation Result\nSuccessfully opened **[{res.get('title', url)}]({res['url']})** using {browser}.",
                    "data": res,
                    "execution_time_ms": elapsed_ms
                }

            # 8. General Search Intent (Google / DuckDuckGo fallback for any natural language query)
            else:
                query = self._extract_query_after_keywords(task_str, [
                    "search google for", "google search for", "search for", "google search", "find", "search"
                ]) or task_str

                res = browser_automation.search_google(query=query, browser=browser, headless=headless)
                agent_summary = f"### Web Search Results for '{query}'\n"
                if res.get("results"):
                    for idx, r in enumerate(res["results"][:5], 1):
                        snippet_text = r.get("snippet") or r.get("title") or ""
                        agent_summary += f"{idx}. **[{r['title']}]({r['url']})**\n   _{snippet_text}_\n"
                else:
                    agent_summary += f"Processed search query **[{query}](https://www.google.com/search?q={urllib.parse.quote(query)})**."

                elapsed_ms = round((time.time() - start_time) * 1000, 2)
                return {
                    "status": "success",
                    "task": task_str,
                    "summary": agent_summary,
                    "data": res.get("results", []),
                    "execution_time_ms": elapsed_ms
                }

        except Exception as e:
            logger.error(f"BrowserAgent error executing task '{task_str}': {e}")
            elapsed_ms = round((time.time() - start_time) * 1000, 2)
            return {
                "status": "error",
                "task": task_str,
                "summary": f"Failed to execute browser agent task: {str(e)}",
                "error": str(e),
                "execution_time_ms": elapsed_ms
            }


browser_agent = BrowserAgent()
