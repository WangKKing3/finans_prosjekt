from concurrent.futures import ThreadPoolExecutor
import datetime
from urllib.parse import urljoin
from bs4 import BeautifulSoup
from models import ArticleModel, Session
import requests
import ollama

def extract_article_text(url):
    """
    Besøker artikkelen og henter ut teksten fra avsnittene (<p>).
    """
    try:
        headers = {
            "User-Agent": (
                "Mozilla/5.0 (Windows NT 10.0; Win64; x64) "
                "AppleWebKit/537.36 (KHTML, like Gecko) "
                "Chrome/120.0.0.0 Safari/537.36"
            )
        }
        resp = requests.get(url, headers=headers, timeout=4)
        if resp.status_code != 200:
            return ""

        soup = BeautifulSoup(resp.content, "html.parser")
        
        # Samler alle paragrafer (<p>) som har litt lengde (hopper over meny/footer-lenker)
        paragraphs = [p.get_text(strip=True) for p in soup.find_all("p") if len(p.get_text(strip=True)) > 30]
        
        # Tar de første 5-8 avsnittene for å unngå at konteksten blir for stor for Ollama
        full_text = " ".join(paragraphs[:8])
        return full_text
    except Exception as e:
        print(f"Kunne ikke hente brødtekst fra {url}: {e}")
        return ""

def analyze_with_ollama(title, text_content=""):
    context = text_content if len(text_content) > 100 else f"Overskrift: {title}"
    prompt = f"""You are an expert in finance and the stock market.
    Analyze this news article/text:

    "{context}"

    Provide your answer in exactly this format (without any other introduction):
    PREDICTION: [Choose either "Positive (Bullish)", "Neutral", or "Negative (Bearish)"]
    SUMMARY: [Write a concise summary of 2–10 sentences in Norwegian covering the key points and the implications for the stock/market]
    """

    try: 
        response = ollama.generate(
            model='gemma4:12b', 
            prompt=prompt
        )
        text = response['response'].strip()

        prediction = "Nøytral"
        summary = text

        for line in text.split("\n"):
            if line.startswith("PREDIKSJON:"):
                prediction = line.replace("PREDIKSJON:", "").strip()
            elif line.startswith("SAMMENDRAG:"):
                summary = line.replace("SAMMENDRAG:", "").strip()

        return summary, prediction

    except Exception as e:
        print(f"Ollama-feil: {e}")
        return "Kunne ikke analysere med AI for øyeblikket.", "Nøytral"


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

                existing = (
                    session.query(ArticleModel)
                    .filter_by(url=article_url)
                    .first()
                )

                has_ai = existing and existing.AI_generated_summary and "Treff på søkeord" not in existing.AI_generated_summary

                if not existing or not has_ai:

                    article_body = extract_article_text(article_url)
                  
                    ai_summary, ai_prediction = analyze_with_ollama(article_title, article_body)

                    if not existing:
                        article = ArticleModel(
                            title=article_title,
                            url=article_url,
                            content=article_body,
                            published_date=now_str,
                            source=target_url,
                            AI_generated_summary=ai_summary,
                            predicted_impact=ai_prediction,
                        )
                        session.add(article)
                    else:
                        existing.content = article_body
                        existing.AI_generated_summary = ai_summary
                        existing.predicted_impact = ai_prediction
                    session.commit()
                    summary_to_show = ai_summary
                    prediction_to_show = ai_prediction
                else:
                    summary_to_show = existing.AI_generated_summary
                    prediction_to_show = existing.predicted_impact

                scraped_articles.append(
                    {
                        "title": article_title,
                        "link": article_url,
                        "summary": summary_to_show,
                        "prediction": prediction_to_show,
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
        url_list = [u.strip() for u in urls_input.split(",") if u.strip()]
    else:
        url_list = urls_input

    all_articles = []

    with ThreadPoolExecutor(max_workers=max_threads) as executor:
        # Start en tråd per URL
        futures = [
            executor.submit(_scrape_single_url, url, keywords_list)
            for url in url_list
        ]

        for future in futures:
            try:
                results = future.result()
                all_articles.extend(results)
            except Exception as e:
                print(f"Tråd-feil: {e}")

    return all_articles