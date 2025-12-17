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
    """List all decks with hierarchical structure."""
    parent_id = request.args.get('parent_id', type=int)
    
    if parent_id:
        # Show sub-decks of a parent
        parent_deck = Deck.query.get(parent_id)
        decks = Deck.query.filter_by(parent_id=parent_id).order_by(Deck.name).all()
        breadcrumb = parent_deck.get_breadcrumb() if parent_deck else []
    else:
        # Show root-level decks only
        decks = Deck.query.filter_by(parent_id=None).order_by(Deck.name).all()
        parent_deck = None
        breadcrumb = []
    
    return render_template('flashcards/decks.html', 
                         decks=decks, 
                         parent_deck=parent_deck,
                         breadcrumb=breadcrumb)


@flashcards_bp.route('/decks/create', methods=['GET', 'POST'])
def create_deck():
    """Create a new deck or folder."""
    parent_id = request.args.get('parent_id', type=int)
    
    if request.method == 'POST':
        name = request.form.get('name', '').strip()
        description = request.form.get('description', '').strip()
        is_folder = request.form.get('is_folder') == 'on'
        form_parent_id = request.form.get('parent_id', type=int)
        
        if not name:
            flash('Please enter a deck name.', 'error')
            return redirect(url_for('flashcards.create_deck', parent_id=parent_id))
        
        deck = Deck(
            name=name,
            description=description,
            parent_id=form_parent_id or parent_id
        )
        
        db.session.add(deck)
        db.session.commit()
        
        deck_type = 'folder' if is_folder else 'deck'
        flash(f'{deck_type.capitalize()} "{name}" created successfully!', 'success')
        
        # Return to the parent folder or root
        if deck.parent_id:
            return redirect(url_for('flashcards.list_decks', parent_id=deck.parent_id))
        return redirect(url_for('flashcards.list_decks'))
    
    # Get parent deck for breadcrumb
    parent_deck = Deck.query.get(parent_id) if parent_id else None
    breadcrumb = parent_deck.get_breadcrumb() if parent_deck else []
    
    return render_template('flashcards/create_deck.html', 
                         parent_deck=parent_deck,
                         parent_id=parent_id,
                         breadcrumb=breadcrumb)


@flashcards_bp.route('/decks/<int:deck_id>/delete', methods=['POST'])
def delete_deck(deck_id):
    """Delete a deck and all its flashcards and sub-decks."""
    deck = Deck.query.get_or_404(deck_id)
    parent_id = deck.parent_id
    
    # Delete will cascade to flashcards and children
    db.session.delete(deck)
    db.session.commit()
    flash('Deck deleted successfully!', 'success')
    
    # Return to parent or root
    if parent_id:
        return redirect(url_for('flashcards.list_decks', parent_id=parent_id))
    return redirect(url_for('flashcards.list_decks'))
