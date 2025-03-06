from flask import Flask, request, render_template, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
import bcrypt
import requests
from googleapiclient.discovery import build
from transformers import pipeline
from datetime import datetime
from collections import defaultdict
import random
import os

HUGGING_FACE_API_URL =os.getenv("HUGGING_FACE_API_URL")
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")

YOUTUBE_API_KEY = "AIzaSyCcpc26X2E_IJSvVBt8CygEtW3xlJmkfPA"
youtube = build('youtube', 'v3', developerKey=YOUTUBE_API_KEY)

app = Flask(__name__)

# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = 'mysql+pymysql://root@localhost:3306/database_name'
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv("app.secret_key")

db = SQLAlchemy(app)


class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), unique=True, nullable=False)
    email = db.Column(db.String(100), unique=True, nullable=False)
    password = db.Column(db.LargeBinary, nullable=False)  # Store hashed password
    name = db.Column(db.String(100), nullable=False)
    age = db.Column(db.Integer, nullable=False)
    gender = db.Column(db.String(50), nullable=False)
    residence = db.Column(db.String(100), nullable=False)
    field = db.Column(db.String(100), nullable=False)

    def __init__(self, username, email, password, name, age, gender, residence, field):
        self.username = username
        self.email = email
        self.password = bcrypt.hashpw(password.encode('utf-8'), bcrypt.gensalt())
        self.name = name
        self.age = age
        self.gender = gender
        self.residence = residence
        self.field = field

    def check_password(self, password):
        return bcrypt.checkpw(password.encode('utf-8'), self.password)


# Create the database tables
with app.app_context():
    db.create_all()

# Add new GratitudeEntry model
class GratitudeEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    content = db.Column(db.Text, nullable=False)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    last_modified = db.Column(db.DateTime, onupdate=datetime.utcnow)
    mood = db.Column(db.String(50))


@app.route('/')
def index():
    return render_template('index.html')

@app.route('/about')
def about():
    return render_template('about.html')  

@app.route('/faq')
def faq():
    return render_template('faq.html')  


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        email = request.form['email']
        password = request.form['password']
        name = request.form['name']
        age = int(request.form['age'])
        gender = request.form['gender']
        residence = request.form['residence']
        field = request.form['field']

        new_user = User(username, email, password, name, age, gender, residence, field)
        db.session.add(new_user)
        db.session.commit()
        return redirect('/login')
    return render_template('register.html')


@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        email = request.form['email']
        password = request.form['password']

        user = User.query.filter_by(email=email).first()

        if user and user.check_password(password):
            session['email'] = user.email
            return redirect('/dashboard')
        else:
            return render_template('login.html', error='Invalid User')

    return render_template('login.html')


@app.route('/dashboard')
def dashboard():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    default_query = "mental health tips"
    videos = get_recommended_videos(default_query)
    
    # Add this line to fetch gratitude entries
    entries = GratitudeEntry.query.filter_by(user_id=user.id).order_by(GratitudeEntry.date_created.desc()).all()
    
    return render_template('dashboard.html', 
                         user=user,
                         videos=videos,
                         query=default_query,
                         entries=entries,  # Add this line
                         active_tab='profile')


@app.route('/chat', methods=['POST'])
def chat():
    if 'email' not in session:
        return {'error': 'Unauthorized'}, 401

    user_message = request.json.get('message')
    if not user_message:
        return {'error': 'No message provided'}, 400

    headers = {
        "Authorization": f"Bearer {HUGGING_FACE_API_KEY}",
        "Content-Type": "application/json"
    }
    payload = {
        "inputs": user_message,  # User's message
        "options": {"use_cache": False}  # Prevent cached responses
    }

    response = requests.post(HUGGING_FACE_API_URL, headers=headers, json=payload)

    if response.status_code == 200:
        response_data = response.json()
        
        # Check if the response is a list and extract the text
        if isinstance(response_data, list) and len(response_data) > 0:
            chatbot_response = response_data[0].get('generated_text', "I'm not sure how to respond to that.")
        elif isinstance(response_data, dict):  # For models returning dict
            chatbot_response = response_data.get('generated_text', "I'm not sure how to respond to that.")
        else:
            chatbot_response = "Unexpected response format from the model."

        return {'response': chatbot_response}
    else:
        error_message = response.json().get('error', 'Something went wrong.')
        return {'error': error_message}, response.status_code


