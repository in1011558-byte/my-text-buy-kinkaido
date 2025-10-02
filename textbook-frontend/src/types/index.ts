export interface User {
  user_id: number;
  username: string;
  email: string;
  first_name: string;
  last_name: string;
  role: 'student' | 'admin';
  school_id: number;
  student_id?: string;
  grade?: string;
  class_name?: string;
  is_active: boolean;
  created_at: string;
  updated_at: string;
}

export interface Textbook {
  id: number;
  title: string;
  author: string;
  isbn: string;
  price: number;
  stock_quantity: number;
  description?: string;
  image_url?: string;
  category_id: number;
  school_id: number;
  created_at: string;
  updated_at: string;
}

export interface Category {
  id: number;
  category_name: string;
  description?: string;
  created_at: string;
  updated_at: string;
}

export interface School {
  id: number;
  school_name: string;
  prefecture: string;
  city: string;
  address: string;
  phone?: string;
  email?: string;
  created_at: string;
  updated_at: string;
}

export interface CartItem {
  id: number;
  user_id: number;
  textbook_id: number;
  quantity: number;
  textbook: Textbook;
  created_at: string;
  updated_at: string;
}

export interface Order {
  id: number;
  user_id: number;
  order_date: string;
  total_amount: number;
  status: 'pending' | 'confirmed' | 'shipped' | 'delivered' | 'cancelled';
  shipping_address?: string;
  payment_method?: string;
  payment_status: string;
  order_items: OrderItem[];
  created_at: string;
  updated_at: string;
}

export interface OrderItem {
  id: number;
  order_id: number;
  textbook_id: number;
  quantity: number;
  unit_price: number;
  total_price: number;
  textbook: Textbook;
  created_at: string;
  updated_at: string;
}

export interface AuthContextType {
  user: User | null;
  login: (email: string, password: string) => Promise<void>;
  logout: () => void;
  register: (userData: RegisterData) => Promise<void>;
  loading: boolean;
}

export interface RegisterData {
  username: string;
  email: string;
  password: string;
  first_name: string;
  last_name: string;
  school_id: number;
  student_id?: string;
  grade?: string;
  class_name?: string;
}
