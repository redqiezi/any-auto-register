"""Playwright 执行器 - 支持 headless/headed 模式与持久 browser profile"""
from ..base_executor import BaseExecutor, Response


class PlaywrightExecutor(BaseExecutor):
    def __init__(self, proxy: str = None, headless: bool = True,
                 user_data_dir: str = None, extension_paths: list[str] = None):
        super().__init__(proxy)
        self.headless = headless
        self.user_data_dir = user_data_dir
        self.extension_paths = extension_paths or []
        self._browser = None
        self._context = None
        self._page = None
        self._pw = None
        self._init()

    def _init(self):
        from playwright.sync_api import sync_playwright
        self._pw = sync_playwright().start()
        launch_opts = {"headless": self.headless}
        if self.proxy:
            launch_opts["proxy"] = {"server": self.proxy}
        browser_args = []
        if self.extension_paths:
            joined = ",".join(self.extension_paths)
            browser_args.extend([
                f"--disable-extensions-except={joined}",
                f"--load-extension={joined}",
            ])
        if browser_args:
            launch_opts["args"] = browser_args
        if self.user_data_dir:
            self._context = self._pw.chromium.launch_persistent_context(
                self.user_data_dir,
                **launch_opts,
            )
            self._page = self._context.pages[0] if self._context.pages else self._context.new_page()
            self._browser = self._context.browser
        else:
            self._browser = self._pw.chromium.launch(**launch_opts)
            self._context = self._browser.new_context()
            self._page = self._context.new_page()

    def get(self, url, *, headers=None, params=None) -> Response:
        import urllib.parse
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        if headers:
            self._page.set_extra_http_headers(headers)
        resp = self._page.goto(url)
        return Response(
            status_code=resp.status,
            text=self._page.content(),
            headers=dict(resp.headers),
            cookies=self.get_cookies(),
        )

    def post(self, url, *, headers=None, params=None, data=None, json=None) -> Response:
        import urllib.parse
        import json as _json
        if params:
            url = url + "?" + urllib.parse.urlencode(params)
        post_data = None
        content_type = "application/x-www-form-urlencoded"
        if json is not None:
            post_data = _json.dumps(json)
            content_type = "application/json"
        elif data:
            post_data = urllib.parse.urlencode(data)
        h = {"Content-Type": content_type}
        if headers:
            h.update(headers)
        resp = self._page.request.post(url, headers=h, data=post_data)
        return Response(
            status_code=resp.status,
            text=resp.text(),
            headers=dict(resp.headers),
            cookies=self.get_cookies(),
        )

    def get_cookies(self) -> dict:
        return {c["name"]: c["value"] for c in self._context.cookies()}

    def set_cookies(self, cookies: dict, domain: str = ".example.com") -> None:
        page_url = self._page.url if self._page else None
        if page_url and page_url.startswith("http"):
            self._context.add_cookies([
                {"name": k, "value": v, "url": page_url} for k, v in cookies.items()
            ])
        else:
            self._context.add_cookies([
                {"name": k, "value": v, "domain": domain, "path": "/"} for k, v in cookies.items()
            ])

    def close(self) -> None:
        if self._context:
            self._context.close()
            self._context = None
        elif self._browser:
            self._browser.close()
            self._browser = None
        if self._pw:
            self._pw.stop()
            self._pw = None

    def get_context(self):
        return self._context

    def get_page(self):
        return self._page
