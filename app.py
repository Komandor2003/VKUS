from flask import Flask, flash, render_template, request, redirect, url_for, session
from flask_sqlalchemy import SQLAlchemy
from werkzeug.security import generate_password_hash, check_password_hash
import os

app = Flask(__name__)
app.secret_key = 'your_secret_key'
base_dir = os.path.abspath(os.path.dirname(__file__))
app.config['SQLALCHEMY_DATABASE_URI'] = 'sqlite:///' + os.path.join(base_dir, 'database.db')
app.config['SQLALCHEMY_TRACK_MODIFICATIONS'] = False

db = SQLAlchemy(app)

# ------------------ МОДЕЛИ ------------------ #
class User(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    username = db.Column(db.String(100), nullable=False)
    password = db.Column(db.String(200), nullable=False)
    orders = db.relationship('Order', backref='user', lazy=True)

class Product(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    name = db.Column(db.String(100), nullable=False)
    description = db.Column(db.String(200))
    price = db.Column(db.Float, nullable=False)
    image_url = db.Column(db.String(200))

class Order(db.Model):
    id = db.Column(db.Integer, primary_key=True)
    user_id = db.Column(db.Integer, db.ForeignKey('user.id'), nullable=False)
    total_price = db.Column(db.Float, nullable=False)
    items = db.Column(db.Text, nullable=False)  # возможно, это JSON или строка
    status = db.Column(db.String(50), default='В ожидании')

# ------------------ МАРШРУТЫ ------------------ #

@app.route('/')
def index():
    return render_template('index.html')

@app.route('/menu')
def menu():
    products = Product.query.all()
    return render_template('menu.html', products=products)

@app.route('/add_to_cart/<int:product_id>', methods=['POST'])
def add_to_cart(product_id):
    cart = session.get('cart', {})
    cart = dict(cart)
    product_id = str(product_id)

    if product_id in cart:
        cart[product_id] += 1
    else:
        cart[product_id] = 1

    session['cart'] = cart
    flash('Товар добавлен в корзину.')
    return redirect(url_for('menu'))

@app.route('/admin/update_order_status/<int:order_id>', methods=['POST'])
def update_order_status(order_id):
    new_status = request.form['status']
    order = Order.query.get(order_id)
    if order:
        order.status = new_status
        db.session.commit()
    return redirect(url_for('admin'))

@app.route('/my_orders')
def my_orders():
    user_id = session.get('user_id')
    orders = Order.query.filter_by(user_id=user_id).all()

    enriched_orders = []
    for order in orders:
        product_ids = [int(pid) for pid in order.items.split(',') if pid.strip()]
        products = Product.query.filter(Product.id.in_(product_ids)).all()
        enriched_orders.append({
            'id': order.id,
            'total_price': order.total_price,
            'products': products
        })

    return render_template('my_orders.html', orders=enriched_orders)




@app.route('/remove_from_cart/<int:product_id>', methods=['GET', 'POST'])
def remove_from_cart(product_id):
    cart = session.get('cart', {})
    product_id = str(product_id)

    if product_id in cart:
        cart.pop(product_id)

    session['cart'] = cart
    flash('Товар удален из корзины.')
    return redirect(url_for('cart'))

@app.route('/cart')
def cart():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    cart = session.get('cart', {})
    products = []
    total = 0

    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            product.quantity = quantity
            products.append(product)
            total += product.price * quantity

    return render_template('cart.html', products=products, total=total, cart=cart)

@app.route('/update_cart', methods=['POST'])
def update_cart():
    if not session.get('user_id'):
        return redirect(url_for('login'))

    cart = {}

    for key, value in request.form.items():
        if key.startswith('quantity_'):
            try:
                product_id = key.split('_')[1]
                quantity = int(value)
                if quantity > 0:
                    cart[product_id] = quantity
            except (IndexError, ValueError):
                continue  # если формат некорректный, пропустить

    session['cart'] = cart
    flash('Корзина обновлена.')
    return redirect(url_for('cart'))

@app.route('/cart/update_quantity/<int:product_id>/<action>', methods=['POST'])
def update_quantity(product_id, action):
    cart = session.get('cart', {})
    product_id_str = str(product_id)

    if product_id_str in cart:
        if action == 'increase':
            cart[product_id_str] += 1
        elif action == 'decrease' and cart[product_id_str] > 1:
            cart[product_id_str] -= 1
        elif action == 'decrease' and cart[product_id_str] == 1:
            cart.pop(product_id_str)  # можно сразу удалить товар, если 1 → 0

    session['cart'] = cart
    return redirect(url_for('cart'))



@app.route('/checkout')
def checkout():
    cart = session.get('cart', {})
    if not cart:
        return redirect(url_for('menu'))

    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))

    total = 0
    product_ids = []
    for product_id, quantity in cart.items():
        product = Product.query.get(int(product_id))
        if product:
            total += product.price * quantity
            product_ids.extend([product_id] * quantity)

    item_ids = ','.join(product_ids)
    order = Order(user_id=user_id, items=item_ids, total_price=total)
    db.session.add(order)
    db.session.commit()
    session.pop('cart', None)
    return render_template('checkout.html', order=order)

@app.route('/admin', methods=['GET', 'POST'])
def admin():
    if request.method == 'POST':
        name = request.form['name']
        description = request.form['description']
        price = request.form['price']
        image_url = request.form['image_url']
        product = Product(name=name, description=description, price=price, image_url=image_url)
        db.session.add(product)
        db.session.commit()
        return redirect(url_for('admin'))

    products = Product.query.all()
    orders = Order.query.order_by(Order.id.desc()).all()  # загрузим все заказы
    return render_template('admin.html', products=products, orders=orders)


@app.route('/register', methods=['GET', 'POST'])
def register():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        hashed_password = generate_password_hash(password)
        user = User(username=username, password=hashed_password)
        db.session.add(user)
        db.session.commit()
        return redirect(url_for('login'))
    return render_template('register.html')

@app.route('/login', methods=['GET', 'POST'])
def login():
    if request.method == 'POST':
        username = request.form['username']
        password = request.form['password']
        user = User.query.filter_by(username=username).first()
        if user and check_password_hash(user.password, password):
            session['user_id'] = user.id
            session['username'] = user.username
            session['is_admin'] = user.username == 'admin'
            return redirect(url_for('profile'))
        else:
            flash('Неверные имя пользователя или пароль')
    return render_template('login.html')

@app.route('/logout')
def logout():
    session.clear()
    return redirect(url_for('index'))

@app.route('/profile')
def profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    orders = Order.query.filter_by(user_id=user_id).all()
    return render_template('profile.html', user=user, orders=orders, Product=Product)

@app.route('/edit_profile', methods=['GET', 'POST'])
def edit_profile():
    user_id = session.get('user_id')
    if not user_id:
        return redirect(url_for('login'))
    user = User.query.get(user_id)
    if request.method == 'POST':
        new_username = request.form['username']
        new_password = request.form['password']
        if new_username:
            user.username = new_username
        if new_password:
            user.password = generate_password_hash(new_password)
        db.session.commit()
        session['username'] = user.username
        return redirect(url_for('profile'))
    return render_template('edit_profile.html', user=user)

@app.route('/delivery')
def delivery():

    return render_template('delivery.html')

@app.route('/booking')
def booking():

    return render_template('booking.html')

@app.route('/loyality')
def loyality():

    return render_template('loyality.html')

if __name__ == '__main__':
    with app.app_context():
        db.create_all()
    app.run(host='0.0.0.0', port=80, use_reloader=False, debug=True)
