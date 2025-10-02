from . import db, BaseModel

class School(BaseModel):
    __tablename__ = 'schools'

    id = db.Column(db.Integer, primary_key=True)
    school_name = db.Column(db.String(120), unique=True, nullable=False)
    prefecture = db.Column(db.String(50), nullable=False)
    city = db.Column(db.String(50), nullable=False)
    address = db.Column(db.String(200))
    phone = db.Column(db.String(20))
    email = db.Column(db.String(120))

    def __repr__(self):
        return f'<School {self.school_name}>'

