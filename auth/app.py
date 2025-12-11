from flask import Flask, request, render_template, redirect, session, jsonify
from flask_sqlalchemy import SQLAlchemy
from flask_socketio import SocketIO, emit,join_room,leave_room,send
from flask_migrate import Migrate
import uuid
import bcrypt
import requests

# Disable transformers for now to avoid loading issues - using basic sentiment analysis instead
pipeline = None

from datetime import datetime, timedelta
from collections import defaultdict
import random
import os
import ollama



HUGGING_FACE_API_URL = os.getenv("HUGGING_FACE_API_URL")
HUGGING_FACE_API_KEY = os.getenv("HUGGING_FACE_API_KEY")
YOUTUBE_API_KEY = os.getenv("YOUTUBE_API_KEY")
# Note: Using requests library directly instead of google-api-python-client for better firewall compatibility

app = Flask(__name__)
socketio = SocketIO(app, cors_allowed_origins="*", async_mode='threading')
# MySQL Database Configuration
app.config['SQLALCHEMY_DATABASE_URI'] = os.getenv('DATABASE_URI', 'mysql+pymysql://root@localhost:3306/mindcare_db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False
app.secret_key = os.getenv('SECRET_KEY', 'dev-secret-key-change-in-production')

db = SQLAlchemy(app)
migrate = Migrate(app, db)  # Add this line


# === end init ===

#websocket connection
active_users = defaultdict(dict)  # {room_id: {sid: username}}

@socketio.on('connect')
def handle_connect():
    print(f'Client connected: {request.sid}')

@socketio.on('join')
def handle_join(data):
    room = data.get('room', 'peer-support')
    username = data.get('username', 'Anonymous')
    
    join_room(room)
    active_users[room][request.sid] = username
    
    # Notify others
    emit('user_joined', {
        'username': username,
        'user_count': len(active_users[room])
    }, room=room, skip_sid=request.sid)
    
    # Send user count to the new user
    emit('user_count', len(active_users[room]))
    
    print(f'{username} joined room {room}')

@socketio.on('message')
def handle_message(data):
    room = data.get('room', 'peer-support')
    message = (data.get('message') or '').strip()
    if not message:
        return

    username = data.get('username') or active_users[room].get(request.sid, 'Anonymous')
    payload = {
        'username': username,
        'message': message,
        'timestamp': datetime.utcnow().isoformat()
    }
    emit('message', payload, room=room)


@socketio.on('typing')
def handle_typing(data):
    room = data.get('room', 'peer-support')
    username = data.get('username') or active_users[room].get(request.sid, 'Anonymous')
    emit('user_typing', {'username': username}, room=room, skip_sid=request.sid)


@socketio.on('stop_typing')
def handle_stop_typing(data):
    room = data.get('room', 'peer-support')
    username = data.get('username') or active_users[room].get(request.sid, 'Anonymous')
    emit('user_stopped_typing', {'username': username}, room=room, skip_sid=request.sid)


@socketio.on('disconnect')
def handle_disconnect():
    for room, users in list(active_users.items()):
        username = users.pop(request.sid, None)
        if username:
            emit('user_left', {'username': username, 'user_count': len(users)}, room=room)
            emit('user_count', len(users), room=room)
        if not users:
            active_users.pop(room, None)
    print(f'Client disconnected: {request.sid}')

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

class MoodEntry(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    mood_score = db.Column(db.Integer, nullable=False)  # 1-10 scale
    energy_level = db.Column(db.Integer, nullable=False)  # 1-10 scale
    sleep_quality = db.Column(db.Integer, nullable=False)  # 1-10 scale
    stress_level = db.Column(db.Integer, nullable=False)  # 1-10 scale
    activities = db.Column(db.Text)  # JSON string of activities
    notes = db.Column(db.Text)
    date_created = db.Column(db.DateTime, nullable=False, default=datetime.utcnow)
    
    def to_dict(self):
        return {
            'id': self.id,
            'mood_score': self.mood_score,
            'energy_level': self.energy_level,
            'sleep_quality': self.sleep_quality,
            'stress_level': self.stress_level,
            'activities': self.activities,
            'notes': self.notes,
            'date': self.date_created.strftime('%Y-%m-%d')
        }

class Room(db.Model):
    id=db.Column(db.Integer, primary_key=True)
    room_id = db.Column(db.String(100), unique=True, nullable=False)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)

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
                         active_tab='support_chat')






