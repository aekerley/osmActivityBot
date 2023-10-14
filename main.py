import telebot
import sqlite3
from datetime import datetime
from telebot import types
import os

# Инициализация бота
bot = telebot.TeleBot('6579878524:AAEOarVc4xHNCnPCOS5JHHr4_PpqktEojic')

# Создаем папку для сохранения фотографий, если она не существует
if not os.path.exists('uploads'):
    os.makedirs('uploads')

# Создаем базу данных и таблицы, если они не существуют
def initialize_database():
    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    # Создаем таблицу users, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            registration_date DATE,
            total_points INTEGER,
            spent_points INTEGER DEFAULT 0
        )
    ''')

    # Создаем таблицу activities, если она не существует
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS activities (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            telegram_id INTEGER,
            first_name TEXT,
            last_name TEXT,
            activity TEXT,
            add_date DATE,
            points INTEGER,
            category TEXT,
            subcategory TEXT,
            confirm TEXT
        )
    ''')

    # Создаем таблицу store
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS store (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT,
            price REAL,
            stock INTEGER
        )
    ''')

    # Создаем таблицу purchases
    cursor.execute('''
        CREATE TABLE IF NOT EXISTS purchases (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER,
            product_id INTEGER,
            purchase_date DATE,
            quantity INTEGER
        )
    ''')
    conn.commit()
    conn.close()

# Обработчик кнопки "Инструкция"
@bot.message_handler(func=lambda message: message.text == "Инструкция")
def send_instruction(message):
    chat_id = message.chat.id
    show_instruction(chat_id)

# Функция для отображения инструкции
def show_instruction(chat_id):
    instruction = """
    Добро пожаловать в бота ОСМ!

    Этот бот предназначен для учета молодежных активностей.

    Вы можете:
    1. Добавить активность.
    2. Посмотреть список ваших активностей.
    3. Посмотреть количество баллов.

    Для добавления активности:
    - Выберите категорию и подкатегорию активности.
    - Введите название активности.
    - Отправьте фотографию, подтверждающую ваше участие.

    Баллы начисляются после проверки не позднее 1 числа каждого месяца.

    По всем вопросам обращайтесь к администратору.
    """
    bot.send_message(chat_id, instruction)
    bot.send_sticker(chat_id, 'CAACAgIAAxkBAAEKd4VlIFDScHU7reqdHkHFRKF09gybhgACyhkAAsD48UsLyNJ16RFqUjAE')

# Обработчик для команды /start
@bot.message_handler(commands=['start'])
def start(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    cursor.execute("SELECT * FROM users WHERE telegram_id=?", (user_id,))
    user_data = cursor.fetchone()

    if user_data:
        bot.send_message(chat_id, f'Привет, {message.from_user.first_name}!')
        show_main_menu(chat_id)
    else:
        bot.send_sticker(chat_id, 'CAACAgIAAxkBAAEKd49lIFNBWnDhlTHEenvgIZpi-RNSvAACtCMAAkHhEEnpzviG2GDu2jAE')
        bot.send_message(chat_id, f'Привет! Говорят тебя зовут {message.from_user.first_name}. А как мне тебя записать?')
        bot.send_message(chat_id, "Для продолжения, введите своё полное имя и фамилию (например, Михаил Атомов):")
        bot.register_next_step_handler(message, process_name)

    conn.close()

# Обработчик для получения имени пользователя
def process_name(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    full_name = message.text

    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    if not full_name or len(full_name.split()) < 2:
        bot.send_message(chat_id, "Пожалуйста, введите своё полное имя и фамилию (например, Михаил Атомов):")
        bot.register_next_step_handler(message, process_name)  # Регистрируем себя снова для получения имени
        return

    first_name, last_name = full_name.split(' ', 1)

    cursor.execute("INSERT INTO users (telegram_id, first_name, last_name, registration_date) VALUES (?, ?, ?, ?)",
                   (user_id, first_name, last_name, datetime.now()))
    conn.commit()

    bot.send_message(chat_id, f"Спасибо, {first_name} {last_name}! Вы успешно зарегистрированы.")
    bot.send_sticker(chat_id, 'CAACAgIAAxkBAAEKd4dlIFLL2aPfSPUkO-KC_fCmP19zFwAC_BoAAvfa2EubQGsWnyAuVjAE')
    show_main_menu(chat_id)

    conn.close()

# Функция для отображения основного меню с кнопками
def show_main_menu(chat_id, is_registered=True):
    markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
    if is_registered:
        markup.row(types.KeyboardButton("Добавить активность⚡"))
        markup.row(types.KeyboardButton("Посмотреть активности"), types.KeyboardButton("Баллы"))
        markup.row(types.KeyboardButton("Магазин"))
        markup.row(types.KeyboardButton("Инструкция"))
    else:
        markup.add(types.KeyboardButton("Инструкция"))

    bot.send_message(chat_id, "Выберите действие:", reply_markup=markup)

# Обработчик кнопок
@bot.message_handler(func=lambda message: True)
def handle_buttons(message):
    chat_id = message.chat.id
    text = message.text

    if text == "Добавить активность⚡":
        # Отправляем список категорий активностей
        send_activity_categories(chat_id)
    elif text == "Посмотреть активности":
        view_activities(message)
    elif text == "Баллы":
        view_points(message)
    elif text == "Магазин":
        show_store(message)
    elif text == "/start":
        show_main_menu(chat_id, is_registered=True)
    elif text == "Отмена":
        show_main_menu(chat_id, is_registered=True)

# Функция для отправки списка категорий активностей
def send_activity_categories(chat_id):
    markup = types.ReplyKeyboardMarkup(one_time_keyboard=True, resize_keyboard=True)
    for category in activity_categories:
        markup.add(types.KeyboardButton(category))
    markup.add(types.KeyboardButton("Отмена"))

    bot.send_message(chat_id, "Выберите категорию активности:", reply_markup=markup)
    bot.register_next_step_handler_by_chat_id(chat_id, process_activity_category)

# Обработчик выбора категории активности
def process_activity_category(message):
    chat_id = message.chat.id
    text = message.text

    if text == "Отмена":
        show_main_menu(chat_id, is_registered=True)
        return

    user_id = message.from_user.id
    user_states[chat_id] = {"category": text}

    if text in activity_subcategories:
        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        for subcategory in activity_subcategories[text]:
            markup.add(types.KeyboardButton(subcategory))
        markup.add(types.KeyboardButton("Отмена"))

        bot.send_message(chat_id, f"Вы выбрали категорию: {text}\nТеперь выберите подкатегорию:", reply_markup=markup)
        bot.register_next_step_handler(message, process_activity_subcategory)
    else:
        bot.send_message(chat_id, f"Вы выбрали категорию: {text}\nТеперь введите название активности:")
        bot.register_next_step_handler(message, process_activity_name)

# Обработчик выбора подкатегории активности
def process_activity_subcategory(message):
    chat_id = message.chat.id
    text = message.text

    if text == "Отмена":
        show_main_menu(chat_id, is_registered=True)
        return

    if chat_id in user_states and "category" in user_states[chat_id]:
        subcategory = text
        user_states[chat_id]["subcategory"] = subcategory

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, "Теперь введите название активности:", reply_markup=markup)
        bot.register_next_step_handler(message, process_activity_name)
    else:
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, начните процесс добавления активности заново.")
        show_main_menu(chat_id, is_registered=True)

# Обработчик ввода названия активности
def process_activity_name(message):
    chat_id = message.chat.id
    user_id = message.from_user.id
    activity_name = message.text

    if activity_name == "Отмена":
        show_main_menu(chat_id, is_registered=True)
        return

    if chat_id in user_states and "category" in user_states[chat_id]:
        category = user_states[chat_id]["category"]
        subcategory = user_states[chat_id].get("subcategory", "")

        user_states[chat_id]["activity"] = activity_name

        markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
        markup.add(types.KeyboardButton("Отмена"))
        bot.send_message(chat_id, "Отправьте фотографию, которая подтверждает ваше участие:", reply_markup=markup)
        bot.register_next_step_handler(message, process_confirmation_photo)
    else:
        bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, начните процесс добавления активности заново.")
        show_main_menu(chat_id, is_registered=True)


# Обработчик ввода фотографии
def process_confirmation_photo(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    if message.content_type == 'photo':
        confirmation_photo = message.photo[-1]  # Получаем фотографию из сообщения

        if chat_id in user_states and "category" in user_states[chat_id] and "activity" in user_states[chat_id]:
            category = user_states[chat_id]["category"]
            activity_name = user_states[chat_id]["activity"]
            subcategory = user_states[chat_id].get("subcategory", "")

            conn = sqlite3.connect('database_aleksey.db')
            cursor = conn.cursor()

            cursor.execute("SELECT first_name, last_name FROM users WHERE telegram_id=?", (user_id,))
            user_data = cursor.fetchone()
            if user_data:
                first_name, last_name = user_data
            else:
                first_name, last_name = "", ""

            # Создаем папку для загрузки, если она не существует
            upload_folder = os.path.join('uploads', datetime.now().strftime('%Y_%m'))
            os.makedirs(upload_folder, exist_ok=True)

            # Формируем имя файла на основе данных пользователя и текущей даты
            current_date = datetime.now().strftime('%Y-%m-%d')
            filename = f"{first_name}_{last_name}_{activity_name}_{category}_{subcategory}_{current_date}.jpg"  # Измените расширение, если необходимо

            # Сохраняем фотографию на сервере в соответствующей папке
            photo_id = confirmation_photo.file_id
            photo_info = bot.get_file(photo_id)
            photo_extension = os.path.splitext(photo_info.file_path)[1]
            photo_filename = os.path.join(upload_folder, filename + photo_extension)

            photo_file = bot.download_file(photo_info.file_path)  # Здесь получаем байты фотографии
            with open(photo_filename, 'wb') as photo:
                photo.write(photo_file)  # Записываем байты в файл

            # Формируем ссылку на фотографию на сервере
            photo_link = photo_filename

            # Обновляем запись в таблице activities, добавляя имя фотографии в поле confirm
            cursor.execute("INSERT INTO activities (telegram_id, first_name, last_name, activity, add_date, points, category, subcategory, confirm) VALUES (?, ?, ?, ?, ?, ?, ?, ?, ?)",
                           (user_id, first_name, last_name, activity_name, datetime.now(), 0, category, subcategory, photo_link))
            conn.commit()

            bot.send_message(chat_id, f"Активность '{activity_name}' успешно добавлена в категорию '{category}'.")
            show_main_menu(chat_id, is_registered=True)

            conn.close()
        else:
            bot.send_message(chat_id, "Произошла ошибка. Пожалуйста, начните процесс добавления активности заново.")
            show_main_menu(chat_id, is_registered=True)
    else:
        if message.text.lower() == "отмена":
            show_main_menu(chat_id, is_registered=True)
        else:
            bot.send_message(chat_id, "Пожалуйста, отправьте фотографию вместо текстовой ссылки.")
            markup = types.ReplyKeyboardMarkup(resize_keyboard=True)
            markup.add(types.KeyboardButton("Отмена"))
            bot.send_message(chat_id, "Отправьте фотографию, которая подтверждает ваше участие:", reply_markup=markup)
            bot.register_next_step_handler(message, process_confirmation_photo)  # Рекурсивный вызов обработчика


# Функция для просмотра активностей пользователя
def view_activities(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    cursor.execute("SELECT activity, add_date, points FROM activities WHERE telegram_id=?", (user_id,))
    activities_data = cursor.fetchall()

    if not activities_data:
        bot.send_message(chat_id, "У вас пока нет активностей.")
    else:
        response = "Ваши активности:\n"
        for idx, (activity, add_date, points) in enumerate(activities_data, start=1):
            response += f"{idx}. ⚡️Активность: {activity}\nДата добавления: {add_date}\nБаллы: {points}\n\n"

        bot.send_message(chat_id, response)

    conn.close()

# Функция для просмотра баллов пользователя
def view_points(message):
    chat_id = message.chat.id
    user_id = message.from_user.id

    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    cursor.execute("SELECT SUM(points) FROM activities WHERE telegram_id=?", (user_id,))
    total_points = cursor.fetchone()[0]

    cursor.execute("SELECT spent_points FROM users WHERE telegram_id=?", (user_id,))
    spent_points = cursor.fetchone()[0]

    conn.close()

    if total_points is not None:
        available_points = total_points - spent_points
        bot.send_message(chat_id, f"Ваши баллы: {available_points}\n*Баллы обновляются 1 числа каждого месяца!")
    else:
        bot.send_message(chat_id, "У вас пока нет баллов.\n*Баллы обновляются 1 числа каждого месяца!", parse_mode='html')

@bot.message_handler(func=lambda message: message.text == "Магазин")
def show_store(message):
    chat_id = message.chat.id
    bot.send_message(chat_id, "Вы находитесь в разделе 'Магазин'.", reply_markup=types.ReplyKeyboardMarkup(resize_keyboard=True).add(types.KeyboardButton("Отмена")))

    # Получите список товаров из таблицы store
    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, price, stock FROM store")
    products = cursor.fetchall()
    conn.close()

    if not products:
        bot.send_message(chat_id, "В магазине нет доступных товаров.")
    else:
        store_info = "Магазин:\n"
        keyboard = types.InlineKeyboardMarkup(row_width=2)

        for product in products:
            product_id, name, price, stock = product
            item_text = f"{name} - ${price} (В наличии: {stock} шт.)"
            callback_data = f"buy_{product_id}"

            button = types.InlineKeyboardButton(item_text, callback_data=callback_data)
            keyboard.add(button)

        bot.send_message(chat_id, store_info, reply_markup=keyboard)
        bot.send_message(chat_id, "Выберите товар или введите другую команду.")

# Обработчик для инлайн-кнопок товаров
@bot.callback_query_handler(func=lambda call: call.data.startswith("buy_"))
def handle_buy_callback(call):
    product_id = int(call.data.replace("buy_", ""))

    # Получите информацию о товаре из таблицы store
    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()
    cursor.execute("SELECT name, price, stock FROM store WHERE id=?", (product_id,))
    product_info = cursor.fetchone()
    conn.close()

    if product_info:
        name, price, stock = product_info
        message_text = f"{name} - ${price}\nВ наличии: {stock} шт."

        # Получите путь к изображению товара
        images_path = 'img/'  # Укажите путь к папке с изображениями
        image_filename = os.path.join(images_path, f"{product_id}.png")

        # Проверяем, существует ли файл изображения
        if os.path.isfile(image_filename):
            # Отправляем изображение товара с подписью и инлайн-клавиатурой
            with open(image_filename, 'rb') as image_file:
                bot.send_photo(call.message.chat.id, image_file, caption=message_text, reply_markup=create_confirmation_keyboard(product_id))
        else:
            bot.send_message(call.message.chat.id, message_text, reply_markup=create_confirmation_keyboard(product_id))
    else:
        bot.send_message(call.message.chat.id, "Информация о товаре не найдена.")

# Функция для создания инлайн-клавиатуры "Купить"
def create_confirmation_keyboard(product_id):
    keyboard = types.InlineKeyboardMarkup(row_width=1)
    buy_button = types.InlineKeyboardButton("Купить", callback_data=f"confirm_buy_{product_id}")
    keyboard.add(buy_button)
    return keyboard

# Обработчик для инлайн-кнопок "Купить"
@bot.callback_query_handler(func=lambda call: call.data.startswith("confirm_buy_"))
def handle_buy_button_callback(call):
    product_id = int(call.data.replace("confirm_buy_", ""))

    # Здесь вы можете добавить логику покупки товара
    increase_spent_points(call.message.chat.id, product_id)
    # Уменьшаем количество товара на складе
    decrease_stock(product_id)

    bot.send_message(call.message.chat.id, f"Вы успешно купили товар с ID {product_id}. Сумма покупки добавлена в spent_points.")

def decrease_stock(product_id):
    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    # Уменьшаем количество товара на складе (stock) на 1
    cursor.execute("UPDATE store SET stock = stock - 1 WHERE id = ?", (product_id,))

    conn.commit()
    conn.close()


# Функция для увеличения суммы потраченных средств

def increase_spent_points(user_id, product_id):
    conn = sqlite3.connect('database_aleksey.db')
    cursor = conn.cursor()

    # Здесь предполагается, что у вас есть таблица "users" с полем "spent_points" для отслеживания потраченных средств
    cursor.execute("UPDATE users SET spent_points = spent_points + (SELECT price FROM store WHERE id=?) WHERE telegram_id = ?", (product_id, user_id))

    conn.commit()
    conn.close()

@bot.message_handler(commands=['Отмена'])
def cancel(message):
    chat_id = message.chat.id
    show_main_menu(chat_id, is_registered=True)

# Глобальные переменные
user_states = {}
images_path = "img"
activity_categories = ["Участие в молодёжном мероприятии", "Организация мероприятия для молодёжи", "Выступление спикером или лектором на мероприятии ОСМ", "Получение наград за работу в молодежных сообществах", "Получение наград за продвижение молодежных инициатив", "Получение наград за реализацию проектов"]
activity_subcategories = {
    "Участие в молодёжном мероприятии": ["Мероприятие уровня предприятия", "Мероприятие уровня дивизиона", "Мероприятие уровня отрасли"],
    "Организация мероприятия для молодёжи": ["Мероприятие уровня предприятия", "Мероприятие уровня дивизиона", "Мероприятие уровня отрасли"],
}

# Инициализация базы данных
initialize_database()

if __name__ == "__main__":
    bot.polling(none_stop=True)