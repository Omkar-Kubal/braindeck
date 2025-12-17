from flask import Blueprint, render_template
from datetime import datetime
from app.models import Flashcard, Deck

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with dashboard overview."""
    total_cards = Flashcard.query.count()
    decks = Deck.query.order_by(Deck.updated_at.desc()).all()
    due_cards = Flashcard.query.filter(
        (Flashcard.next_review <= datetime.utcnow()) | (Flashcard.next_review.is_(None))
    ).count()
    
    return render_template('index.html', 
                         total_cards=total_cards,
                         decks=decks,
                         due_cards=due_cards)

