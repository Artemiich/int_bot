from aiogram.types import ReplyKeyboardMarkup, KeyboardButton

main_menu = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="📦 Каталог"), KeyboardButton(text="🛒 Корзина")],
        [KeyboardButton(text="📞 Контакты"), KeyboardButton(text="ℹ О нас")],  # ✅ Исправлено
        [KeyboardButton(text="📄 Маркетинг План"), KeyboardButton(text="🧾 Сертификаты на Товары")],
        [KeyboardButton(text="💳 Автоматизация Бизнеса"), KeyboardButton(text="📃 Каталог(PDF Файл)")],
        [KeyboardButton(text="🌟 Отзывы")]
    ],
    resize_keyboard=True
)
