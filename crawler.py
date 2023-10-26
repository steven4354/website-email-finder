import re
import pandas as pd
from bs4 import BeautifulSoup
from urllib.parse import urljoin
from collections import deque
from fuzzywuzzy import fuzz
from selenium import webdriver

def get_text_from_html(html_content):
  for element in html_content(["script", "style"]):  # Remove these elements
      element.extract()
  text = ' '.join(html_content.stripped_strings)
  return text

def is_valid_relative_url(url):
    # A relative URL should not contain any spaces or '#'
    return ' ' not in url and '#' not in url

def crawl_website(url, driver, max_depth=10):
  print(f'Crawling {url}')
  visited_urls = set()
  queue = deque([(url, 0)])
  queue_set = set([url])  # Add a set to keep track of the URLs in the queue

  emails = []

  while queue:
    print(f'Queue length: {len(queue)}')
    print(f'Queue: {queue}')
    url, depth = queue.popleft()
    queue_set.remove(url)  # Remove the URL from the queue set

    if depth > max_depth or url in visited_urls:
        continue
    
    if len(emails) > 2 or len(visited_urls) > 20:
        break

    visited_urls.add(url)

    driver.get(url)
    page_content = BeautifulSoup(driver.page_source, 'html.parser')
    text = get_text_from_html(page_content)
    email_addresses = re.findall(r'\b[A-Za-z0-9._%+-]+@[A-Za-z0-9.-]+\.[A-Z|a-z]{2,}\b', text)

    for email in email_addresses:
        if email not in emails:
            print(f'Found email: {email}')
            emails.append(email)

    links = page_content.find_all('a')
    links.sort(key=lambda link: fuzz.ratio(link.get_text().lower(), 'contact'), reverse=True)
    for link in links:
        href = link.get('href')
        if href and not href.startswith('#') and is_valid_relative_url(href):
            # dont go to the links to facebook, twitter, linkedin
            if any(social in href for social in ['facebook', 'twitter', 'linkedin', 'tel', 'google', '.gov', 'blog', 'mailto', 'wikipedia', 'sms', 'instagram']):
                continue
            full_url = urljoin(url, href)
            # Only append full_url if the url is not already in the queue
            if full_url not in queue_set:
                queue.append((full_url, depth + 1))
                queue_set.add(full_url)  # Add the URL to the queue set

  return emails

# Read the CSV file
df = pd.read_csv('outscraper.csv')

# Create columns for the emails
df['email_1'] = None
df['email_2'] = None

driver = webdriver.Firefox()  # or webdriver.Chrome(), etc.

# Crawl each website and store the found emails
for i, row in df.iterrows():
    site = row['site']
    if pd.isna(site) or not (site.startswith('http://') or site.startswith('https://')):
        continue
    emails = crawl_website(site, driver, 2)
    for j, email in enumerate(emails):
        df.loc[i, f'email_{j+1}'] = email
    df.to_csv('outscraper.csv', index=False)  # Save after each row

driver.quit()

# Write the DataFrame back to the CSV file
df.to_csv('outscraper.csv', index=False)