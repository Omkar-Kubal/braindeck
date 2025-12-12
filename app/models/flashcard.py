from datetime import datetime
from app import db


class Flashcard(db.Model):
    """Flashcard model with spaced repetition support."""
    __tablename__ = 'flashcards'
    
    id = db.Column(db.Integer, primary_key=True)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=True)
    question = db.Column(db.Text, nullable=False)
    answer = db.Column(db.Text, nullable=False)
    
    # Spaced repetition fields
    difficulty = db.Column(db.Integer, default=1)  # 1-5 scale
    times_reviewed = db.Column(db.Integer, default=0)
    times_correct = db.Column(db.Integer, default=0)
    ease_factor = db.Column(db.Float, default=2.5)  # SM-2 ease factor
    interval_days = db.Column(db.Integer, default=1)
    next_review = db.Column(db.DateTime)
    last_reviewed = db.Column(db.DateTime)
    
    # Metadata
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow)
    
    def __repr__(self):
        return f'<Flashcard {self.id}: {self.question[:30]}...>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'deck_id': self.deck_id,
            'question': self.question,
            'answer': self.answer,
            'difficulty': self.difficulty,
            'times_reviewed': self.times_reviewed,
            'times_correct': self.times_correct,
            'accuracy': round(self.times_correct / self.times_reviewed * 100, 1) if self.times_reviewed > 0 else 0,
            'next_review': self.next_review.isoformat() if self.next_review else None,
            'created_at': self.created_at.isoformat() if self.created_at else None
        }
    
    def update_spaced_repetition(self, quality):
        """
        Update spaced repetition parameters using SM-2 algorithm.
        Quality: 0-5 (0=complete blackout, 5=perfect response)
        """
        self.times_reviewed += 1
        
        if quality >= 3:
            self.times_correct += 1
            
            # Calculate new ease factor
            self.ease_factor = max(1.3, self.ease_factor + (0.1 - (5 - quality) * (0.08 + (5 - quality) * 0.02)))
            
            # Calculate new interval
            if self.times_reviewed == 1:
                self.interval_days = 1
            elif self.times_reviewed == 2:
                self.interval_days = 6
            else:
                self.interval_days = round(self.interval_days * self.ease_factor)
        else:
            # Reset on failure
            self.interval_days = 1
            self.ease_factor = max(1.3, self.ease_factor - 0.2)
        
        self.last_reviewed = datetime.utcnow()
        from datetime import timedelta
        self.next_review = datetime.utcnow() + timedelta(days=self.interval_days)