@app.route('/logout')
def logout():
    session.pop('email', None)
    return redirect('/login')


# Function to get recommended videos based on a search query
def get_recommended_videos(query, max_results=6):
    try:
        print(f"Fetching videos for query: {query}")  # Debug print
        
        # If query is general mental health term, enhance it
        mental_health_keywords = ['mental health', 'anxiety', 'depression', 'stress', 'meditation', 
                                 'mindfulness', 'therapy', 'wellness', 'self care', 'coping']
        
        is_mental_health_query = any(keyword in query.lower() for keyword in mental_health_keywords)
        
        if is_mental_health_query:
            search_query = f"{query}"
        else:
            search_query = f"{query} mental health wellness"
        
        # Use requests library instead of google-api-python-client for better firewall compatibility
        import urllib.parse
        encoded_query = urllib.parse.quote(search_query)
        api_url = f"https://www.googleapis.com/youtube/v3/search?part=snippet&q={encoded_query}&type=video&maxResults={max_results}&relevanceLanguage=en&safeSearch=strict&videoEmbeddable=true&order=relevance&key={YOUTUBE_API_KEY}"
        
        response = requests.get(api_url, timeout=10)
        response.raise_for_status()
        
        data = response.json()
        print(f"Found {len(data.get('items', []))} videos")  # Debug print
        
        videos = []
        for item in data.get('items', []):
            # Get video ID based on response structure
            video_id = item['id'].get('videoId', '')
            if not video_id:
                continue
                
            # Get best available thumbnail
            thumbnails = item['snippet'].get('thumbnails', {})
            thumbnail_url = (thumbnails.get('high', {}).get('url') or 
                           thumbnails.get('medium', {}).get('url') or 
                           thumbnails.get('default', {}).get('url', ''))
            
            video_data = {
                'title': item['snippet'].get('title', 'Untitled'),
                'description': item['snippet'].get('description', 'No description available'),
                'thumbnail': thumbnail_url,
                'video_id': video_id
            }
            videos.append(video_data)
        
        return videos
    except requests.exceptions.RequestException as e:
        print(f"Network error fetching videos: {str(e)}")  # Debug print
        return []
    except Exception as e:
        print(f"Error fetching videos: {str(e)}")  # Debug print
        import traceback
        traceback.print_exc()
        return []

# Route to display recommendations on the dashboard
@app.route('/youtube_recommendations', methods=['GET', 'POST'])
def youtube_recommendations():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    
    # Get search query from POST or use default
    if request.method == 'POST':
        query = request.form.get('query', '').strip()
        if not query:
            query = "mental health tips"
    else:
        query = "mental health tips"

    # Fetch videos
    videos = get_recommended_videos(query)
    
    # Pass empty list if no videos found
    if not videos:
        videos = []
    
    return render_template('dashboard.html', 
                         user=user,
                         videos=videos,
                         query=query,
                         active_tab='youtube')


# Initialize sentiment analyzer with error handling
try:
    if pipeline is not None:
        sentiment_analyzer = pipeline("text-classification", 
                                    model="finiteautomata/bertweet-base-sentiment-analysis")
    else:
        sentiment_analyzer = None
        print("Warning: Sentiment analyzer not available - transformers library not installed")
except Exception as e:
    print(f"Error initializing sentiment analyzer: {e}")
    sentiment_analyzer = None

# Enhanced sentiment analysis functions

