from extensions import db
from models.base_model import BaseModel
from sqlalchemy.orm import validates
from decimal import Decimal

class Textbook(BaseModel):
    """教科書モデル"""
    __tablename__ = 'textbooks'
    
    textbook_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    category_id = db.Column(db.Integer, db.ForeignKey('categories.category_id'), nullable=False)
    title = db.Column(db.String(255), nullable=False)
    price = db.Column(db.Numeric(10, 2), nullable=False)
    stock_quantity = db.Column(db.Integer, default=0, nullable=False)
    grade_level = db.Column(db.String(20))
    subject = db.Column(db.String(100))
    image_url = db.Column(db.String(500))
    is_active = db.Column(db.Boolean, default=True, nullable=False)
    
    # リレーション
    cart_items = db.relationship('Cart', backref='textbook', lazy='dynamic')
    order_items = db.relationship('OrderItem', backref='textbook', lazy='dynamic')
    
    # インデックス
    __table_args__ = (
        db.Index('idx_textbooks_category', 'category_id'),
        db.Index('idx_textbooks_grade_subject', 'grade_level', 'subject'),
        db.Index('idx_textbooks_active', 'is_active'),
        db.Index('idx_textbooks_stock', 'stock_quantity'),
    )
    
    def __repr__(self):
        return f'<Textbook {self.title}>'
    
    @validates('price')
    def validate_price(self, key, price):
        """価格のバリデーション"""
        if price is None or price < 0:
            raise ValueError('Price must be a positive number')
        return price
    
    @validates('stock_quantity')
    def validate_stock_quantity(self, key, quantity):
        """在庫数のバリデーション"""
        if quantity is None or quantity < 0:
            raise ValueError('Stock quantity must be a non-negative number')
        return quantity
    
    @validates('title')
    def validate_title(self, key, title):
        """タイトルのバリデーション"""
        if not title or len(title.strip()) == 0:
            raise ValueError('Title cannot be empty')
        return title.strip()
    
    @property
    def is_in_stock(self):
        """在庫があるかどうか"""
        return self.stock_quantity > 0
    
    @property
    def is_low_stock(self, threshold=5):
        """在庫が少ないかどうか（デフォルトは5冊以下）"""
        return 0 < self.stock_quantity <= threshold
    
    @property
    def price_formatted(self):
        """フォーマットされた価格"""
        return f"¥{self.price:,.0f}"
    
    def can_order(self, quantity):
        """指定数量の注文が可能かどうか"""
        return self.is_active and self.stock_quantity >= quantity
    
    def reduce_stock(self, quantity):
        """在庫を減らす"""
        if not self.can_order(quantity):
            raise ValueError(f"Insufficient stock for {self.title}")
        self.stock_quantity -= quantity
        return self
    
    def increase_stock(self, quantity):
        """在庫を増やす（キャンセル時など）"""
        if quantity < 0:
            raise ValueError("Quantity must be positive")
        self.stock_quantity += quantity
        return self
    
    def to_dict(self):
        """辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'textbook_id': self.textbook_id,
            'category_id': self.category_id,
            'category_name': self.category.category_name if self.category else None,
            'title': self.title,
            'price': float(self.price),
            'price_formatted': self.price_formatted,
            'stock_quantity': self.stock_quantity,
            'grade_level': self.grade_level,
            'subject': self.subject,
            'image_url': self.image_url,
            'is_active': self.is_active,
            'is_in_stock': self.is_in_stock,
            'is_low_stock': self.is_low_stock
        })
        return base_dict
    
    @classmethod
    def get_available_textbooks(cls):
        """利用可能な教科書（有効かつ在庫あり）を取得"""
        return cls.query.filter_by(is_active=True).filter(cls.stock_quantity > 0).all()
    
    @classmethod
    def get_low_stock_textbooks(cls, threshold=5):
        """在庫が少ない教科書を取得"""
        return cls.query.filter_by(is_active=True).filter(
            cls.stock_quantity > 0,
            cls.stock_quantity <= threshold
        ).all()
    
    @classmethod
    def get_out_of_stock_textbooks(cls):
        """在庫切れ教科書を取得"""
        return cls.query.filter_by(is_active=True, stock_quantity=0).all()
    
    @classmethod
    def search(cls, query=None, category_id=None, grade_level=None, 
              subject=None, in_stock_only=False, min_price=None, max_price=None):
        """教科書検索"""
        textbooks = cls.query.filter_by(is_active=True)
        
        if query:
            textbooks = textbooks.filter(
                db.or_(
                    cls.title.contains(query),
                    cls.subject.contains(query)
                )
            )
        
        if category_id:
            textbooks = textbooks.filter_by(category_id=category_id)
        
        if grade_level:
            textbooks = textbooks.filter_by(grade_level=grade_level)
        
        if subject:
            textbooks = textbooks.filter_by(subject=subject)
        
        if in_stock_only:
            textbooks = textbooks.filter(cls.stock_quantity > 0)
        
        if min_price:
            textbooks = textbooks.filter(cls.price >= min_price)
        
        if max_price:
            textbooks = textbooks.filter(cls.price <= max_price)
        
        return textbooks.order_by(cls.title)
    
    @classmethod
    def get_popular_textbooks(cls, limit=10):
        """人気教科書を取得（注文数順）"""
        from models.order import OrderItem
        
        return db.session.query(cls).join(OrderItem).group_by(cls.textbook_id)\
            .order_by(db.func.sum(OrderItem.quantity).desc()).limit(limit).all()
