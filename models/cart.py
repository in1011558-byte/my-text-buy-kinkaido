from extensions import db
from models.base_model import BaseModel
from sqlalchemy.orm import validates
from decimal import Decimal

class Cart(BaseModel):
    """ショッピングカートモデル"""
    __tablename__ = 'carts'
    
    cart_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.textbook_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    added_at = db.Column(db.DateTime, default=db.func.current_timestamp(), nullable=False)
    
    # インデックス
    __table_args__ = (
        db.Index('idx_carts_user', 'user_id'),
        db.UniqueConstraint('user_id', 'textbook_id', name='unique_user_textbook'),
        db.CheckConstraint('quantity > 0', name='check_positive_quantity'),
    )
    
    def __repr__(self):
        return f'<Cart User:{self.user_id} Textbook:{self.textbook_id} Qty:{self.quantity}>'
    
    @validates('quantity')
    def validate_quantity(self, key, quantity):
        """数量のバリデーション"""
        if quantity is None or quantity <= 0:
            raise ValueError('Quantity must be a positive number')
        return quantity
    
    @property
    def subtotal(self):
        """小計を計算"""
        if self.textbook:
            return self.textbook.price * self.quantity
        return Decimal('0.00')
    
    @property
    def subtotal_formatted(self):
        """フォーマットされた小計"""
        return f"¥{self.subtotal:,.0f}"
    
    def can_fulfill(self):
        """注文可能かどうか（在庫チェック）"""
        return self.textbook and self.textbook.can_order(self.quantity)
    
    def to_dict(self):
        """辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'cart_id': self.cart_id,
            'user_id': self.user_id,
            'textbook_id': self.textbook_id,
            'textbook_title': self.textbook.title if self.textbook else None,
            'textbook_price': float(self.textbook.price) if self.textbook else 0,
            'textbook_image_url': self.textbook.image_url if self.textbook else None,
            'quantity': self.quantity,
            'subtotal': float(self.subtotal),
            'subtotal_formatted': self.subtotal_formatted,
            'can_fulfill': self.can_fulfill(),
            'added_at': self.added_at.isoformat() if self.added_at else None
        })
        return base_dict
    
    @classmethod
    def get_user_cart(cls, user_id):
        """ユーザーのカート内容を取得"""
        return cls.query.filter_by(user_id=user_id).join(
            cls.textbook
        ).filter_by(is_active=True).order_by(cls.added_at.desc()).all()
    
    @classmethod
    def get_cart_total(cls, user_id):
        """カートの合計金額を計算"""
        cart_items = cls.get_user_cart(user_id)
        total = sum(item.subtotal for item in cart_items)
        return total
    
    @classmethod
    def get_cart_item_count(cls, user_id):
        """カート内のアイテム数を取得"""
        return cls.query.filter_by(user_id=user_id).count()
    
    @classmethod
    def add_or_update_item(cls, user_id, textbook_id, quantity):
        """カートアイテムを追加または更新"""
        from models.textbook import Textbook
        
        # 教科書の存在と在庫をチェック
        textbook = Textbook.query.get(textbook_id)
        if not textbook or not textbook.is_active:
            raise ValueError("Textbook not found or not active")
        
        if not textbook.can_order(quantity):
            raise ValueError(f"Insufficient stock. Available: {textbook.stock_quantity}")
        
        # 既存のカートアイテムをチェック
        existing_item = cls.query.filter_by(
            user_id=user_id, 
            textbook_id=textbook_id
        ).first()
        
        if existing_item:
            # 既存アイテムの数量を更新
            new_quantity = existing_item.quantity + quantity
            if not textbook.can_order(new_quantity):
                raise ValueError(f"Total quantity exceeds stock. Available: {textbook.stock_quantity}")
            existing_item.quantity = new_quantity
            return existing_item.save()
        else:
            # 新しいアイテムを作成
            new_item = cls(
                user_id=user_id,
                textbook_id=textbook_id,
                quantity=quantity
            )
            return new_item.save()
    
    @classmethod
    def update_quantity(cls, cart_id, user_id, new_quantity):
        """カートアイテムの数量を更新"""
        cart_item = cls.query.filter_by(cart_id=cart_id, user_id=user_id).first()
        if not cart_item:
            raise ValueError("Cart item not found")
        
        if new_quantity <= 0:
            cart_item.delete()
            return None
        
        if not cart_item.textbook.can_order(new_quantity):
            raise ValueError(f"Insufficient stock. Available: {cart_item.textbook.stock_quantity}")
        
        cart_item.quantity = new_quantity
        return cart_item.save()
    
    @classmethod
    def remove_item(cls, cart_id, user_id):
        """カートからアイテムを削除"""
        cart_item = cls.query.filter_by(cart_id=cart_id, user_id=user_id).first()
        if cart_item:
            cart_item.delete()
            return True
        return False
    
    @classmethod
    def clear_user_cart(cls, user_id):
        """ユーザーのカートを空にする"""
        cls.query.filter_by(user_id=user_id).delete()
        db.session.commit()
    
    @classmethod
    def validate_cart_for_checkout(cls, user_id):
        """チェックアウト前のカート検証"""
        cart_items = cls.get_user_cart(user_id)
        errors = []
        
        if not cart_items:
            errors.append("Cart is empty")
            return False, errors
        
        for item in cart_items:
            if not item.can_fulfill():
                errors.append(f"Insufficient stock for {item.textbook.title}")
        
        return len(errors) == 0, errors

