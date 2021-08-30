import time

from pathlib import Path
from selenium import webdriver
from selenium.webdriver.firefox.options import Options

from foxford._const import BASE, JS_INJECT, STYLES

class FoxfordBrowser(object):
    def __init__(self, session, loadtime=4):
        self._session = session

        self._browser = None
        self._launch_status = 'not_launched'

        self._page_loadtime = loadtime
        
    def _launch(self):
        try:
            options = Options()
            options.headless = True
            self._browser = webdriver.Firefox(options=options)

            cookies = [
                {
                    'name': c.name,
                    'value': c.value,
                    'domain': c.domain,
                    'path': c.path,
                    'expires': c.expires
                }
                for c in self._session.cookies
            ]
            self._browser.get(BASE)
            for c in cookies:
                self._browser.add_cookie(c)
            
            self._browser.refresh()

            if 'dashboard' in self._browser.current_url:
                self._launch_status = 'ok'
                self._browser.implicitly_wait(self._page_loadtime)

                print('[FoxfordBrowser] Запущен')
            else:
                self._launch_status = 'fail'
                self._browser.quit()
                print('[FoxfordBrowser] Не удалось авторизоваться')
        except:
            if self._browser: self._browser.quit()
            self._launch_status = 'fail'
            print('[FoxfordBrowser] Не удалось запустить')
    
    def _quit(self):
        return self._browser.quit()
    
    def _inject_styles(self):
        try:
            self._browser.execute_script(JS_INJECT.format(styles=STYLES))
        except:
            print('[FoxfordBrowser] Не удалось выполнить CSS инъекцию')
    
    def print(self, url, filepath, element='taskContent'):
        if self._launch_status == 'not_launched':
            self._launch()
        
        if self._launch_status == 'fail':
            return
        
        filepath = Path(filepath)
        filepath.parent.mkdir(parents=True, exist_ok=True)
        filepath = filepath.with_suffix('.png')

        try:
            self._browser.get(url)
            if url != self._browser.current_url:
                print('[Browser] Страница недоступна')
                return
            self._inject_styles()
            time.sleep(self._page_loadtime)
            e = self._browser.find_element_by_id(element)
            e.screenshot(f'{filepath}')
        except:
            print('[FoxfordBrowser] Не удалось найти элемент')