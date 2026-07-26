from flask import Flask, render_template, request
from scraper import scrape_and_save 

app = Flask(__name__)


@app.route("/")
def index():
    return render_template("index.html", articles=None)


@app.route("/scrape", methods=["POST"])
def scrape():
    target_url = request.form.get("url")
    raw_keywords = request.form.get("keywords", "")

    keywords_list = [k.strip() for k in raw_keywords.split(",") if k.strip()]

    found_articles = scrape_and_save(target_url, keywords_list)

    return render_template(
        "index.html",
        articles=found_articles,
        target_url=target_url,
        raw_keywords=raw_keywords,
    )

if __name__ == "__main__":
    app.run(debug=True, port=5000)