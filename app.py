import os
from flask import Flask, jsonify
from flask_cors import CORS
from extensions import db, migrate



# 設定のインポート
from config import config

def create_app(config_name=None):
    """アプリケーションファクトリ"""
    if config_name is None:
        config_name = os.environ.get("FLASK_CONFIG", "default")
    
    app = Flask(__name__)
    app.config.from_object(config[config_name])
    
    # 拡張機能の初期化
    db.init_app(app)
    migrate.init_app(app, db)

    # モデルのインポート
    from models.base_model import BaseModel
    from models.school import School
    from models.school_auth import SchoolAuth
    from models.user import User
    from models.category import Category
    from models.textbook import Textbook
    from models.cart import Cart
    from models.order import Order, OrderItem
    
    # JWT設定
    jwt = JWTManager(app)
    
    # JWT設定のカスタマイズ
    @jwt.expired_token_loader
    def expired_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": {
                "code": "TOKEN_EXPIRED",
                "message": "Token has expired"
            }
        }), 401
    
    @jwt.invalid_token_loader
    def invalid_token_callback(error):
        return jsonify({
            "error": {
                "code": "INVALID_TOKEN",
                "message": "Invalid token"
            }
        }), 401
    
    @jwt.unauthorized_loader
    def missing_token_callback(error):
        return jsonify({
            "error": {
                "code": "MISSING_TOKEN",
                "message": "Authentication token is required"
            }
        }), 401
    
    @jwt.needs_fresh_token_loader
    def token_not_fresh_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": {
                "code": "FRESH_TOKEN_REQUIRED",
                "message": "Fresh token required"
            }
        }), 401
    
    @jwt.revoked_token_loader
    def revoked_token_callback(jwt_header, jwt_payload):
        return jsonify({
            "error": {
                "code": "TOKEN_REVOKED",
                "message": "Token has been revoked"
            }
        }), 401
    
    @jwt.token_in_blocklist_loader
    def check_if_token_revoked(jwt_header, jwt_payload):
        """トークンがブラックリストされているかチェック"""
        from views.auth import blacklisted_tokens
        jti = jwt_payload["jti"]
        return jti in blacklisted_tokens
    
    # CORS設定
    CORS(app, origins=["http://localhost:3000", "http://localhost:5000"])
    

    
    # アップロードフォルダの作成
    if not os.path.exists(app.config["UPLOAD_FOLDER"]):
        os.makedirs(app.config["UPLOAD_FOLDER"])
    
    # ブループリントの登録
    from views.auth import auth_bp
    from views.school_auth import school_auth_bp
    from views.textbooks import textbooks_bp
    from views.orders import orders_bp
    from views.admin import admin_bp
    
    app.register_blueprint(auth_bp, url_prefix="/api/v1/auth")
    app.register_blueprint(school_auth_bp, url_prefix="/api/v1/school-auth")
    app.register_blueprint(textbooks_bp, url_prefix="/api/v1/textbooks")
    app.register_blueprint(orders_bp, url_prefix="/api/v1/orders")
    app.register_blueprint(admin_bp, url_prefix="/api/v1/admin")
    
    # エラーハンドラー
    @app.errorhandler(404)
    def not_found(error):
        return jsonify({
            "error": {
                "code": "NOT_FOUND",
                "message": "Resource not found"
            }
        }), 404
    
    @app.errorhandler(500)
    def internal_error(error):
        db.session.rollback()
        return jsonify({
            "error": {
                "code": "INTERNAL_ERROR",
                "message": "Internal server error"
            }
        }), 500
    
    @app.errorhandler(400)
    def bad_request(error):
        return jsonify({
            "error": {
                "code": "BAD_REQUEST",
                "message": "Bad request"
            }
        }), 400
    
    @app.errorhandler(403)
    def forbidden(error):
        return jsonify({
            "error": {
                "code": "FORBIDDEN",
                "message": "Forbidden"
            }
        }), 403
    
    # ヘルスチェックエンドポイント
    @app.route("/health")
    def health_check():
        return jsonify({
            "status": "healthy", 
            "message": "Textbook Management System API is running",
            "version": "1.0.0"
        })
    
    # API情報エンドポイント
    @app.route("/api/v1")
    def api_info():
        return jsonify({
            "name": "Textbook Management System API",
            "version": "1.0.0",
            "endpoints": {
                "auth": "/api/v1/auth",
                "textbooks": "/api/v1/textbooks",
                "orders": "/api/v1/orders",
                "admin": "/api/v1/admin"
            }
        })
    
    # データベース初期化コマンド
    @app.cli.command()
    def init_db():
        """データベースを初期化"""
        db.create_all()
        print("Database tables created.")
    
    @app.cli.command()
    def seed_db():
        """サンプルデータを投入"""
        seed_database()
        print("Database seeded with sample data.")
    
    return app


