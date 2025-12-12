#!/usr/bin/env python
"""
FlashMaster - AI-Powered Flashcard Application
Entry point for running the Flask development server.
"""
import os
from app import create_app

# Determine environment
env = os.environ.get('FLASK_ENV', 'development')
app = create_app(env)

if __name__ == '__main__':
    print("""
    ╔═══════════════════════════════════════════════════════════╗
    ║                                                           ║
    ║   🎓 FlashMaster - AI-Powered Learning                   ║
    ║                                                           ║
    ║   Open your browser and go to:                           ║
    ║   http://127.0.0.1:5000                                  ║
    ║                                                           ║
    ║   Press Ctrl+C to stop the server                        ║
    ║                                                           ║
    ╚═══════════════════════════════════════════════════════════╝
    """)
    app.run(debug=True, host='127.0.0.1', port=5000)
