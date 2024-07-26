from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import threading
import os
import time
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.orm import declarative_base, sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
import json
import logging
from logging.handlers import RotatingFileHandler
import requests_cache

# Set the base directory
base_dir = os.path.abspath(os.path.dirname(__file__))

# Configure logging
log_file = os.path.join(base_dir, 'app.log')
handler = RotatingFileHandler(log_file, maxBytes=10000, backupCount=1)
handler.setLevel(logging.WARNING)
formatter = logging.Formatter('%(asctime)s %(levelname)s: %(message)s [in %(pathname)s:%(lineno)d]')
handler.setFormatter(formatter)
logger = logging.getLogger(__name__)
logger.addHandler(handler)
logger.setLevel(logging.WARNING)

# Suppress SQLAlchemy info logs
logging.getLogger('sqlalchemy.engine').setLevel(logging.WARNING)

app = Flask(__name__, template_folder='templates')

# Enable caching for HTTP requests
requests_cache.install_cache('web_cache', expire_after=3600)

# Global variables to store user search and related data
your_search = ''
keywords = []
top_100 = []

# Set the starting URL for the crawler
Spider = "https://en.wikipedia.org/wiki/Spider"

# Set the path to the SQLite database and JSON file in the base folder
db_path = os.getenv('WEB_CRAWLER_DB_PATH', os.path.join(base_dir, 'web_crawler.db'))
json_path = os.getenv('WEB_CRAWLER_JSON_PATH', os.path.join(base_dir, 'click_data.json'))

# Setup SQLAlchemy
Base = declarative_base()
engine = create_engine(f'sqlite:///{db_path}', echo=False)
Session = scoped_session(sessionmaker(bind=engine))

# Initialize the JSON data file
if not os.path.exists(json_path):
    with open(json_path, 'w') as f:
        json.dump({}, f)

# Define ignored words and punctuation
IgnoredWords = set([
    'i', 'me', 'my', 'myself', 'we', 'our', 'ours', 'ourselves', 'you', 'your', 'yours',
    'yourself', 'yourselves', 'he', 'him', 'his', 'himself', 'she', 'her', 'hers',
    'herself', 'it', 'its', 'itself', 'they', 'them', 'their', 'theirs', 'themselves',
    'what', 'which', 'who', 'whom', 'this', 'that', 'these', 'those', 'am', 'is', 'are',
    'was', 'were', 'be', 'been', 'being', 'have', 'has', 'had', 'having', 'do', 'does',
    'did', 'doing', 'a', 'an', 'the', 'and', 'but', 'if', 'or', 'because', 'as', 'until',
    'while', 'of', 'at', 'by', 'for', 'with', 'about', 'against', 'between', 'into',
    'through', 'during', 'before', 'after', 'above', 'below', 'to', 'from', 'up', 'down',
    'in', 'out', 'on', 'off', 'over', 'under', 'again', 'further', 'then', 'once', 'here',
    'there', 'when', 'where', 'why', 'how', 'all', 'any', 'both', 'each', 'few', 'more',
    'most', 'other', 'some', 'such', 'no', 'nor', 'not', 'only', 'own', 'same', 'so',
    'than', 'too', 'very', 'can', 'will', 'just', 'should', 'now'
])

Punctuation = '.,;:!?\'"()[]{}-–—…‘’“”/\\|@#$%^&*_+=<>~'
Depnctuator = str.maketrans('', '', Punctuation)

class Page(Base):
    __tablename__ = 'pages'
    id = Column(Integer, primary_key=True)
    title = Column(String)
    url = Column(String, unique=True)
    processed = Column(String)
    keyword_1 = Column(String)
    keyword_2 = Column(String)
    keyword_3 = Column(String)
    keyword_4 = Column(String)
    keyword_5 = Column(String)
    keyword_6 = Column(String)
    keyword_7 = Column(String)
    keyword_8 = Column(String)
    keyword_9 = Column(String)
    keyword_10 = Column(String)
    keyword_11 = Column(String)
    keyword_12 = Column(String)
    keyword_13 = Column(String)
    keyword_14 = Column(String)
    keyword_15 = Column(String)
    keyword_16 = Column(String)
    keyword_17 = Column(String)
    keyword_18 = Column(String)
    keyword_19 = Column(String)
    keyword_20 = Column(String)
    keyword_21 = Column(String)
    keyword_22 = Column(String)
    keyword_23 = Column(String)
    keyword_24 = Column(String)
    keyword_25 = Column(String)
    keyword_26 = Column(String)
    keyword_27 = Column(String)
    keyword_28 = Column(String)
    keyword_29 = Column(String)
    keyword_30 = Column(String)
    clicks = Column(Integer, default=0)
    keyword_clicks = Column(String)

