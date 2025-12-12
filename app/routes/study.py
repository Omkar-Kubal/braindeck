from flask import Blueprint, render_template, request, redirect, url_for, flash, session, jsonify
from datetime import datetime
from app import db
from app.models import Flashcard, Deck, Student, TestResult
import random
import re

study_bp = Blueprint('study', __name__)


@study_bp.route('/')
def study_home():
    """Study mode selection page."""
    decks = Deck.query.all()
    total_cards = Flashcard.query.count()
    due_cards = Flashcard.query.filter(
        (Flashcard.next_review <= datetime.utcnow()) | (Flashcard.next_review.is_(None))
    ).count()
    
    return render_template('study/index.html', 
                         decks=decks, 
                         total_cards=total_cards,
                         due_cards=due_cards)


@study_bp.route('/session')
def study_session():
    """Start a study session with random cards."""
    deck_id = request.args.get('deck_id', type=int)
    
    if deck_id:
        cards = Flashcard.query.filter_by(deck_id=deck_id).all()
        deck = Deck.query.get(deck_id)
    else:
        cards = Flashcard.query.all()
        deck = None
    
    if not cards:
        flash('No flashcards available. Add some cards first!', 'warning')
        return redirect(url_for('study.study_home'))
    
    # Shuffle cards
    random.shuffle(cards)
    
    # Store card IDs in session
    session['study_cards'] = [c.id for c in cards]
    session['study_index'] = 0
    session['study_correct'] = 0
    session['study_wrong'] = 0
    
    return redirect(url_for('study.study_card'))


@study_bp.route('/card')
def study_card():
    """Display current study card."""
    if 'study_cards' not in session or not session['study_cards']:
        return redirect(url_for('study.study_home'))
    
    index = session.get('study_index', 0)
    card_ids = session['study_cards']
    
    if index >= len(card_ids):
        # Study session complete
        return redirect(url_for('study.study_complete'))
    
    card = Flashcard.query.get(card_ids[index])
    if not card:
        session['study_index'] = index + 1
        return redirect(url_for('study.study_card'))
    
    return render_template('study/card.html', 
                         card=card, 
                         current=index + 1, 
                         total=len(card_ids),
                         correct=session.get('study_correct', 0),
                         wrong=session.get('study_wrong', 0))


@study_bp.route('/answer', methods=['POST'])
def submit_answer():
    """Submit answer and update spaced repetition."""
    if 'study_cards' not in session:
        return redirect(url_for('study.study_home'))
    
    card_id = request.form.get('card_id', type=int)
    quality = request.form.get('quality', type=int, default=3)  # 0-5 scale
    
    card = Flashcard.query.get(card_id)
    if card:
        card.update_spaced_repetition(quality)
        db.session.commit()
        
        if quality >= 3:
            session['study_correct'] = session.get('study_correct', 0) + 1
        else:
            session['study_wrong'] = session.get('study_wrong', 0) + 1
    
    session['study_index'] = session.get('study_index', 0) + 1
    return redirect(url_for('study.study_card'))


@study_bp.route('/complete')
def study_complete():
    """Study session complete summary."""
    correct = session.get('study_correct', 0)
    wrong = session.get('study_wrong', 0)
    total = correct + wrong
    
    # Clear session
    session.pop('study_cards', None)
    session.pop('study_index', None)
    
    return render_template('study/complete.html', 
                         correct=correct, 
                         wrong=wrong, 
                         total=total)


@study_bp.route('/test', methods=['GET', 'POST'])
def start_test():
    """Start a graded test."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        roll_no = request.form.get('roll_no', '').strip()
        student_class = request.form.get('student_class', '').strip()
        deck_id = request.form.get('deck_id', type=int)
        
        # Validate roll number format
        if not re.match(r'^R\d+$', roll_no):
            flash('Roll number should start with "R" followed by digits (e.g., R123).', 'error')
            return redirect(url_for('study.start_test'))
        
        # Find or create student
        student = Student.query.filter_by(roll_no=roll_no).first()
        if not student:
            student = Student(name=name, roll_no=roll_no, student_class=student_class)
            db.session.add(student)
            db.session.commit()
        
        # Get cards for test
        if deck_id:
            cards = Flashcard.query.filter_by(deck_id=deck_id).all()
        else:
            cards = Flashcard.query.all()
        
        if not cards:
            flash('No flashcards available for testing.', 'warning')
            return redirect(url_for('study.start_test'))
        
        session['test_student_id'] = student.id
        session['test_deck_id'] = deck_id
        session['test_cards'] = [c.id for c in cards]
        session['test_answers'] = {}
        session['test_start_time'] = datetime.utcnow().isoformat()
        
        return redirect(url_for('study.test_questions'))
    
    decks = Deck.query.all()
    return render_template('study/test_start.html', decks=decks)


@study_bp.route('/test/questions', methods=['GET', 'POST'])
def test_questions():
    """Display all test questions."""
    if 'test_cards' not in session:
        return redirect(url_for('study.start_test'))
    
    if request.method == 'POST':
        # Collect all answers
        answers = {}
        for key, value in request.form.items():
            if key.startswith('answer_'):
                card_id = int(key.replace('answer_', ''))
                answers[card_id] = value.strip()
        
        session['test_answers'] = answers
        return redirect(url_for('study.test_results'))
    
    card_ids = session['test_cards']
    cards = Flashcard.query.filter(Flashcard.id.in_(card_ids)).all()
    
    return render_template('study/test_questions.html', cards=cards)


@study_bp.route('/test/results')
def test_results():
    """Display test results and save to database."""
    if 'test_cards' not in session or 'test_answers' not in session:
        return redirect(url_for('study.start_test'))
    
    card_ids = session['test_cards']
    answers = session['test_answers']
    student_id = session.get('test_student_id')
    deck_id = session.get('test_deck_id')
    start_time = session.get('test_start_time')
    
    cards = Flashcard.query.filter(Flashcard.id.in_(card_ids)).all()
    
    correct = 0
    wrong = 0
    results = []
    
    for card in cards:
        student_answer = answers.get(card.id, '')
        is_correct = student_answer.lower() == card.answer.lower()
        
        if is_correct:
            correct += 1
        else:
            wrong += 1
        
        results.append({
            'question': card.question,
            'correct_answer': card.answer,
            'student_answer': student_answer,
            'is_correct': is_correct
        })
    
    total = len(cards)
    score = round((correct / total) * 100, 2) if total > 0 else 0
    
    # Calculate time taken
    time_taken = 0
    if start_time:
        start_dt = datetime.fromisoformat(start_time)
        time_taken = int((datetime.utcnow() - start_dt).total_seconds())
    
    # Save test result
    if student_id:
        test_result = TestResult(
            student_id=student_id,
            deck_id=deck_id,
            total_questions=total,
            correct_answers=correct,
            wrong_answers=wrong,
            score_percentage=score,
            time_taken_seconds=time_taken
        )
        db.session.add(test_result)
        db.session.commit()
    
    # Clear test session
    session.pop('test_cards', None)
    session.pop('test_answers', None)
    session.pop('test_student_id', None)
    session.pop('test_deck_id', None)
    session.pop('test_start_time', None)
    
    return render_template('study/test_results.html',
                         results=results,
                         correct=correct,
                         wrong=wrong,
                         total=total,
                         score=score,
                         time_taken=time_taken)


@study_bp.route('/reports')
def reports():
    """View all test reports."""
    test_results = TestResult.query.order_by(TestResult.completed_at.desc()).all()
    return render_template('study/reports.html', results=test_results)
