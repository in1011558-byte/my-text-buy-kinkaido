from datetime import datetime
from extensions import db

class BaseModel(db.Model):
    """全モデルの基底クラス"""
    __abstract__ = True
    
    created_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    updated_at = db.Column(db.DateTime, default=datetime.utcnow, onupdate=datetime.utcnow, nullable=False)
    
    def save(self):
        """レコードを保存"""
        db.session.add(self)
        db.session.commit()
        return self
    
    def delete(self):
        """レコードを削除"""
        db.session.delete(self)
        db.session.commit()
    
    def to_dict(self):
        """辞書形式に変換（基本実装）"""
        return {
            'created_at': self.created_at.isoformat() if self.created_at else None,
            'updated_at': self.updated_at.isoformat() if self.updated_at else None
        }
