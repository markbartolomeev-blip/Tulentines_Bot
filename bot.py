import asyncio
import random
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher
from aiogram.filters import Command
from aiogram.types import Message

# ----------------- НАСТРОЙКИ -----------------
TOKEN = "8483249261:AAF2GFIHmJ2uBXvXgeYR_nDf1JJ-SuE_7LI"
ADMIN_ID = 1221509369

bot = Bot(TOKEN)
dp = Dispatcher()

participants = {}  # user_id -> {"username":..., "role":..., "show":..., "partner":...}
draw_done = False

SHOWS_PRIORITY = [
    "Холостяк",
    "Любовь с первого взгляда",
    "Давай поженимся"
]

SARATOV_TZ = timezone(timedelta(hours=4))
DRAW_TIME = datetime(2026, 2, 9, 12, 0, tzinfo=SARATOV_TZ)

# ----------------- /start -----------------
@dp.message(Command("start"))
async def start(message: Message):
    user_id = message.from_user.id
    if user_id in participants:
        await message.answer("Ты уже зарегистрирован 😉")
        return

    participants[user_id] = {
        "username": message.from_user.username or "без_юзернейма",
        "role": None,
        "show": None,
        "partner": None
    }
    await message.answer(
        "🎬 Ты зарегистрирован! Жди жеребьёвку 9 февраля в 12:00 💘"
    )

# ----------------- /list (админ) -----------------
@dp.message(Command("list"))
async def list_players(message: Message):
    if message.from_user.id != ADMIN_ID:
        return
    text = "📋 Участники (без Тайных Любовников):\n\n"
    for data in participants.values():
        if data["role"] == "Обычный участник":
            text += f"@{data['username']} — {data['show']}\n"
    await message.answer(text or "Пока данных нет")

# ----------------- Жеребьёвка -----------------
async def draw_lottery():
    global draw_done
    if draw_done:
        return

    users = list(participants.keys())
    count = len(users)

    if count < 7:
        for uid in users:
            await bot.send_message(uid, "😔 К сожалению, для твоего шоу не хватило участников, сожалеем")
        draw_done = True
        return

    random.shuffle(users)

    # Определяем какие шоу использовать
    if count >= 9:
        shows = SHOWS_PRIORITY
    elif count == 8:
        shows = SHOWS_PRIORITY
    else:  # 7 человек
        shows = SHOWS_PRIORITY[:2]

    index = 0
    for show in shows:
        if index + 2 > count:
            break

        pair = users[index:index + 2]
        index += 2

        lover = random.choice(pair)
        normal = pair[0] if pair[1] == lover else pair[1]

        participants[lover]["role"] = "Тайный Любовник"
        participants[lover]["show"] = show

        participants[normal]["role"] = "Обычный участник"
        participants[normal]["show"] = show
        participants[normal]["partner"] = lover

    # Отправка сообщений участникам
    for uid, data in participants.items():
        if data["role"] == "Тайный Любовник":
            await bot.send_message(
                uid,
                f"🎉 Поздравляем, ты попал в шоу «{data['show']}»!\n"
                f"💗 Твоя роль — Тайный Любовник\n"
                f"💌 Твоя задача: хранить тайну и подготовить 2 подарка общей суммой до 200₽"
            )
        elif data["role"] == "Обычный участник":
            partner_username = participants[data["partner"]]["username"]
            await bot.send_message(
                uid,
                f"🎉 Поздравляем, ты попал в шоу «{data['show']}»!\n"
                f"💗 Твоя роль — Обычный участник\n"
                f"😍 Твой напарник/напарница — @{partner_username}\n"
                f"💌 Твоя задача: вместе вычислить Тайного Любовника"
            )

    draw_done = True

# ----------------- Смотрим время жеребьёвки -----------------
async def scheduler():
    now = datetime.now(SARATOV_TZ)
    delay = (DRAW_TIME - now).total_seconds()
    if delay > 0:
        print(f"Ждём жеребьёвку {delay} секунд...")
        await asyncio.sleep(delay)
    print("Запускаем жеребьёвку!")
    await draw_lottery()

# ----------------- Запуск бота -----------------
async def main():
    asyncio.create_task(scheduler())
    await dp.start_polling(bot)

if __name__ == "__main__":
    asyncio.run(main())
