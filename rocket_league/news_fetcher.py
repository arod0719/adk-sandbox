import os
import requests
from dotenv import load_dotenv
from bs4 import BeautifulSoup

# Load env variables
load_dotenv('/home/raspberrypi4/ADK/rocket_league/.env')
API_KEY = os.getenv('RLSTATS_API_KEY')

def fetch_latest_news(count: int = 5, offset: int = 0):
    """
    Fetches the latest news articles from the RLStats API with support for limit count and offset paging.
    Embeds cover images inline.
    """
    url = f"https://api.rlstats.net/v1/news?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()
        
        text = response.text.strip()
        if text.startswith("Access Denied!"):
            text = text[len("Access Denied!"):].strip()
            
        import json
        articles = json.loads(text)
        
        if not articles:
            return "No news articles found."
            
        articles_slice = articles[offset : offset + count]
        if not articles_slice:
            return "No older articles found matching this query offset."

        result = [f"Here are Rocket League news articles (showing {len(articles_slice)} articles):"]
        for i, art in enumerate(articles_slice, 1):
            title = art.get('Title', 'No Title').strip()
            desc = art.get('Description', '').strip()
            post_date = art.get('PostedAt', 'Unknown Date')
            link = art.get('Link', '').replace('\\/', '/')
            image = art.get('Image', '').replace('\\/', '/')
            
            item = f"{i}. **{title}** ({post_date})\n   {desc}\n   [Read Full Article]({link})"
            if image:
                item += f'\n   <img src="{image}" alt="{title}" width="240" height="135" style="max-width: 240px; max-height: 135px; object-fit: cover; border-radius: 6px; margin-top: 5px; display: block;" />'
            result.append(item)
            
        return "\n\n".join(result)
    except Exception as e:
        return f"Error fetching news from API: {e}."

def get_news_article_details(url: str):
    """
    Fetches the main text content of a specific Rocket League news article webpage.
    """
    url = url.replace('\\/', '/')
    if not url.startswith('http'):
        url = f"https://www.rocketleague.com{url}"
        
    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.get(url, impersonate="chrome", timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        article = soup.find('article') or soup.find('div', class_='_1eu3eal0') or soup.find('div', id='page-content')
        if not article:
            article = soup.find(class_='_1eu3eal0') or soup.find(class_='_1va58ya0') or soup
            
        elements = article.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4'])
        text_blocks = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
        
        if not text_blocks:
            return "Could not parse text content from this article. Please check the page directly."
            
        return "\n\n".join(text_blocks[:30])
        
    except Exception as e:
        return f"Error loading article details: {e}."
