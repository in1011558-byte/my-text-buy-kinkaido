from . import db, BaseModel
from sqlalchemy.orm import validates
from decimal import Decimal
from datetime import datetime

class Order(BaseModel):
    """注文モデル"""
    __tablename__ = 'orders'
    
    order_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    user_id = db.Column(db.Integer, db.ForeignKey('users.user_id'), nullable=False)
    total_amount = db.Column(db.Numeric(10, 2), nullable=False)
    status = db.Column(db.Enum('pending', 'processing', 'shipped', 'delivered', 'cancelled', 
                               name='order_status'), default='pending', nullable=False)
    payment_method = db.Column(db.String(50))
    shipping_address = db.Column(db.Text)
    notes = db.Column(db.Text)
    ordered_at = db.Column(db.DateTime, default=datetime.utcnow, nullable=False)
    
    # リレーション
    order_items = db.relationship('OrderItem', backref='order', lazy='dynamic', cascade='all, delete-orphan')
    
    # インデックス
    __table_args__ = (
        db.Index('idx_orders_user', 'user_id'),
        db.Index('idx_orders_status', 'status'),
        db.Index('idx_orders_date', 'ordered_at'),
    )
    
    def __repr__(self):
        return f'<Order #{self.order_id} User:{self.user_id} Status:{self.status}>'
    
    @validates('total_amount')
    def validate_total_amount(self, key, amount):
        """合計金額のバリデーション"""
        if amount is None or amount < 0:
            raise ValueError('Total amount must be a positive number')
        return amount
    
    @validates('status')
    def validate_status(self, key, status):
        """ステータスの変更バリデーション"""
        valid_transitions = {
            'pending': ['processing', 'cancelled'],
            'processing': ['shipped', 'cancelled'],
            'shipped': ['delivered'],
            'delivered': [],  # 最終状態
            'cancelled': []   # 最終状態
        }
        
        if hasattr(self, 'status') and self.status:
            current_status = self.status
            if current_status in valid_transitions and status not in valid_transitions[current_status]:
                raise ValueError(f"Invalid status transition from {current_status} to {status}")
        
        return status
    
    @property
    def order_number(self):
        """注文番号（表示用）"""
        return f"#{self.order_id:06d}"
    
    @property
    def total_amount_formatted(self):
        """フォーマットされた合計金額"""
        return f"¥{self.total_amount:,.0f}"
    
    @property
    def items_count(self):
        """注文アイテム数"""
        return self.order_items.count()
    
    @property
    def can_cancel(self):
        """キャンセル可能かどうか"""
        return self.status in ['pending', 'processing']
    
    @property
    def is_completed(self):
        """完了状態かどうか"""
        return self.status in ['delivered', 'cancelled']
    
    def calculate_total(self):
        """合計金額を再計算"""
        total = sum(item.total_price for item in self.order_items)
        self.total_amount = total
        return total
    
    def cancel_order(self, reason=None):
        """注文をキャンセル"""
        if not self.can_cancel:
            raise ValueError(f"Cannot cancel order with status: {self.status}")
        
        # 在庫を復元
        for item in self.order_items:
            item.textbook.increase_stock(item.quantity)
        
        self.status = 'cancelled'
        if reason:
            self.notes = (self.notes or '') + f"\nCancellation reason: {reason}"
        
        return self.save()
    
    def update_status(self, new_status, notes=None):
        """ステータスを更新"""
        self.status = new_status
        if notes:
            self.notes = (self.notes or '') + f"\nStatus update: {notes}"
        return self.save()
    
    def to_dict(self):
        """辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'order_id': self.order_id,
            'order_number': self.order_number,
            'user_id': self.user_id,
            'user_name': self.user.full_name if self.user else None,
            'user_email': self.user.email if self.user else None,
            'total_amount': float(self.total_amount),
            'total_amount_formatted': self.total_amount_formatted,
            'status': self.status,
            'payment_method': self.payment_method,
            'shipping_address': self.shipping_address,
            'notes': self.notes,
            'ordered_at': self.ordered_at.isoformat() if self.ordered_at else None,
            'items_count': self.items_count,
            'can_cancel': self.can_cancel,
            'is_completed': self.is_completed
        })
        return base_dict
    
    def to_dict_with_items(self):
        """アイテム詳細を含む辞書形式"""
        order_dict = self.to_dict()
        order_dict['items'] = [item.to_dict() for item in self.order_items]
        return order_dict
    
    @classmethod
    def create_from_cart(cls, user_id, payment_method=None, shipping_address=None, notes=None):
        """カートから注文を作成"""
        from .cart import Cart
        
        # カートの検証
        cart_items = Cart.get_user_cart(user_id)
        is_valid, errors = Cart.validate_cart_for_checkout(user_id)
        
        if not is_valid:
            raise ValueError(f"Cart validation failed: {', '.join(errors)}")
        
        # トランザクション開始
        try:
            # 注文作成
            order = cls(
                user_id=user_id,
                total_amount=Cart.get_cart_total(user_id),
                payment_method=payment_method,
                shipping_address=shipping_address,
                notes=notes
            )
            order.save()
            
            # 注文アイテム作成と在庫更新
            for cart_item in cart_items:
                order_item = OrderItem(
                    order_id=order.order_id,
                    textbook_id=cart_item.textbook_id,
                    quantity=cart_item.quantity,
                    unit_price=cart_item.textbook.price,
                    total_price=cart_item.subtotal
                )
                order_item.save()
                
                # 在庫減算
                cart_item.textbook.reduce_stock(cart_item.quantity)
            
            # カートをクリア
            Cart.clear_user_cart(user_id)
            
            return order
            
        except Exception as e:
            db.session.rollback()
            raise e
    
    @classmethod
    def get_user_orders(cls, user_id, status=None):
        """ユーザーの注文履歴を取得"""
        orders = cls.query.filter_by(user_id=user_id)
        
        if status:
            orders = orders.filter_by(status=status)
        
        return orders.order_by(cls.ordered_at.desc()).all()
    
    @classmethod
    def search(cls, user_id=None, status=None, start_date=None, end_date=None):
        """注文検索"""
        orders = cls.query
        
        if user_id:
            orders = orders.filter_by(user_id=user_id)
        
        if status:
            orders = orders.filter_by(status=status)
        
        if start_date:
            orders = orders.filter(cls.ordered_at >= start_date)
        
        if end_date:
            orders = orders.filter(cls.ordered_at <= end_date)
        
        return orders.order_by(cls.ordered_at.desc())


class OrderItem(BaseModel):
    """注文詳細モデル"""
    __tablename__ = 'order_items'
    
    order_item_id = db.Column(db.Integer, primary_key=True, autoincrement=True)
    order_id = db.Column(db.Integer, db.ForeignKey('orders.order_id'), nullable=False)
    textbook_id = db.Column(db.Integer, db.ForeignKey('textbooks.textbook_id'), nullable=False)
    quantity = db.Column(db.Integer, nullable=False)
    unit_price = db.Column(db.Numeric(10, 2), nullable=False)
    total_price = db.Column(db.Numeric(10, 2), nullable=False)
    
    # インデックス
    __table_args__ = (
        db.Index('idx_order_items_order', 'order_id'),
        db.CheckConstraint('quantity > 0', name='check_positive_quantity'),
        db.CheckConstraint('unit_price >= 0', name='check_positive_unit_price'),
        db.CheckConstraint('total_price >= 0', name='check_positive_total_price'),
    )
    
    def __repr__(self):
        return f'<OrderItem Order:{self.order_id} Textbook:{self.textbook_id} Qty:{self.quantity}>'
    
    @validates('quantity', 'unit_price', 'total_price')
    def validate_positive_values(self, key, value):
        """正数のバリデーション"""
        if value is None or value <= 0:
            raise ValueError(f'{key} must be a positive number')
        return value
    
    def calculate_total(self):
        """合計価格を計算"""
        self.total_price = self.unit_price * self.quantity
        return self.total_price
    
    @property
    def unit_price_formatted(self):
        """フォーマットされた単価"""
        return f"¥{self.unit_price:,.0f}"
    
    @property
    def total_price_formatted(self):
        """フォーマットされた合計価格"""
        return f"¥{self.total_price:,.0f}"
    
    def to_dict(self):
        """辞書形式に変換"""
        base_dict = super().to_dict()
        base_dict.update({
            'order_item_id': self.order_item_id,
            'order_id': self.order_id,
            'textbook_id': self.textbook_id,
            'textbook_title': self.textbook.title if self.textbook else None,
            'textbook_image_url': self.textbook.image_url if self.textbook else None,
            'quantity': self.quantity,
            'unit_price': float(self.unit_price),
            'unit_price_formatted': self.unit_price_formatted,
            'total_price': float(self.total_price),
            'total_price_formatted': self.total_price_formatted
        })
        return base_dict

