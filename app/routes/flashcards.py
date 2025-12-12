from flask import Blueprint, render_template, request, redirect, url_for, flash
from app import db
from app.models import Flashcard, Deck

flashcards_bp = Blueprint('flashcards', __name__)


@flashcards_bp.route('/')
def list_flashcards():
    """List all flashcards with optional deck filter."""
    deck_id = request.args.get('deck_id', type=int)
    
    if deck_id:
        flashcards = Flashcard.query.filter_by(deck_id=deck_id).order_by(Flashcard.created_at.desc()).all()
        deck = Deck.query.get(deck_id)
    else:
        flashcards = Flashcard.query.order_by(Flashcard.created_at.desc()).all()
        deck = None
    
    decks = Deck.query.all()
    return render_template('flashcards/list.html', flashcards=flashcards, decks=decks, current_deck=deck)


@flashcards_bp.route('/create', methods=['GET', 'POST'])
def create_flashcard():
    """Create a new flashcard."""
    if request.method == 'POST':
        question = request.form.get('question', '').strip()
        answer = request.form.get('answer', '').strip()
        deck_id = request.form.get('deck_id', type=int)
        
        if not question or not answer:
            flash('Please enter both question and answer.', 'error')
            return redirect(url_for('flashcards.create_flashcard'))
        
        flashcard = Flashcard(question=question, answer=answer, deck_id=deck_id)
        db.session.add(flashcard)
        
        # Update deck card count
        if deck_id:
            deck = Deck.query.get(deck_id)
            if deck:
                deck.card_count = Flashcard.query.filter_by(deck_id=deck_id).count() + 1
        
        db.session.commit()
        flash('Flashcard created successfully!', 'success')
        return redirect(url_for('flashcards.list_flashcards'))
    
    decks = Deck.query.all()
    return render_template('flashcards/create.html', decks=decks)


@flashcards_bp.route('/<int:id>/edit', methods=['GET', 'POST'])
def edit_flashcard(id):
    """Edit an existing flashcard."""
    flashcard = Flashcard.query.get_or_404(id)
    
    if request.method == 'POST':
        flashcard.question = request.form.get('question', '').strip()
        flashcard.answer = request.form.get('answer', '').strip()
        flashcard.deck_id = request.form.get('deck_id', type=int)
        
        db.session.commit()
        flash('Flashcard updated successfully!', 'success')
        return redirect(url_for('flashcards.list_flashcards'))
    
    decks = Deck.query.all()
    return render_template('flashcards/edit.html', flashcard=flashcard, decks=decks)


@flashcards_bp.route('/<int:id>/delete', methods=['POST'])
def delete_flashcard(id):
    """Delete a flashcard."""
    flashcard = Flashcard.query.get_or_404(id)
    deck_id = flashcard.deck_id
    
    db.session.delete(flashcard)
    
    # Update deck card count
    if deck_id:
        deck = Deck.query.get(deck_id)
        if deck:
            deck.card_count = max(0, Flashcard.query.filter_by(deck_id=deck_id).count() - 1)
    
    db.session.commit()
    flash('Flashcard deleted successfully!', 'success')
    return redirect(url_for('flashcards.list_flashcards'))


@flashcards_bp.route('/decks')
def list_decks():
    """List all decks."""
    decks = Deck.query.order_by(Deck.created_at.desc()).all()
    return render_template('flashcards/decks.html', decks=decks)


@flashcards_bp.route('/decks/create', methods=['GET', 'POST'])
def create_deck():
    """Create a new deck."""
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        category = request.form.get('category', '').strip()
        tags = request.form.get('tags', '').strip()
        
        if not name:
            flash('Please enter a deck name.', 'error')
            return redirect(url_for('flashcards.create_deck'))
        
        deck = Deck(name=name, description=description, category=category, tags=tags)
        db.session.add(deck)
        db.session.commit()
        flash('Deck created successfully!', 'success')
        return redirect(url_for('flashcards.list_decks'))
    
    return render_template('flashcards/create_deck.html')


@flashcards_bp.route('/decks/<int:id>/delete', methods=['POST'])
def delete_deck(id):
    """Delete a deck and all its flashcards."""
    deck = Deck.query.get_or_404(id)
    db.session.delete(deck)
    db.session.commit()
    flash('Deck deleted successfully!', 'success')
    return redirect(url_for('flashcards.list_decks'))