@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')


# Function to get recommended videos based on a search query
def get_recommended_videos(query, max_results=6):
    try:
        print(f"Fetching videos for query: {query}")  # Debug print
        enhanced_query = f"{query} mental health help guide"
        
        request = youtube.search().list(
            part='snippet',
            q=enhanced_query,
            type='video',
            maxResults=max_results,
            relevanceLanguage='en',
            safeSearch='strict',
            videoEmbeddable='true'
        )
        response = request.execute()
        print(f"Found {len(response['items'])} videos")  # Debug print
        
        videos = []
        for item in response['items']:
            video_data = {
                'title': item['snippet']['title'],
                'description': item['snippet']['description'],
                'thumbnail': item['snippet']['thumbnails']['high']['url'],
                'video_id': item['id']['videoId']
            }
            videos.append(video_data)
        return videos
    except Exception as e:
        print(f"Error fetching videos: {e}")  # Debug print
        return []

# Route to display recommendations on the dashboard
@app.route('/youtube_recommendations', methods=['GET', 'POST'])
def youtube_recommendations():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    
    if request.method == 'POST':
        query = request.form.get('query', 'mental health')
    else:
        query = "mental health"

    videos = get_recommended_videos(query)
    
    return render_template('dashboard.html', 
                         user=user,
                         videos=videos,
                         query=query,
                         active_tab='youtube')  # Add this line


sentiment_analyzer = pipeline("text-classification", 
                            model="finiteautomata/bertweet-base-sentiment-analysis")

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    if 'email' not in session:
        return {'error': 'Unauthorized'}, 401
    
    text = request.json.get('text', '')
    if not text:
        return {'error': 'No text provided'}, 400

    # Analyze sentiment
    sentiment = sentiment_analyzer(text)[0]
    
    # Generate response based on sentiment
    response = generate_analysis_response(sentiment['label'], text)
    
    return jsonify(response)



def generate_analysis_response(sentiment, text):
    # Map sentiment to emotions and suggestions
    emotion_map = {
        'POS': 'Positive/Happy',
        'NEU': 'Neutral/Calm',
        'NEG': 'Negative/Distressed'
    }
    
    suggestions = {
        'POS': [
            "Keep up the positive mindset!",
            "Share your joy with others",
            "Document what made you happy today"
        ],
        'NEU': [
            "Practice mindfulness meditation",
            "Try some light exercise",
            "Connect with friends or family"
        ],
        'NEG': [
            "Take deep breaths and practice relaxation",
            "Talk to someone you trust about your feelings",
            "Consider professional support if needed",
            "Try some mood-lifting activities"
        ]
    }
    
    resources = {
        'POS': [
            {'title': 'Maintaining Positive Mental Health', 'link': 'https://www.nimh.nih.gov/health/topics/caring-for-your-mental-health'},
            {'title': 'Gratitude Journaling Guide', 'link': 'https://ggia.berkeley.edu/practice/gratitude_journal'}
        ],
        'NEU': [
            {'title': 'Mindfulness Meditation Guide', 'link': 'https://www.mindful.org/meditation/mindfulness-getting-started/'},
            {'title': 'Stress Management Techniques', 'link': 'https://www.nhs.uk/mental-health/self-help/guides-tools-and-activities/tips-to-reduce-stress/'}
        ],
        'NEG': [
            {'title': 'Crisis Helpline', 'link': 'https://findahelpline.com/countries/in/topics/suicidal-thoughts'},
            {'title': 'Finding Professional Help', 'link': 'https://www.amahahealth.com/centre/bengaluru/'},
            {'title': 'Self-Care Strategies', 'link': 'https://www.verywellmind.com/self-care-strategies-overall-stress-reduction-3144729'}
        ]
    }
    
    return {
        'emotion': emotion_map[sentiment],
        'stress_level': calculate_stress_level(text),
        'suggestions': suggestions[sentiment],
        'resources': resources[sentiment]
    }