def seed_database():
    """サンプルデータの投入"""
    try:
        # 学校データ
        schools_data = [
            {
                "school_name": "東京高等学校",
                "prefecture": "東京都",
                "city": "渋谷区",
                "address": "渋谷区神南1-1-1",
                "phone": "03-1234-5678",
                "email": "info@tokyo-hs.ac.jp"
            },
            {
                "school_name": "大阪高等学校",
                "prefecture": "大阪府",
                "city": "大阪市",
                "address": "大阪市中央区難波1-1-1",
                "phone": "06-1234-5678",
                "email": "info@osaka-hs.ac.jp"
            },
            {
                "school_name": "名古屋高等学校",
                "prefecture": "愛知県",
                "city": "名古屋市",
                "address": "名古屋市中区栄1-1-1",
                "phone": "052-1234-5678",
                "email": "info@nagoya-hs.ac.jp"
            }
        ]
        
        schools = []
        for school_data in schools_data:
            if not School.query.filter_by(school_name=school_data["school_name"]).first():
                school = School(**school_data)
                school.save()
                schools.append(school)
        
        # カテゴリデータ
        categories_data = [
            {"category_name": "数学", "description": "数学関連の教科書"},
            {"category_name": "国語", "description": "国語・現代文・古典"},
            {"category_name": "英語", "description": "英語関連の教科書"},
            {"category_name": "理科", "description": "物理・化学・生物・地学"},
            {"category_name": "社会", "description": "日本史・世界史・地理・公民"},
            {"category_name": "情報", "description": "情報処理・プログラミング"}
        ]
        
        categories = []
        for cat_data in categories_data:
            if not Category.query.filter_by(category_name=cat_data["category_name"]).first():
                category = Category(**cat_data)
                category.save()
                categories.append(category)
        
        # 管理者ユーザー
        admin_data = {
            "school_id": schools[0].school_id if schools else 1,
            "username": "admin",
            "email": "admin@example.com",
            "first_name": "管理",
            "last_name": "太郎",
            "role": "admin"
        }
        
        if not User.find_by_email(admin_data["email"]):
            admin = User(**admin_data)
            admin.set_password("admin123")
            admin.save()
        
        # サンプル学生ユーザー
        students_data = [
            {
                "school_id": schools[0].school_id if schools else 1,
                "username": "student001",
                "email": "student001@example.com",
                "first_name": "太郎",
                "last_name": "田中",
                "student_id": "S2024001",
                "grade": "1年",
                "class_name": "A組",
                "role": "student"
            },
            {
                "school_id": schools[0].school_id if schools else 1,
                "username": "student002",
                "email": "student002@example.com",
                "first_name": "花子",
                "last_name": "佐藤",
                "student_id": "S2024002",
                "grade": "1年",
                "class_name": "B組",
                "role": "student"
            }
        ]
        
        for student_data in students_data:
            if not User.find_by_email(student_data["email"]):
                student = User(**student_data)
                student.set_password("student123")
                student.save()
        
        # サンプル教科書データ
        textbooks_data = [
            {
                "category_id": categories[0].category_id if categories else 1,  # 数学
                "title": "高校数学I",
                "price": 1200.00,
                "stock_quantity": 50,
                "grade_level": "1年",
                "subject": "数学I"
            },
            {
                "category_id": categories[0].category_id if categories else 1,  # 数学
                "title": "高校数学A",
                "price": 1300.00,
                "stock_quantity": 45,
                "grade_level": "1年",
                "subject": "数学A"
            },
            {
                "category_id": categories[1].category_id if categories else 2,  # 国語
                "title": "現代文B",
                "price": 1500.00,
                "stock_quantity": 30,
                "grade_level": "2年",
                "subject": "現代文"
            },
            {
                "category_id": categories[1].category_id if categories else 2,  # 国語
                "title": "古典B",
                "price": 1400.00,
                "stock_quantity": 25,
                "grade_level": "2年",
                "subject": "古典"
            },
            {
                "category_id": categories[2].category_id if categories else 3,  # 英語
                "title": "コミュニケーション英語I",
                "price": 1600.00,
                "stock_quantity": 40,
                "grade_level": "1年",
                "subject": "英語"
            },
            {
                "category_id": categories[3].category_id if categories else 4,  # 理科
                "title": "化学基礎",
                "price": 1800.00,
                "stock_quantity": 35,
                "grade_level": "1年",
                "subject": "化学"
            },
            {
                "category_id": categories[3].category_id if categories else 4,  # 理科
                "title": "物理基礎",
                "price": 1750.00,
                "stock_quantity": 20,
                "grade_level": "1年",
                "subject": "物理"
            },
            {
                "category_id": categories[4].category_id if categories else 5,  # 社会
                "title": "世界史A",
                "price": 1650.00,
                "stock_quantity": 28,
                "grade_level": "1年",
                "subject": "世界史"
            }
        ]
        
        for textbook_data in textbooks_data:
            if not Textbook.query.filter_by(title=textbook_data["title"]).first():
                textbook = Textbook(**textbook_data)
                textbook.save()
        
        print("Sample data inserted successfully!")
        
    except Exception as e:
        db.session.rollback()
        print(f"Error seeding database: {e}")
        raise


app = create_app()

