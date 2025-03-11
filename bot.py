import asyncio
import logging
from aiogram import Dispatcher
from data.loader import bot, dp
from database.db_manager import init_db
from handlers import commands, callbacks, admin_handlers

logging.basicConfig(level=logging.INFO)


async def main():
    init_db()

    dp.include_router(commands.router)
    dp.include_router(admin_handlers.router)
    dp.include_router(callbacks.router)



    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())

