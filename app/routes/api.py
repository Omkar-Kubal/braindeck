from flask import Blueprint, request, jsonify
from app import db
from app.models import Flashcard, Deck

api_bp = Blueprint('api', __name__)


@api_bp.route('/flashcards', methods=['GET'])
def get_flashcards():
    """Get all flashcards as JSON."""
    deck_id = request.args.get('deck_id', type=int)
    
    if deck_id:
        flashcards = Flashcard.query.filter_by(deck_id=deck_id).all()
    else:
        flashcards = Flashcard.query.all()
    
    return jsonify([card.to_dict() for card in flashcards])


@api_bp.route('/flashcards', methods=['POST'])
def create_flashcard():
    """Create a new flashcard via API."""
    data = request.get_json()
    
    if not data or not data.get('question') or not data.get('answer'):
        return jsonify({'error': 'Question and answer are required'}), 400
    
    flashcard = Flashcard(
        question=data['question'],
        answer=data['answer'],
        deck_id=data.get('deck_id')
    )
    db.session.add(flashcard)
    db.session.commit()
    
    return jsonify(flashcard.to_dict()), 201


@api_bp.route('/flashcards/<int:id>', methods=['GET'])
def get_flashcard(id):
    """Get a single flashcard by ID."""
    flashcard = Flashcard.query.get_or_404(id)
    return jsonify(flashcard.to_dict())


@api_bp.route('/flashcards/<int:id>', methods=['PUT'])
def update_flashcard(id):
    """Update a flashcard."""
    flashcard = Flashcard.query.get_or_404(id)
    data = request.get_json()
    
    if data.get('question'):
        flashcard.question = data['question']
    if data.get('answer'):
        flashcard.answer = data['answer']
    if 'deck_id' in data:
        flashcard.deck_id = data['deck_id']
    
    db.session.commit()
    return jsonify(flashcard.to_dict())


@api_bp.route('/flashcards/<int:id>', methods=['DELETE'])
def delete_flashcard(id):
    """Delete a flashcard."""
    flashcard = Flashcard.query.get_or_404(id)
    db.session.delete(flashcard)
    db.session.commit()
    return jsonify({'message': 'Flashcard deleted'})


@api_bp.route('/decks', methods=['GET'])
def get_decks():
    """Get all decks as JSON."""
    decks = Deck.query.all()
    return jsonify([deck.to_dict() for deck in decks])


@api_bp.route('/decks', methods=['POST'])
def create_deck():
    """Create a new deck via API."""
    data = request.get_json()
    
    if not data or not data.get('name'):
        return jsonify({'error': 'Deck name is required'}), 400
    
    deck = Deck(
        name=data['name'],
        description=data.get('description'),
        category=data.get('category'),
        tags=','.join(data.get('tags', [])) if isinstance(data.get('tags'), list) else data.get('tags')
    )
    db.session.add(deck)
    db.session.commit()
    
    return jsonify(deck.to_dict()), 201


@api_bp.route('/flashcards/random', methods=['GET'])
def get_random_flashcard():
    """Get a random flashcard."""
    import random
    
    deck_id = request.args.get('deck_id', type=int)
    
    if deck_id:
        cards = Flashcard.query.filter_by(deck_id=deck_id).all()
    else:
        cards = Flashcard.query.all()
    
    if not cards:
        return jsonify({'error': 'No flashcards available'}), 404
    
    card = random.choice(cards)
    return jsonify(card.to_dict())
