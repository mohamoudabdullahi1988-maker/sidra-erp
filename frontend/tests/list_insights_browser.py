"""Isolated browser tests using the existing synthetic response fixtures."""
import json
from pathlib import Path
from playwright.sync_api import sync_playwright, expect
from browser import BOOT, answer
with sync_playwright() as p:
 browser=p.chromium.launch()
 for width in (1440,390):
  page=browser.new_page(viewport={'width':width,'height':950},accept_downloads=True)
  page.add_init_script('window.berjaya_boot='+json.dumps(BOOT))
  errors=[]
  page.on('pageerror',lambda error:errors.append(str(error)))
  def respond(route):
   status,body=answer(route.request.url)
   route.fulfill(status=status,json=body)
  page.route('**/api/**',respond)
  for path in ['/contracts','/construction','/customers','/sales/quotations','/collections','/finance']:
   page.goto('http://127.0.0.1:8080/berjaya'+path)
   panel=page.locator('.insights').first
   expect(panel).to_be_visible()
   panel.locator('summary').click()
   expect(panel.locator('.chart')).to_be_visible()
   expect(panel.get_by_text('Only records already loaded',exact=False)).to_be_visible()
   panel.get_by_label('Find in loaded records').fill('NO-SUCH-RECORD-SYNTHETIC')
   expect(panel.get_by_text('No loaded records match.',exact=True)).to_be_visible()
   panel.get_by_label('Find in loaded records').fill('')
   select=panel.get_by_label('Sort preview')
   value=select.locator('option').nth(1).get_attribute('value')
   select.select_option(value)
   with page.expect_download() as info:
    panel.get_by_role('button',name='rows (CSV)',exact=False).click()
   content=Path(info.value.path()).read_text(encoding='utf-8-sig')
   assert content.startswith('"'),content
   assert page.evaluate('document.documentElement.scrollWidth <= innerWidth'),path
   assert not errors,errors
   print(f'PASS {width}px {path}: chart, search, sort, CSV, no overflow')
  page.close()
 browser.close()
