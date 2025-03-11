import sqlite3

DB_PATH = "database/inventory.db"


def init_db():
    """Создает базу данных и добавляет стартовые продукты, если они отсутствуют."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    # Создание таблицы товаров без stock
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS products (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT UNIQUE NOT NULL,
            description TEXT NOT NULL,
            price REAL NOT NULL,
            image_path TEXT NOT NULL
        )
    """)

    # Создание таблицы корзины
    cursor.execute("""
        CREATE TABLE IF NOT EXISTS cart (
            user_id INTEGER NOT NULL,
            product_id INTEGER NOT NULL,
            quantity INTEGER NOT NULL DEFAULT 1,
            PRIMARY KEY (user_id, product_id),
            FOREIGN KEY (product_id) REFERENCES products (id) ON DELETE CASCADE
        )
    """)

    conn.commit()
    conn.close()
    add_default_products()  # Добавляем стартовые продукты


def add_product(name, description, price, image_path):
    """Добавляет новый продукт в базу данных."""
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT OR IGNORE INTO products (name, description, price, image_path)
        VALUES (?, ?, ?, ?)
    """, (name, description, price, image_path))

    conn.commit()
    conn.close()

def add_default_products():
    """Добавляет стартовые продукты, если их нет в базе."""
    products = [
        ("NutriMAX",
         "100% натуральный и полезный напиток.\n"
         "NutriMAX - комплекс полноценного питания, который отлично вписывается "
         "в ритм жизни каждого современного человека, это оптимальное решение "
         "при условии напряжённого графика и нехватки времени.",
         71.0, "static/images/nutrimax.jpg"),

        ("GreenMAX",
         "Безопасный, здоровый и удобный способ очистить и восстановить "
         "естественный баланс и сияние вашего тела.\n"
         "Специальная запатентованная формула GreenMAX помогает очищению и оздоровлению кишечника, "
         "способствует избавлению от лишнего веса, выводит токсины.",
         73.0, "static/images/greenmax.jpg"),

        ("MiMAX",
         "Омоложение и здоровый образ жизни.\n"
         "Растительный комплекс с антиоксидантами, замедляет старение.\n"
         "Содержит ресвератрол - природный полифенол, обладающий антиканцерогенными свойствами.",
         73.0, "static/images/mimax.jpg"),

        ("BluMAX",
         "Тонус иммунной системы, противовоспалительное средство.\n"
         "BluMAX - 100% мощный антиоксидант, снижает риск сердечных заболеваний, "
         "активирует иммунные клетки, улучшает здоровье дыхательных путей.",
         73.0, "static/images/blumax.jpg"),

        ("KordyMAX",
         "Инновационный эликсир с 16-тью видами аминокислот + 100 мг свободного селена.\n"
         "Обладает противоопухолевым действием, регулирует уровень липидов в крови, "
         "восстанавливает функцию почек.",
         73.0, "static/images/kordymax.jpg"),

        ("FlexiMAX",
         "Уникальное средство для укрепления здоровья суставов и костей, устраняет симптомы воспаления, облегчает болевой синдром .\n"
         "Показания к приему FlexiМАХ - это артриты, артрозы, остеопорозы, иные проблемы с соединительными тканями организма и костями, а также проблемы с печенью. Продукт 100% натуральный и очень эффективный.",
         73.0, "static/images/fleximax.jpg"),

        ("MachoMan",
         "Сексуальное здоровье - важная часть качества жизни мужчины, особенно для людей старше 30 лет.\n"
         "МасhoMAN - наша лучшая в своем классе мужская формула с научно доказанными активными ингредиентами, поддерживает общее мужское сексуальное здоровье и обеспечивает здоровый кровоток. ",
         73.0, "static/images/machoman.jpg"),

        ("E-Katerina",
         "Гель для интимной гигиены и женского здоровья.\n"
         "Натуральный состав из идеально подобранных экстрактов трав суникальными свойствами. "
         "Ye-Katerina помогает регулировать менструальный цикл, ликвидирует  неприятные выделения из влагалища и запахи, тонизирует и сужает стенки влагалища, увеличивает уровень тестостерона и сексуальность, устраняет гормональный дисбаланс и вагинальный зуд, раздражение влагалища, сухость и кандидоз, укрепляет грудь и ткани молочных желез (после нескольких месяцев использования), облегчает менопаузу.",
         39.26, "static/images/e-katerina.jpg"),

    ]

    for product in products:
        add_product(*product)


# ✅ Получение всех товаров (с ID и фото)
def get_products():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name, description, price, image_path FROM products")
    products = cursor.fetchall()
    conn.close()
    return products


def update_product(product_id, name=None, description=None, price=None, image_path=None):
    with sqlite3.connect(DB_PATH) as conn:
        cursor = conn.cursor()

        updates = []
        values = []

        if name:
            updates.append("name = ?")
            values.append(name)
        if description:
            updates.append("description = ?")
            values.append(description)
        if price is not None:
            updates.append("price = ?")
            values.append(price)
        if image_path:
            updates.append("image_path = ?")
            values.append(image_path)

        if updates:
            values.append(product_id)
            query = f"UPDATE products SET {', '.join(updates)} WHERE id = ?"
            cursor.execute(query, values)
            conn.commit()


# ✅ Удаление товара по ID
def delete_product(product_id):
    conn = sqlite3.connect(DB_PATH, check_same_thread=False)
    cursor = conn.cursor()

    cursor.execute("DELETE FROM cart WHERE product_id = ?", (product_id,))
    cursor.execute("DELETE FROM products WHERE id = ?", (product_id,))

    conn.commit()
    conn.close()
    print(f"🗑 Удалён товар ID {product_id}")  # 👈 Логирование





# ✅ Получение всех товаров (для удаления)
def get_all_products():
    """Получает список всех товаров с ID и названием"""
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("SELECT id, name FROM products")
    products = cursor.fetchall()
    conn.close()
    return products


# ✅ Добавление товара в корзину
def add_to_cart(user_id, product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        INSERT INTO cart (user_id, product_id, quantity)
        VALUES (?, ?, 1)
        ON CONFLICT(user_id, product_id) DO UPDATE SET quantity = quantity + 1
    """, (user_id, product_id))
    conn.commit()
    conn.close()


# ✅ Уменьшение количества товара в корзине
def remove_from_cart(user_id, product_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("SELECT quantity FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))
    result = cursor.fetchone()

    if result is None:
        conn.close()
        return

    quantity = result[0]

    if quantity > 1:
        cursor.execute("UPDATE cart SET quantity = quantity - 1 WHERE user_id = ? AND product_id = ?",
                       (user_id, product_id))
    else:
        cursor.execute("DELETE FROM cart WHERE user_id = ? AND product_id = ?", (user_id, product_id))

    conn.commit()
    conn.close()


# ✅ Получение содержимого корзины
def get_cart(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        SELECT DISTINCT products.id, products.name, products.price, cart.quantity 
        FROM cart 
        JOIN products ON cart.product_id = products.id 
        WHERE cart.user_id = ?
    """, (user_id,))
    items = cursor.fetchall()
    conn.close()
    return items



def clear_cart(user_id):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("DELETE FROM cart WHERE user_id = ?", (user_id,))
    conn.commit()
    conn.close()

def remove_cart_duplicates():
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()
    cursor.execute("""
        DELETE FROM cart
        WHERE rowid NOT IN (
            SELECT MIN(rowid) FROM cart GROUP BY user_id, product_id
        )
    """)
    conn.commit()
    conn.close()


init_db()
remove_cart_duplicates()