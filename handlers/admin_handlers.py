from aiogram import Router, types, F
from aiogram.fsm.context import FSMContext
from aiogram.fsm.state import StatesGroup, State
from aiogram.types import InlineKeyboardMarkup, InlineKeyboardButton, ReplyKeyboardMarkup, KeyboardButton
from database.db_manager import add_product, get_products, delete_product
from aiogram.filters import Command

ADMIN_ID = 1921904628  # ID админа
router = Router()

admin_keyboard = ReplyKeyboardMarkup(
    keyboard=[
        [KeyboardButton(text="➕ Добавить товар"), KeyboardButton(text="🗑 Удалить товар")],
        [KeyboardButton(text="📜 Показать каталог"), KeyboardButton(text="✏ Редактировать товар")]

    ],
    resize_keyboard=True
)

# 🚀 Команда для входа в админ-панель
@router.message(Command("admin"))
async def admin_panel(message: types.Message):
    print(f"👤 Ваш ID: {message.from_user.id} (ADMIN_ID = {ADMIN_ID})")  # Лог в консоль
    if message.from_user.id != ADMIN_ID:
        await message.answer("⛔ У вас нет прав доступа!")
        return
    await message.answer("🔧 Добро пожаловать в админ-панель! Выберите действие:", reply_markup=admin_keyboard)


# 📌 Машина состояний для добавления товара
class AddProductState(StatesGroup):
    name = State()
    description = State()
    price = State()
    photo = State()


# ➕ Добавление товара
@router.message(F.text == "➕ Добавить товар")
async def cmd_add_product(message: types.Message, state: FSMContext):
    await state.set_state(AddProductState.name)
    await message.answer("📝 Введите название товара:")

@router.message(AddProductState.name)
async def process_name(message: types.Message, state: FSMContext):
    await state.update_data(name=message.text)
    await state.set_state(AddProductState.description)
    await message.answer("✏ Введите описание товара:")

@router.message(AddProductState.description)
async def process_description(message: types.Message, state: FSMContext):
    await state.update_data(description=message.text)
    await state.set_state(AddProductState.price)
    await message.answer("💰 Введите цену товара (в долларах):")

@router.message(AddProductState.price)
async def process_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        await state.update_data(price=price)
        await state.set_state(AddProductState.photo)
        await message.answer("📸 Отправьте фото товара:")
    except ValueError:
        await message.answer("⚠ Ошибка! Введите число (например, 199.99):")

@router.message(AddProductState.photo, F.photo)
async def process_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_path = f"static/images/{data['name'].replace(' ', '_').lower()}.jpg"

    # Скачиваем фото
    await message.bot.download(message.photo[-1], destination=photo_path)

    # Добавляем в БД
    add_product(
        name=data['name'],
        description=data['description'],
        price=data['price'],
        image_path=photo_path
    )

    await message.answer("✅ Товар успешно добавлен в каталог!", reply_markup=admin_keyboard)
    await state.clear()


# 🗑 Удаление товара
@router.message(F.text == "🗑 Удалить товар")
async def cmd_delete_product(message: types.Message):
    products = get_products()
    if not products:
        await message.answer("❌ В каталоге нет товаров для удаления.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"delete_{product_id}")]
            for product_id, name, *_ in products
        ]
    )
    for product_id, name, *_ in products:
        print(f"✅ Кнопка: {name} -> delete_{product_id}")
    await message.answer("Выберите товар для удаления:", reply_markup=keyboard)



@router.callback_query(lambda c: c.data and c.data.startswith("delete_"))
async def confirm_delete_product(callback: types.CallbackQuery):
    product_id = callback.data.replace("delete_", "")
    print(f"🛑 Подтверждение удаления товара ID {product_id}")

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [
                InlineKeyboardButton(text="✅ Да", callback_data=f"confirm_delete_{product_id}"),
                InlineKeyboardButton(text="❌ Нет", callback_data="cancel_delete")
            ]
        ]
    )

    await callback.message.edit_text(f"❗ Вы уверены, что хотите удалить товар?", reply_markup=keyboard)
    await callback.answer("Выберите действие")  # Telegram не должен зависать


# 🗑️ Удаление товара после подтверждения
@router.callback_query(F.data.startswith("confirm_delete_"))
async def delete_selected_product(callback: types.CallbackQuery):
    product_id = int(callback.data.replace("confirm_delete_", ""))  # Приводим к int
    print(f"❌ Удаление товара ID {product_id}")  # Лог в консоль

    delete_product(product_id)  # Удаляем из базы
    await callback.message.edit_text("✅ Товар удалён.")  # Без клавиатуры, чтобы избежать ошибки
    await callback.message.answer("🔧 Выберите действие:", reply_markup=admin_keyboard)
    await callback.answer("")


# ❌ Отмена удаления
@router.callback_query(F.data == "cancel_delete")
async def cancel_delete(callback: types.CallbackQuery):
    await callback.message.edit_text("❌ Удаление отменено.", reply_markup=None)  # Убираем inline-кнопку
    await callback.message.answer("🔧 Выберите действие:", reply_markup=admin_keyboard)  # Новое сообщение с ReplyKeyboardMarkup
    await callback.answer()


