# 🧠 BrainDeck

**AI-Powered Flashcard Learning Platform**

BrainDeck is a modern web application that revolutionizes studying through intelligent flashcard generation and spaced repetition learning. Transform any educational content into interactive flashcards using AI, and study smarter with personalized learning algorithms.

![BrainDeck Dashboard](https://img.shields.io/badge/Status-Beta-yellow) ![Python](https://img.shields.io/badge/Python-3.12-blue) ![Flask](https://img.shields.io/badge/Flask-3.0-green) ![TailwindCSS](https://img.shields.io/badge/TailwindCSS-3.0-blueviolet)

---

## ✨ Features

### 🤖 AI-Powered Content Generation
- **Text-to-Flashcards**: Paste educational text and instantly generate comprehensive flashcards
- **PDF Upload**: Extract and convert PDF content into structured study materials
- **Wikipedia Integration**: Search any topic and automatically create flashcards from Wikipedia articles
- Intelligent question generation with context-aware AI

### 📚 Smart Learning System
- **Spaced Repetition Algorithm**: Scientifically-proven method that optimizes review timing for maximum retention
- **AI Answer Validation**: Natural language processing evaluates answers semantically, not just exact matches
- **Progress Tracking**: Visual analytics showing mastery levels, study streaks, and performance trends
- **Adaptive Difficulty**: System learns from your performance and adjusts content accordingly

### 🎯 Study Tools
- **Interactive Study Sessions**: Flip-card interface with self-assessment (Easy/Medium/Hard)
- **Multiple-Choice Tests**: Auto-generated quizzes with detailed performance analytics
- **Multi-Deck Management**: Organize flashcards by topic with deck-specific statistics
- **Session Analytics**: Track time spent, cards reviewed, and improvement over time

### 🎨 Modern Interface
- Beautiful dark-mode UI with premium aesthetics
- Fully responsive design (works on desktop, tablet, and mobile)
- Smooth animations and micro-interactions
- Intuitive navigation with real-time feedback

---

## 🚀 Getting Started

### Prerequisites

- Python 3.12 or higher
- pip package manager
- Git

### Installation

1. **Clone the repository**
   ```bash
   git clone https://github.com/yourusername/BrainDeck.git
   cd BrainDeck
   ```

2. **Create a virtual environment**
   ```bash
   python -m venv venv
   
   # Windows
   venv\Scripts\activate
   
   # macOS/Linux
   source venv/bin/activate
   ```

3. **Install dependencies**
   ```bash
   pip install -r requirements.txt
   ```

4. **Set up environment variables**
   
   Create a `.env` file in the root directory:
   ```env
   SECRET_KEY=your-secret-key-here
   GEMINI_API_KEY=your-google-gemini-api-key
   ```
   
   > **Get your Gemini API key**: Visit [Google AI Studio](https://makersuite.google.com/app/apikey)

5. **Initialize the database**
   ```bash
   python
   >>> from app import create_app, db
   >>> app = create_app()
   >>> with app.app_context():
   ...     db.create_all()
   >>> exit()
   ```

6. **Run the application**
   ```bash
   python run.py
   ```

7. **Open your browser**
   
   Navigate to `http://localhost:5000`

---

## 📖 Usage

### Creating Your First Deck

1. **Sign up** for a new account or **log in**
2. Navigate to **Dashboard**
3. Click **"Create New Deck"**
4. Name your deck (e.g., "Biology 101")
5. Start adding flashcards manually or use AI generation

### Generating Flashcards with AI

#### Method 1: Paste Text
1. Go to **AI Generate** from the sidebar
2. Select **"Paste Text"** tab
3. Paste your study material (notes, textbook excerpts, etc.)
4. Set the number of flashcards to generate
5. Click **"Generate Flashcards"**

#### Method 2: Upload PDF
1. Go to **AI Generate**
2. Select **"Upload PDF"** tab
3. Drag and drop or browse for your PDF file
4. AI extracts text and generates flashcards automatically

#### Method 3: Topic Search
1. Go to **AI Generate**
2. Select **"Topic Search"** tab
3. Enter a topic (e.g., "Photosynthesis")
4. AI fetches Wikipedia content and creates flashcards

### Studying with Spaced Repetition

1. Navigate to **Study** section
2. Select a deck to study
3. Click **"Start Study Session"**
4. Review each flashcard:
   - Read the question
   - Think of your answer
   - Click to reveal the correct answer
   - Rate yourself: **Easy**, **Medium**, or **Hard**
5. The algorithm schedules when you'll see each card next

### Taking Tests

1. Go to **Study** → **Take Test**
2. Select a deck
3. Choose number of questions
4. Complete the multiple-choice test
5. View detailed results and explanations

---

## 🛠️ Technology Stack

### Backend
- **Framework**: Flask (Python)
- **Database**: SQLite with SQLAlchemy ORM
- **Authentication**: Flask-Login
- **AI**: Google Gemini API

### Frontend
- **CSS Framework**: TailwindCSS
- **Icons**: Material Symbols
- **Templating**: Jinja2
- **JavaScript**: Vanilla JS

### Architecture
```
BrainDeck/
├── app/
│   ├── models/          # Database models (User, Deck, Flashcard, etc.)
│   ├── routes/          # API endpoints (auth, flashcards, study, AI)
│   ├── services/        # Business logic (AI generation, spaced repetition)
│   └── templates/       # HTML templates with Jinja2
├── instance/            # SQLite database (gitignored)
├── venv/               # Virtual environment (gitignored)
├── .env                # Environment variables (gitignored)
├── requirements.txt    # Python dependencies
└── run.py             # Application entry point
```

---

## 🎯 Key Concepts

### Spaced Repetition
BrainDeck implements a spaced repetition algorithm that schedules card reviews at optimal intervals:
- Cards you find **Easy** are shown less frequently
- Cards you find **Hard** are reviewed more often
- Review timing is scientifically optimized for long-term retention

### AI Answer Validation
Unlike traditional flashcard apps that only accept exact matches, BrainDeck uses natural language processing to:
- Understand synonyms and paraphrasing
- Accept answers with different wording but same meaning
- Provide intelligent feedback on partial answers

---

## 🔐 Environment Variables

| Variable | Description | Required |
|----------|-------------|----------|
| `SECRET_KEY` | Flask secret key for session security | ✅ |
| `GEMINI_API_KEY` | Google Gemini API key for AI features | ✅ |
| `DATABASE_URL` | Database connection string | ❌ (defaults to SQLite) |
| `FLASK_ENV` | Environment (development/production) | ❌ (defaults to production) |

---

## 📝 API Endpoints

### Authentication
- `POST /auth/signup` - Create new account
- `POST /auth/login` - User login
- `GET /auth/logout` - User logout

### Flashcards
- `GET /flashcards/decks` - List all decks
- `POST /flashcards/deck/create` - Create new deck
- `POST /flashcards/create` - Add flashcard to deck
- `PUT /flashcards/edit/<id>` - Edit flashcard
- `DELETE /flashcards/delete/<id>` - Delete flashcard

### AI Generation
- `POST /ai/generate` - Generate flashcards from text
- `POST /ai/upload_pdf` - Extract text from PDF
- `POST /ai/search_topic` - Search Wikipedia and generate cards

### Study
- `GET /study/session/<deck_id>` - Start study session
- `POST /study/rate` - Rate flashcard difficulty
- `GET /study/test/<deck_id>` - Generate multiple-choice test

---

## 🤝 Contributing

Contributions are welcome! Here's how you can help:

1. **Fork the repository**
2. **Create a feature branch** (`git checkout -b feature/AmazingFeature`)
3. **Commit your changes** (`git commit -m 'Add some AmazingFeature'`)
4. **Push to the branch** (`git push origin feature/AmazingFeature`)
5. **Open a Pull Request**

### Development Guidelines
- Follow PEP 8 style guide for Python code
- Use meaningful variable and function names
- Add comments for complex logic
- Test thoroughly before submitting PR

---

## 🐛 Known Issues

- PDF extraction may not work perfectly with scanned documents (OCR not implemented)
- Wikipedia search returns only the first article result
- Mobile UI optimizations ongoing

---

## 🗺️ Roadmap

### Upcoming Features
- [ ] Collaborative decks (share with friends)
- [ ] Mobile native apps (iOS/Android)
- [ ] Audio/image flashcard support
- [ ] Gamification (badges, achievements, leaderboards)
- [ ] Study groups and social learning
- [ ] Advanced analytics with ML insights
- [ ] Offline mode support
- [ ] Export/import deck functionality

---

## 📄 License

This project is licensed under the MIT License - see the [LICENSE](LICENSE) file for details.

---

## 🙏 Acknowledgments

- **Google Gemini AI** for powering intelligent flashcard generation
- **Flask** for the robust web framework
- **TailwindCSS** for the beautiful UI components
- **SQLAlchemy** for seamless database interactions

---

## 📧 Contact

**Developer**: Your Name  
**Email**: your.email@example.com  
**GitHub**: [@yourusername](https://github.com/yourusername)  
**LinkedIn**: [Your LinkedIn](https://linkedin.com/in/yourprofile)

---

## 🌟 Star this repository if you find it helpful!

Made with ❤️ and ☕ by passionate developers who believe learning should be smarter, not harder.
