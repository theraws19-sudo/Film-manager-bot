import config
import telebot
from telebot import types
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from datetime import datetime

from random import randint
import sqlite3 

bot = telebot.TeleBot(config.API_TOKEN)

def senf_info(bot, message, row):
        
        info = f"""
📍Title of movie:   {row[2]}
📍Year:                   {row[3]}
📍Genres:              {row[4]}
📍Rating IMDB:      {row[5]}


🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻🔻
{row[6]}
"""
        bot.send_photo(message.chat.id,row[1])
        bot.send_message(message.chat.id, info, reply_markup=add_to_favorite(row[0]))

def send_top_10(bot, message, row):
    info = f"""
1. 
"""

@bot.message_handler(commands=['help'])
def send_help(message):
    # Создаем inline-клавиатуру
    markup = types.InlineKeyboardMarkup(row_width=2)  # row_width - кнопок в строке
    
    # Создаем кнопки
    btn1 = types.InlineKeyboardButton("Топ 10 фильмов по рейтингу", callback_data='rating')
    btn2 = types.InlineKeyboardButton("Топ-10 фильмов по бюджету", callback_data='budget')
    btn3 = types.InlineKeyboardButton("Показать фильмы определенного года", callback_data='year')
    
    # Добавляем кнопки в клавиатуру
    markup.add(btn1, btn2, btn3)
    
    # Отправляем сообщение с клавиатурой
    bot.send_message(
        message.chat.id,
        "📋 **Доступные команды:**\n\n"
        "• /start - Начать работу\n"
        "• /help - Показать это меню\n"
        "• /top_movies - Показать топ-10 фильмов по рейтингу\n"
        "• /top_budget - Показать топ-10 фильмов по бюджету\n"
        "• /films_by_year - Показать фильмы определенного года\n"
        "• /top_movies_genre - Показать фильмы по определенному жанру\n"
        "Выберите действие:",
        reply_markup=markup,
        parse_mode='Markdown'
    )

# Обработчик нажатий на inline-кнопки
@bot.callback_query_handler(func=lambda call: True)
def callback_inline(call):
    if call.data == 'rating':
        random_movie()
    
    elif call.data == 'budget':
        bot.answer_callback_query(call.id, "Настройки открыты")
        bot.send_message(call.message.chat.id, "⚙️ Здесь будут настройки...")
    
    elif call.data == 'stats':
        bot.answer_callback_query(call.id, "Статистика загружена")
        bot.send_message(call.message.chat.id, "📊 Статистика: 100 пользователей")
    
    elif call.data == 'contacts':
        bot.answer_callback_query(call.id, "Контактная информация")
        bot.send_message(call.message.chat.id, "📞 Связь: @username")


def add_to_favorite(id):
        markup = InlineKeyboardMarkup()
        markup.row_width = 1
        markup.add(InlineKeyboardButton("Добавить фильм в избранное 🌟", callback_data=f'favorite_{id}'))
        return markup


def main_markup():
  markup = ReplyKeyboardMarkup()
  markup.add(KeyboardButton('/random'))
  return markup


@bot.callback_query_handler(func=lambda call: True)
def callback_query(call):
    if call.data.startswith("favorite"):
        id = call.data[call.data.find("_")+1:]


@bot.message_handler(commands=['start'])
def send_welcome(message):
    bot.send_message(message.chat.id, """Hello! You're welcome to the best Movie-Chat-Bot🎥!
Here you can find 1000 movies 🔥
Click /random to get random movie
Or write the title of movie and I will try to find it! 🎬 """, reply_markup=main_markup())

@bot.message_handler(commands=['random'])
def random_movie(message):
    con = sqlite3.connect("movie_database.db")
    with con:
        cur = con.cursor()
        cur.execute(f"SELECT * FROM movies ORDER BY RANDOM() LIMIT 1")
        row = cur.fetchall()[0]
        cur.close()
    senf_info(bot, message, row)


