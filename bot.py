import telebot
from telebot import types
import os
import pickle
import random
from collections import defaultdict

TOKEN = '7443819857:AAEC_6SL5yN8aVqGpPVPnU-LAmIX51NeX0Q'
bot = telebot.TeleBot(TOKEN)
ADMIN_USER_ID = '409555770' # Сюда впишите ваш Telegram ID как администратора
CATEGORIES = ['fruits', 'vegetables', 'berries']

USER_STATE = defaultdict(lambda: 'START')

USER_STATE_START = 0
USER_STATE_NAME = 1
USER_STATE_PRICE = 2
USER_STATE_DESCRIPTION = 3
USER_STATE_CATEGORY = 4
USER_STATE_PHOTO = 5

product_temp = {}
EDIT_ITEM = {}



def get_user_state(user_id):
    return USER_STATE.get(user_id, USER_STATE_START)

def update_user_state(user_id, state):
    USER_STATE[user_id] = state

def reset_user_state(user_id):
    USER_STATE.pop(user_id, None)


random_digit = 0

def get_markup_from_list(items_list):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for item in items_list:
        markup.add(item)
    return markup


def save_products(products):
    with open('products.pickle', 'wb') as handle:
        pickle.dump(products, handle)


# Обработчик команды /start
@bot.message_handler(commands=['start'])
def start(message):
    try:
        if str(message.from_user.id) == ADMIN_USER_ID:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Добавить товар', 'Редактировать товар')
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
            USER_STATE[message.chat.id] = 'CHOOSE_ACTION'
        else:
            bot.send_message(message.chat.id, "Добро пожаловать! Ваш ID не обладает правами администратора.")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка start: {e}')


@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'START')
def start2(message):
    try:
        if str(message.from_user.id) == ADMIN_USER_ID:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Добавить товар', 'Редактировать товар')
            bot.send_message(message.chat.id, "Выберите действие:", reply_markup=markup)
            USER_STATE[message.chat.id] = 'CHOOSE_ACTION'
        else:
            bot.send_message(message.chat.id, "Добро пожаловать! Ваш ID не обладает правами администратора.")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка start2: {e}')


# Начало процесса добавления товара
@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'CHOOSE_ACTION')
def add_product(message):
    global random_digit
    random_digit = str(random.randint(0, 1000000))
    if str(message.from_user.id) == ADMIN_USER_ID:
        if message.text == 'Добавить товар':
            bot.send_message(message.chat.id, "Введите название товара:")
            USER_STATE[message.chat.id] = 'USER_STATE_NAME'
            product_temp[random_digit] = {}
        elif message.text == 'Редактировать товар':
            with open('products.pickle', 'rb') as handle:
                products = pickle.load(handle)
                print(products)
            markup = get_markup_from_list(products.keys())
            prod_list = ''
            for key in products:
                prod_list += f'{key} - '
                prod_list += products[key]['name']
                prod_list += '\n'
            bot.send_message(message.chat.id, prod_list)
            bot.send_message(message.chat.id, "Выберите товар для редактирования:", reply_markup=markup)
            USER_STATE[message.chat.id] = 'EDIT_ITEM'
    else:
        bot.send_message(message.chat.id, "У вас нет прав для добавления товара.")


@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'EDIT_ITEM')
def handle_edit_choice(message):
    try:
        if str(message.from_user.id) == ADMIN_USER_ID:
            with open('products.pickle', 'rb') as handle:
                products = pickle.load(handle)
            if message.text in products:
                bot.send_message(message.chat.id, f"Выбран товар для редактирования: {message.text}")
                EDIT_ITEM[message.chat.id] = message.text
                markup = get_markup_from_list(['name', 'price', 'description', 'category', 'Готово'])
                bot.send_message(message.chat.id, "Выберите, что хотите редактировать:", reply_markup=markup)
                USER_STATE[message.chat.id] = 'EDIT_CHOICE'
        else:
            bot.send_message(message.chat.id, "У вас нет прав для добавления товара.")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка handle_edit_choice: {e}')


@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'EDIT_CHOICE')
def handle_edit_field_choice(message):
    try:
        if str(message.from_user.id) == ADMIN_USER_ID:
            if message.text == 'Готово':
                with open('products.pickle', 'rb') as handle:
                    products = pickle.load(handle)
                markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
                markup.add('Добавить товар', 'Редактировать товар')
                bot.send_message(message.chat.id, "Редактирование завершено.", reply_markup=markup)
                save_products(products)  # Сохранить изменения в продуктах
                USER_STATE[message.chat.id] = 'START'
            else:
                bot.send_message(message.chat.id, f"Введите новое значение для {message.text}:")
                USER_STATE[message.chat.id] = f'EDITING_{message.text.upper()}'
        else:
            bot.send_message(message.chat.id, "У вас нет прав для добавления товара.")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка handle_edit_field_choice: {e}')


