from . import db, BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

class SchoolAuth(BaseModel):
    """学校認証情報モデル（学校ごとの共通ログイン）"""
    __tablename__ = 'school_auths'

    id = db.Column(db.Integer, primary_key=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.id'), nullable=False)
    email = db.Column(db.String(120), unique=True, nullable=False)
    password_hash = db.Column(db.String(128), nullable=False)
    created_at = db.Column(db.DateTime, default=db.func.current_timestamp())
    updated_at = db.Column(db.DateTime, default=db.func.current_timestamp(), onupdate=db.func.current_timestamp())

    school = db.relationship('School', backref=db.backref('auths', lazy=True))

    def set_password(self, password):
        self.password_hash = generate_password_hash(password)

    def check_password(self, password):
        return check_password_hash(self.password_hash, password)

    @validates('email')
    def validate_email(self, key, email):
        if not email or '@' not in email:
            raise ValueError('有効なメールアドレスが必要です。')
        return email

    def __repr__(self):
        return f'<SchoolAuth {self.email}>'

