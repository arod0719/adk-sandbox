#!/usr/bin/env python3
"""
Deterministic news fetcher and article scraper for Rocket League.
Interacts with the RLStats news API and rocketleague.com articles.
"""

import os
import sys
import json
import argparse
from pathlib import Path
import requests
from bs4 import BeautifulSoup
from dotenv import load_dotenv

# Load environment variables safely
for env_path in [
    Path("/home/raspberrypi4/ADK/.env"),
    Path("/home/raspberrypi4/ADK/rocket_league/.env"),
    Path.cwd() / ".env"
]:
    if env_path.exists():
        load_dotenv(env_path)

API_KEY = os.getenv("RLSTATS_API_KEY")

def fetch_latest_news(count: int = 5, offset: int = 0) -> str:
    url = f"https://api.rlstats.net/v1/news?apikey={API_KEY}"
    try:
        response = requests.get(url, timeout=10)
        response.raise_for_status()

        text = response.text.strip()
        if text.startswith("Access Denied!"):
            text = text[len("Access Denied!"):].strip()

        articles = json.loads(text)
        if not articles:
            return "No news articles found."

        articles_slice = articles[offset : offset + count]
        if not articles_slice:
            return "No older articles found matching this query offset."

        result = [f"Here are Rocket League news articles (showing {len(articles_slice)} articles):"]
        for i, art in enumerate(articles_slice, 1):
            title = art.get("Title", "No Title").strip()
            desc = art.get("Description", "").strip()
            post_date = art.get("PostedAt", "Unknown Date")
            link = art.get("Link", "").replace("\\/", "/")
            image = art.get("Image", "").replace("\\/", "/")

            item = f"{i}. **{title}** ({post_date})\n   {desc}\n   [Read Full Article]({link})"
            if image:
                item += f'\n   <img src="{image}" alt="{title}" width="240" height="135" style="max-width: 240px; max-height: 135px; object-fit: cover; border-radius: 6px; margin-top: 5px; display: block;" />'
            result.append(item)

        return "\n\n".join(result)
    except Exception as e:
        return f"Error fetching news from API: {e}."

def get_news_article_details(url: str) -> str:
    url = url.replace("\\/", "/")
    if not url.startswith("http"):
        url = f"https://www.rocketleague.com{url}"

    try:
        from curl_cffi import requests as curl_requests
        response = curl_requests.get(url, impersonate="chrome120", timeout=12)
        response.raise_for_status()

        soup = BeautifulSoup(response.text, "html.parser")
        article = soup.find("article") or soup.find("div", class_="_1eu3eal0") or soup.find("div", id="page-content")
        if not article:
            article = soup.find(class_="_1eu3eal0") or soup.find(class_="_1va58ya0") or soup

        elements = article.find_all(["p", "li", "h1", "h2", "h3", "h4"])
        text_blocks = [el.get_text(strip=True) for el in elements if el.get_text(strip=True)]

        if not text_blocks:
            return "Could not parse text content from this article. Please check the page directly."

        return "\n\n".join(text_blocks[:30])

    except Exception as e:
        return f"Error loading article details: {e}."

def main():
    parser = argparse.ArgumentParser(description="Fetch Rocket League News and Article Content")
    parser.add_argument("--action", choices=["list", "details"], default="list", help="Action")
    parser.add_argument("--count", type=int, default=5, help="Number of articles to list")
    parser.add_argument("--offset", type=int, default=0, help="Offset for pagination")
    parser.add_argument("--url", help="URL of article to scrape details for")
    args = parser.parse_args()

    if args.action == "list":
        print(fetch_latest_news(count=args.count, offset=args.offset))
    elif args.action == "details":
        if not args.url:
            print("Error: --url is required for action 'details'.", file=sys.stderr)
            sys.exit(1)
        print(get_news_article_details(args.url))

if __name__ == "__main__":
    main()
