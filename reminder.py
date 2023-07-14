# Импортируем необходимые модули
import logging
import asyncio
from datetime import datetime, timedelta
from aiogram import Bot, Dispatcher, types
from aiogram.contrib.fsm_storage.memory import MemoryStorage
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters import Text
from aiogram.dispatcher.filters.state import State, StatesGroup

# Устанавливаем токен бота
TOKEN = '6381802557:AAFWY0gQdmD1FRC9lXuvzC2L0OMABkfgXjs'

# Создаем экземпляр бота и хранилища состояний
bot = Bot(token=TOKEN)
storage = MemoryStorage()

# Создаем диспетчер и настраиваем логирование
dp = Dispatcher(bot, storage=storage)
logging.basicConfig(level=logging.INFO)

# Создаем класс состояний для напоминания о событиях
class Reminder(StatesGroup):
    waiting_for_event = State()
    waiting_for_time = State()

# Обработчик команды /start
@dp.message_handler(commands=['start'])
async def start(message: types.Message):
    # Получаем id чата пользователя и сохраняем его в storage
    chat_id = message.chat.id
    await bot.send_message(chat_id=chat_id, text="Привет! Я бот для напоминания о событиях. Введите /newreminder, чтобы создать новое напоминание.")
    await storage.set_data(chat_id=chat_id)

# Обработчик команды /newreminder
@dp.message_handler(commands=['newreminder'])
async def new_reminder(message: types.Message):
    await message.reply("Введите событие, на которое нужно напомнить.")
    await Reminder.waiting_for_event.set()

# Обработчик ввода события пользователем
@dp.message_handler(state=Reminder.waiting_for_event)
async def set_event(message: types.Message, state: FSMContext):
    event = message.text
    await state.update_data(event=event)
    await message.reply("Введите время в формате 'HH:MM', когда нужно напомнить о событии.")
    await Reminder.waiting_for_time.set()

# Обработчик ввода времени пользователем
@dp.message_handler(state=Reminder.waiting_for_time, content_types=types.ContentType.TEXT)
async def set_time(message: types.Message, state: FSMContext):
    time_str = message.text
    try:
        # Преобразуем введенное время в объект datetime
        time = datetime.strptime(time_str, '%H:%M')
        now = datetime.now()
        # Если введенное время уже прошло, устанавливаем напоминание на следующий день
        if time.time() < now.time():
            date = now.date() + timedelta(days=1)
        else:
            date = now.date()

        remind_time = datetime.combine(date, time.time())
        data = await state.get_data()
        event = data.get('event')
        # Вычисляем количество секунд до напоминания
        delta = remind_time - now
        seconds = delta.seconds + delta.days * 24 * 3600
        # Запускаем задачу на отправку напоминания через указанное время
        asyncio.create_task(send_reminder(event, seconds, message.chat.id))
        await message.reply(f"Напоминание на '{event}' установлено на {time_str}.")
    except ValueError:
        await message.reply("Некорректный формат времени. Введите время в формате 'HH:MM'.")

# Функция отправки напоминания
async def send_reminder(event, seconds, chat_id):
    try:
        await asyncio.sleep(seconds)
        await bot.send_message(chat_id=chat_id, text=f"Напоминание: {event}")
    except Exception as e:
        logging.error(f"Error sending reminder: {e}")

# Запуск бота
if __name__ == '__main__':
    from aiogram import executor
    executor.start_polling(dp, skip_updates=True)