def calculate_stress_level(text):
    # Simple stress level calculation based on keywords
    stress_keywords = ['stress', 'anxiety', 'worried', 'fear', 'tired', 'exhausted']
    stress_count = sum(1 for keyword in stress_keywords if keyword in text.lower())
    
    if stress_count <= 1:
        return 'Low'
    elif stress_count <= 3:
        return 'Moderate'
    else:
        return 'High'
    
# Add new route to handle journal entries
@app.route('/gratitude', methods=['GET', 'POST'])
def gratitude():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    
    if request.method == 'POST':
        content = request.form.get('content')
        mood = request.form.get('mood')
        if content:
            entry = GratitudeEntry(
                user_id=user.id,
                content=content,
                mood=mood
            )
            db.session.add(entry)
            db.session.commit()
            return redirect('/gratitude')
    
    # Get filter parameters
    start_date = request.args.get('start_date')
    end_date = request.args.get('end_date')
    mood_filter = request.args.get('mood')
    
    # Base query
    query = GratitudeEntry.query.filter_by(user_id=user.id)
    
    # Apply filters
    if start_date:
        query = query.filter(GratitudeEntry.date_created >= datetime.strptime(start_date, '%Y-%m-%d'))
    if end_date:
        query = query.filter(GratitudeEntry.date_created <= datetime.strptime(end_date, '%Y-%m-%d'))
    if mood_filter:
        query = query.filter(GratitudeEntry.mood == mood_filter)
    
    entries = query.order_by(GratitudeEntry.date_created.desc()).all()
    
    return render_template('dashboard.html', 
                         user=user, 
                         entries=entries,
                         active_tab='gratitude')

@app.route('/gratitude/edit/<int:entry_id>', methods=['POST'])
def edit_gratitude(entry_id):
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    entry = GratitudeEntry.query.get_or_404(entry_id)
    user = User.query.filter_by(email=session['email']).first()
    
    if entry.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    content = request.json.get('content')
    mood = request.json.get('mood')
    
    if content:
        entry.content = content
        entry.mood = mood
        db.session.commit()
        return jsonify({
            'message': 'Entry updated successfully',
            'content': content,
            'mood': mood,
            'last_modified': entry.last_modified.strftime('%Y-%m-%d %H:%M:%S')
        })
    
    return jsonify({'error': 'No content provided'}), 400

@app.route('/gratitude/delete/<int:entry_id>', methods=['POST'])
def delete_gratitude(entry_id):
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    entry = GratitudeEntry.query.get_or_404(entry_id)
    user = User.query.filter_by(email=session['email']).first()
    
    if entry.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db.session.delete(entry)
    db.session.commit()
    return jsonify({'message': 'Entry deleted successfully'})

@app.route('/get_mood_data')
def get_mood_data():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(email=session['email']).first()
    entries = GratitudeEntry.query.filter_by(user_id=user.id).order_by(GratitudeEntry.date_created).all()

    mood_data = {
        'labels': [],
        'moods': [],
        'counts': defaultdict(int),
        'timeline': []
    }

    for entry in entries:
        date_str = entry.date_created.strftime('%Y-%m-%d')
        mood_data['labels'].append(date_str)
        mood_data['moods'].append(entry.mood)
        mood_data['counts'][entry.mood] += 1
        mood_data['timeline'].append({'date': date_str, 'mood': entry.mood, 'content': entry.content})

    return jsonify(mood_data)

@app.route('/mood_insights')
def mood_insights():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401

    user = User.query.filter_by(email=session['email']).first()
    entries = GratitudeEntry.query.filter_by(user_id=user.id).all()
    
    mood_patterns = defaultdict(int)
    for entry in entries:
        mood_patterns[entry.mood] += 1

    most_common_mood = max(mood_patterns, key=mood_patterns.get) if mood_patterns else "Unknown"
    insights = [
        f"Your most frequent mood is {most_common_mood}",
        f"Your moods are generally {random.choice(['balanced', 'fluctuating', 'positive'])}",
        "Try maintaining a gratitude journal for better well-being."
    ]

    return jsonify({'insights': insights})





if __name__ == '__main__':
    app.run(debug=True)
