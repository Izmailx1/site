import os
from flask import Flask, render_template, request, redirect, url_for, jsonify, session, flash
from datetime import datetime, timedelta
import requests
import pickle


app = Flask(__name__)
app.config['SECRET_KEY'] = os.urandom(24)
TELEGRAM_CHAT_ID = '409555770'
TELEGRAM_TOKEN = '7443819857:AAEC_6SL5yN8aVqGpPVPnU-LAmIX51NeX0Q'

# # Эмуляция базы данных с товарами
# products = {
#     '1': {'name': 'Яблоко', 'price': 150, 'description': 'Тухляк', 'category': 'fruits', 'image': 'static/images/apple.jpg'},
#     '2': {'name': 'Ананас', 'price': 800, 'description': 'Новый сорт говна', 'category': 'fruits', 'image': 'static/images/pineapple.jpeg'},
#     '3': {'name': 'Помидоры', 'price': 300, 'description': 'Вонючие', 'category': 'berries', 'image': 'static/images/pomidor.png'},
#     '4': {'name': 'Агурцы', 'price': 280, 'description': 'Гнилые', 'category': 'vegetables', 'image': 'static/images/cucumber.jpg'}
# }
# with open('products.pickle', 'wb') as handle:
#     pickle.dump(products, handle)

products = {}



def send_telegram_message(text):
    url = f'https://api.telegram.org/bot{TELEGRAM_TOKEN}/sendMessage'
    payload = {'chat_id': TELEGRAM_CHAT_ID, 'text': text}
    requests.post(url, json=payload)


def add_product_to_cart(product_id):
    """Добавить товар в корзину или увеличить его количество."""
    if product_id in session['cart']:
        session['cart'][product_id] += 1
    else:
        session['cart'][product_id] = 1
    session.modified = True


def remove_product_from_cart(product_id):
    """Уменьшить количество товара в корзине или удалить его, если товара осталось меньше одного."""
    if product_id in session['cart']:
        if session['cart'][product_id] > 1:
            session['cart'][product_id] -= 1
        else:
            del session['cart'][product_id]
        session.modified = True


def delete_product_from_cart(product_id):
    """Полностью удалить товар из корзины."""
    if product_id in session['cart']:
        del session['cart'][product_id]
        session.modified = True



def get_cart_quantity(product_id):
    """Получить количество определенного товара в корзине."""
    return session['cart'].get(product_id, 0)


def calculate_cart_total():
    """Подсчитать общую стоимость товаров в корзине."""
    total = sum(int(qty) * int(products[product_id]['price']) for product_id, qty in session['cart'].items())
    return total


def get_product_total_price(product_id):
    """Получить общую стоимость товара в корзине."""
    return products[product_id]['price'] * session['cart'].get(product_id, 0)


@app.before_request
def before_request():
    global products
    with open('products.pickle', 'rb') as handle:
        products = pickle.load(handle)
    if 'cart' not in session:
        session['cart'] = {}
        session['token'] = os.urandom(24)


@app.route('/')
def index():
    """ Главная страница с товарами """
    cart_total = sum(session['cart'].values())
    return render_template('index.html', products=products, cart_total=cart_total)


@app.route('/product/<product_id>')
def product(product_id):
    """ Страница конкретного товара """
    product = products.get(product_id).copy()
    product['image'] = product['image'][7:]
    if not product:
        return "Товар не найден"

    return render_template('product.html', product=product)


@app.route('/add_to_cart/<product_id>', methods=['POST'])
def add_to_cart(product_id):
    # Имитируем добавление в корзину (на самом деле здесь нужна ваша логика)
    session['cart'][product_id] = session['cart'].get(product_id, 0) + 1
    session.modified = True
    # В ответ на AJAX-запрос отправляем JSON с обновленным количеством товаров
    return jsonify(cart_total=sum(session['cart'].values()))


@app.route('/category/<category_name>')
def category(category_name):
    category_products = {id: product for id, product in products.items() if product['category'] == category_name}
    return render_template('category.html', category=category_name, products=category_products)


@app.route('/cart')
def cart():
    total_sum = sum(products[product_id]['price'] * quantity for product_id, quantity in session['cart'].items())
    """ Страница корзины с выбранными товарами """
    cart_data = {product_id: products[product_id] for product_id in session['cart'].keys()}
    total_price = sum(int(products[product_id]['price']) * int(session['cart'][product_id]) for product_id in session['cart'])
    cart_total = sum(session['cart'].values())
    return render_template('cart.html', cart_products=cart_data, cart_items=session['cart'], total_price=total_price, products=products, total_sum=total_sum, cart_total=cart_total)


