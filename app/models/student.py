from datetime import datetime
from app import db


class Student(db.Model):
    """Student model for tracking users and their progress."""
    __tablename__ = 'students'
    
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    roll_no = db.Column(db.String(20), unique=True, nullable=False)
    student_class = db.Column(db.String(20), nullable=False)
    email = db.Column(db.String(120))
    created_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    # Relationships
    test_results = db.relationship('TestResult', backref='student', lazy='dynamic')
    
    def __repr__(self):
        return f'<Student {self.name} ({self.roll_no})>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'name': self.name,
            'roll_no': self.roll_no,
            'student_class': self.student_class,
            'email': self.email,
            'total_tests': self.test_results.count(),
            'created_at': self.created_at.isoformat() if self.created_at else None
        }


class TestResult(db.Model):
    """Test result model for tracking student performance."""
    __tablename__ = 'test_results'
    
    id = db.Column(db.Integer, primary_key=True)
    student_id = db.Column(db.Integer, db.ForeignKey('students.id'), nullable=False)
    deck_id = db.Column(db.Integer, db.ForeignKey('decks.id'))
    total_questions = db.Column(db.Integer, nullable=False)
    correct_answers = db.Column(db.Integer, nullable=False)
    wrong_answers = db.Column(db.Integer, nullable=False)
    score_percentage = db.Column(db.Float, nullable=False)
    time_taken_seconds = db.Column(db.Integer)
    completed_at = db.Column(db.DateTime, default=datetime.utcnow)
    
    def __repr__(self):
        return f'<TestResult {self.id}: {self.score_percentage}%>'
    
    def to_dict(self):
        return {
            'id': self.id,
            'student_id': self.student_id,
            'deck_id': self.deck_id,
            'total_questions': self.total_questions,
            'correct_answers': self.correct_answers,
            'wrong_answers': self.wrong_answers,
            'score_percentage': self.score_percentage,
            'time_taken_seconds': self.time_taken_seconds,
            'completed_at': self.completed_at.isoformat() if self.completed_at else None
        }