Base.metadata.create_all(engine)

@app.route('/', methods=['GET', 'POST'])
def index():
    global your_search

    if request.method == 'GET':
        return render_template('index.html')
    
    elif request.method == 'POST':
        your_search = request.form.get('YourSearch')
        formatted_search = your_search.replace(' ', '_')
        return redirect(url_for('search_page', search_page_url=formatted_search, page=1))

def keyword_def():
    """Extracts and processes keywords from the search input."""
    global keywords
    punctuation = '.,;:!?\'"()[]{}-–—…‘’“”/\\|@#$%^&*_+=<>~`'
    depunctuator = str.maketrans('', '', punctuation)
    depunc_search = your_search.translate(depunctuator)
    lower_search = depunc_search.lower()
    keywords = lower_search.split()

def find_top_100():
    """Finds the top 100 relevant URLs based on keywords in the database."""
    global keywords
    global top_100
    top_tally = {}

    try:
        session = Session()
        rows = session.query(Page).filter(Page.processed == 'Yes').all()

        for row in rows:
            title, url = row.title, row.url
            row_keywords = [row.keyword_1, row.keyword_2, row.keyword_3, row.keyword_4, row.keyword_5,
                            row.keyword_6, row.keyword_7, row.keyword_8, row.keyword_9, row.keyword_10,
                            row.keyword_11, row.keyword_12, row.keyword_13, row.keyword_14, row.keyword_15,
                            row.keyword_16, row.keyword_17, row.keyword_18, row.keyword_19, row.keyword_20,
                            row.keyword_21, row.keyword_22, row.keyword_23, row.keyword_24, row.keyword_25,
                            row.keyword_26, row.keyword_27, row.keyword_28, row.keyword_29, row.keyword_30]
            score = 0
            
            keyword_clicks = json.loads(row.keyword_clicks) if row.keyword_clicks else {}

            for position, word in enumerate(row_keywords):
                for keyword in keywords:
                    if word == keyword:
                        score += (len(row_keywords) - position) * 1.0
                        score += keyword_clicks.get(keyword, 0) * 10
                    elif keyword in word:
                        score += (len(row_keywords) - position) * 0.1
                        score += keyword_clicks.get(keyword, 0) * 1

            title_lower = title.lower()
            for keyword in keywords:
                if keyword in title_lower:
                    score += 10

            score += row.clicks * 5

            if score > 0:
                top_tally[(title, url)] = score

        sorted_top_tally = dict(sorted(top_tally.items(), key=lambda item: item[1], reverse=True))
        top_100 = list(sorted_top_tally.keys())[:100]
    except Exception as e:
        logger.error(f"Database error: {e}")
    finally:
        session.close()

