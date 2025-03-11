from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton
from handlers.callbacks import ProductCallback, CartCallback


def catalog_keyboard(products):
    """Генерирует клавиатуру каталога с товарами"""
    keyboard = []

    print(f"Received products: {products}")  # Отладочный вывод

    for item in products:
        if len(item) < 3:
            print(f"Ошибка: в {item} меньше 3 элементов!")
            continue  # Пропускаем некорректные данные

        product_id, name, price, *extra = item  # Берём первые 3 значения

        keyboard.append([
            InlineKeyboardButton(
                text=f"{name} - {price} ",
                callback_data=ProductCallback(product_id=product_id).pack()
            )
        ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)  # ЭТОГО НЕ БЫЛО



def cart_keyboard(cart_items):
    """Генерирует клавиатуру для корзины"""
    keyboard = []

    for product_id, name, price, quantity in cart_items:
        keyboard.append([
            InlineKeyboardButton(text="➖", callback_data=CartCallback(action="decrease", product_id=product_id).pack()),
            InlineKeyboardButton(text=f"{name} - {quantity} шт.", callback_data="ignore"),
            InlineKeyboardButton(text="➕", callback_data=CartCallback(action="add", product_id=product_id).pack())
        ])

    keyboard.append([
        InlineKeyboardButton(text="🗑 Очистить", callback_data="clear_cart"),
        InlineKeyboardButton(text="✅ Оформить", callback_data="checkout"),

    ])

    return InlineKeyboardMarkup(inline_keyboard=keyboard)


def back_to_catalog_keyboard():
    """Кнопка для возврата в каталог"""
    return InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="🔙 Назад в каталог", callback_data="open_catalog")]
        ]
    )
