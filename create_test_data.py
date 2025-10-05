from app import create_app
from extensions import db
from models.school import School
from models.category import Category
from models.user import User

app = create_app()

with app.app_context():
    # テーブルを作成
    db.create_all()

    # テスト用学校を作成
    if not School.query.first():
        school = School(
            school_name='テスト高等学校',
            prefecture='東京都',
            city='渋谷区',
            address='渋谷1-1-1'
        )
        school.save()
        print('Test school created')
    else:
        school = School.query.first()

    # テスト用カテゴリを作成
    if not Category.query.first():
        category = Category(
            category_name='数学',
            description='数学の教科書'
        )
        category.save()
        print('Test category created')

    # テスト用ユーザーを作成 (school_idを既存の学校に紐付け)
    if not User.query.first():
        user = User(
            username='testuser',
            email='test@example.com',
            school_id=school.id, # 既存の学校のIDを使用
            is_admin=False
        )
        user.set_password('password')
        user.save()
        print('Test user created')

    print('Test data creation completed')
