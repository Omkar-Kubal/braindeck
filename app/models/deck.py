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
    
    # User ownership (optional for backwards compatibility)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=True)
    
    # Hierarchical structure - sub-decks
    parent_id = db.Column(db.Integer, db.ForeignKey('decks.id'), nullable=True)
    
    # Relationships
    flashcards = db.relationship('Flashcard', backref='deck', lazy='dynamic', cascade='all, delete-orphan')
    
    # Self-referential relationship for sub-decks
    children = db.relationship('Deck', 
                              backref=db.backref('parent', remote_side=[id]),
                              lazy='dynamic',
                              cascade='all, delete-orphan')
    
    def __repr__(self):
        return f'<Deck {self.name}>'
    
    @property
    def is_folder(self):
        """Check if this deck is a folder (has children but no cards)."""
        return self.children.count() > 0 and self.card_count == 0
    
    @property
    def total_card_count(self):
        """Get total cards including all sub-decks recursively."""
        total = self.card_count
        for child in self.children:
            total += child.total_card_count
        return total
    
    @property
    def depth(self):
        """Get the depth level of this deck (0 = root)."""
        if self.parent_id is None:
            return 0
        return self.parent.depth + 1
    
    def get_breadcrumb(self):
        """Get the full path breadcrumb for this deck."""
        if self.parent_id is None:
            return [self]
        return self.parent.get_breadcrumb() + [self]
    
    def to_dict(self, include_children=False, include_parent=False):
        data = {
            'id': self.id,
            'name': self.name,
            'description': self.description,
            'category': self.category,
            'tags': self.tags.split(',') if self.tags else [],
            'card_count': self.card_count,
            'total_card_count': self.total_card_count,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'is_folder': self.is_folder,
            'depth': self.depth,
            'parent_id': self.parent_id
        }
        
        if include_children:
            data['children'] = [child.to_dict() for child in self.children]
        
        if include_parent and self.parent:
            data['parent'] = {
                'id': self.parent.id,
                'name': self.parent.name
            }
        
        return data