# 📜 Показать каталог
@router.message(F.text == "📜 Показать каталог")
async def show_catalog(message: types.Message):
    products = get_products()
    if not products:
        await message.answer("❌ В каталоге пока нет товаров.")
        return

    text = "📦 *Каталог товаров:*\n\n"
    for product in products:
        product_id, name, description, price, *_ = product
        text += f"🔹 *{name}*\n💰 {price} $.\n📜 {description}\n\n"

    await message.answer(text, parse_mode="Markdown")

from database.db_manager import update_product  # Импортируем функцию обновления
class EditProductState(StatesGroup):
    product_id = State()
    edit_choice = State()
    name = State()
    description = State()
    price = State()
    photo = State()

# ✏ Кнопка "Редактировать товар"
@router.message(F.text == "✏ Редактировать товар")
async def cmd_edit_product(message: types.Message):
    products = get_products()
    if not products:
        await message.answer("❌ В каталоге нет товаров для редактирования.")
        return

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text=name, callback_data=f"edit_{product_id}")]
            for product_id, name, *_ in products
        ]
    )
    await message.answer("Выберите товар для редактирования:", reply_markup=keyboard)

# 📝 Выбор товара для редактирования
@router.callback_query(F.data.startswith("edit_"))
async def edit_product_menu(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[1])  # Исправлено на правильное извлечение ID
    await state.update_data(product_id=product_id)

    keyboard = InlineKeyboardMarkup(
        inline_keyboard=[
            [InlineKeyboardButton(text="✏ Изменить название", callback_data=f"change_name_{product_id}")],
            [InlineKeyboardButton(text="📜 Изменить описание", callback_data=f"change_description_{product_id}")],
            [InlineKeyboardButton(text="💰 Изменить цену", callback_data=f"change_price_{product_id}")],
            [InlineKeyboardButton(text="📸 Изменить фото", callback_data=f"change_photo_{product_id}")],
            [InlineKeyboardButton(text="❌ Отмена", callback_data="cancel_edit")]
        ]
    )

    await state.set_state(EditProductState.edit_choice)
    await callback.message.edit_text("Что вы хотите изменить?", reply_markup=keyboard)
    await callback.answer()

# 📝 Изменение Названия
@router.callback_query(F.data.startswith("change_name_"))
async def edit_name(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])  # Исправлено
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductState.name)
    await callback.message.edit_text("📝 Введите новое название товара:")
    await callback.answer()

@router.message(EditProductState.name)
async def process_edit_name(message: types.Message, state: FSMContext):
    data = await state.get_data()
    update_product(data["product_id"], name=message.text)

    await message.answer("✅ Название успешно обновлено!", reply_markup=admin_keyboard)
    await state.clear()

# 📜 Изменение Описания
@router.callback_query(F.data.startswith("change_description_"))
async def edit_description(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])  # Исправлено
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductState.description)
    await callback.message.edit_text("📜 Введите новое описание товара:")
    await callback.answer()

@router.message(EditProductState.description)
async def process_edit_description(message: types.Message, state: FSMContext):
    data = await state.get_data()
    update_product(data["product_id"], description=message.text)

    await message.answer("✅ Описание успешно обновлено!", reply_markup=admin_keyboard)
    await state.clear()

# 💰 Изменение Цены
@router.callback_query(F.data.startswith("change_price_"))
async def edit_price(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])  # Исправлено
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductState.price)
    await callback.message.edit_text("💰 Введите новую цену товара (в $(долларах)):")
    await callback.answer()

@router.message(EditProductState.price)
async def process_edit_price(message: types.Message, state: FSMContext):
    try:
        price = float(message.text)
        data = await state.get_data()
        update_product(data["product_id"], price=price)

        await message.answer("✅ Цена успешно обновлена!", reply_markup=admin_keyboard)
        await state.clear()
    except ValueError:
        await message.answer("⚠ Ошибка! Введите число (например, 199.99):")

# 📸 Изменение Фото
@router.callback_query(F.data.startswith("change_photo_"))
async def edit_photo(callback: types.CallbackQuery, state: FSMContext):
    product_id = int(callback.data.split("_")[2])  # Исправлено
    await state.update_data(product_id=product_id)
    await state.set_state(EditProductState.photo)
    await callback.message.edit_text("📸 Отправьте новое фото товара:")
    await callback.answer()

@router.message(EditProductState.photo, F.photo)
async def process_edit_photo(message: types.Message, state: FSMContext):
    data = await state.get_data()
    photo_path = f"static/images/product_{data['product_id']}.jpg"

    await message.bot.download(message.photo[-1], destination=photo_path)
    update_product(data["product_id"], image_path=photo_path)

    await message.answer("✅ Фото успешно обновлено!", reply_markup=admin_keyboard)
    await state.clear()


@router.callback_query(F.data == "cancel_edit")
async def cancel_edit(callback: types.CallbackQuery, state: FSMContext):
    await callback.message.edit_text("❌ Редактирование отменено.")
    await callback.message.answer("🔧 Выберите действие:", reply_markup=admin_keyboard)
    await state.clear()
    await callback.answer()