@app.route('/analyze_text', methods=['POST'])
def analyze_text():
    if 'email' not in session:
        return {'error': 'Unauthorized'}, 401
    
    text = request.json.get('text', '')
    if not text:
        return {'error': 'No text provided'}, 400

    try:
        # Check if sentiment analyzer is available
        if sentiment_analyzer is None:
            # Fallback to basic sentiment analysis using keyword matching
            sentiment_label = perform_basic_sentiment_analysis(text)
        else:
            # Get sentiment analysis from transformers
            sentiment_result = sentiment_analyzer(text)[0]
            # Map transformer labels (POSITIVE, NEGATIVE, NEUTRAL) to our format
            label_map = {
                'POSITIVE': 'POS',
                'NEGATIVE': 'NEG',
                'NEUTRAL': 'NEU'
            }
            sentiment_label = label_map.get(sentiment_result['label'], 'NEU')
        
        # Get user data
        user = User.query.filter_by(email=session['email']).first()
        
        # Generate comprehensive analysis
        analysis = generate_analysis_response(sentiment_label, text, user)
        
        return jsonify(analysis)
    except Exception as e:
        print(f"Error in analysis: {str(e)}")
        return {'error': 'Analysis failed'}, 500


def perform_basic_sentiment_analysis(text):
    """Fallback sentiment analysis using keyword matching with negation handling"""
    text_lower = text.lower()
    
    # Expanded keyword lists
    positive_words = ['happy', 'joy', 'joyful', 'great', 'excellent', 'wonderful', 'amazing', 'good', 
                     'blessed', 'grateful', 'love', 'loving', 'excited', 'pleased', 'delighted', 
                     'content', 'peaceful', 'calm', 'relaxed', 'fantastic', 'awesome', 'brilliant',
                     'perfect', 'beautiful', 'lovely', 'cheerful', 'optimistic', 'hopeful', 'proud']
    
    negative_words = ['sad', 'angry', 'terrible', 'horrible', 'awful', 'depressed', 'depression',
                     'anxious', 'anxiety', 'worried', 'worry', 'stressed', 'stress', 'upset', 
                     'frustrated', 'frustration', 'overwhelmed', 'hopeless', 'afraid', 'fearful', 
                     'panic', 'exhausted', 'tired', 'bad', 'worst', 'miserable', 'lonely', 'alone',
                     'crying', 'hurt', 'pain', 'suffering', 'scared', 'fear', 'nervous', 'down',
                     'unhappy', 'disappointed', 'failure', 'failed', 'worthless', 'helpless']
    
    # Negation words that flip sentiment
    negations = ['not', 'no', 'never', 'neither', "n't", 'hardly', 'barely', 'cannot', "can't", 
                 "won't", "wouldn't", "shouldn't", "couldn't", "don't", "doesn't", "didn't"]
    
    # Split into words for better analysis
    words = text_lower.split()
    
    positive_score = 0
    negative_score = 0
    
    # Check for negations and adjust scores
    for i, word in enumerate(words):
        # Check if previous word is a negation
        has_negation = i > 0 and any(neg in words[i-1] for neg in negations)
        
        # Check for positive words
        if any(pos_word in word for pos_word in positive_words):
            if has_negation:
                negative_score += 2  # "not happy" = negative
            else:
                positive_score += 1
        
        # Check for negative words
        if any(neg_word in word for neg_word in negative_words):
            if has_negation:
                positive_score += 0.5  # "not sad" = somewhat positive
            else:
                negative_score += 1
    
    # Also check for direct negation phrases
    negation_phrases = ['not feeling good', 'not feeling well', 'not doing well', 'not okay', 
                       'not fine', 'not great', 'not happy', 'not feeling happy', 'feeling down',
                       'feel bad', 'feeling bad', 'not good', 'not well', "don't feel okay"]
    for phrase in negation_phrases:
        if phrase in text_lower:
            negative_score += 2
    
    # Determine sentiment
    if negative_score > positive_score:
        return 'NEG'
    elif positive_score > negative_score:
        return 'POS'
    else:
        return 'NEU'


