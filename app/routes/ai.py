"""AI Routes for flashcard generation and answer evaluation."""

import os
import requests
from flask import Blueprint, render_template, request, jsonify, flash, redirect, url_for, current_app
from werkzeug.utils import secure_filename
from app import db
from app.models import Flashcard, Deck
from app.services.ai_service import FlashcardGenerator
from app.services.evaluation_service import AnswerEvaluator

ai_bp = Blueprint('ai', __name__, url_prefix='/ai')

ALLOWED_EXTENSIONS = {'pdf'}
MAX_FILE_SIZE = 10 * 1024 * 1024  # 10MB


def allowed_file(filename):
    return '.' in filename and filename.rsplit('.', 1)[1].lower() in ALLOWED_EXTENSIONS


@ai_bp.route('/generate')
def generate():
    """Display the AI flashcard generation page."""
    decks = Deck.query.order_by(Deck.name).all()
    return render_template('ai/generate.html', decks=decks)


@ai_bp.route('/search-topic', methods=['POST'])
def search_topic():
    """Search Wikipedia for a topic and return summary."""
    try:
        data = request.get_json()
        topic = data.get('topic', '').strip()
        
        if not topic:
            return jsonify({'error': 'Topic is required'}), 400
        
        # Search Wikipedia API
        search_url = f'https://en.wikipedia.org/api/rest_v1/page/summary/{requests.utils.quote(topic)}'
        
        response = requests.get(search_url, timeout=10)
        
        if response.status_code == 404:
            return jsonify({'error': f'Topic "{topic}" not found on Wikipedia'}), 404
        
        response.raise_for_status()
        data = response.json()
        
        # Extract text content
        title = data.get('title', topic)
        extract = data.get('extract', '')
        
        if not extract:
            return jsonify({'error': 'No content found for this topic'}), 404
        
        # Limit to 5000 characters
        if len(extract) > 5000:
            extract = extract[:5000]
        
        return jsonify({
            'success': True,
            'title': title,
            'text': extract,
            'source': 'Wikipedia',
            'url': data.get('content_urls', {}).get('desktop', {}).get('page', '')
        })
        
    except requests.exceptions.Timeout:
        return jsonify({'error': 'Search timed out. Please try again.'}), 504
    except requests.exceptions.RequestException as e:
        current_app.logger.error(f"Wikipedia search failed: {e}")
        return jsonify({'error': 'Failed to search Wikipedia'}), 500
    except Exception as e:
        current_app.logger.error(f"Topic search error: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/upload-pdf', methods=['POST'])
def upload_pdf():
    """Extract text from uploaded PDF file."""
    try:
        if 'pdf_file' not in request.files:
            return jsonify({'error': 'No file uploaded'}), 400
        
        file = request.files['pdf_file']
        
        if file.filename == '':
            return jsonify({'error': 'No file selected'}), 400
        
        if not allowed_file(file.filename):
            return jsonify({'error': 'Only PDF files are allowed'}), 400
        
        # Check file size
        file.seek(0, 2)
        size = file.tell()
        file.seek(0)
        
        if size > MAX_FILE_SIZE:
            return jsonify({'error': f'File too large. Maximum size is {MAX_FILE_SIZE // (1024*1024)}MB'}), 400
        
        # Extract text from PDF
        try:
            from PyPDF2 import PdfReader
            
            reader = PdfReader(file)
            text_content = []
            
            for page in reader.pages:
                page_text = page.extract_text()
                if page_text:
                    text_content.append(page_text)
            
            extracted_text = '\n\n'.join(text_content)
            
            if not extracted_text.strip():
                return jsonify({'error': 'Could not extract text from PDF. The file may be image-based or encrypted.'}), 400
            
            # Trim to 5000 chars max
            if len(extracted_text) > 5000:
                extracted_text = extracted_text[:5000]
            
            return jsonify({
                'success': True,
                'text': extracted_text,
                'pages': len(reader.pages),
                'chars': len(extracted_text)
            })
            
        except Exception as e:
            current_app.logger.error(f"PDF extraction failed: {e}")
            return jsonify({'error': f'Failed to read PDF: {str(e)}'}), 500
    
    except Exception as e:
        current_app.logger.error(f"PDF upload failed: {e}")
        return jsonify({'error': str(e)}), 500


@ai_bp.route('/generate', methods=['POST'])
def generate_flashcards():
    """Generate flashcards from text using AI."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        text = data.get('text', '').strip()
        card_type = data.get('card_type', 'mixed')
        difficulty = data.get('difficulty', 'intermediate')
        quantity = int(data.get('quantity', 10))
        focus_area = data.get('focus_area', 'key_concepts')
        
        if not text:
            if request.is_json:
                return jsonify({'error': 'Source text is required'}), 400
            flash('Please provide source text to generate flashcards.', 'error')
            return redirect(url_for('ai.generate'))
        
        generator = FlashcardGenerator()
        flashcards = generator.generate_flashcards(
            text=text,
            card_type=card_type,
            difficulty=difficulty,
            quantity=quantity,
            focus_area=focus_area
        )
        
        if request.is_json:
            return jsonify({
                'success': True,
                'flashcards': flashcards,
                'count': len(flashcards)
            })
        
        # For form submission, store in session and redirect to preview
        from flask import session
        session['generated_flashcards'] = flashcards
        session['generation_params'] = {
            'card_type': card_type,
            'difficulty': difficulty,
            'quantity': quantity
        }
        return redirect(url_for('ai.preview'))
        
    except ValueError as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 400
        flash(str(e), 'error')
        return redirect(url_for('ai.generate'))
    except RuntimeError as e:
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Generation failed: {str(e)}', 'error')
        return redirect(url_for('ai.generate'))


@ai_bp.route('/preview')
def preview():
    """Preview generated flashcards before saving."""
    from flask import session
    flashcards = session.get('generated_flashcards', [])
    params = session.get('generation_params', {})
    decks = Deck.query.order_by(Deck.name).all()
    
    return render_template('ai/preview.html', 
                         flashcards=flashcards,
                         params=params,
                         decks=decks)


@ai_bp.route('/save', methods=['POST'])
def save_flashcards():
    """Save generated flashcards to a deck."""
    try:
        data = request.get_json() if request.is_json else request.form
        
        deck_id = data.get('deck_id')
        deck_name = data.get('deck_name')
        deck_name = deck_name.strip() if deck_name else ''
        flashcards_data = data.get('flashcards', [])
        
        # Get flashcards from session if not provided
        if not flashcards_data:
            from flask import session
            flashcards_data = session.get('generated_flashcards', [])
        
        if not flashcards_data:
            if request.is_json:
                return jsonify({'error': 'No flashcards to save'}), 400
            flash('No flashcards to save.', 'error')
            return redirect(url_for('ai.generate'))
        
        # Create new deck if needed
        if deck_name and not deck_id:
            deck = Deck(name=deck_name, description='AI-generated deck')
            db.session.add(deck)
            db.session.flush()
            deck_id = deck.id
        
        # Save flashcards
        saved_count = 0
        for card_data in flashcards_data:
            if isinstance(card_data, str):
                import json
                card_data = json.loads(card_data)
            
            flashcard = Flashcard(
                deck_id=deck_id,
                question=card_data.get('question', ''),
                answer=card_data.get('answer', ''),
                difficulty=_map_difficulty(card_data.get('difficulty', 'intermediate'))
            )
            db.session.add(flashcard)
            saved_count += 1
        
        # Update deck card count
        if deck_id:
            deck = Deck.query.get(deck_id)
            if deck:
                deck.card_count = Flashcard.query.filter_by(deck_id=deck_id).count()
        
        db.session.commit()
        
        # Clear session
        from flask import session
        session.pop('generated_flashcards', None)
        session.pop('generation_params', None)
        
        if request.is_json:
            return jsonify({
                'success': True,
                'saved_count': saved_count,
                'deck_id': deck_id
            })
        
        flash(f'Successfully saved {saved_count} flashcards!', 'success')
        return redirect(url_for('flashcards.list_flashcards', deck_id=deck_id))
        
    except Exception as e:
        db.session.rollback()
        if request.is_json:
            return jsonify({'error': str(e)}), 500
        flash(f'Failed to save flashcards: {str(e)}', 'error')
        return redirect(url_for('ai.preview'))


@ai_bp.route('/evaluate', methods=['POST'])
def evaluate_answer():
    """Evaluate a student's answer using AI."""
    try:
        data = request.get_json()
        
        question = data.get('question', '')
        expected_answer = data.get('expected_answer', '')
        student_answer = data.get('student_answer', '')
        card_type = data.get('card_type', 'qa')
        
        if not all([question, expected_answer, student_answer]):
            return jsonify({'error': 'Question, expected answer, and student answer are required'}), 400
        
        evaluator = AnswerEvaluator()
        result = evaluator.evaluate(
            question=question,
            expected_answer=expected_answer,
            student_answer=student_answer,
            card_type=card_type
        )
        
        return jsonify({
            'success': True,
            'score': result.score,
            'score_percentage': int(result.score * 100),
            'is_correct': result.is_correct,
            'partial_credit': result.partial_credit,
            'feedback': result.feedback,
            'model_answer': result.model_answer,
            'highlights': result.highlights
        })
        
    except Exception as e:
        return jsonify({'error': str(e)}), 500


def _map_difficulty(difficulty_str: str) -> int:
    """Map difficulty string to integer (1-5)."""
    mapping = {
        'beginner': 1,
        'easy': 2,
        'intermediate': 3,
        'advanced': 4,
        'expert': 5
    }
    return mapping.get(difficulty_str.lower(), 3)
