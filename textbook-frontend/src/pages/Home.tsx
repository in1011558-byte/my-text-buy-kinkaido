import React from 'react';
import { Link } from 'react-router-dom';
import { useAuth } from '../contexts/AuthContext';
import { BookOpen, ShoppingCart, Package, TrendingUp } from 'lucide-react';

const Home: React.FC = () => {
  const { user } = useAuth();

  return (
    <div className="px-4 py-8">
      <div className="text-center mb-12">
        <h1 className="text-4xl font-bold text-gray-900 mb-4">
          教科書販売・管理システムへようこそ
        </h1>
        <p className="text-xl text-gray-600 mb-8">
          {user?.first_name} {user?.last_name}さん、お疲れ様です
        </p>
      </div>

      <div className="grid grid-cols-1 md:grid-cols-2 lg:grid-cols-3 gap-6 mb-12">
        <Link
          to="/textbooks"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200"
        >
          <div className="flex items-center mb-4">
            <BookOpen className="h-8 w-8 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">教科書を探す</h2>
          </div>
          <p className="text-gray-600">
            必要な教科書を検索して、カートに追加できます。
          </p>
        </Link>

        <Link
          to="/cart"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200"
        >
          <div className="flex items-center mb-4">
            <ShoppingCart className="h-8 w-8 text-green-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">カートを確認</h2>
          </div>
          <p className="text-gray-600">
            選択した教科書を確認して、注文を確定できます。
          </p>
        </Link>

        <Link
          to="/orders"
          className="bg-white rounded-lg shadow-md p-6 hover:shadow-lg transition-shadow duration-200"
        >
          <div className="flex items-center mb-4">
            <Package className="h-8 w-8 text-purple-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">注文履歴</h2>
          </div>
          <p className="text-gray-600">
            過去の注文履歴を確認できます。
          </p>
        </Link>
      </div>

      {user?.role === 'admin' && (
        <div className="bg-blue-50 rounded-lg p-6">
          <div className="flex items-center mb-4">
            <TrendingUp className="h-8 w-8 text-blue-600 mr-3" />
            <h2 className="text-xl font-semibold text-gray-900">管理者機能</h2>
          </div>
          <p className="text-gray-600 mb-4">
            管理者として、システム全体の管理を行えます。
          </p>
          <Link
            to="/admin"
            className="inline-flex items-center px-4 py-2 border border-transparent text-sm font-medium rounded-md text-white bg-blue-600 hover:bg-blue-700"
          >
            管理画面へ
          </Link>
        </div>
      )}
    </div>
  );
};

export default Home;
