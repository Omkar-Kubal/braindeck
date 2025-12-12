from flask import Blueprint, render_template
from app.models import Flashcard, Deck

main_bp = Blueprint('main', __name__)


@main_bp.route('/')
def index():
    """Homepage with dashboard overview."""
    total_cards = Flashcard.query.count()
    total_decks = Deck.query.count()
    recent_cards = Flashcard.query.order_by(Flashcard.created_at.desc()).limit(5).all()
    
    return render_template('index.html', 
                         total_cards=total_cards,
                         total_decks=total_decks,
                         recent_cards=recent_cards)
