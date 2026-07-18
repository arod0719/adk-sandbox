from curl_cffi import requests
from bs4 import BeautifulSoup

def fetch_latest_news():
    """
    Fetches the latest news titles, dates, and links from the official Rocket League news website.
    Uses curl_cffi to bypass Cloudflare bot protection.
    """
    url = "https://www.rocketleague.com/news"
    
    try:
        response = requests.get(url, impersonate="chrome", timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        articles = []
        
        for a in soup.find_all('a', href=True):
            href = a['href']
            if '/news/' in href and not href.startswith('/news/tag/') and href != '/news/':
                parent = a.parent
                heading = parent.find(['h1', 'h2', 'h3', 'h4', 'h5', 'h6'])
                date_span = parent.find('span')
                
                title = heading.get_text(strip=True) if heading else a.get_text(strip=True)
                date = date_span.get_text(strip=True) if date_span else 'Unknown Date'
                
                # Deduplicate "Read More" text if heading was resolved
                if title.lower() == 'read more' and heading:
                    title = heading.get_text(strip=True)
                    
                full_url = href if href.startswith('http') else f"https://www.rocketleague.com{href}"
                
                # Check for duplicates
                if (title, full_url) not in [(art['title'], art['url']) for art in articles]:
                    articles.append({'title': title, 'url': full_url, 'date': date})
                    
        if not articles:
            return "Could not extract specific news articles. The site structure may have changed. Please visit https://www.rocketleague.com/news directly."
            
        result = ["Here are the latest news articles from Rocket League:"]
        for i, art in enumerate(articles[:10], 1):
            result.append(f"{i}. {art['title']} ({art['date']})\n   Link: {art['url']}")
            
        return "\n".join(result)
        
    except Exception as e:
        return f"Error fetching news: {e}. Please visit https://www.rocketleague.com/news directly."

def get_news_article_details(url: str):
    """
    Fetches the main text content of a specific Rocket League news article webpage.
    """
    if not url.startswith('http'):
        url = f"https://www.rocketleague.com{url}"
        
    try:
        response = requests.get(url, impersonate="chrome", timeout=10)
        response.raise_for_status()
        
        soup = BeautifulSoup(response.text, 'html.parser')
        
        # Try to locate the main text container
        article = soup.find('article') or soup.find('div', class_='_1eu3eal0') or soup.find('div', id='page-content')
        if not article:
            # Fallback to general content container elements
            article = soup.find(class_='_1eu3eal0') or soup.find(class_='_1va58ya0') or soup
            
        # Extract paragraph and header texts
        elements = article.find_all(['p', 'li', 'h1', 'h2', 'h3', 'h4'])
        text_blocks = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]
        
        if not text_blocks:
            return "Could not parse text content from this article. Please check the page directly."
            
        return "\n\n".join(text_blocks[:30]) # Limit length to keep token count reasonable
        
    except Exception as e:
        return f"Error loading article details: {e}."
