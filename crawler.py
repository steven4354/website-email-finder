import re
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from fuzzywuzzy import fuzz
from selenium import webdriver

visited_urls = set()

def get_text_from_html(html_content):
  for element in html_content(["script", "style"]):  # Remove these elements
      element.extract()
  text = ' '.join(html_content.stripped_strings)
  return text

def crawl_website(start_url, max_depth=10):
  global visited_urls

  queue = deque([(start_url, 0)])

  driver = webdriver.Firefox()  # or webdriver.Chrome(), etc.

  while queue:
    url, depth = queue.popleft()

    if depth > max_depth or url in visited_urls:
        continue

    visited_urls.add(url)

    driver.get(url)
    page_content = BeautifulSoup(driver.page_source, 'html.parser')
    text = get_text_from_html(page_content)
    email_addresses = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

    print(f"Found the following email addresses on {url}:")
    for email in email_addresses:
        print(email)

    links = page_content.find_all('a')
    links.sort(key=lambda link: fuzz.ratio(link.get_text().lower(), 'contact'), reverse=True)
    for link in links:
        href = link.get('href')
        if href and not href.startswith('#') and href.startswith(('http:', 'https:')):
            full_url = urljoin(url, href)
            queue.append((full_url, depth + 1))

  driver.quit()

websites = ['https://www.prattlawcorp.com/']
for website in websites:
    crawl_website(website, 10)