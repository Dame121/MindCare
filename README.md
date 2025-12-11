# 🧠 MindCare - Mental Health Companion

<div align="center">

**Guidance at your fingertips.**

A comprehensive mental health support platform that provides resources, tools, and community support to help manage stress and improve mental well-being.

[![Flask](https://img.shields.io/badge/Flask-2.0+-000000?style=flat&logo=flask&logoColor=white)](https://flask.palletsprojects.com/)
[![Python](https://img.shields.io/badge/Python-3.8+-3776AB?style=flat&logo=python&logoColor=white)](https://www.python.org/)
[![MySQL](https://img.shields.io/badge/MySQL-8.0+-4479A1?style=flat&logo=mysql&logoColor=white)](https://www.mysql.com/)
[![Socket.IO](https://img.shields.io/badge/Socket.IO-Real--time-010101?style=flat&logo=socket.io&logoColor=white)](https://socket.io/)

</div>

---

## 📋 Table of Contents

- [Overview](#-overview)
- [Features](#-features)
- [Tech Stack](#-tech-stack)
- [Getting Started](#-getting-started)
  - [Prerequisites](#prerequisites)
  - [Installation](#installation)
  - [Configuration](#configuration)
- [Usage](#-usage)
- [Project Structure](#-project-structure)
- [API Integrations](#-api-integrations)
- [Contributing](#-contributing)
- [License](#-license)
- [Disclaimer](#-disclaimer)

---

## 🌟 Overview

MindCare is not a replacement for therapy but a comprehensive tool designed to help you explore mental health resources, track your emotional well-being, and connect with trusted support systems. The platform combines AI-powered mood analysis, personalized recommendations, and peer support to create a holistic mental health companion.

---

## ✨ Features

### 🎯 Core Features

- **🔐 User Authentication & Profile Management**
  - Secure registration and login with bcrypt password hashing
  - Personalized user profiles with demographic information

- **💬 AI-Powered MindChat**
  - Interactive chatbot using Voiceflow AI integration
  - Context-aware conversations for mental health support
  - Real-time sentiment analysis of user inputs

- **📊 Mood Tracking & Analytics**
  - Daily mood journaling with multiple metrics (mood, energy, sleep, stress)
  - Visual progress tracking with charts and insights
  - Streak tracking to encourage consistent journaling
  - Trend analysis to identify patterns in mental well-being

- **🙏 Gratitude Journal**
  - Create, edit, and delete gratitude entries
  - Mood tagging for each entry
  - Historical view of all gratitude moments

- **🎥 Personalized YouTube Recommendations**
  - Curated mental health content based on user mood
  - Safe search with embeddable, relevant videos
  - Search functionality for specific topics

- **🧘 Meditation Resources**
  - Ambient soundscapes (rain, ocean, forest, bells)
  - Guided meditation support
  - Relaxation techniques

- **👥 Peer Support Chat**
  - Real-time WebSocket-based group chat
  - Anonymous or identified participation
  - Active user count and presence indicators
  - Typing indicators for enhanced interaction

- **🏥 Therapist Finder**
  - Location-based search using OpenStreetMap data
  - Find nearby mental health professionals
  - Distance calculation and sorting
  - Contact information and facility details

### 🔍 Advanced Features

- **Sentiment Analysis**
  - Advanced text analysis with negation handling
  - Emotion detection (anxiety, joy, stress, etc.)
  - Stress level assessment
  - Personalized suggestions based on analysis

- **Progress Insights**
  - Average calculations for mood metrics
  - Trend identification (improving/declining)
  - Journaling streak tracking
  - Data visualization ready

---

## 🛠️ Tech Stack

### Backend
- **Framework:** Flask 2.0+
- **Database:** MySQL with SQLAlchemy ORM
- **Real-time:** Flask-SocketIO with WebSockets
- **Authentication:** bcrypt for password hashing
- **Migrations:** Flask-Migrate (Alembic)

### Frontend
- **Styling:** Tailwind CSS
- **JavaScript:** Vanilla JS with modern ES6+ features
- **Real-time:** Socket.IO client

### APIs & Integrations
- **Voiceflow:** AI chatbot for mental health conversations
- **YouTube Data API v3:** Video recommendations
- **Hugging Face:** Sentiment analysis (optional)
- **Nominatim (OpenStreetMap):** Geocoding for therapist finder
- **Overpass API:** Finding healthcare facilities

### AI/ML
- **Ollama:** Local AI model integration (optional)
- **Sentiment Analysis:** Custom keyword-based with negation handling

---

## 🚀 Getting Started

### Prerequisites

Before you begin, ensure you have the following installed:

- **Python 3.8+** ([Download](https://www.python.org/downloads/))
- **MySQL 8.0+** ([Download](https://dev.mysql.com/downloads/))
- **pip** (Python package manager)
- **Git** ([Download](https://git-scm.com/downloads))

### Installation

1. **Clone the repository**

   ```bash
   git clone https://github.com/Dame121/MindCare.git
   cd MindCare/auth
   ```

2. **Create a virtual environment**

   ```bash
   # Windows
   python -m venv venv
   venv\Scripts\activate

   # macOS/Linux
   python3 -m venv venv
   source venv/bin/activate
   ```

3. **Install dependencies**

   ```bash
   pip install -r requirements.txt
   ```

   **Required packages:**
   ```
   Flask>=2.0.0
   Flask-SQLAlchemy
   Flask-SocketIO
   Flask-Migrate
   PyMySQL
   bcrypt
   requests
   python-dotenv
   ollama (optional)
   ```

4. **Set up MySQL database**

   ```sql
   CREATE DATABASE mindcare_db;
   ```

5. **Run database migrations**

   ```bash
   flask db upgrade
   ```

### Configuration

1. **Create a `.env` file** in the `auth/` directory:

   ```env
   # Database Configuration
   DATABASE_URI=mysql+pymysql://username:password@localhost:3306/mindcare_db

   # Security
   SECRET_KEY=your-super-secret-key-change-this-in-production

   # API Keys
   YOUTUBE_API_KEY=your-youtube-api-key
   VOICEFLOW_API_KEY=your-voiceflow-api-key
   HUGGING_FACE_API_KEY=your-huggingface-api-key (optional)
   HUGGING_FACE_API_URL=https://api-inference.huggingface.co/models/facebook/blenderbot-400M-distill
   ```

2. **Obtain API Keys:**

   - **YouTube Data API v3:**
     1. Go to [Google Cloud Console](https://console.cloud.google.com/)
     2. Create a new project
     3. Enable YouTube Data API v3
     4. Create credentials (API Key)

   - **Voiceflow:**
     1. Sign up at [Voiceflow](https://www.voiceflow.com/)
     2. Create a conversational AI agent for mental health
     3. Get your API key from project settings

   - **Hugging Face (Optional):**
     1. Sign up at [Hugging Face](https://huggingface.co/)
     2. Generate an API token from settings

3. **Update configuration in `.env`** with your actual values

---

## 💻 Usage

### Starting the Application

1. **Activate virtual environment** (if not already activated)

   ```bash
   # Windows
   venv\Scripts\activate

   # macOS/Linux
   source venv/bin/activate
   ```

2. **Run the Flask application**

   ```bash
   python app.py
   ```

3. **Access the application**

   Open your browser and navigate to: `http://localhost:5000`

### First-Time Setup

1. **Register an account** at `/register`
2. **Log in** with your credentials
3. **Explore features** from the dashboard

### Available Routes

- `/` - Landing page
- `/register` - User registration
- `/login` - User login
- `/dashboard` - Main dashboard (requires login)
- `/about` - About page
- `/faq` - Frequently asked questions
- `/logout` - Logout

---

## 📁 Project Structure

```
MindCare/
├── auth/
│   ├── app.py                      # Main Flask application
│   ├── .env                        # Environment variables (not committed)
│   ├── instance/                   # Instance-specific files
│   ├── migrations/                 # Database migrations
│   │   ├── versions/
│   │   └── env.py
│   ├── static/
│   │   ├── css/
│   │   │   └── dashboard.css       # Dashboard styles
│   │   ├── js/
│   │   │   └── dashboard.js        # Dashboard interactions
│   │   └── meditation/
│   │       ├── rain.mp3
│   │       ├── ocean.mp3
│   │       ├── forest.mp3
│   │       └── bells.mp3
│   ├── templates/
│   │   ├── index.html              # Landing page
│   │   ├── login.html              # Login page
│   │   ├── register.html           # Registration page
│   │   ├── dashboard.html          # Main dashboard
│   │   ├── about.html              # About page
│   │   └── faq.html                # FAQ page
│   └── test_*.py                   # Test files
├── relationship/                    # Future feature module
├── todo/                           # Future feature module
└── README.md                       # This file
```

---

## 🔌 API Integrations

### YouTube Data API v3
- **Purpose:** Fetch mental health-related videos
- **Endpoint:** `https://www.googleapis.com/youtube/v3/search`
- **Features:** Safe search, relevance ranking, embeddable videos

### Voiceflow API
- **Purpose:** AI-powered conversational support
- **Endpoint:** `https://general-runtime.voiceflow.com/state/user`
- **Features:** Context-aware responses, mental health guidance

### OpenStreetMap APIs
- **Nominatim:** Geocoding user locations
- **Overpass:** Finding healthcare facilities and therapists

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch**
   ```bash
   git checkout -b feature/AmazingFeature
   ```
3. **Commit your changes**
   ```bash
   git commit -m 'Add some AmazingFeature'
   ```
4. **Push to the branch**
   ```bash
   git push origin feature/AmazingFeature
   ```
5. **Open a Pull Request**

### Development Guidelines

- Follow PEP 8 style guide for Python code
- Write descriptive commit messages
- Test your changes thoroughly
- Update documentation as needed
- Ensure no sensitive data is committed

---

## 📄 License

This project is licensed under the MIT License - see the LICENSE file for details.

---

## ⚠️ Disclaimer

**IMPORTANT:** MindCare is a mental health support tool and is **NOT** a replacement for professional therapy or medical treatment. 

- **For emergencies:** Contact emergency services (911 in the US)
- **Crisis support:** 
  - National Suicide Prevention Lifeline: 988 or 1-800-273-8255
  - Crisis Text Line: Text HOME to 741741
  - International Association for Suicide Prevention: https://www.iasp.info/resources/Crisis_Centres/

If you're experiencing a mental health crisis or having thoughts of self-harm, please seek immediate professional help.

---

## 📞 Support

For questions, issues, or suggestions:

- **GitHub Issues:** [Create an issue](https://github.com/Dame121/MindCare/issues)
- **Discussions:** [Join the discussion](https://github.com/Dame121/MindCare/discussions)

---

<div align="center">

**Made with ❤️ for mental health awareness**

*Remember: It's okay to not be okay. Seeking help is a sign of strength.*

</div>
