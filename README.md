# Mental Health Companion Web Application

## Overview
The Mental Health Companion Web Application is designed to assist users in managing their mental well-being through AI-powered sentiment analysis, gratitude journaling, and personalized YouTube recommendations.

## Features
- **User Authentication**: Secure user registration and login system with password hashing.
- **Sentiment Analysis**: Uses AI to analyze user input and provide tailored responses and resources.
- **Gratitude Journal**: Allows users to log daily gratitude entries, track moods, and gain insights.
- **YouTube Video Recommendations**: Fetches relevant mental health videos based on user queries.
- **Dashboard**: Displays user information, sentiment insights, and gratitude history.
- **Chatbot Integration**: AI-powered chatbot to provide emotional support and guidance.

## Technologies Used
- **Backend**: Python, Flask, Flask-SQLAlchemy
- **Frontend**: HTML, CSS, JavaScript
- **Database**: MySQL (via Flask-SQLAlchemy)
- **AI & NLP**:
  - Hugging Face Transformers for sentiment analysis
  - Google YouTube API for video recommendations
- **Authentication**: bcrypt for password hashing

## Installation
### Prerequisites
- Python 3.7+
- MySQL Database
- Virtual environment (recommended)

### Steps to Run
1. Clone the repository:
   ```sh
   git clone https://github.com/your-repo-url.git
   cd mental-health-companion
   ```
2. Create and activate a virtual environment:
   ```sh
   python -m venv venv
   source venv/bin/activate  # On Windows use: venv\Scripts\activate
   ```
3. Install dependencies:
   ```sh
   pip install -r requirements.txt
   ```
4. Set up environment variables:
   ```sh
   export HUGGING_FACE_API_URL='your_huggingface_api_url'
   export HUGGING_FACE_API_KEY='your_huggingface_api_key'
   export FLASK_APP=app.py
   export FLASK_ENV=development
   ```
5. Configure MySQL database:
   - Update `app.config['SQLALCHEMY_DATABASE_URI']` with your MySQL credentials.
   - Run database migrations:
     ```sh
     flask db upgrade
     ```
6. Start the Flask application:
   ```sh
   python app.py
   ```
7. Open the browser and navigate to:
   ```
   http://127.0.0.1:5000/
   ```

## API Endpoints
| Method | Endpoint | Description |
|--------|---------|-------------|
| GET | `/` | Home Page |
| GET | `/about` | About Page |
| GET, POST | `/register` | User Registration |
| GET, POST | `/login` | User Login |
| GET | `/dashboard` | User Dashboard |
| POST | `/chat` | Chatbot Interaction |
| POST | `/analyze_text` | Sentiment Analysis |
| GET, POST | `/gratitude` | Manage Gratitude Entries |
| POST | `/gratitude/edit/<id>` | Edit Gratitude Entry |
| POST | `/gratitude/delete/<id>` | Delete Gratitude Entry |
| GET | `/youtube_recommendations` | Fetch Mental Health Videos |
| GET | `/mood_insights` | Retrieve Mood Insights |

## Future Enhancements
- Mobile app integration
- Voice-based AI interaction
- More advanced sentiment tracking
- AI-powered mood prediction

## Contributors
- **Damewan Bareh** (Developer)

## License
This project is licensed under the MIT License.
