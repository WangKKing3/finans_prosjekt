from concurrent.futures import ThreadPoolExecutor
import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from models import ArticleModel, Session
import requests

def _scrape_single_url(target_url, keywords_list):
    session = Session()
    scraped_articles = []

    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        response = requests.get(target_url, headers=headers, timeout=5)
        soup = BeautifulSoup(response.content, "html.parser")

        for a_tag in soup.find_all("a", href=True):
            article_url = urljoin(target_url, a_tag["href"])
            article_title = a_tag.get_text(strip=True)

            if len(article_title) < 10:
                continue

            if any(
                kw.lower() in article_title.lower() for kw in keywords_list
            ):
                now_str = datetime.datetime.now().strftime("%Y-%m-%d %H:%M")

                # Sjekk om saken finnes i databasen fra før
                existing = (
                    session.query(ArticleModel)
                    .filter_by(url=article_url)
                    .first()
                )

                if not existing:
                    article = ArticleModel(
                        title=article_title,
                        url=article_url,
                        content=None,
                        published_date=now_str,
                        source=target_url,
                    )
                    session.add(article)
                    session.commit()

                scraped_articles.append(
                {
                    "title": article_title,
                    "link": article_url,
                    "summary": (
                        existing.AI_generated_summary
                        if (existing and existing.AI_generated_summary)
                        else f"Treff på søkeord fra {target_url}."
                    ),
                    "prediction": (
                        getattr(existing, "predicted_impact", None)
                        if existing
                        else None
                    ),
                    "pub_date": now_str,
                    "scraped_at": now_str,
                }
            )

    except Exception as e:
        print(f"Feil under skraping av {target_url}: {e}")
        session.rollback()
    finally:
        session.close()

    return scraped_articles

def scrape_and_save(urls_input, keywords_list, max_threads=5):
   
    if isinstance(urls_input, str):
        # Støtter at brukeren skriver flere URL-er separert med komma
        url_list = [u.strip() for u in urls_input.split(",") if u.strip()]
    else:
        url_list = urls_input

    all_articles = []

    # Bruk ThreadPoolExecutor for å kjøre skrapingen i parallell
    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Start en tråd per URL
        futures = [
            executor.submit(_scrape_single_url, url, keywords_list)
            for url in url_list
        ]

        # Samle opp resultatene
        for future in futures:
            try:
                results = future.result()
                all_articles.extend(results)
            except Exception as e:
                print(f"Tråd-feil: {e}")

    return all_articles