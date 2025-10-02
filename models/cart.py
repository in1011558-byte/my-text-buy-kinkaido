from extensions import db
from models.base_model import BaseModel

class Cart(BaseModel ):
    __tablename__ = 'carts'
    
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.id'), nullable=False)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False, default=1)
    
    # Relationships
    user = db.relationship('User', backref='cart_items')
    textbook = db.relationship('Textbook', backref='cart_items')
    
    def to_dict(self):
        return {
            'id': self.id,
            'user_id': self.user_id,
            'textbook_id': self.textbook_id,
            'quantity': self.quantity,
            'textbook': self.textbook.to_dict() if self.textbook else None,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
