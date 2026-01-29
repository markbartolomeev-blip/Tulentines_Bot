import asyncio
import random
from datetime import datetime, timezone, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.filters import Command

# Вставь сюда токен своего бота
TOKEN = "ВСТАВЬ_СЮДА_ТОКЕН"

bot = Bot(token=TOKEN)
dp = Dispatcher()

# Словарь: user_id → текст письма
letters = {}

# Саратовское время (UTC+4)
SARATOV_TZ = timezone(timedelta(hours=4))
SEND_TIME = datetime(2026, 2, 14, 0, 0, 0, tzinfo=SARATOV_TZ)

sent = False

def now_saratov():
    return datetime.now(SARATOV_TZ)

def is_before_send_time():
    return now_saratov() < SEND_TIME


@dp.message(Command("start"))
async def start(msg: types.Message):
    text = (
        "💖 Добро пожаловать в Tulentine’s Box! 💕\n\n"
        "Здесь ты можешь отправить анонимное послание, и оно достанется случайному человеку из группы, "
        "кто тоже написал сообщение! 💌\n\n"
        "Будь вежлив, пиши только искренние и добрые слова! "
        "Не нужно писать конкретному человеку, так как шанс того, что оно попадет именно ему мал! 💘\n\n"
        "/send — написать послание 💝\n"
        "/check — посмотреть статус письма 💟"
    )
    await msg.answer(text)


@dp.message(Command("send"))
async def send(msg: types.Message):
    if msg.chat.type != "private":
        await msg.answer("💌 Напиши мне в личные сообщения, чтобы отправить послание 😉")
        return

    if not is_before_send_time():
        await msg.answer("⛔ Приём посланий уже закрыт.")
        return
    if msg.from_user.id in letters:
        await msg.answer("💔 Ты уже отправил письмо. Второе отправить нельзя.")
        return

    await msg.answer("✍️ Пиши своё послание, и оно отправится в ящик Tulentine’s!")


@dp.message(lambda msg: msg.text and not msg.text.startswith("/"))
async def save_letter(msg: types.Message):
    if not is_before_send_time():
        await msg.answer("⛔ Послания больше не принимаются.")
        return
    if msg.from_user.id in letters:
        await msg.answer("💔 Ты уже отправил письмо.")
        return

    letters[msg.from_user.id] = msg.text
    await msg.answer("💖 Твоё письмо сохранено! Жди 14 февраля 🎁")


@dp.message(Command("check"))
async def check(msg: types.Message):
    if msg.from_user.id in letters:
        await msg.answer(
            "💌 Твоё письмо сохранено!\n"
            "14 февраля оно попадёт в руки случайному человеку! ☺️"
        )
    else:
        await msg.answer(
            "❗ Твоё письмо не отправлено.\n"
            "Отправляй через команду /send 🤩"
        )


async def send_valentines():
    global sent
    while True:
        if not sent and now_saratov() >= SEND_TIME and len(letters) > 1:
            users = list(letters.keys())
            texts = list(letters.values())

            shuffled = texts.copy()

            # Защита: письмо не может попасть самому себе
            while True:
                random.shuffle(shuffled)
                ok = True
                for i in range(len(texts)):
                    if texts[i] == shuffled[i]:
                        ok = False
                        break
                if ok:
                    break

            # Рассылаем письма
            for i, user_id in enumerate(users):
                await bot.send_message(
                    user_id,
                    "💌 Тебе пришло послание из Tulentine’s Box:\n\n" + shuffled[i]
                )

            sent = True

        await asyncio.sleep(2)


async def main():
    asyncio.create_task(send_valentines())
    await dp.start_polling(bot)


if __name__ == "__main__":
    asyncio.run(main())
