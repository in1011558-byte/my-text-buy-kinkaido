from . import db, BaseModel

class Category(BaseModel):
    __tablename__ = 'categories'

    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(80), unique=True, nullable=False)

    textbooks = db.relationship('Textbook', backref='category', lazy=True)

    def __repr__(self):
        return f'<Category {self.name}>'