@app.route('/remove_from_cart/<product_id>')
def remove_from_cart(product_id):
    """ Удаление товара из корзины полностью """
    session['cart'].pop(product_id, None) # Удаляем товар одним действием
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/remove_one_from_cart/<product_id>')
def remove_one_from_cart(product_id):
    """ Удаление одной единицы товара из корзины """
    if session['cart'].get(product_id, 0) > 1:
        session['cart'][product_id] -= 1  # Уменьшаем количество на 1
    else: # Если товар один, удаляем его из корзины
        session['cart'].pop(product_id, None)
    session.modified = True
    return redirect(url_for('cart'))


@app.route('/update_cart/<product_id>/<string:action>', methods=['POST'])
def update_cart(product_id, action):
    # Предполагается, что у вас есть методы для управления корзиной
    # Например, add_product_to_cart, remove_product_from_cart, и delete_product_from_cart

    if action == 'add':
        add_product_to_cart(product_id)
    elif action == 'remove':
        remove_product_from_cart(product_id)
    elif action == 'delete':
        delete_product_from_cart(product_id)

    cart_total = calculate_cart_total()  # Подсчет общей стоимости корзины
    product_quantity = get_cart_quantity(product_id)  # Количество определенного товара
    product_total_price = get_product_total_price(product_id)  # Общая стоимость этого товара

    return jsonify({
        'status': 'success',
        'quantity': product_quantity,
        'total_price': product_total_price,
        'cart_total': cart_total
    })


@app.route('/checkout')
def checkout():
    # Создаем словарь, который содержит товары в корзине с подсчитанной стоимостью по каждому
    checkout_items = {
        'items': [
            {'name': products[product_id]['name'],
             'quantity': qty,
             'unit_price': products[product_id]['price'],
             'total_price': int(qty) * int(products[product_id]['price'])}
            for product_id, qty in session['cart'].items()
        ],
        'total': sum(int(qty) * int(products[product_id]['price']) for product_id, qty in session['cart'].items())
    }
    today = datetime.today()
    dates = [today.strftime('%d.%m'), (today + timedelta(days=1)).strftime('%d.%m'), (today + timedelta(days=2)).strftime('%d.%m')]
    # Передаем в шаблон данные о товарах в корзине и общую сумму заказа
    return render_template('checkout.html', checkout_items=checkout_items, dates=dates)


@app.route('/place_order', methods=['POST'])
def place_order():
    # Здесь должен быть ваш код для обработки данных формы и выполнять запись заказа в базу данных

    # После оформления заказа, очищаем корзину пользователя

    full_name = request.form.get('fullName')
    phone = request.form.get('phone')
    address = request.form.get('address')
    delivery_time = request.form.get('deliveryTime')
    delivery_date = request.form.get('deliveryDate')

    # Структурируем сообщение
    message_lines = [
        "Новый заказ:",
        f"Имя: {full_name}",
        f"Телефон: {phone}",
        f"Адрес: {address}",
        f"Время доставки: {delivery_time}",
        f"Дата доставки: {delivery_date}",
        "",
        "Заказанные товары:"
    ]

    # Добавляем детали товаров из корзины
    total_sum = 0  # Для подсчета общей суммы
    for product_id, quantity in session['cart'].items():
        product = products.get(product_id)
        product_sum = product['price'] * quantity
        total_sum += product_sum
        message_lines.append(f"{product['name']}: {quantity} шт. - {product_sum} руб.")

    # Добавляем общую сумму заказа
    message_lines.append("")
    message_lines.append(f"Итого: {total_sum} руб.")

    # Преобразуем список строк в одну строку сообщения
    message = "\n".join(message_lines)

    session['cart'] = {}
    session.modified = True

    # Отправка сообщения в Telegram
    send_telegram_message(message)

    # Добавляем сообщение об успешном оформлении заказа
    flash('Ваш заказ успешно оформлен! Ожидайте звонка оператора')

    # Перенаправляем пользователя на главную страницу
    return redirect(url_for('index'))


if __name__ == '__main__':
    app.run(debug=False)
