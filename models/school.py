from extensions import db
from models.base_model import BaseModel

class School(BaseModel):
    __tablename__ = 'schools'
    
    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(200), nullable=False)
    prefecture = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(100), nullable=False)
    address = db.Column(db.Text, nullable=False)
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))
    
    # Relationships（back_populatesを使用）
    textbooks = db.relationship('Textbook', back_populates='school')
    users = db.relationship('User', back_populates='school')
    
    def to_dict(self):
        return {
            'id': self.id,
            'school_name': self.school_name,
            'prefecture': self.prefecture,
            'city': self.city,
            'address': self.address,
            'phone': self.phone,
            'email': self.email,
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
