"""Test-only Playwright shim: when PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH is set, pin
BrowserType.launch to that binary. Needed in dev sandboxes where the pip-installed
`playwright` package version doesn't match whatever browser revision happens to be
pre-installed on the machine (Docker/CI installs both together via
`playwright install --with-deps chromium`, so this never applies there).
Unconditionally installed but a no-op unless the env var is set - production code is
never touched."""
import os

from playwright.async_api import BrowserType

_original_launch = BrowserType.launch


async def _patched_launch(self, *args, **kwargs):
    exe = os.environ.get("PLAYWRIGHT_CHROMIUM_EXECUTABLE_PATH")
    if exe and "executable_path" not in kwargs:
        kwargs["executable_path"] = exe
    return await _original_launch(self, *args, **kwargs)


BrowserType.launch = _patched_launch