def generate_analysis_response(sentiment, text, user):
    # Emotion mapping adjusted to match UI expectations
    emotion_map = {
        'NEG': ['Anxiety', 'Sadness', 'Stress', 'Frustration', 'Depression'],
        'NEU': ['Neutral', 'Calm', 'Contemplative', 'Reflective', 'Balanced'],
        'POS': ['Joy', 'Gratitude', 'Contentment', 'Happiness', 'Excitement']
    }
    
    # Calculate stress level first as it affects emotion selection
    stress_level = calculate_stress_level(text)
    
    # Select emotion based on both sentiment and stress level with better logic
    if stress_level == 'High':
        # High stress overrides sentiment - always negative emotions
        specific_emotion = random.choice(emotion_map['NEG'])
    elif stress_level == 'Low' and sentiment == 'POS':
        # Low stress + positive sentiment = positive emotions
        specific_emotion = random.choice(emotion_map['POS'])
    elif stress_level == 'Low' and sentiment == 'NEG':
        # Low stress but negative sentiment = mild negative emotions
        specific_emotion = random.choice(['Contemplative', 'Reflective', 'Calm'])
    elif stress_level == 'Moderate' and sentiment == 'NEG':
        # Moderate stress + negative sentiment = negative emotions
        specific_emotion = random.choice(emotion_map['NEG'])
    elif stress_level == 'Moderate' and sentiment == 'POS':
        # Moderate stress + positive sentiment = neutral/positive emotions
        specific_emotion = random.choice(emotion_map['NEU'] + ['Contentment', 'Hopeful'])
    else:
        # Default: use sentiment-based emotion
        specific_emotion = random.choice(emotion_map.get(sentiment, emotion_map['NEU']))

    # Suggestions based on emotion and stress level
    suggestions = []
    if stress_level == 'High':
        suggestions = [
            "Practice deep breathing exercises to help reduce immediate stress",
            "Consider talking to a trusted friend or professional about your feelings",
            "Try the 5-4-3-2-1 grounding technique to center yourself",
            "Take small breaks throughout the day to decompress"
        ]
    elif stress_level == 'Moderate':
        suggestions = [
            "Incorporate mindfulness practices into your daily routine",
            "Maintain a balanced schedule between work and rest",
            "Engage in light physical activity to boost your mood",
            "Practice self-care activities that you enjoy"
        ]
    else:
        suggestions = [
            "Continue your positive practices and self-care routine",
            "Share your positive energy with others who might need support",
            "Document these good moments in your gratitude journal",
            "Build on this positive state with activities you enjoy"
        ]

    # Resources tailored to stress level
    resources = [
        {
            'title': 'Immediate Coping Strategies',
            'link': 'https://www.mindtools.com/pages/article/dealing-with-stress.htm'
        },
        {
            'title': 'Professional Mental Health Support',
            'link': 'https://www.betterhelp.com'
        },
        {
            'title': 'Mindfulness Meditation Guide',
            'link': 'https://www.mindful.org/meditation/mindfulness-getting-started/'
        }
    ]

    return {
        'emotion': specific_emotion,
        'stress_level': stress_level,
        'suggestions': suggestions[:3],  # Limit to 3 suggestions for UI
        'resources': resources
    }


