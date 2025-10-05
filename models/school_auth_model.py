from . import db, BaseModel
from werkzeug.security import generate_password_hash, check_password_hash
from sqlalchemy.orm import validates

class SchoolAuth(BaseModel):
    """学校認証情報モデル（学校ごとの共通ログイン）"""
    __tablename__ = 'school_auths'
    
    auth_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    school_id = db.Column(db.Integer, db.ForeignKey('schools.school_id'), nullable=False, unique=True)
    login_id = db.Column(db.String(50), nullable=False, unique=True)
    password_hash = db.Column(db.String(255), nullable=False)
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # リレーション
    school = db.relationship('School', backref='auth', uselist=False)
    
    def __repr__(self):
        return f'<SchoolAuth {self.login_id}>'
    
    @validates('login_id')
    def validate_login_id(self, key, login_id):
        """ログインIDのバリデーション"""
        if not login_id or len(login_id) < 4:
            raise ValueError('Login ID must be at least 4 characters long')
        if len(login_id) > 50:
            raise ValueError('Login ID is too long')
        return login_id
    
    def set_password(self, password):
        """パスワードをハッシュ化して設定"""
        if len(password) < 6:
            raise ValueError('Password must be at least 6 characters long')
        self.password_hash = generate_password_hash(password)
    
    def check_password(self, password):
        """パスワードの検証"""
        return check_password_hash(self.password_hash, password)
    
    def to_dict(self):
        """辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'auth_id': self.auth_id,
            'school_id': self.school_id,
            'school_name': self.school.school_name if self.school else None,
            'login_id': self.login_id,
            'is_active': self.is_active
        })
        return base_dict
    
    @classmethod
    def find_by_login_id(cls, login_id):
        """ログインIDで検索"""
        return cls.query.filter_by(login_id=login_id).first()
    
    @classmethod
    def create_for_school(cls, school_id, login_id, password):
        """学校用の認証情報を作成"""
        auth = cls(school_id=school_id, login_id=login_id)
        auth.set_password(password)
        return auth.save()