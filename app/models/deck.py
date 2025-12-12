from datetime import datetime
from app import db


class Deck(db.Model):
    """Deck model for organizing flashcards into collections."""
    __tablename__ = 'decks'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.Text)
    category = db.Column(db.String(50))
    tags = db.Column(db.String(200))  # Comma-separated tags
    card_count = db.Column(db.Integer, default=0)
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    # Relationships
    flashcards = db.relationship('Flashcard', backref='deck', lazy='dynamic', cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Deck {self.name}>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'card_count': self.card_count,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
