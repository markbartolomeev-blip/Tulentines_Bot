import asyncio
import re
import aiosqlite
from datetime import datetime, timedelta

from aiogram import Bot, Dispatcher, F
from aiogram.types import Message, ChatPermissions
from aiogram.enums import ParseMode
from aiogram.client.default import DefaultBotProperties
from aiogram.exceptions import TelegramBadRequest


TOKEN = "8483249261:AAF2GFIHmJ2uBXvXgeYR_nDf1JJ-SuE_7LI"
DB_NAME = "reputation.db"


# ================== АНТИ-ОБХОД ==================

def normalize(text: str) -> str:
    text = text.lower()
    text = text.replace("0", "o")
    text = text.replace("1", "i")
    text = text.replace("3", "e")
    text = re.sub(r"[^a-zа-яё]", "", text)
    return text


def contains_toji(text: str) -> bool:
    text = normalize(text)
    patterns = [
        "тоджи", "тожи", "тощи",
        "toji", "todji", "tozhi"
    ]
    return any(p in text for p in patterns)


# ================== БАЗА ==================

async def init_db():
    async with aiosqlite.connect(DB_NAME) as db:
        await db.execute("""
        CREATE TABLE IF NOT EXISTS users (
            user_id INTEGER,
            chat_id INTEGER,
            reputation INTEGER DEFAULT 100,
            violations INTEGER DEFAULT 0,
            last_violation TEXT,
            muted_until TEXT,
            PRIMARY KEY (user_id, chat_id)
        )
        """)
        await db.commit()


async def get_user(user_id, chat_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT reputation, violations, last_violation, muted_until FROM users WHERE user_id=? AND chat_id=?",
            (user_id, chat_id)
        )
        row = await cursor.fetchone()

        if row is None:
            await db.execute(
                "INSERT INTO users (user_id, chat_id) VALUES (?, ?)",
                (user_id, chat_id)
            )
            await db.commit()
            return 100, 0, None, None

        return row


async def update_user(user_id, chat_id, **kwargs):
    async with aiosqlite.connect(DB_NAME) as db:
        for key, value in kwargs.items():
            await db.execute(
                f"UPDATE users SET {key}=? WHERE user_id=? AND chat_id=?",
                (value, user_id, chat_id)
            )
        await db.commit()


async def get_top(chat_id):
    async with aiosqlite.connect(DB_NAME) as db:
        cursor = await db.execute(
            "SELECT user_id, reputation FROM users WHERE chat_id=? ORDER BY reputation DESC LIMIT 10",
            (chat_id,)
        )
        return await cursor.fetchall()


# ================== БОТ ==================

async def main():
    await init_db()

    bot = Bot(
        token=TOKEN,
        default=DefaultBotProperties(parse_mode=ParseMode.HTML)
    )
    dp = Dispatcher()

    # ===== ПРОВЕРКА СООБЩЕНИЙ =====

    @dp.message(F.text)
    async def check_message(message: Message):
        user_id = message.from_user.id
        chat_id = message.chat.id

        reputation, violations, last_violation, muted_until = await get_user(user_id, chat_id)
        now = datetime.utcnow()

        # ===== НЕДЕЛЬНЫЙ БОНУС =====
        if last_violation:
            last_time = datetime.fromisoformat(last_violation)
            if now - last_time >= timedelta(days=7):
                reputation += 10
                await update_user(
                    user_id,
                    chat_id,
                    reputation=reputation,
                    last_violation=None
                )
                await message.answer(
                    f"🎉 {message.from_user.mention_html()} получает +10 к репутации за неделю без нарушений!\n"
                    f"Репутация: <b>{reputation}</b>"
                )

        # ===== ПРОВЕРКА СЛОВА =====
        if contains_toji(message.text):

            try:
                await message.delete()
            except:
                pass

            reputation -= 10
            violations += 1

            await update_user(
                user_id,
                chat_id,
                reputation=reputation,
                violations=violations,
                last_violation=now.isoformat()
            )

            await message.answer(
                f"🚨 {message.from_user.mention_html()}, ты упомянул Тоджи!\n"
                f"-10 к репутации и 10 лет исправительных работ в колонии строгого режима!\n"
                f"Репутация: <b>{reputation}</b> | Нарушений: {violations}"
            )

            # ===== МУТ ИЛИ БАН =====
            if reputation <= 0:

                if not muted_until:
                    mute_until = now + timedelta(hours=24)

                    await message.chat.restrict(
                        user_id,
                        permissions=ChatPermissions(
                            can_send_messages=False
                        ),
                        until_date=mute_until
                    )

                    await update_user(
                        user_id,
                        chat_id,
                        muted_until=mute_until.isoformat()
                    )

                    await message.answer(
                        f"🔇 {message.from_user.mention_html()} получает мут на 24 часа."
                    )

                else:
                    await message.chat.ban(user_id)
                    await message.answer(
                        f"⛔ {message.from_user.mention_html()} был забанен окончательно."
                    )

    # ===== КОМАНДЫ =====

    @dp.message(F.text == "/rep")
    async def rep_command(message: Message):
        reputation, violations, _, _ = await get_user(message.from_user.id, message.chat.id)
        await message.answer(
            f"📊 {message.from_user.mention_html()}, твоя репутация: <b>{reputation}</b>\n"
            f"Нарушений: {violations}"
        )

    @dp.message(F.text == "/top")
    async def top_command(message: Message):
        top_users = await get_top(message.chat.id)

        if not top_users:
            await message.answer("Пока нет данных.")
            return

        text = "<b>🏆 Топ 10 по репутации:</b>\n\n"
        for i, (user_id, rep) in enumerate(top_users, start=1):
            text += f"{i}. ID <code>{user_id}</code> — {rep}\n"

        await message.answer(text)

    print("🚀 Toji Guard Bot запущен")
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
