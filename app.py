from flask import Flask, jsonify, request
from flask_cors import CORS
from flask_migrate import Migrate
import os
import csv
from io import StringIO

from config import config
from models import db, User, School, Book, Order, OrderItem
from auth import generate_jwt_token, verify_jwt_token, login_required, admin_required

def create_app(config_name=None):
    app = Flask(__name__)
    
    # 設定の読み込み
    config_name = config_name or os.environ.get('FLASK_ENV', 'default')
    app.config.from_object(config[config_name])
    
    # CORS設定
    CORS(app, supports_credentials=True, origins=[
        "http://localhost:3000",
        "https://whimsical-parfait-d0937e.netlify.app",
        "https://frontend-6xqpzm.manus.space",
        "https://textbook-vbtu3b.manus.space"
    ])
    
    # データベース初期化
    db.init_app(app)
    migrate = Migrate(app, db)
    
    # 認証関連のエンドポイント
    @app.route('/api/auth/register', methods=['POST'])
    def register():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        username = data.get('username', email.split('@')[0])
        school_id = data.get('school_id')
        
        if not email or not password:
            return jsonify({'message': 'メールアドレスとパスワードは必須です'}), 400
        
        if User.query.filter_by(email=email).first():
            return jsonify({'message': 'このメールアドレスは既に登録されています'}), 409
        
        user = User(
            email=email,
            username=username,
            school_id=school_id
        )
        user.set_password(password)
        
        db.session.add(user)
        db.session.commit()
        
        return jsonify({'message': 'ユーザー登録が完了しました'}), 201
    
    @app.route('/api/auth/login', methods=['POST'])
    def login():
        data = request.get_json()
        email = data.get('email')
        password = data.get('password')
        
        user = User.query.filter_by(email=email).first()
        if not user or not user.check_password(password):
            return jsonify({'message': '無効な認証情報です'}), 401
        
        token = generate_jwt_token(user.id, user.is_admin)
        response = jsonify({
            'message': 'ログイン成功',
            'isAdmin': user.is_admin,
            'username': user.username
        })
        response.set_cookie('token', token, httponly=True, samesite='Lax', secure=True)
        return response, 200
    
    @app.route('/api/auth/logout', methods=['POST'])
    def logout():
        response = jsonify({'message': 'ログアウト成功'})
        response.set_cookie('token', '', expires=0, httponly=True, samesite='Lax', secure=True)
        return response, 200
    
    @app.route('/api/auth/check', methods=['GET'])
    def check_auth():
        payload = verify_jwt_token()
        if payload:
            user = User.query.get(payload['sub'])
            if user:
                return jsonify({
                    'isAuthenticated': True,
                    'isAdmin': user.is_admin,
                    'username': user.username
                }), 200
        return jsonify({'isAuthenticated': False}), 401
    
    # ユーザープロフィール関連
    @app.route('/api/users/profile', methods=['GET'])
    @login_required
    def get_profile():
        user = User.query.get(request.current_user_id)
        if not user:
            return jsonify({'message': 'ユーザーが見つかりません'}), 404
        return jsonify(user.to_dict()), 200
    
    @app.route('/api/users/profile', methods=['PUT'])
    @login_required
    def update_profile():
        user = User.query.get(request.current_user_id)
        if not user:
            return jsonify({'message': 'ユーザーが見つかりません'}), 404
        
        data = request.get_json()
        user.username = data.get('username', user.username)
        user.school_id = data.get('school_id', user.school_id)
        
        db.session.commit()
        return jsonify({'message': 'プロフィールが更新されました'}), 200
    
    # 教科書関連のエンドポイント
    @app.route('/api/books', methods=['GET'])
    def get_books():
        books = Book.query.all()
        return jsonify([book.to_dict() for book in books]), 200
    
    @app.route('/api/books/<int:book_id>', methods=['GET'])
    def get_book(book_id):
        book = Book.query.get_or_404(book_id)
        return jsonify(book.to_dict()), 200
    
    @app.route('/api/books', methods=['POST'])
    @admin_required
    def add_book():
        data = request.get_json()
        book = Book(
            title=data.get('title'),
            price=data.get('price'),
            stock=data.get('stock', 0)
        )
        db.session.add(book)
        db.session.commit()
        return jsonify(book.to_dict()), 201
    
    @app.route('/api/books/<int:book_id>', methods=['PUT'])
    @admin_required
    def update_book(book_id):
        book = Book.query.get_or_404(book_id)
        data = request.get_json()
        
        book.title = data.get('title', book.title)
        book.price = data.get('price', book.price)
        book.stock = data.get('stock', book.stock)
        
        db.session.commit()
        return jsonify(book.to_dict()), 200
    
    @app.route('/api/books/<int:book_id>', methods=['DELETE'])
    @admin_required
    def delete_book(book_id):
        book = Book.query.get_or_404(book_id)
        db.session.delete(book)
        db.session.commit()
        return jsonify({'message': '書籍が削除されました'}), 200
    
    # カート機能（セッションベース）
    @app.route('/api/cart', methods=['GET'])
    @login_required
    def get_cart():
        # 簡単な実装として、セッションベースのカートを使用
        # 実際のプロダクションでは、データベースに保存することを推奨
        cart = request.cookies.get('cart', '[]')
        import json
        try:
            cart_items = json.loads(cart)
            return jsonify(cart_items), 200
        except:
            return jsonify([]), 200
    
    @app.route('/api/cart/add', methods=['POST'])
    @login_required
    def add_to_cart():
        data = request.get_json()
        book_id = data.get('book_id')
        quantity = data.get('quantity', 1)
        
        book = Book.query.get_or_404(book_id)
        if book.stock < quantity:
            return jsonify({'message': '在庫が不足しています'}), 400
        
        # カートの取得と更新
        cart = request.cookies.get('cart', '[]')
        import json
        try:
            cart_items = json.loads(cart)
        except:
            cart_items = []
        
        # 既存のアイテムを探す
        existing_item = next((item for item in cart_items if item['book_id'] == book_id), None)
        if existing_item:
            existing_item['quantity'] += quantity
        else:
            cart_items.append({
                'book_id': book_id,
                'quantity': quantity,
                'title': book.title,
                'price': book.price
            })
        
        response = jsonify(cart_items)
        response.set_cookie('cart', json.dumps(cart_items), httponly=True, samesite='Lax', secure=True)
        return response, 200
    
    @app.route('/api/cart/remove', methods=['POST'])
    @login_required
    def remove_from_cart():
        data = request.get_json()
        book_id = data.get('book_id')
        quantity = data.get('quantity', 1)
        
        cart = request.cookies.get('cart', '[]')
        import json
        try:
            cart_items = json.loads(cart)
        except:
            cart_items = []
        
        # アイテムを探して削除または数量を減らす
        for i, item in enumerate(cart_items):
            if item['book_id'] == book_id:
                if item['quantity'] <= quantity:
                    cart_items.pop(i)
                else:
                    item['quantity'] -= quantity
                break
        
        response = jsonify(cart_items)
        response.set_cookie('cart', json.dumps(cart_items), httponly=True, samesite='Lax', secure=True)
        return response, 200
    
    # 注文関連のエンドポイント
    @app.route('/api/orders', methods=['POST'])
    @login_required
    def create_order():
        cart = request.cookies.get('cart', '[]')
        import json
        try:
            cart_items = json.loads(cart)
        except:
            return jsonify({'message': 'カートが空です'}), 400
        
        if not cart_items:
            return jsonify({'message': 'カートが空です'}), 400
        
        # 注文の作成
        total_price = 0
        order = Order(user_id=request.current_user_id, total_price=0)
        db.session.add(order)
        db.session.flush()  # IDを取得するため
        
        # 注文アイテムの作成
        for item in cart_items:
            book = Book.query.get(item['book_id'])
            if not book or book.stock < item['quantity']:
                db.session.rollback()
                return jsonify({'message': f'書籍「{item["title"]}」の在庫が不足しています'}), 400
            
            order_item = OrderItem(
                order_id=order.id,
                book_id=item['book_id'],
                quantity=item['quantity'],
                price=book.price
            )
            db.session.add(order_item)
            
            # 在庫を減らす
            book.stock -= item['quantity']
            total_price += book.price * item['quantity']
        
        order.total_price = total_price
        db.session.commit()
        
        # カートをクリア
        response = jsonify({'message': '注文が完了しました', 'order_id': order.id})
        response.set_cookie('cart', '[]', httponly=True, samesite='Lax', secure=True)
        return response, 201
    
    @app.route('/api/orders', methods=['GET'])
    @login_required
    def get_orders():
        if request.current_user_is_admin:
            # 管理者は全ての注文を取得
            orders = Order.query.all()
        else:
            # 一般ユーザーは自分の注文のみ取得
            orders = Order.query.filter_by(user_id=request.current_user_id).all()
        
        return jsonify([order.to_dict() for order in orders]), 200
    
    @app.route('/api/orders/<int:order_id>', methods=['GET'])
    @login_required
    def get_order(order_id):
        order = Order.query.get_or_404(order_id)
        
        # 管理者でない場合は自分の注文のみアクセス可能
        if not request.current_user_is_admin and order.user_id != request.current_user_id:
            return jsonify({'message': 'アクセス権限がありません'}), 403
        
        return jsonify(order.to_dict()), 200
    
    @app.route('/api/orders/<int:order_id>/status', methods=['PUT'])
    @admin_required
    def update_order_status(order_id):
        order = Order.query.get_or_404(order_id)
        data = request.get_json()
        
        order.status = data.get('status', order.status)
        db.session.commit()
        
        return jsonify({'message': '注文ステータスが更新されました'}), 200
    
    # 学校管理のエンドポイント
    @app.route('/api/schools', methods=['GET'])
    def get_schools():
        schools = School.query.all()
        return jsonify([school.to_dict() for school in schools]), 200
    
    @app.route('/api/schools', methods=['POST'])
    @admin_required
    def add_school():
        data = request.get_json()
        
        if School.query.filter_by(name=data.get('name')).first():
            return jsonify({'message': 'この学校名は既に登録されています'}), 409
        
        school = School(name=data.get('name'))
        db.session.add(school)
        db.session.commit()
        
        return jsonify(school.to_dict()), 201
    
    @app.route('/api/schools/<int:school_id>', methods=['PUT'])
    @admin_required
    def update_school(school_id):
        school = School.query.get_or_404(school_id)
        data = request.get_json()
        
        school.name = data.get('name', school.name)
        db.session.commit()
        
        return jsonify(school.to_dict()), 200
    
    @app.route('/api/schools/<int:school_id>', methods=['DELETE'])
    @admin_required
    def delete_school(school_id):
        school = School.query.get_or_404(school_id)
        db.session.delete(school)
        db.session.commit()
        
        return jsonify({'message': '学校が削除されました'}), 200
    
    # レポート機能のエンドポイント
    @app.route('/api/reports/sales', methods=['GET'])
    @admin_required
    def get_sales_report():
        # 販売実績の集計
        from sqlalchemy import func
        
        total_sales = db.session.query(func.sum(Order.total_price)).scalar() or 0
        
        book_sales = db.session.query(
            Book.id,
            Book.title,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
        ).join(OrderItem).group_by(Book.id, Book.title).all()
        
        book_sales_data = [
            {
                'book_id': sale.id,
                'title': sale.title,
                'total_quantity': sale.total_quantity,
                'total_revenue': sale.total_revenue
            }
            for sale in book_sales
        ]
        
        return jsonify({
            'total_sales': total_sales,
            'book_sales': book_sales_data
        }), 200
    
    @app.route('/api/reports/inventory', methods=['GET'])
    @admin_required
    def get_inventory_report():
        books = Book.query.all()
        inventory_data = [
            {
                'book_id': book.id,
                'title': book.title,
                'current_stock': book.stock
            }
            for book in books
        ]
        
        return jsonify(inventory_data), 200
    
    @app.route('/api/reports/sales/export/csv', methods=['GET'])
    @admin_required
    def export_sales_csv():
        from sqlalchemy import func
        
        book_sales = db.session.query(
            Book.id,
            Book.title,
            func.sum(OrderItem.quantity).label('total_quantity'),
            func.sum(OrderItem.quantity * OrderItem.price).label('total_revenue')
        ).join(OrderItem).group_by(Book.id, Book.title).all()
        
        output = StringIO()
        writer = csv.writer(output)
        writer.writerow(['書籍ID', 'タイトル', '販売数量', '売上金額'])
        
        for sale in book_sales:
            writer.writerow([sale.id, sale.title, sale.total_quantity, sale.total_revenue])
        
        output.seek(0)
        
        from flask import Response
        return Response(
            output.getvalue(),
            mimetype='text/csv',
            headers={'Content-Disposition': 'attachment; filename=sales_report.csv'}
        )
    
    return app

if __name__ == '__main__':
    app = create_app()
    with app.app_context():
        db.create_all()
        
        # 初期データの作成（開発用）
        if not School.query.first():
            school = School(name='サンプル学校')
            db.session.add(school)
            
            admin_user = User(
                email='admin@example.com',
                username='管理者',
                is_admin=True,
                school_id=1
            )
            admin_user.set_password('admin123')
            db.session.add(admin_user)
            
            # サンプル書籍
            books = [
                Book(title='Python入門', price=3000, stock=10),
                Book(title='JavaScript基礎', price=2500, stock=5),
                Book(title='Webデザイン', price=3500, stock=8)
            ]
            for book in books:
                db.session.add(book)
            
            db.session.commit()
    
    app.run(debug=True, host='0.0.0.0', port=int(os.environ.get('PORT', 5000)))