def calculate_stress_level(text):
    # Enhanced stress keywords with weights
    stress_indicators = {
        'high': ['anxiety', 'panic', 'overwhelmed', 'depressed', 'depression', 'stressed', 
                'worried', 'worry', 'fear', 'terrible', 'horrible', 'awful', 'sad', 'angry', 
                'upset', 'exhausted', 'hopeless', 'crying', 'suffering', 'miserable', 
                'desperate', 'scared', 'help me', 'can\'t cope', 'breakdown', 'crisis',
                'suicidal', 'worthless', 'pain', 'hurt', 'alone', 'isolated', 'failing'],
        'moderate': ['concerned', 'uneasy', 'nervous', 'tired', 'frustrated', 'uncertain', 
                    'busy', 'confused', 'bothered', 'unsure', 'annoyed', 'restless', 
                    'uncomfortable', 'difficult', 'challenging', 'tough', 'hard', 'struggle'],
        'low': ['calm', 'happy', 'peaceful', 'relaxed', 'good', 'great', 'blessed', 'grateful', 
                'content', 'joy', 'joyful', 'excited', 'pleased', 'delighted', 'wonderful',
                'amazing', 'fantastic', 'excellent', 'perfect', 'beautiful', 'cheerful']
    }
    
    text_lower = text.lower()
    words = text_lower.split()
    
    if len(words) == 0:
        return 'Low'
    
    # Check for negation phrases that indicate distress
    distress_phrases = ['not feeling good', 'not feeling well', 'not okay', 'not fine', 
                       'feeling bad', 'feeling down', 'not doing well', 'feel terrible',
                       'feel awful', 'feel sad', 'feel depressed']
    
    negation_boost = sum(2 for phrase in distress_phrases if phrase in text_lower)
    
    # Count occurrences of stress indicators
    high_count = sum(1 for word in words if any(indicator in word for indicator in stress_indicators['high']))
    moderate_count = sum(1 for word in words if any(indicator in word for indicator in stress_indicators['moderate']))
    low_count = sum(1 for word in words if any(indicator in word for indicator in stress_indicators['low']))
    
    # Add negation boost to high count
    high_count += negation_boost
    
    # Calculate weighted score
    total_score = (high_count * 3) + (moderate_count * 1.5) - (low_count * 2)
    
    # Normalize by word count to handle different text lengths
    normalized_score = total_score / len(words)
    
    # Determine stress level with improved thresholds
    if high_count >= 2 or normalized_score > 0.4:
        return 'High'
    elif high_count >= 1 or moderate_count >= 2 or normalized_score > 0.15:
        return 'Moderate'
    elif low_count >= 1 and high_count == 0:
        return 'Low'
    elif high_count == 0 and moderate_count == 0 and low_count == 0:
        return 'Moderate'  # Neutral text
    else:
        return 'Moderate'  # Default to moderate if unclear


def select_personalized_suggestions(text, suggestions_list, stress_level):
    # Select most appropriate suggestions based on text content and stress level
    selected_suggestions = []
    
    # Always include first suggestion as a general one
    if suggestions_list:
        selected_suggestions.append(suggestions_list[0])
    
    # Add stress-level appropriate suggestions
    if stress_level == 'High' and len(suggestions_list) > 3:
        selected_suggestions.append(suggestions_list[3])
    elif stress_level == 'Moderate' and len(suggestions_list) > 2:
        selected_suggestions.append(suggestions_list[2])
    elif len(suggestions_list) > 1:
        selected_suggestions.append(suggestions_list[1])
    
    # Add one more random suggestion for variety
    remaining_suggestions = [s for s in suggestions_list if s not in selected_suggestions]
    if remaining_suggestions:
        selected_suggestions.append(random.choice(remaining_suggestions))
    
    return selected_suggestions


def generate_insight(text, sentiment):
    # Generate a personalized insight based on the text
    insights = {
        'POS': [
            "You seem to be in a positive frame of mind. Regular gratitude practice can help maintain this.",
            "Positive emotions like these can boost your resilience for future challenges.",
            "Acknowledging good moments, as you're doing now, is a powerful mental health practice."
        ],
        'NEU': [
            "Your balanced perspective provides a good foundation for self-reflection.",
            "This neutral state is perfect for mindfulness practice and clear thinking.",
            "Times of calm are excellent for setting intentions and planning."
        ],
        'NEG': [
            "Remember that emotions are temporary - this feeling will pass with time.",
            "It takes courage to acknowledge difficult feelings, which is an important first step.",
            "Your awareness of these emotions shows emotional intelligence and self-awareness."
        ]
    }
    
    return random.choice(insights[sentiment])


