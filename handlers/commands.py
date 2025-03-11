from aiogram import Router, types, F
from aiogram.filters.callback_data import CallbackData
from database.db_manager import get_products, add_to_cart, get_cart, clear_cart, remove_from_cart
from keyboards.inline import catalog_keyboard, cart_keyboard
from keyboards.reply import main_menu  # Исправленный импорт
from handlers.callbacks import ProductCallback, CartCallback
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, FSInputFile
import os

router = Router()

@router.message(F.text.startswith("/start"))
async def start(message: types.Message):
    await message.answer("Здравствуйте! Добро пожаловать в магазин! Выберите действие👇:", reply_markup=main_menu)

class ProductCallback(CallbackData, prefix="product"):
    product_id: int

class CartCallback(CallbackData, prefix="cart"):
    action: str
    product_id: int

@router.message(F.text == "📦 Каталог")
async def show_catalog(message: types.Message):
    products = get_products()
    if not products:
        await message.answer("Каталог пуст.")
        return
    keyboard = catalog_keyboard(products)
    await message.answer("Выберите товар:", reply_markup=keyboard)

@router.callback_query(ProductCallback.filter())
async def show_product_details(callback_query: types.CallbackQuery, callback_data: ProductCallback):
    products = get_products()

    for product in products:
        product_id, name, description, price, image_path = product

        if product_id == callback_data.product_id:
            text = f"<b>{name}</b>\n{description}\n💰 Цена: {price} $"
            keyboard = cart_keyboard([(product_id, name, price, 1)])

            # ➕ Добавляем кнопку "Назад в каталог"
            keyboard.inline_keyboard.append([
                InlineKeyboardButton(text="🔙 Назад в каталог", callback_data="back_to_catalog")
            ])

            # ✅ Удаляем старый каталог (если он есть)
            try:
                await callback_query.message.delete()
            except Exception as e:
                print(f"⚠️ Ошибка удаления старого каталога: {e}")

            # ✅ Отправляем новый товар с фото
            if os.path.exists(image_path):
                try:
                    photo = FSInputFile(image_path)
                    await callback_query.message.answer_photo(photo, caption=text, parse_mode="HTML", reply_markup=keyboard)
                except Exception as e:
                    print(f"Ошибка отправки фото: {e}")
                    await callback_query.message.answer("⚠️ Ошибка загрузки фото!", parse_mode="HTML", reply_markup=keyboard)
            else:
                print(f"Файл не найден: {image_path}")
                await callback_query.message.answer("⚠️ Файл с фото не найден!", parse_mode="HTML", reply_markup=keyboard)

            await callback_query.answer()
            return


@router.callback_query(F.data == "back_to_catalog")
async def back_to_catalog(callback_query: types.CallbackQuery):
    products = get_products()
    keyboard = catalog_keyboard(products)

    try:
        # Если сообщение текстовое — редактируем
        await callback_query.message.edit_text("📦 Каталог товаров:", reply_markup=keyboard)
    except Exception:
        # Если сообщение было фото, удаляем его и отправляем новый каталог
        await callback_query.message.delete()
        await callback_query.message.answer("📦 Каталог товаров:", reply_markup=keyboard)

    await callback_query.answer()


@router.callback_query(CartCallback.filter())
async def process_cart_action(callback_query: types.CallbackQuery, callback_data: CartCallback):
    user_id = callback_query.from_user.id
    product_id = callback_data.product_id
    action = callback_data.action

    cart_items = get_cart(user_id)
    cart_dict = {item[0]: item for item in cart_items}

    if action == "add":
        add_to_cart(user_id, product_id)
        await callback_query.answer("✅ Товар добавлен!")
    elif action == "decrease":
        if product_id in cart_dict and cart_dict[product_id][3] > 1:
            remove_from_cart(user_id, product_id)
            await callback_query.answer("➖ Количество уменьшено!")
        else:
            remove_from_cart(user_id, product_id)
            await callback_query.answer("❌ Товар удалён из корзины!")

    await show_cart(callback_query.message, edit=True)

@router.message(F.text == "🛒 Корзина")
async def open_cart(message: types.Message):
    await show_cart(message)

@router.callback_query(lambda c: c.data == "open_cart")
async def show_cart_callback(callback_query: types.CallbackQuery):
    await show_cart(callback_query.message, edit=True)
    await callback_query.answer()

async def show_cart(message: types.Message, edit=False):
    user_id = message.chat.id
    cart_items = get_cart(user_id)

    if not cart_items:
        text = "🛒 Ваша корзина пуста."
        if edit:
            try:
                await message.edit_text(text)
            except:
                await message.answer(text)
        else:
            await message.answer(text)
        return

    cart_text = "🛍️ <b>Ваша корзина:</b>\n\n"
    total_price = sum(price * quantity for _, _, price, quantity in cart_items)
    cart_text += "\n".join(
        f"{name} - {quantity} шт. × {price} $ = {quantity * price} $" for _, name, price, quantity in cart_items)
    cart_text += f"\n\n💰 <b>Итого: {total_price} $</b>"

    keyboard = cart_keyboard(cart_items)
    if edit:
        try:
            await message.edit_text(cart_text, parse_mode="HTML", reply_markup=keyboard)
        except:
            await message.answer(cart_text, parse_mode="HTML", reply_markup=keyboard)
    else:
        await message.answer(cart_text, parse_mode="HTML", reply_markup=keyboard)

@router.callback_query(lambda c: c.data == "clear_cart")
async def clear_cart_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    clear_cart(user_id)
    await callback_query.answer("🗑 Корзина очищена!")
    await show_cart(callback_query.message, edit=True)