def get_top_movies(limit=10, order_by='rating', genre=None, year=None):
    """
    Получение топ-N фильмов из БД
    
    Args:
        limit: количество фильмов (по умолчанию 10)
        order_by: поле для сортировки (по умолчанию 'rating')
        genre: фильтр по жанру (опционально)
        year: фильтр по году (опционально)
    
    Returns:
        list: список кортежей с данными фильмов
    """
    try:
        conn = sqlite3.connect('movies.db')
        cursor = conn.cursor()
        query = """
        SELECT 
            title, 
            rating, 
            year, 
            genre, 
            director,
            owerview
        FROM movies
        WHERE rating IS NOT NULL
        """
        
        params = []
        
        # Добавляем фильтры
        if genre:
            query += " AND genre LIKE ?"
            params.append(f'%{genre}%')
        
        if year:
            query += " AND release_year = ?"
            params.append(year)
        
        # Добавляем сортировку и лимит
        query += f" ORDER BY {order_by} DESC LIMIT ?"
        params.append(limit)
        
        cursor.execute(query, params)
        results = cursor.fetchall()
        
        conn.close()
        return results
    except Exception as e:
        print(f"Ошибка при получении фильмов из БД: {e}")
        return []

@bot.message_handler(commands=['top_movies'])
def handle_top_movies(message):
    """
    Основной хэндлер команды /top_movies
    Выводит топ-10 фильмов по рейтингу
    """
    try:
        # Получаем топ-10 фильмов
        movies = get_top_movies(limit=10, order_by='rating')
        
        if not movies:
            bot.reply_to(message, "🎬 Кинобаза пуста или произошла ошибка при загрузке данных.")
            return
        
        # Формируем красивое сообщение
        response = "🍿 **ТОП-10 ФИЛЬМОВ ПО РЕЙТИНГУ** 🎬\n\n"
        
        for index, (title, rating, year, genre, director, description) in enumerate(movies, 1):
            # Форматируем рейтинг
            rating_str = "⭐" * int(rating)
            if rating % 1 != 0:
                rating_str += "½"
            
            # Обрезаем длинное описание
            short_desc = (description[:80] + '...') if description and len(description) > 80 else description or ""
            
            response += (
                f"**{index}. {title}** ({year})\n"
                f"   ⭐ **Рейтинг:** {rating}/10 {rating_str}\n"
                f"   🎭 **Жанр:** {genre or 'Не указан'}\n"
                f"   👨‍🎨 **Режиссер:** {director or 'Не указан'}\n"
            )
            
            if short_desc:
                response += f"   📝 **Описание:** {short_desc}\n"
            
            response += "━━━━━━━━━━━━━━━━━━━━━━━━\n"
        
        # Добавляем статистику
        response += f"\n📊 Всего фильмов в базе: {len(movies)}"
        
        # Отправляем сообщение
        bot.send_message(
            message.chat.id,
            response,
            parse_mode='Markdown',
            disable_web_page_preview=True
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Произошла ошибка: {str(e)}")

@bot.message_handler(commands=['top_movies_genre'])
def handle_top_movies_by_genre(message):
    """
    Хэндлер для выбора жанра перед показом топа
    """
    # Предлагаем популярные жанры
    markup = types.InlineKeyboardMarkup(row_width=2)
    
    genres = ["Фантастика", "Action", "Drama", "Комедия", "Ужасы", "Триллер", 
              "Мультфильм", "Детектив", "Мелодрама", "Adventure", "Crime", "Romance"]
    
    buttons = []
    for genre in genres:
        buttons.append(types.InlineKeyboardButton(genre, callback_data=f'top_genre_{genre}'))
    
    # Распределяем кнопки по 2 в ряд
    for i in range(0, len(buttons), 2):
        if i + 1 < len(buttons):
            markup.add(buttons[i], buttons[i+1])
        else:
            markup.add(buttons[i])
    
    bot.send_message(
        message.chat.id,
        "🎭 **Выберите жанр для просмотра топа фильмов:**",
        parse_mode='Markdown',
        reply_markup=markup
    )

@bot.callback_query_handler(func=lambda call: call.data.startswith('top_genre_'))
def handle_genre_callback(call):
    """
    Обработчик выбора жанра
    """
    try:
        genre = call.data.replace('top_genre_', '')
        
        # Получаем топ-10 фильмов по выбранному жанру
        movies = get_top_movies(limit=10, order_by='rating', genre=genre)
        
        if not movies:
            bot.answer_callback_query(
                call.id, 
                f"❌ Нет фильмов в жанре '{genre}'",
                show_alert=True
            )
            return
        
        # Формируем сообщение
        response = f"🎭 **ТОП-10 ФИЛЬМОВ В ЖАНРЕ: {genre.upper()}** 🎬\n\n"
        
        for index, (title, rating, year, genre_list, director, _) in enumerate(movies, 1):
            rating_str = "⭐" * int(rating)
            if rating % 1 != 0:
                rating_str += "½"
            
            response += (
                f"**{index}. {title}** ({year})\n"
                f"   ⭐ **Рейтинг:** {rating}/10\n"
                f"   👨‍🎨 **Режиссер:** {director or 'Не указан'}\n"
                f"   ━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
        
        # Редактируем сообщение
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=response,
            parse_mode='Markdown'
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}")

@bot.message_handler(commands=['top_movies_year'])
def handle_top_movies_by_year(message):
    """
    Топ фильмов по году
    """
    try:
        # Получаем текущий год
        current_year = datetime.now().year
        
        # Создаем клавиатуру с годами (последние 10 лет)
        markup = types.InlineKeyboardMarkup(row_width=3)
        
        buttons = []
        for year in range(current_year, current_year - 10, -1):
            buttons.append(types.InlineKeyboardButton(str(year), callback_data=f'top_year_{year}'))
        
        # Распределяем кнопки по 3 в ряд
        for i in range(0, len(buttons), 3):
            row_buttons = buttons[i:i+3]
            markup.add(*row_buttons)
        
        bot.send_message(
            message.chat.id,
            f"📅 **Выберите год для просмотра топа фильмов:**",
            parse_mode='Markdown',
            reply_markup=markup
        )
        
    except Exception as e:
        bot.reply_to(message, f"❌ Ошибка: {str(e)}")

@bot.callback_query_handler(func=lambda call: call.data.startswith('top_year_'))
def handle_year_callback(call):
    """
    Обработчик выбора года
    """
    try:
        year = int(call.data.replace('top_year_', ''))
        
        # Получаем топ-10 фильмов за выбранный год
        movies = get_top_movies(limit=10, order_by='rating', year=year)
        
        if not movies:
            bot.answer_callback_query(
                call.id,
                f"❌ Нет фильмов {year} года в базе",
                show_alert=True
            )
            return
        
        # Формируем сообщение
        response = f"📅 **ТОП-10 ФИЛЬМОВ {year} ГОДА** 🎬\n\n"
        
        for index, (title, rating, _, genre, director, _) in enumerate(movies, 1):
            rating_str = "⭐" * int(rating)
            if rating % 1 != 0:
                rating_str += "½"
            
            response += (
                f"**{index}. {title}**\n"
                f"   ⭐ **Рейтинг:** {rating}/10 {rating_str}\n"
                f"   🎭 **Жанр:** {genre or 'Не указан'}\n"
                f"   ━━━━━━━━━━━━━━━━━━━━━━━━\n"
            )
        
        # Редактируем сообщение
        bot.edit_message_text(
            chat_id=call.message.chat.id,
            message_id=call.message.message_id,
            text=response,
            parse_mode='Markdown'
        )
        
        bot.answer_callback_query(call.id)
        
    except Exception as e:
        bot.answer_callback_query(call.id, f"❌ Ошибка: {str(e)}")

    
@bot.message_handler(func=lambda message: True)
def echo_message(message):

    con = sqlite3.connect("movie_database.db")
    with con:
        cur = con.cursor()
        cur.execute(f"select * from movies where LOWER(title) = '{message.text.lower()}'")
        row = cur.fetchall()
        if row:
            row = row[0]
            bot.send_message(message.chat.id,"Of course! I know this movie😌")
            senf_info(bot, message, row)
        else:
            bot.send_message(message.chat.id,"I don't know this movie ")

        cur.close()



bot.infinity_polling()
