import os
import datetime
from playwright.sync_api import sync_playwright
from feedgen.feed import FeedGenerator

# --- CONFIGURATION ---
# Change this to the username of the profile you want to scrape!
# Example: https://www.linkedin.com/in/satyanadella/ -> TARGET_USER = 'satyanadella'
TARGET_USER = 'satyanadella' 
COOKIE = os.environ.get('LI_AT_COOKIE')

def scrape_linkedin():
    print(f"Scraping posts for {TARGET_USER}...")
    
    with sync_playwright() as p:
        # Launch browser
        browser = p.chromium.launch(headless=True)
        context = browser.new_context()
        
        # Inject the login cookie
        context.add_cookies([{
            'name': 'li_at', 
            'value': COOKIE, 
            'domain': '.www.linkedin.com', 
            'path': '/'
        }])
        
        page = context.new_page()
        page.goto(f'https://www.linkedin.com/in/{TARGET_USER}/recent-activity/all/')
        
        # Wait for the feed to load
        try:
            page.wait_for_selector('.feed-shared-update-v2', timeout=15000)
        except Exception as e:
            print("Could not find posts. LinkedIn might have blocked the IP or changed selectors.")
            browser.close()
            return []

        # Scrape the first 5 posts
        posts_elements = page.query_selector_all('.feed-shared-update-v2')[:5]
        scraped_data = []

        for post in posts_elements:
            try:
                # Extract text
                text_element = post.query_selector('.break-words')
                text = text_element.inner_text() if text_element else "No text content"
                
                # Extract link (if available, otherwise link to the user's feed)
                link_element = post.query_selector('a.app-aware-link')
                link = link_element.get_attribute('href') if link_element else f'https://www.linkedin.com/in/{TARGET_USER}/recent-activity/all/'
                
                scraped_data.append({'text': text, 'link': link})
            except Exception as e:
                continue

        browser.close()
        return scraped_data

def generate_rss(posts):
    fg = FeedGenerator()
    fg.title(f'LinkedIn Feed: {TARGET_USER}')
    fg.link(href=f'https://www.linkedin.com/in/{TARGET_USER}/recent-activity/all/', rel='alternate')
    fg.description(f'Recent LinkedIn posts from {TARGET_USER}')
    fg.language('en')

    for post in posts:
        fe = fg.add_entry()
        fe.title(post['text'][:50] + "...") # Title is first 50 chars
        fe.link(href=post['link'])
        fe.description(post['text'])
        # Set publish date to right now (since LinkedIn doesn't easily expose exact timestamps in standard HTML)
        fe.pubDate(datetime.datetime.now(datetime.timezone.utc)) 

    # Save to file
    fg.rss_file('feed.xml')
    print("feed.xml generated successfully!")

if __name__ == "__main__":
    data = scrape_linkedin()
    if data:
        generate_rss(data)
    else:
        print("No data scraped.")
