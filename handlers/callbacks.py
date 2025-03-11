from aiogram import Router, types
from data.loader import bot, ADMIN_ID

router = Router()

@router.callback_query()
async def handle_callback(query: types.CallbackQuery):
    action, product_id = query.data.split("_")

    if action == "add":
        await query.answer("Товар добавлен в корзину!")
    elif action == "remove":
        await query.answer("Товар удален из корзины!")
    elif action == "checkout":
        await bot.send_message(ADMIN_ID, "🔔 Новый заказ!")
        await query.answer("Заказ отправлен!")

from aiogram.filters.callback_data import CallbackData

class ProductCallback(CallbackData, prefix="product"):
    product_id: int

class CartCallback(CallbackData, prefix="cart"):
    action: str
    product_id: int