def get_motivational_quote(sentiment):
    # Return an appropriate motivational quote based on sentiment
    quotes = {
        'POS': [
            "Happiness is not something ready-made. It comes from your own actions. - Dalai Lama",
            "The more you praise and celebrate your life, the more there is in life to celebrate. - Oprah Winfrey",
            "Joy does not simply happen to us. We have to choose joy and keep choosing it every day. - Henri Nouwen"
        ],
        'NEU': [
            "Balance is not something you find, it's something you create. - Jana Kingsford",
            "The middle path is the way to wisdom. - Rumi",
            "Peace is the result of retraining your mind to process life as it is, rather than as you think it should be. - Wayne Dyer"
        ],
        'NEG': [
            "You don't have to see the whole staircase, just take the first step. - Martin Luther King Jr.",
            "This too shall pass. - Persian Proverb",
            "The darkest hour has only sixty minutes. - Morris Mandel"
        ]
    }
    
    return random.choice(quotes[sentiment])
    
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

@app.route('/join_room', methods=['POST'])
def join_support_chat():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.filter_by(email=session['email']).first()
    
    # Generate a unique room ID
    room_id = str(uuid.uuid4())
    
    new_room = Room(room_id=room_id, user_id=user.id)
    db.session.add(new_room)
    db.session.commit()
    
    return jsonify({'room_id': room_id})


# Add VoiceFlow configuration after other configurations
VOICEFLOW_API_KEY = os.getenv("VOICEFLOW_API_KEY")
VOICEFLOW_BASE_URL = "https://general-runtime.voiceflow.com/state/user"

# Add VoiceFlow helper class before routes
class VoiceFlowAgent:
    @staticmethod
    def interact(user_id: str, request_data: dict) -> str:
        try:
            response = requests.post(
                f'{VOICEFLOW_BASE_URL}/{user_id}/interact',
                json={'request': request_data},
                headers={
                    'Authorization': VOICEFLOW_API_KEY,
                    'versionID': 'production'
                }
            )
            response.raise_for_status()
            
            messages = []
            for trace in response.json():
                if trace["type"] == "text":
                    messages.append(trace["payload"]["message"])
            
            return " ".join(messages) if messages else "No response from agent."
        except Exception as e:
            print(f"VoiceFlow API Error: {str(e)}")
            return "Sorry, I'm having trouble connecting right now."

# Add new route for mood journal interactions
@app.route('/mood_journal/interact', methods=['POST'])
def mood_journal_interact():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.filter_by(email=session['email']).first()
    message = request.json.get('message')
    
    if not message:
        return jsonify({'error': 'No message provided'}), 400
    
    user_id = user.email
    is_first = request.json.get('is_first_interaction', False)
    
    request_data = {"type": "launch"} if is_first else {"type": "text", "payload": message}
    response = VoiceFlowAgent.interact(user_id, request_data)
    
    return jsonify({'response': response})


# Add new route for voice-based mood journal interactions
@app.route('/mood_journal/voice/interact', methods=['POST'])
def mood_journal_voice_interact():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.filter_by(email=session['email']).first()
    transcribed_text = request.json.get('transcribed_text')
    
    if not transcribed_text:
        return jsonify({'error': 'No voice input provided'}), 400
    
    user_id = user.email
    is_first = request.json.get('is_first_interaction', False)
    
    request_data = {"type": "launch"} if is_first else {"type": "text", "payload": transcribed_text}
    response = VoiceFlowAgent.interact(user_id, request_data)
    
    return jsonify({
        'response': response,
        'transcribed_text': transcribed_text
    })

@app.route('/progress_tracker', methods=['GET', 'POST'])
def progress_tracker():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    
    if request.method == 'POST':
        mood_score = int(request.form.get('mood_score'))
        energy_level = int(request.form.get('energy_level'))
        sleep_quality = int(request.form.get('sleep_quality'))
        stress_level = int(request.form.get('stress_level'))
        activities = request.form.get('activities', '')
        notes = request.form.get('notes', '')
        
        entry = MoodEntry(
            user_id=user.id,
            mood_score=mood_score,
            energy_level=energy_level,
            sleep_quality=sleep_quality,
            stress_level=stress_level,
            activities=activities,
            notes=notes
        )
        db.session.add(entry)
        db.session.commit()
        
        return jsonify({'success': True, 'message': 'Entry saved successfully'})
    
    return render_template('dashboard.html', user=user, active_tab='progress_tracker')

