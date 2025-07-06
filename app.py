import requests
from bs4 import BeautifulSoup
import nltk
import re
from nltk.tokenize import word_tokenize
from nltk.corpus import stopwords
nltk.download('punkt')
nltk.download('stopwords')
nltk.download('punkt_tab')
from selenium import webdriver
from selenium.webdriver.common.by import By
from selenium.webdriver.chrome.options import Options
import time
from google import genai
from google.genai import types
from flask import Flask, render_template, request

# def setup_driver():
#     options = Options()
#     options.add_argument("--headless")
#     options.add_argument("--disable-gpu")
#     options.add_argument('--no-sandbox')
#     driver = webdriver.Chrome(options=options)
#     return driver
from selenium import webdriver
from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options

from selenium.webdriver.chrome.service import Service
from selenium.webdriver.chrome.options import Options
from selenium import webdriver

def setup_driver():
    options = Options()
    options.binary_location = "/usr/bin/google-chrome"
    options.add_argument("--headless=new")
    options.add_argument("--no-sandbox")
    options.add_argument("--disable-dev-shm-usage")
    options.add_argument("--disable-gpu")
    options.add_argument("--disable-software-rasterizer")
    options.add_argument("--remote-debugging-port=9222")

    service = Service("/usr/local/bin/chromedriver")
    driver = webdriver.Chrome(service=service, options=options)
    return driver


def scrape_website_info(url):
    driver = setup_driver()
    driver.get(url)
    time.sleep(3)

    soup = BeautifulSoup(driver.page_source, 'html.parser')


    title = soup.title.string.strip() if soup.title else ""


    meta_desc = ""
    meta_tag = soup.find('meta', attrs={'name': 'description'})
    if meta_tag and 'content' in meta_tag.attrs:
        meta_desc = meta_tag['content'].strip()


    h1_tags = [h1.get_text(strip=True) for h1 in soup.find_all('h1')]


    links = [a['href'] for a in soup.find_all('a', href=True) if 'about' in a['href'].lower()]
    about_content = ""
    if links:
        about_url = links[0]
        if about_url.startswith('/'):
            base_url = re.match(r'^https?://[^/]+', url).group(0)
            about_url = base_url + about_url
        driver.get(about_url)
        time.sleep(2)
        about_soup = BeautifulSoup(driver.page_source, 'html.parser')
        paragraphs = about_soup.find_all('p')
        about_content = ' '.join(p.get_text() for p in paragraphs)
        about_content = about_content.strip()[:3000]

    homepage_paragraphs = soup.find_all('p')
    homepage_text = ' '.join(p.get_text() for p in homepage_paragraphs)
    homepage_text = homepage_text.strip()[:3000]

    driver.quit()

    return {
        'title': title,
        'meta_description': meta_desc,
        'h1_tags': h1_tags,
        'about_content': about_content,
        'homepage_text': homepage_text
    }

def get_main_keywords(text, limit=8):
    text = re.sub(r'[^\w\s]', '', text.lower())
    tokens = word_tokenize(text)
    stop_words = set(stopwords.words('english'))
    words = [word for word in tokens if word.isalpha() and word not in stop_words and len(word) > 2]

    relevant_words = [
        'marketing', 'growth', 'strategy', 'brand', 'experience', 'customers',
        'clients', 'design', 'technology', 'innovation', 'solutions', 'services',
        'campaigns', 'team', 'creative', 'performance', 'development', 'results',
        'insights', 'business', 'products', 'reach', 'digital', 'engagement'
    ]

    filtered = [word for word in words if word in relevant_words]
    frequency = {}
    for word in filtered:
        frequency[word] = frequency.get(word, 0) + 1

    sorted_keywords = sorted(frequency.items(), key=lambda x: x[1], reverse=True)
    return [kw[0] for kw in sorted_keywords[:limit]]

# def write_brand_summary(url, keywords, site_info):
#     if not keywords:
#         return (
#             f"{site_info['title'] if site_info['title'] else url} is a digital agency helping businesses grow through strategic marketing and performance-driven solutions. "
#             f"The team focuses on delivering measurable results through creativity and execution."
#         )

#     key_areas = keywords[:3]
#     support_areas = keywords[3:5] if len(keywords) > 4 else keywords[:2]

#     return (
#         f"{site_info['title'] if site_info['title'] else url} is a results-driven digital agency specializing in {key_areas[0]}, {key_areas[1]}, and {key_areas[2]}. "
#         f"With a strong foundation in {support_areas[0]} and {support_areas[1] if len(support_areas) > 1 else key_areas[0]}, "
#         f"the agency delivers tailored solutions that align with real business goals."
#     )

def write_brand_summary(url, keywords, site_info):
    title = site_info['title'] if site_info['title'] else url

    if not keywords:
        return (
            f"{title} is a digital agency helping businesses grow through strategic marketing and performance-driven solutions. "
            f"The team focuses on delivering measurable results through creativity and execution."
        )

    key_areas = keywords[:3]
    support_areas = keywords[3:5] if len(keywords) > 4 else keywords[:2]

    key_text = ", ".join(key_areas)
    support_text = " and ".join(support_areas) if len(support_areas) > 1 else support_areas[0] if support_areas else "various areas"

    return (
        f"{title} is a results-driven digital agency specializing in {key_text}. "
        f"With a strong foundation in {support_text}, "
        f"the agency delivers tailored solutions that align with real business goals."
    )


app = Flask(__name__)
@app.route('/')
def index():
    return render_template('index2.html')

@app.route('/predict', methods = ['POST'])
def recomend_crop():
    url = request.form.get('url')
    API = request.form.get('API')
    websites = []
    websites.append(url)
    for site in websites:
        site_info = scrape_website_info(site)
        combined_text = site_info['about_content'] + " " + site_info['homepage_text']

        if len(combined_text) < 200:
            print(f"Skipped {site} due to low content quality.")
            continue

        keywords = get_main_keywords(combined_text)
        summary = write_brand_summary(site, keywords, site_info)

    prompt = list(summary)
    client = genai.Client(api_key = API)
    response = client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = prompt,
        config = types.GenerateContentConfig(
            max_output_tokens = 1000,
            temperature = 0.1,
            system_instruction = "generate complete latex code to create ppt to pitch to the company. The code should be short and complete. give only code and nothing else."
        )
    )
    response2 = client.models.generate_content(
        model = "gemini-2.0-flash",
        contents = response.text,
        config = types.GenerateContentConfig(
            max_output_tokens = 1000,
            temperature = 0.1,
            system_instruction = "debug the code. give only code and nothing else."
        )
    )

    result = str(response2.text).replace("```latex", "")
    result2 = result[:-3]
    file = open("pitch.tex", "w")
    file.write(result2)
    file.close()
    import os
    os.system("pdflatex pitch.tex")
    import shutil
    shutil.move("pitch.pdf", "static/pitch.pdf")
    return '', 200
import shutil
from flask import send_from_directory

@app.route('/download')
def download_pdf():
    return send_from_directory('static', 'pitch.pdf', as_attachment=True)

import os
if __name__ == '__main__':
    port = int(os.environ.get('PORT', 5000))  
    app.run(host='0.0.0.0', port=port) 