@bot.message_handler(func=lambda message: USER_STATE[message.chat.id].startswith('EDITING_'))
def handle_edit_update(message):
    try:
        if str(message.from_user.id) == ADMIN_USER_ID:
            with open('products.pickle', 'rb') as handle:
                products = pickle.load(handle)
            field = USER_STATE[message.chat.id][8:].lower()
            item_key = EDIT_ITEM[message.chat.id]
            products[item_key][field] = message.text
            bot.send_message(message.chat.id, f"{field.capitalize()} обновлено. Продолжайте редактирование или нажмите 'Готово'.", reply_markup=get_markup_from_list(['name', 'price', 'description', 'category', 'Готово']))
            USER_STATE[message.chat.id] = 'EDIT_CHOICE'
        else:
            bot.send_message(message.chat.id, "У вас нет прав для добавления товара.")
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка handle_edit_update: {e}')


# Сбор информации о товаре
@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'USER_STATE_NAME')
def product_name(message):
    try:
        markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
        markup.add('Отменить создание товара')
        product_temp[random_digit]['name'] = message.text
        bot.send_message(message.chat.id, "Введите цену товара:", reply_markup=markup)
        USER_STATE[message.chat.id] = 'USER_STATE_PRICE'
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка product_name: {e}')


@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'USER_STATE_PRICE')
def product_price(message):
    try:
        if message.text == 'Отменить создание товара':
            USER_STATE[message.chat.id] = 'START'
        else:
            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Отменить создание товара')
            product_temp[random_digit]['price'] = int(message.text)
            bot.send_message(message.chat.id, "Введите описание товара:", reply_markup=markup)
            USER_STATE[message.chat.id] = 'USER_STATE_DESCRIPTION'
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка product_price: {e}')

@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'USER_STATE_DESCRIPTION')
def product_description(message):
    try:
        if message.text == 'Отменить создание товара':
            USER_STATE[message.chat.id] = 'START'
        else:
            markup = get_markup_from_list(CATEGORIES)
            product_temp[random_digit]['description'] = message.text
            bot.send_message(message.chat.id, "Введите категорию товара:", reply_markup=markup)
            USER_STATE[message.chat.id] = 'USER_STATE_CATEGORY'
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка product_description: {e}')

@bot.message_handler(func=lambda message: USER_STATE[message.chat.id] == 'USER_STATE_CATEGORY')
def product_category(message):
    try:
        if message.text == 'Отменить создание товара':
            USER_STATE[message.chat.id] = 'START'
        else:
            product_temp[random_digit]['category'] = message.text
            bot.send_message(message.chat.id, "Отправьте изображение товара:")
            USER_STATE[message.chat.id] = 'USER_STATE_PHOTO'
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка product_category: {e}')

# Завершение процесса и добавление товара
@bot.message_handler(content_types=['photo'], func=lambda message: USER_STATE[message.chat.id] == 'USER_STATE_PHOTO')
def product_photo(message):
    try:
        if message.text == 'Отменить создание товара':
            USER_STATE[message.chat.id] = 'START'
        else:
            photo_file = bot.get_file(message.photo[-1].file_id)
            downloaded_file = bot.download_file(photo_file.file_path)
            image_path = os.path.join("static\images", f"{product_temp[random_digit]['name']}.jpg")
            with open(image_path, 'wb') as new_file:
                new_file.write(downloaded_file)

            product_temp[random_digit]['image'] = image_path
            # Здесь код для добавления product_info в вашу структуру данных товаров

            with open('products.pickle', 'rb') as handle:
                products = pickle.load(handle)

            temp = products | product_temp

            with open('products.pickle', 'wb') as handle:
                pickle.dump(temp, handle)

            markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
            markup.add('Добавить товар', 'Редактировать товар')
            bot.send_message(message.chat.id, "Товар успешно добавлен.", reply_markup=markup)
            USER_STATE[message.chat.id] = 'START'
    except Exception as e:
        bot.send_message(message.chat.id, f'Ошибка product_photo: {e}')

if __name__ == '__main__':
    bot.infinity_polling()