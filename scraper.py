import os
import datetime
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

TARGET_USER = 'mahmouddesouky1'
LI_AT_COOKIE = os.environ.get('LI_AT_COOKIE')

def run_scraper():
    print("Launching browser...")
    with sync_playwright() as p:
        browser = p.chromium.launch(headless=True)
        context = browser.new_context(user_agent="Mozilla/5.0 (Windows NT 10.0; Win64; x64) AppleWebKit/537.36 (KHTML, like Gecko) Chrome/119.0.0.0 Safari/537.36")
        context.add_cookies([{'name': 'li_at', 'value': LI_AT_COOKIE, 'domain': '.www.linkedin.com', 'path': '/'}])
        
        page = context.new_page()
        url = f'https://www.linkedin.com/in/{TARGET_USER}/recent-activity/all/'
        page.goto(url)
        
        # Wait for the page to settle
        page.wait_for_timeout(5000) 
        
        # Take a screenshot to see what LinkedIn is actually seeing
        page.screenshot(path='debug.png')
        
        # Try to find posts by a more generic selector
        # We look for the "feed-shared-update-v2" container
        posts = page.query_selector_all('div.feed-shared-update-v2')
        print(f"Found {len(posts)} potential post containers.")
        
        results = []
        for post in posts[:5]:
            text = post.inner_text()[:200] # Get first 200 chars
            results.append({'text': text, 'link': f'https://www.linkedin.com/in/{TARGET_USER}/'})
            
        browser.close()
        return results

if __name__ == '__main__':
    posts = run_scraper()
    if posts:
        fg = FeedGenerator()
        fg.title(f'LinkedIn Feed for {TARGET_USER}')
        fg.link(href=f'https://www.linkedin.com/in/{TARGET_USER}/', rel='alternate')
        fg.description('LinkedIn RSS')
        for p in posts:
            fe = fg.add_entry()
            fe.title("New post found")
            fe.description(p['text'])
            fe.pubDate(datetime.datetime.now(datetime.timezone.utc))
        fg.rss_file('feed.xml')
        print("feed.xml created!")
    else:
        print("Scrape failed: No posts found.")
