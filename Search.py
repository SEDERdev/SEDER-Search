from flask import Flask, render_template, request, redirect, url_for
import requests
from bs4 import BeautifulSoup
import threading
import os
import time
from sqlalchemy import create_engine, Column, Integer, String
from sqlalchemy.ext.declarative import declarative_base
from sqlalchemy.orm import sessionmaker, scoped_session
from sqlalchemy.exc import IntegrityError
from sqlalchemy import inspect

app = Flask(__name__, template_folder='templates')

# Global variables to store user search and related data
your_search = ''
keywords = []
top_100 = []

# Set the starting URL for the crawler
Spider = "https://en.wikipedia.org/wiki/Spider"

# Set the path to the SQLite database in the base folder
base_dir = os.path.abspath(os.path.dirname(__file__))
db_path = os.path.join(base_dir, 'web_crawler.db')

# Setup SQLAlchemy
Base = declarative_base()
engine = create_engine(f'sqlite:///{db_path}', echo=True)  # Enable SQLAlchemy logging
Session = scoped_session(sessionmaker(bind=engine))

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

def initialize_database():
    """Initialize the SQLite database and tables if not already present."""
    inspector = inspect(engine)
    if not inspector.has_table(Page.__tablename__):
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
    top_results = []
    top_tally = {}

    try:
        session = Session()
        rows = session.query(Page).filter_by(processed='Yes').all()

        for row in rows:
            title, url = row.title, row.url
            row_keywords = [row.keyword_1, row.keyword_2, row.keyword_3, row.keyword_4, row.keyword_5,
                            row.keyword_6, row.keyword_7, row.keyword_8, row.keyword_9, row.keyword_10,
                            row.keyword_11, row.keyword_12, row.keyword_13, row.keyword_14, row.keyword_15,
                            row.keyword_16, row.keyword_17, row.keyword_18, row.keyword_19, row.keyword_20,
                            row.keyword_21, row.keyword_22, row.keyword_23, row.keyword_24, row.keyword_25,
                            row.keyword_26, row.keyword_27, row.keyword_28, row.keyword_29, row.keyword_30]
            score = 0
            for position, word in enumerate(row_keywords):
                for keyword in keywords:
                    if word == keyword:
                        # Full match
                        score += (len(row_keywords) - position) * 1.0  # Full weight
                    elif keyword in word:
                        # Partial match
                        score += (len(row_keywords) - position) * 0.1  # Partial weight
            # Additional score for title match
            title_lower = title.lower()
            for keyword in keywords:
                if keyword in title_lower:
                    score += 10  # Adjust the weight as needed

            if score > 0:
                top_tally[(title, url)] = score

        sorted_top_tally = dict(sorted(top_tally.items(), key=lambda item: item[1], reverse=True))
        top_100 = list(sorted_top_tally.keys())[:100]
    except Exception as e:
        print(f"Database error: {e}")
    finally:
        session.close()

def fetch_first_paragraph(url):
    """Fetches the first paragraph from the given URL."""
    try:
        response = requests.get(url, timeout=10)
        if response.status_code == 200:
            soup = BeautifulSoup(response.content, 'html.parser')
            
            # Try to find the first meaningful paragraph
            paragraphs = soup.find_all('p')
            for paragraph in paragraphs:
                text = paragraph.get_text().strip()
                if len(text) > 0:
                    return text[:140] + '...' if len(text) > 140 else text
            
            # If no meaningful paragraph found
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
    
    total_pages = (len(top_100) + 19) // 20  # Calculate total number of pages
    
    return render_template('results.html', results=results_with_previews, page=page, total_pages=total_pages, search_page_url=search_page_url)

def PatientZero(Spider):
    """Initialize the database with the starting URL if not already present."""
    session = Session()
    if not session.query(Page).filter_by(url=Spider).first():
        patient_zero = Page(title="", url=Spider, processed="No")
        session.add(patient_zero)
        session.commit()
    session.close()

def ExtractURLInfo(Url):
    """Extract title, text, and URLs from a given page."""
    try:
        UrlRequest = requests.get(Url)
        UrlRequest.raise_for_status()
    except requests.RequestException as e:
        print(f"Request failed: {e}")
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

    # Pad the keywords list to ensure it always has 30 items
    while len(Keywords) < 30:
        Keywords.append('')

    return Keywords

def clean_url(url):
    # Strip any leading/trailing whitespace and remove quotes from URLs
    return url.strip().strip('"').strip("'")

def FindURLs(ExtractedURLs, base_url):
    """Format extracted URLs to be complete links."""
    FullURLs = []
    for url in ExtractedURLs:
        url = clean_url(url)  # Remove quotes from URLs
        if url.startswith('/'):
            full_url = base_url + url
        elif url.startswith('http'):
            full_url = url
        else:
            full_url = base_url + '/' + url
        FullURLs.append(full_url)
    return FullURLs

def PassDataToDatabase(Title, Url, Keywords, FullURLs):
    """Add extracted data to the database and mark the URL as processed."""
    try:
        session = Session()

        with session.no_autoflush:
            # Update the current page record
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
                print(f"Updated page: {Url}")
            
            # Insert new URLs into the database
            for full_url in FullURLs:
                if not session.query(Page).filter_by(url=full_url).first():
                    new_page = Page(url=full_url, processed="No")
                    session.add(new_page)
                    try:
                        session.commit()
                        print(f"Inserted new URL: {full_url}")
                    except IntegrityError:
                        session.rollback()
                        print(f"Duplicate URL found and ignored: {full_url}")

    except Exception as e:
        print(f"Database error: {e}")
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
                break  # Exit the loop if no URLs were found

            Url = clean_url(page.url)
            Title, Text, ExtractedURLs = ExtractURLInfo(Url)
            if Title is None:
                page.processed = 'Error'
                session.commit()
                continue  # Skip if URL extraction failed

            base_url = "/".join(Url.split("/")[:3])
            FullURLs = FindURLs(ExtractedURLs, base_url)
            Keywords = FindKeywords(Text)
            PassDataToDatabase(Title, Url, Keywords, FullURLs)

        session.close()
    except Exception as e:
        print(f"Database error: {e}")

def start_crawling():
    """Start the web crawling process."""
    initialize_database()
    PatientZero(Spider)
    while True:
        NewURL()
        time.sleep(1)  # Sleep for a short while to prevent excessive CPU usage

if __name__ == '__main__':
    # Start the web crawling in a separate thread
    threading.Thread(target=start_crawling).start()
    
    # Run the Flask web application
    app.run()
