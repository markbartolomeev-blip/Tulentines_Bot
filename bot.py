import asyncio
import random
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# ====== НАСТРОЙКИ ======

TOKEN = "8483249261:AAF2GFIHmJ2uBXvXgeYR_nDf1JJ-SuE_7LI"
ADMIN_ID = 1221509369

SHOWS_PRIORITY = [
    "Холостяк",
    "Любовь с первого взгляда",
    "Давай поженимся"
]

DRAW_TIME = datetime(
    2026, 2, 9, 12, 0,
    tzinfo=timezone(timedelta(hours=3))
)

# ====== ПЕРЕМЕННЫЕ ======

participants = {}
draw_done = False

bot = Bot(token=TOKEN)
dp = Dispatcher()

# ====== /start ======

@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id

    if user_id not in participants:
        participants[user_id] = {
            "username": message.from_user.username or f"id{user_id}",
            "show": None,
            "role": None,
            "partner": []
        }

        await bot.send_message(
            ADMIN_ID,
            "➕ Новая регистрация\n\n"
            f"👤 @{participants[user_id]['username']}\n"
            f"🆔 {user_id}\n"
            f"📊 Всего участников: {len(participants)}"
        )

        await message.answer(
            "💘 Ты зарегистрирован(а)!\n"
            "Ожидай жеребьёвку 💌"
        )
    else:
        await message.answer(
            "💗 Ты уже зарегистрирован(а)\n"
            "Ожидай жеребьёвку 💌"
        )

# ====== /list — очередь ======

@dp.message(Command("list"))
async def list_queue(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not participants:
        await message.answer("Очередь пуста")
        return

    text = f"📋 Очередь участников ({len(participants)}):\n\n"
    for i, data in enumerate(participants.values(), start=1):
        text += f"{i}. @{data['username']}\n"

    await message.answer(text)

# ====== /list_role — роли ======

@dp.message(Command("list_role"))
async def list_roles(message: Message):
    if message.from_user.id != ADMIN_ID:
        return

    if not draw_done:
        await message.answer("⏳ Жеребьёвка ещё не проведена")
        return

    text = "🎭 Роли участников:\n\n"
    for data in participants.values():
        text += f"@{data['username']} — {data['show']} — {data['role']}\n"

    await message.answer(text)

# ====== ЖЕРЕБЬЁВКА ======

async def draw_lottery():
    global draw_done

    if draw_done:
        return

    users = list(participants.keys())
    count = len(users)

    if count < 6:
        for uid in users:
            await bot.send_message(
                uid,
                "😔 К сожалению, для твоего шоу не хватило участников, сожалеем"
            )
        draw_done = True
        return

    random.shuffle(users)

    if count >= 9:
        shows = SHOWS_PRIORITY
        group_size = 3
    elif count == 8:
        shows = SHOWS_PRIORITY
        group_size = 2
    elif count == 7:
        shows = SHOWS_PRIORITY[:2]
        group_size = 2
    else:  # 6
        shows = SHOWS_PRIORITY[:2]
        group_size = 3

    index = 0

    for show in shows:
        group = users[index:index + group_size]
        index += group_size

        if len(group) < group_size:
            continue

        secret = random.choice(group)

        for uid in group:
            participants[uid]["show"] = show
            if uid == secret:
                participants[uid]["role"] = "Тайный Любовник"
            else:
                participants[uid]["role"] = "Обычный участник"
                participants[uid]["partner"] = [
                    participants[x]["username"] for x in group if x != uid
                ]

    # ====== РАССЫЛКА ======

    for uid, data in participants.items():
        if data["role"] == "Тайный Любовник":
            await bot.send_message(
                uid,
                f"🎉 Поздравляем, ты попал в шоу «{data['show']}»!\n"
                f"💗 Твоя роль — Тайный Любовник\n"
                f"💌 Храни тайну и подготовь 2 подарка до 200₽"
            )
        elif data["role"] == "Обычный участник":
            partners = ", ".join("@" + p for p in data["partner"])
            await bot.send_message(
                uid,
                f"🎉 Поздравляем, ты попал в шоу «{data['show']}»!\n"
                f"💗 Твоя роль — Обычный участник\n"
                f"😍 Твои напарники: {partners}\n"
                f"💌 Вычисли Тайного Любовника"
            )

    draw_done = True

# ====== ТАЙМЕР ======

async def scheduler():
    while not draw_done:
        now = datetime.now(timezone(timedelta(hours=3)))
        if now >= DRAW_TIME:
            await draw_lottery()
            break
        await asyncio.sleep(30)

# ====== ЗАПУСК ======

async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
