from boxtodocx.utils.logger import setup_logger
from yattag import Doc
import logging
from selenium import webdriver
from selenium.webdriver.chrome.options import Options
from ..utils.logger import setup_logger
import os
import time
import requests
from typing import Optional

class HTMLHandler:
    def __init__(self):
        self.doc, self.tag, self.text = Doc().tagtext()
        self.browser = None
        self.cookies = None
        self.is_logged_in = False
        self.pending_images = []
        self.logger = setup_logger()

    def convert_to_html(self, content_list, dest_dir):
        try:
            with self.tag('html'):
                with self.tag('body'):
                    for elm in content_list:
                        self._process_element(elm, dest_dir=dest_dir)
            
            if self.pending_images:
                self._download_images()
            
            return self.doc.getvalue()
        finally:
            self.cleanup()

    def _handle_browser(self, initial_url):
        if not self.browser:
            for name, driver in [('chrome', webdriver.Chrome), ('firefox', webdriver.Firefox), ('safari', webdriver.Safari)]:
                try:
                    options = self._get_browser_options(name)
                    self.browser = driver(options=options)
                    self.logger.info(f"Using {name} browser")
                    break
                except Exception:
                    continue

            if not self.browser:
                raise RuntimeError("No supported browser found")

            self.browser.get(initial_url)
            self.logger.info("Please log in to Box. Browser will be minimized after login.")
            input("Press Enter after logging in...")
            self.browser.minimize_window()
            self.cookies = self.browser.get_cookies()
            self.is_logged_in = True

    def _process_element(self, el, dest_dir):
        if 'content' in el:
            self._handle_content_element(el, dest_dir)
        elif 'text' in el:
            self._handle_text_element(el)

    def _handle_content_element(self, el, dest_dir):
        if el['type'] == 'image':
            self._handle_image(el, dest_dir)
        elif el['type'] == 'table':
            self._handle_table(el)
        else:
            self._handle_other_content(el, dest_dir)

    def _handle_image(self, el, dest_dir):
        if 'attrs' in el and 'src' in el['attrs']:
            if not os.path.exists(dest_dir):
                os.makedirs(dest_dir)
            
            image_path = os.path.join(dest_dir, f"image_{hash(el['attrs']['src'])}.png")
            self.pending_images.append((el['attrs']['src'], image_path))
            
            if not self.is_logged_in:
                self._handle_browser(el['attrs']['src'])

    def _download_images(self):
        session = requests.Session()
        for cookie in self.cookies:
            session.cookies.set(cookie['name'], cookie['value'])

        for img_url, dest_path in self.pending_images:
            try:
                response = session.get(img_url)
                if response.status_code == 200:
                    with open(dest_path, 'wb') as f:
                        f.write(response.content)
                    self.logger.info(f"Downloaded: {dest_path}")
            except Exception as e:
                self.logger.error(f"Failed to download {img_url}: {str(e)}")

    def cleanup(self):
        if self.browser:
            self.browser.quit()
            self.logger.info("Browser session closed")