@app.route('/progress_tracker/data', methods=['GET'])
def get_progress_data():
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.filter_by(email=session['email']).first()
    days = request.args.get('days', 30, type=int)
    
    start_date = datetime.utcnow() - timedelta(days=days)
    entries = MoodEntry.query.filter(
        MoodEntry.user_id == user.id,
        MoodEntry.date_created >= start_date
    ).order_by(MoodEntry.date_created.asc()).all()
    
    # Calculate insights
    if entries:
        avg_mood = sum(e.mood_score for e in entries) / len(entries)
        avg_energy = sum(e.energy_level for e in entries) / len(entries)
        avg_sleep = sum(e.sleep_quality for e in entries) / len(entries)
        avg_stress = sum(e.stress_level for e in entries) / len(entries)
        
        # Trend analysis (simple linear trend)
        recent_entries = entries[-7:] if len(entries) >= 7 else entries
        trend = "improving" if recent_entries[-1].mood_score > recent_entries[0].mood_score else "declining"
        
        insights = {
            'averages': {
                'mood': round(avg_mood, 1),
                'energy': round(avg_energy, 1),
                'sleep': round(avg_sleep, 1),
                'stress': round(avg_stress, 1)
            },
            'trend': trend,
            'total_entries': len(entries),
            'streak': calculate_streak(entries)
        }
    else:
        insights = {
            'averages': {'mood': 0, 'energy': 0, 'sleep': 0, 'stress': 0},
            'trend': 'none',
            'total_entries': 0,
            'streak': 0
        }
    
    return jsonify({
        'entries': [e.to_dict() for e in entries],
        'insights': insights
    })

def calculate_streak(entries):
    if not entries:
        return 0
    
    streak = 1
    entries_sorted = sorted(entries, key=lambda x: x.date_created, reverse=True)
    
    for i in range(len(entries_sorted) - 1):
        current_date = entries_sorted[i].date_created.date()
        next_date = entries_sorted[i + 1].date_created.date()
        
        if (current_date - next_date).days == 1:
            streak += 1
        else:
            break
    
    return streak

@app.route('/progress_tracker/delete/<int:entry_id>', methods=['POST'])
def delete_progress_entry(entry_id):
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    user = User.query.filter_by(email=session['email']).first()
    entry = MoodEntry.query.get_or_404(entry_id)
    
    if entry.user_id != user.id:
        return jsonify({'error': 'Unauthorized'}), 401
    
    db.session.delete(entry)
    db.session.commit()
    
    return jsonify({'success': True})


@app.route('/therapist_finder')
def therapist_finder():
    if 'email' not in session:
        return redirect('/login')
    
    user = User.query.filter_by(email=session['email']).first()
    return render_template('dashboard.html', 
                         user=user,
                         active_tab='therapist_finder')


@app.route('/api/geocode', methods=['POST'])
def geocode_location():
    """Geocode an address using Nominatim (OpenStreetMap) API"""
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        location = data.get('location', '')
        
        if not location:
            return jsonify({'error': 'Location is required'}), 400
        
        # Use Nominatim API (free OpenStreetMap geocoding)
        import urllib.parse
        import urllib.request
        import json
        
        encoded_location = urllib.parse.quote(location)
        url = f'https://nominatim.openstreetmap.org/search?q={encoded_location}&format=json&limit=1'
        
        req = urllib.request.Request(
            url,
            headers={'User-Agent': 'MindCare-TherapistFinder/1.0'}
        )
        
        with urllib.request.urlopen(req) as response:
            results = json.loads(response.read())
        
        if not results:
            return jsonify({'error': 'Location not found'}), 404
        
        result = results[0]
        return jsonify({
            'lat': float(result['lat']),
            'lon': float(result['lon']),
            'display_name': result['display_name']
        })
    
    except Exception as e:
        print(f"Geocoding error: {str(e)}")
        return jsonify({'error': 'Failed to geocode location'}), 500