def fetch_first_paragraph(url):
    """Fetches the first paragraph from the given URL."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            paragraphs = soup.find_all('p')
            for paragraph in paragraphs:
                text = paragraph.get_text().strip()
                if len(text) > 0:
                    return text[:140] + '...' if len(text) > 140 else text
            
            return "No meaningful paragraph found."
        else:
            return "Failed to retrieve content."
    except requests.RequestException:
        return "Failed to retrieve content."

@app.route('/Search/<search_page_url>/<int:page>')
def search_page(search_page_url, page):
    """Displays the search results page with previews."""
    keyword_def()
    find_top_100()
    results_with_previews = []
    start = (page - 1) * 20
    end = start + 20
    paginated_results = top_100[start:end]
    
    for title, url in paginated_results:
        preview = fetch_first_paragraph(url)
        results_with_previews.append((title, url, preview))
    
    total_pages = (len(top_100) + 19) // 20
    
    return render_template('results.html', results=results_with_previews, page=page, total_pages=total_pages, search_page_url=search_page_url)

def update_json_file(url, keyword):
    with open(json_path, 'r+') as f:
        click_data = json.load(f)
        if url not in click_data:
            click_data[url] = {}
        if keyword in click_data[url]:
            click_data[url][keyword] += 1
        else:
            click_data[url][keyword] = 1
        f.seek(0)
        json.dump(click_data, f)
        f.truncate()

@app.route('/click/<int:page_id>/<keyword>')
def record_click(page_id, keyword):
    try:
        session = Session()
        page = session.query(Page).filter_by(id=page_id).first()
        if page:
            page.clicks += 1
            
            keyword_clicks = json.loads(page.keyword_clicks) if page.keyword_clicks else {}
            keyword_clicks[keyword] = keyword_clicks.get(keyword, 0) + 1
            page.keyword_clicks = json.dumps(keyword_clicks)
            session.commit()
            
            update_json_file(page.url, keyword)
        return redirect(request.referrer)
    except Exception as e:
        logger.error(f"Database error: {e}")
    finally:
        session.close()

def initialize_database():
    """Initialize the SQLite database and tables if not already present."""
    Base.metadata.create_all(engine)

def PatientZero(Spider):
    """Initialize the database with the starting URL if not already present."""
    session = Session()
    try:
        if not session.query(Page).filter_by(url=Spider).first():
            patient_zero = Page(title="", url=Spider, processed="No")
            session.add(patient_zero)
            session.commit()
    except Exception as e:
        logger.error(f"Error initializing PatientZero: {e}")
        session.rollback()
    finally:
        session.close()

def ExtractURLInfo(Url):
    """Extract title, text, and URLs from a given page."""
    try:
        UrlRequest = requests.get(Url)
        UrlRequest.raise_for_status()
    except requests.RequestException as e:
        logger.error(f"Request failed: {e}")
        return None, None, []

    Autopsy = BeautifulSoup(UrlRequest.content, 'html.parser')
    Title = Autopsy.title.string.strip() if Autopsy.title else 'No Title'
    MessyText = Autopsy.find_all('p')
    Text = '\n'.join(p.get_text() for p in MessyText)
    ExtractedURLs = [a['href'] for a in Autopsy.find_all('a', href=True)]
    return Title, Text, ExtractedURLs

def FindKeywords(Text):
    """Identify the top 30 keywords from the text."""
    Tally = {}
    Keywords = []

    for word in Text.split():
        word = word.lower()
        word_without_punctuation = word.translate(Depnctuator)
        if word_without_punctuation not in IgnoredWords:
            Tally[word_without_punctuation] = Tally.get(word_without_punctuation, 0) + 1

    for _ in range(30):
        if not Tally:
            break
        keyword = max(Tally, key=Tally.get)
        Keywords.append(keyword)
        Tally.pop(keyword)

    while len(Keywords) < 30:
        Keywords.append('')

    return Keywords

def clean_url(url):
    return url.strip().strip('"').strip("'")

def FindURLs(ExtractedURLs, base_url):
    """Format extracted URLs to be complete links."""
    FullURLs = []
    for url in ExtractedURLs:
        url = clean_url(url)
        if url.startswith('/'):
            full_url = base_url.rstrip('/') + url  # Remove trailing slash from base_url
        elif url.startswith('http'):
            full_url = url
        else:
            full_url = base_url.rstrip('/') + '/' + url  # Remove trailing slash from base_url
        FullURLs.append(full_url)
    return FullURLs

def PassDataToDatabase(Title, Url, Keywords, FullURLs):
    """Add extracted data to the database and mark the URL as processed."""
    try:
        session = Session()

        with session.no_autoflush:
            page = session.query(Page).filter_by(url=Url).first()
            if page:
                page.title = Title
                page.processed = "Yes"
                page.keyword_1, page.keyword_2, page.keyword_3, page.keyword_4, page.keyword_5 = Keywords[:5]
                page.keyword_6, page.keyword_7, page.keyword_8, page.keyword_9, page.keyword_10 = Keywords[5:10]
                page.keyword_11, page.keyword_12, page.keyword_13, page.keyword_14, page.keyword_15 = Keywords[10:15]
                page.keyword_16, page.keyword_17, page.keyword_18, page.keyword_19, page.keyword_20 = Keywords[15:20]
                page.keyword_21, page.keyword_22, page.keyword_23, page.keyword_24, page.keyword_25 = Keywords[20:25]
                page.keyword_26, page.keyword_27, page.keyword_28, page.keyword_29, page.keyword_30 = Keywords[25:30]
                session.commit()
                # logger.info(f"Updated page: {Url}")  # Commented out to reduce terminal spam
            
            for full_url in FullURLs:
                if not session.query(Page).filter_by(url=full_url).first():
                    new_page = Page(url=full_url, processed="No")
                    session.add(new_page)
                    try:
                        session.commit()
                        # logger.info(f"Inserted new URL: {full_url}")  # Commented out to reduce terminal spam
                    except IntegrityError:
                        session.rollback()
                        # logger.info(f"Duplicate URL found and ignored: {full_url}")  # Commented out to reduce terminal spam

    except Exception as e:
        logger.error(f"Database error: {e}")
        session.rollback()
    finally:
        session.close()

def NewURL():
    """Process new URLs from the database sequentially and extract their information."""
    try:
        session = Session()

        while True:
            page = session.query(Page).filter_by(processed='No').first()
            if not page:
                break

            Url = clean_url(page.url)
            Title, Text, ExtractedURLs = ExtractURLInfo(Url)
            if Title is None:
                page.processed = 'Error'
                session.commit()
                continue

            base_url = "/".join(Url.split("/")[:3])
            FullURLs = FindURLs(ExtractedURLs, base_url)
            Keywords = FindKeywords(Text)
            PassDataToDatabase(Title, Url, Keywords, FullURLs)

        session.close()
    except Exception as e:
        logger.error(f"Database error: {e}")

def start_crawling():
    """Start the web crawling process."""
    initialize_database()
    PatientZero(Spider)
    while True:
        if get_combined_size() < 20 * 1024 * 1024 * 1024:
            NewURL()
            time.sleep(1)
        else:
            logger.info("Combined size limit reached. Pausing for 5 days.")
            time.sleep(5 * 24 * 3600)
            clean_database()
            repopulate_database()
            logger.info("Resuming crawling after cleaning and repopulating the database.")

def get_combined_size():
    """Returns the combined size of the database and JSON data in bytes."""
    db_size = os.path.getsize(db_path)
    json_size = os.path.getsize(json_path)
    return db_size + json_size

def check_url_availability(url):
    """Check if a URL is still available."""
    try:
        response = requests.get(url, timeout=10)
        return response.status_code == 200
    except requests.RequestException:
        return False

def clean_database():
    """Clean the database by removing unavailable and least-used URLs."""
    try:
        session = Session()

        pages = session.query(Page).all()
        for page in pages:
            if not check_url_availability(page.url):
                session.delete(page)
                session.commit()
                remove_from_json(page.url)
                logger.info(f"Deleted unavailable URL: {page.url}")

        total_pages = session.query(Page).count()
        least_used_count = total_pages // 5
        least_used_pages = session.query(Page).order_by(Page.clicks).limit(least_used_count).all()
        for page in least_used_pages:
            session.delete(page)
            session.commit()
            remove_from_json(page.url)
            logger.info(f"Deleted least-used URL: {page.url}")

    except Exception as e:
        logger.error(f"Database error: {e}")
    finally:
        session.close()

def remove_from_json(url):
    """Remove a URL from the JSON data."""
    with open(json_path, 'r+') as f:
        click_data = json.load(f)
        if url in click_data:
            del click_data[url]
        f.seek(0)
        json.dump(click_data, f)
        f.truncate()

def repopulate_database():
    """Repopulate the database by crawling the most-used sites for new links."""
    try:
        session = Session()

        most_used_pages = session.query(Page).order_by(Page.clicks.desc()).limit(100).all()
        for page in most_used_pages:
            Url = clean_url(page.url)
            Title, Text, ExtractedURLs = ExtractURLInfo(Url)
            if Title is None:
                continue

            base_url = "/".join(Url.split("/")[:3])
            FullURLs = FindURLs(ExtractedURLs, base_url)
            Keywords = FindKeywords(Text)
            PassDataToDatabase(Title, Url, Keywords, FullURLs)

    except Exception as e:
        logger.error(f"Database error: {e}")
    finally:
        session.close()

if __name__ == '__main__':
    threading.Thread(target=start_crawling).start()
    app.run(host='0.0.0.0', port=5000, debug=True)
