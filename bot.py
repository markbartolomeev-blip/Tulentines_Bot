import asyncio
import random
from datetime import datetime, timezone, timedelta

from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

TOKEN = "8483249261:AAF2GFIHmJ2uBXvXgeYR_nDf1JJ-SuE_7LI"

bot = Bot(token=TOKEN)
dp = Dispatcher()

letters = {}

SARATOV_TZ = timezone(timedelta(hours=4))
SEND_TIME = datetime(2026, 2, 14, 0, 0, 0, tzinfo=SARATOV_TZ)

sent = False


def now_saratov():
    return datetime.now(SARATOV_TZ)


def is_before_send_time():
    return now_saratov() < SEND_TIME


@dp.message(Command("start"))
async def start(msg: types.Message):
    await msg.answer(
        "Привет! 💘\n"
        "Это бот анонимных валентинок.\n\n"
        "Ты можешь отправить только 1 валентинку.\n"
        "14 февраля в 00:00 по Саратову она будет отправлена случайному человеку 💌\n\n"
        "Команды:\n"
        "/send — написать валентинку 💝\n"
        "/check — статус"
    )


@dp.message(Command("send"))
async def send(msg: types.Message):
    if not is_before_send_time():
        await msg.answer("⛔ Приём валентинок уже закрыт.")
        return
    if msg.from_user.id in letters:
        await msg.answer("💔 Ты уже отправил валентинку.")
        return
    await msg.answer("Напиши свою валентинку 💌")


@dp.message()
async def save_letter(msg: types.Message):
    if msg.text.startswith("/"):
        return

    if not is_before_send_time():
        await msg.answer("⛔ Валентинки больше не принимаются.")
        return
    if msg.from_user.id in letters:
        await msg.answer("💔 Ты уже отправил валентинку.")
        return

    letters[msg.from_user.id] = msg.text
    await msg.answer("💖 Валентинка сохранена! Жди 14 февраля 🎁")


@dp.message(Command("check"))
async def check(msg: types.Message):
    if msg.from_user.id in letters:
        await msg.answer("💘 Твоя валентинка сохранена.")
    else:
        await msg.answer("Ты ещё не написал валентинку 😢")


async def send_valentines():
    global sent
    while True:
        if not sent and now_saratov() >= SEND_TIME and len(letters) > 1:
            users = list(letters.keys())
            texts = list(letters.values())

            shuffled = texts.copy()
            while True:
                random.shuffle(shuffled)
                if all(texts[i] != shuffled[i] for i in range(len(texts))):
                    break

            for i, user_id in enumerate(users):
                await bot.send_message(
                    user_id,
                    "💌 Тебе пришла валентинка:\n\n" + shuffled[i]
                )

            sent = True

        await asyncio.sleep(1)


async def main():
    asyncio.create_task(send_valentines())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