@app.route('/api/find_therapists', methods=['POST'])
def find_therapists():
    """Find nearby therapists using Overpass API (OpenStreetMap data)"""
    if 'email' not in session:
        return jsonify({'error': 'Unauthorized'}), 401
    
    try:
        data = request.json
        lat = data.get('lat')
        lon = data.get('lon')
        radius = data.get('radius', 5000)  # Default 5km radius
        
        if not lat or not lon:
            return jsonify({'error': 'Coordinates are required'}), 400
        
        # Use Overpass API to find healthcare facilities
        import urllib.request
        import json
        
        # Query for doctors, clinics, hospitals, and psychologists
        overpass_query = f"""
        [out:json][timeout:25];
        (
          node["amenity"="doctors"](around:{radius},{lat},{lon});
          node["amenity"="clinic"](around:{radius},{lat},{lon});
          node["amenity"="hospital"](around:{radius},{lat},{lon});
          node["healthcare"="psychologist"](around:{radius},{lat},{lon});
          node["healthcare"="therapist"](around:{radius},{lat},{lon});
          node["healthcare"="counselling"](around:{radius},{lat},{lon});
          way["amenity"="doctors"](around:{radius},{lat},{lon});
          way["amenity"="clinic"](around:{radius},{lat},{lon});
          way["healthcare"="psychologist"](around:{radius},{lat},{lon});
          way["healthcare"="therapist"](around:{radius},{lat},{lon});
        );
        out center;
        """
        
        url = 'https://overpass-api.de/api/interpreter'
        data_encoded = overpass_query.encode('utf-8')
        
        req = urllib.request.Request(
            url,
            data=data_encoded,
            headers={'User-Agent': 'MindCare-TherapistFinder/1.0'}
        )
        
        with urllib.request.urlopen(req, timeout=30) as response:
            result = json.loads(response.read())
        
        therapists = []
        for element in result.get('elements', []):
            tags = element.get('tags', {})
            
            # Get coordinates
            if 'lat' in element and 'lon' in element:
                element_lat = element['lat']
                element_lon = element['lon']
            elif 'center' in element:
                element_lat = element['center']['lat']
                element_lon = element['center']['lon']
            else:
                continue
            
            # Extract relevant information
            name = tags.get('name', 'Unnamed Healthcare Facility')
            amenity = tags.get('amenity', tags.get('healthcare', 'healthcare'))
            address = tags.get('addr:street', '')
            city = tags.get('addr:city', '')
            phone = tags.get('phone', tags.get('contact:phone', 'N/A'))
            website = tags.get('website', tags.get('contact:website', ''))
            
            # Calculate distance
            from math import radians, sin, cos, sqrt, atan2
            R = 6371  # Earth's radius in km
            
            lat1, lon1 = radians(lat), radians(lon)
            lat2, lon2 = radians(element_lat), radians(element_lon)
            
            dlat = lat2 - lat1
            dlon = lon2 - lon1
            
            a = sin(dlat/2)**2 + cos(lat1) * cos(lat2) * sin(dlon/2)**2
            c = 2 * atan2(sqrt(a), sqrt(1-a))
            distance = R * c
            
            therapists.append({
                'name': name,
                'type': amenity.replace('_', ' ').title(),
                'address': f"{address}, {city}" if address and city else address or city or 'Address not available',
                'phone': phone,
                'website': website,
                'lat': element_lat,
                'lon': element_lon,
                'distance': round(distance, 2)
            })
        
        # Sort by distance
        therapists.sort(key=lambda x: x['distance'])
        
        return jsonify({
            'therapists': therapists[:20],  # Limit to 20 results
            'count': len(therapists)
        })
    
    except Exception as e:
        print(f"Find therapists error: {str(e)}")
        import traceback
        traceback.print_exc()
        return jsonify({'error': 'Failed to find therapists'}), 500



if __name__ == '__main__':
    socketio.run(app, debug=True)