@router.callback_query(lambda c: c.data == "checkout")
async def checkout_callback(callback_query: types.CallbackQuery):
    user_id = callback_query.from_user.id
    username = callback_query.from_user.username or "Без имени"
    cart_items = get_cart(user_id)

    if not cart_items:
        await callback_query.answer("Ваша корзина пуста!")
        return

    order_text = f"🛍 <b>Новый заказ!</b>\n\n👤 <b>Покупатель:</b> @{username} (ID: <code>{user_id}</code>)\n\n"
    total_price = sum(price * quantity for _, _, price, quantity in cart_items)

    order_text += "\n".join(
        f"📌 {name} - {quantity} шт. × {price} $ = {quantity * price} $"
        for _, name, price, quantity in cart_items
    )

    order_text += f"\n\n💰 <b>Итого: {total_price} $</b>\n📩 Потенциальный клиент"

    ADMIN_ID = 1921904628
    await callback_query.bot.send_message(ADMIN_ID, order_text, parse_mode="HTML")

    clear_cart(user_id)

    await callback_query.message.edit_text("✅ Ваш заказ отправлен администратору! Ожидайте подтверждения.", parse_mode="HTML")

@router.message(F.text == "📄 Маркетинг План")
async def send_marketing_plan(message: types.Message):
    pdf_path = "static/files/маркетинг_новый_2025.pdf"
    if not os.path.exists(pdf_path):
        await message.answer("❌ Ошибка: файл не найден. Проверь путь.")
        return
    pdf_file = FSInputFile(pdf_path)
    await message.answer_document(pdf_file, caption="📑 Маркетинг-план на 2025 год")

@router.message(F.text == "📃 Каталог(PDF Файл)")
async def send_catalog(message: types.Message):
    pdf_path = "static/files/каталог_m_int.pdf"
    if not os.path.exists(pdf_path):
        await message.answer("❌ Ошибка: файл не найден. Проверь путь.")
        return
    pdf_file = FSInputFile(pdf_path)
    await message.answer_document(pdf_file, caption="📑 Каталог")

@router.message(F.text == "💳 Автоматизация Бизнеса")
async def automation_products(message: types.Message):
    text = (
        "🔗 [Ссылка на автоматический набор трафика](https://clck.ru/3DJRfa)\n\n"
        "☝️ Устанавливайте и подписчиков в ВК станет значительно больше! "
        "А это ваши потенциальные партнеры."
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)


@router.message(F.text == "🧾 Сертификаты на Товары")
async def Sertif(message: types.Message):
    text = (
        "‼️ Ссылки на российские декларации-соответствия по юр.компаниям, указанным на сертификатах:\n\n"
        "✨ [M International SDN BHD (MY)](https://декларации-соответствия.рус/kompaniya/m-international-sdn-bhd-my/)\n"
        "✨ [Everlasting Food Industries SDN BHD](https://декларации-соответствия.рус/kompaniya/everlasting-food-industries-sdnbhd/)\n"
        "✨ [Green NatureCare Foods Manufacturer SDN BHD](https://декларации-соответствия.рус/kompaniya/green-naturecare-foods-manufacturer-sdn-bhd/)\n\n"
        "✅ Вся продукция прошла проверку на соответствие российскими лабораториями по запросам от иных юридических компаний!"
    )
    await message.answer(text, parse_mode="Markdown", disable_web_page_preview=True)




@router.message(lambda message: message.text == "ℹ О нас")
async def about_company(message: types.Message):
    text = (
        "<b>M INFO | О КОМПАНИИ</b>\n\n"
        "📆 <b>ДАТА ОСНОВАНИЯ M International:</b>\n"
        "• Февраль 2019 г.\n\n"
        "🚀 <b>ОСНОВАТЕЛИ</b> 🚀\n\n"
        "• <b>Барбара Кабуки</b> -\n"
        " - Президент «M International»\n"
        " - Уроженка Японии\n"
        " - Бизнес Wooman\n"
        " - Владелица 65 % всех LUX Отелей на территории Японии\n"
        " - Миллиардер\n\n"
        "• <b>Мистер Ли</b> -\n"
        " - Сооснователь «M International»\n"
        " - Уроженец Малайзии\n"
        " - Бизнесмен\n"
        " - Блокчейн эксперт\n"
        " - Крипто эксперт\n"
        " - Миллиардер\n\n"
        "• <b>Эстер Вонг</b> -\n"
        " - Уроженец Малайзии\n"
        " - Более 10 лет в управлении Компании Amway\n\n"
        "• <b>Мачо Янг (Энххишиг Баярболд)</b>\n"
        " - CVO, Директор по стратегическому Планированию и Развитию «M International»\n"
        " - Уроженец Монголии\n"
        " - ТОП Лидер международного уровня\n"
        " - Амбициозная личность с Человеческими Принципами и Предпринимательской порядочностью\n"
        " - Миллионер\n\n"
        "#окомпании"
    )

    image_path = "static/images/logo.jpg"
    if os.path.exists(image_path):
        photo = FSInputFile(image_path)
        await message.answer_photo(photo, caption=text, parse_mode="HTML")
    else:
        await message.answer("⚠️ Файл с фото не найден!", parse_mode="HTML")

@router.message(lambda message: message.text == "🌟 Отзывы")
async def send_info(message: types.Message):
    text = "Вот отзывы\n\nСсылка: https://t.me/+k1Md-ltI29RkOWVi"
    await message.answer(text)

@router.message(F.text == "📞 Контакты")
async def send_contacts(message: types.Message):
    text = "📞 Контакты:\n\n☎ +7 937 328-21-99\n☎ +7 937 150-65-98"
    await message.answer(text)






