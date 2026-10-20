import json
import os
import re
import time

from loguru import logger
from changedetectionio.content_fetchers.base import Fetcher


def _browser_name():
    name = os.getenv("WEBDRIVER_BROWSER", "chrome").strip().lower()
    return name if name in ("firefox", "chrome") else "chrome"


class fetcher(Fetcher):
    _browser = _browser_name()

    if _browser == "firefox":
        if os.getenv("WEBDRIVER_URL"):
            fetcher_description = f"WebDriver Firefox/Javascript via \"{os.getenv('WEBDRIVER_URL', '')}\""
        else:
            fetcher_description = "WebDriver Firefox/Javascript (geckodriver)"
    else:
        if os.getenv("WEBDRIVER_URL"):
            fetcher_description = f"WebDriver Chrome/Javascript via \"{os.getenv('WEBDRIVER_URL', '')}\""
        else:
            fetcher_description = "WebDriver Chrome/Javascript"

    proxy = None
    proxy_url = None

    # Capability flags
    supports_browser_steps = True
    supports_screenshots = True
    supports_xpath_element_data = True

    @classmethod
    def get_status_icon_data(cls):
        if cls._browser == "firefox":
            return {
                'filename': 'generic-icon.svg',
                'alt': 'Using a Firefox browser',
                'title': 'Using a Firefox browser',
            }
        return {
            'filename': 'google-chrome-icon.png',
            'alt': 'Using a Chrome browser',
            'title': 'Using a Chrome browser'
        }

    def __init__(self, proxy_override=None, custom_browser_connection_url=None, **kwargs):
        super().__init__(**kwargs)

        if custom_browser_connection_url:
            self.browser_connection_is_custom = True
            self.browser_connection_url = custom_browser_connection_url
        else:
            default_url = '' if self._browser == 'firefox' else 'http://browser-chrome:4444/wd/hub'
            self.browser_connection_url = os.getenv("WEBDRIVER_URL", default_url).strip('"')

        ##### PROXY SETUP #####

        proxy_sources = [
            self.system_http_proxy,
            self.system_https_proxy,
            os.getenv('webdriver_proxySocks'),
            os.getenv('webdriver_socksProxy'),
            os.getenv('webdriver_proxyHttp'),
            os.getenv('webdriver_httpProxy'),
            os.getenv('webdriver_proxyHttps'),
            os.getenv('webdriver_httpsProxy'),
            os.getenv('webdriver_sslProxy'),
            proxy_override,  # last one should override
        ]
        for k in filter(None, proxy_sources):
            if not k:
                continue
            self.proxy_url = k.strip()

    # ------------------------------------------------------------------
    # Driver creation
    # ------------------------------------------------------------------
    def _new_chrome_driver(self):
        from selenium.webdriver.chrome.options import Options as ChromeOptions
        from selenium.webdriver.remote.remote_connection import RemoteConnection
        from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver
        from selenium.webdriver.remote.client_config import ClientConfig
        from urllib3.util import Timeout

        options = ChromeOptions()
        for opt in [
            line.strip()
            for line in os.getenv("CHROME_OPTIONS", "").strip().splitlines()
            if line.strip()
        ]:
            options.add_argument(opt)

        if self.proxy_url:
            options.add_argument(f'--proxy-server={self.proxy_url}')

        connection_timeout = int(os.getenv("WEBDRIVER_CONNECTION_TIMEOUT", 90))
        client_config = ClientConfig(
            remote_server_addr=self.browser_connection_url,
            timeout=Timeout(connect=connection_timeout, total=connection_timeout)
        )
        remote_connection = RemoteConnection(client_config=client_config)
        driver = RemoteWebDriver(command_executor=remote_connection, options=options)
        driver.set_page_load_timeout(int(os.getenv("WEBDRIVER_PAGELOAD_TIMEOUT", 45)))
        return driver

    def _new_firefox_driver(self):
        from urllib.parse import urlparse
        from selenium.webdriver.firefox.options import Options as FirefoxOptions
        from selenium.webdriver.firefox.service import Service as FirefoxService
        from selenium.webdriver import Firefox
        from selenium.webdriver.remote.webdriver import WebDriver as RemoteWebDriver

        options = FirefoxOptions()
        options.binary_location = os.getenv("FIREFOX_BIN", "/usr/bin/firefox")
        options.add_argument("-headless")
        options.add_argument("--width=1280")
        options.add_argument("--height=1024")

        for opt in [
            line.strip()
            for line in os.getenv("FIREFOX_OPTIONS", "").strip().splitlines()
            if line.strip()
        ]:
            options.add_argument(opt)

        for key, value in {
            "browser.shell.checkDefaultBrowser": False,
            "browser.startup.homepage": "about:blank",
            "browser.startup.page": 0,
            "datareporting.policy.dataSubmissionEnabled": False,
            "toolkit.telemetry.enabled": False,
            "dom.webdriver.enabled": True,
            "useAutomationExtension": False,
        }.items():
            options.set_preference(key, value)

        if self.proxy_url:
            raw = self.proxy_url if "://" in self.proxy_url else "http://" + self.proxy_url
            parsed = urlparse(raw)
            options.set_preference("network.proxy.type", 1)
            if parsed.scheme.startswith("socks"):
                options.set_preference("network.proxy.socks", parsed.hostname or "127.0.0.1")
                options.set_preference("network.proxy.socks_port", parsed.port or 1080)
                options.set_preference("network.proxy.socks_version", 5 if "5" in parsed.scheme else 4)
                options.set_preference("network.proxy.socks_remote_dns", True)
            else:
                options.set_preference("network.proxy.http", parsed.hostname or "127.0.0.1")
                options.set_preference("network.proxy.http_port", parsed.port or 8080)
                options.set_preference("network.proxy.ssl", parsed.hostname or "127.0.0.1")
                options.set_preference("network.proxy.ssl_port", parsed.port or 8080)

        if self.browser_connection_url:
            driver = RemoteWebDriver(
                command_executor=self.browser_connection_url,
                options=options,
            )
        else:
            service = FirefoxService(
                executable_path=os.getenv("GECKODRIVER_PATH", "/usr/bin/geckodriver")
            )
            driver = Firefox(service=service, options=options)

        driver.set_page_load_timeout(int(os.getenv("WEBDRIVER_PAGELOAD_TIMEOUT", 45)))
        return driver

    # ------------------------------------------------------------------
    # Selenium browser steps
    # ------------------------------------------------------------------
    @staticmethod
    def _selector(selector):
        from selenium.webdriver.common.by import By
        s = (selector or "").strip()
        if s.startswith("//") or s.startswith("(") or s.startswith("/"):
            return By.XPATH, s
        return By.CSS_SELECTOR, s

    @staticmethod
    def _xpath_literal(value):
        if '"' not in value:
            return f'"{value}"'
        if "'" not in value:
            return f"'{value}'"
        parts = value.split('"')
        return "concat(" + ", '\"', ".join(f'"{p}"' for p in parts) + ")"

    def _find(self, driver, selector, timeout=10):
        from selenium.webdriver.support.ui import WebDriverWait
        by, value = self._selector(selector)
        return WebDriverWait(driver, timeout).until(lambda d: d.find_element(by, value))

    def _find_by_text(self, driver, text, timeout=10):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.support.ui import WebDriverWait
        xpath = f"//*[contains(normalize-space(.), {self._xpath_literal(text)})]"
        return WebDriverWait(driver, timeout).until(lambda d: d.find_element(By.XPATH, xpath))

    def _save_step_state(self, driver, label):
        path = self.browser_steps_screenshot_path
        if not path:
            return
        os.makedirs(path, exist_ok=True)
        try:
            from PIL import Image
            import io
            png = driver.get_screenshot_as_png()
            img = Image.open(io.BytesIO(png)).convert("RGB")
            buf = io.BytesIO()
            img.save(buf, format="JPEG", quality=72)
            with open(os.path.join(path, f"step_{label}.jpeg"), "wb") as f:
                f.write(buf.getvalue())
        except Exception as e:
            logger.debug(f"Could not save browser step screenshot {label}: {e}")
        try:
            with open(os.path.join(path, f"step_{label}.html"), "w", encoding="utf-8") as f:
                f.write(driver.page_source)
        except Exception as e:
            logger.debug(f"Could not save browser step HTML {label}: {e}")

    def _call_step(self, driver, operation, selector, value, start_url):
        from selenium.webdriver.common.by import By
        from selenium.webdriver.common.keys import Keys
        from selenium.webdriver.common.action_chains import ActionChains
        from selenium.webdriver.support.ui import WebDriverWait, Select
        from selenium.common.exceptions import (
            NoSuchElementException, TimeoutException, ElementClickInterceptedException,
            StaleElementReferenceException,
        )

        name = re.sub("[^0-9a-zA-Z]+", "_", (operation or "").lower()).strip("_")
        if name in ("", "choose_one"):
            return

        def require_selector():
            if not selector:
                raise ValueError(f"'{operation}' requires a selector")

        if name == "goto_url":
            if not value:
                raise ValueError("'Goto URL' requires a URL")
            from changedetectionio.validate_url import validate_fetch_url
            validate_fetch_url(value)
            driver.get(value)
            return

        if name == "goto_site":
            from changedetectionio.validate_url import validate_fetch_url
            validate_fetch_url(start_url)
            driver.get(start_url)
            return

        if name in ("click_element", "click_button_containing_text"):
            require_selector()
            self._find(driver, selector).click()
            return

        if name == "click_element_if_exists":
            require_selector()
            try:
                self._find(driver, selector, timeout=5).click()
            except (NoSuchElementException, TimeoutException, ElementClickInterceptedException):
                return
            return

        if name == "click_element_containing_text":
            if not value:
                raise ValueError("'Click element containing text' requires text")
            self._find_by_text(driver, value).click()
            return

        if name == "click_element_containing_text_if_exists":
            if not value:
                return
            try:
                self._find_by_text(driver, value, timeout=5).click()
            except (NoSuchElementException, TimeoutException, ElementClickInterceptedException):
                return
            return

        if name == "click_x_y":
            m = re.match(r"^\s*(\d+)\s*,\s*(\d+)\s*$", value or "")
            if not m:
                raise ValueError("'Click X,Y' should look like '100, 90'")
            x, y = int(m.group(1)), int(m.group(2))
            ActionChains(driver).move_by_offset(x, y).click().perform()
            return

        if name == "enter_text_in_field":
            require_selector()
            el = self._find(driver, selector)
            el.clear()
            el.send_keys(value)
            return

        if name == "execute_js":
            if value:
                return driver.execute_script(value)
            return None

        if name in ("select_by_label", "select_by_option_text"):
            require_selector()
            Select(self._find(driver, selector)).select_by_visible_text(value)
            return

        if name == "scroll_down":
            driver.execute_script("window.scrollBy(0, 600)")
            return

        if name == "scroll_to_bottom":
            driver.execute_script("window.scrollTo(0, document.body.scrollHeight)")
            return

        if name == "scroll_to_top":
            driver.execute_script("window.scrollTo(0, 0)")
            return

        if name == "scroll_to_element":
            require_selector()
            driver.execute_script("arguments[0].scrollIntoView({block: 'center'})", self._find(driver, selector))
            return

        if name == "wait_for_seconds":
            try:
                time.sleep(float(value) if value else 1.0)
            except (TypeError, ValueError):
                time.sleep(1.0)
            return

        if name == "wait_for_text":
            if not value:
                return
            WebDriverWait(driver, 30).until(
                lambda d: value in d.find_element(By.TAG_NAME, "body").text
            )
            return

        if name == "wait_for_text_in_element":
            require_selector()
            el = self._find(driver, selector)
            WebDriverWait(driver, 30).until(lambda d: value in el.text)
            return

        if name in ("press_enter", "press_page_up", "press_page_down"):
            key = {
                "press_enter": Keys.ENTER,
                "press_page_up": Keys.PAGE_UP,
                "press_page_down": Keys.PAGE_DOWN,
            }[name]
            try:
                target = driver.switch_to.active_element
            except Exception:
                target = driver.find_element(By.TAG_NAME, "body")
            target.send_keys(key)
            return

        if name in ("check_checkbox", "uncheck_checkbox"):
            require_selector()
            el = self._find(driver, selector)
            desired = name == "check_checkbox"
            if el.is_selected() != desired:
                el.click()
            return

        if name == "remove_elements":
            require_selector()
            for el in driver.find_elements(*self._selector(selector)):
                driver.execute_script("arguments[0].remove()", el)
            return

        if name == "make_all_child_elements_visible":
            require_selector()
            js = """
                arguments[0].querySelectorAll('*').forEach(function(el) {
                    el.style.display = 'block';
                    el.style.visibility = 'visible';
                    el.style.opacity = '1';
                    el.style.position = 'relative';
                    el.style.height = 'auto';
                    el.style.width = 'auto';
                    el.removeAttribute('hidden');
                    el.classList.remove('hidden', 'd-none');
                });
            """
            for el in driver.find_elements(*self._selector(selector)):
                driver.execute_script(js, el)
            return

        if name == "switch_to_iframe_by_index_number":
            driver.switch_to.frame(int(value))
            return

        logger.warning(f"Selenium browser step '{operation}' is not implemented, skipping")

    def _run_browser_steps(self, driver, start_url):
        from changedetectionio.browser_steps.browser_steps import browser_steps_get_valid_steps
        from changedetectionio.jinja2_custom import render as jinja_render
        from changedetectionio.content_fetchers.exceptions import BrowserStepsStepException

        steps = browser_steps_get_valid_steps(self.browser_steps or [])
        if not steps:
            return

        self.delete_browser_steps_screenshots()

        for step_n, step in enumerate(steps, 1):
            logger.debug(f">> Selenium browser Step n {step_n} - {step.get('operation')}...")
            self._save_step_state(driver, f"before-{step_n}")
            try:
                selector = step.get("selector") or ""
                value = step.get("optional_value") or ""
                if "{%" in selector or "{{" in selector:
                    selector = jinja_render(template_str=selector)
                if "{%" in value or "{{" in value:
                    value = jinja_render(template_str=value)
                self._call_step(driver, step.get("operation") or "", selector, value, start_url)
                time.sleep(1.5)
            except Exception as e:
                raise BrowserStepsStepException(step_n=step_n, original_e=e)
            self._save_step_state(driver, str(step_n))

    # ------------------------------------------------------------------
    # Main fetch
    # ------------------------------------------------------------------
    async def run(self,
                  fetch_favicon=True,
                  current_include_filters=None,
                  empty_pages_are_a_change=False,
                  ignore_status_codes=False,
                  is_binary=False,
                  request_body=None,
                  request_headers=None,
                  request_method=None,
                  screenshot_format=None,
                  timeout=None,
                  url=None,
                  watch_uuid=None,
                  ):

        import asyncio

        def _run_sync():
            # request_body, request_method unused for now, until some magic in the future happens.
            driver = None
            try:
                if self._browser == "firefox":
                    driver = self._new_firefox_driver()
                else:
                    driver = self._new_chrome_driver()
            except Exception as e:
                if driver:
                    driver.quit()
                raise e

            try:
                driver.get(url)

                if self.browser_steps:
                    self._run_browser_steps(driver, url)

                if not (self._browser == "firefox" and "--width=" in os.getenv("FIREFOX_OPTIONS", "")):
                    if not (self._browser == "chrome" and "--window-size" in os.getenv("CHROME_OPTIONS", "")):
                        driver.set_window_size(1280, 1024)

                driver.implicitly_wait(int(os.getenv("WEBDRIVER_DELAY_BEFORE_CONTENT_READY", 5)))

                if self.webdriver_js_execute_code is not None:
                    driver.execute_script(self.webdriver_js_execute_code)
                    driver.implicitly_wait(int(os.getenv("WEBDRIVER_DELAY_BEFORE_CONTENT_READY", 5)))

                self.status_code = 200

                time.sleep(int(os.getenv("WEBDRIVER_DELAY_BEFORE_CONTENT_READY", 5)) + self.render_extract_delay)
                self.content = driver.page_source
                self.headers = {}

                # Selenium always captures as PNG, convert to JPEG if needed
                screenshot_png = driver.get_screenshot_as_png()

                if self.screenshot_format and self.screenshot_format.upper() == 'JPEG':
                    from PIL import Image
                    import io
                    img = Image.open(io.BytesIO(screenshot_png))
                    if img.mode in ('RGBA', 'LA', 'P', 'PA'):
                        if img.mode == 'P':
                            img = img.convert('RGBA')
                        background = Image.new('RGB', img.size, (255, 255, 255))
                        if img.mode in ('RGBA', 'LA', 'PA'):
                            background.paste(img, mask=img.split()[-1])
                        img = background
                    elif img.mode != 'RGB':
                        img = img.convert('RGB')
                    jpeg_buffer = io.BytesIO()
                    img.save(jpeg_buffer, format='JPEG', quality=int(os.getenv("SCREENSHOT_QUALITY", 72)))
                    self.screenshot = jpeg_buffer.getvalue()
                    img.close()
                else:
                    self.screenshot = screenshot_png
            except Exception as e:
                driver.quit()
                raise e

            driver.quit()

        # Run the selenium operations in a thread pool to avoid blocking the event loop
        loop = asyncio.get_event_loop()
        await loop.run_in_executor(None, _run_sync)


# Plugin registration for built-in fetcher
class WebDriverSeleniumFetcherPlugin:
    """Plugin class that registers the WebDriver Selenium fetcher as a built-in plugin."""

    def register_content_fetcher(self):
        """Register the WebDriver Selenium fetcher"""
        return ('html_webdriver', fetcher)


# Create module-level instance for plugin registration
webdriver_selenium_plugin = WebDriverSeleniumFetcherPlugin()
