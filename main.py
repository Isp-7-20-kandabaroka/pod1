from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup
from aiogram.types import InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage
TOKEN = "6855767476:AAGB9oVSxHlFe0-2uli8ITEDF-xHHn1Fekg"
bot = Bot(token=TOKEN)
storage = MemoryStorage()  # creating a MemoryStorage for FSM
dp = Dispatcher(bot, storage=storage)  # Now assigning the storage to Dispatcher


ADMIN_IDS = [448076215, 5100515110, 6165219675, 713476634]
CHANNELS = {
    '-1001735601596': 'https://t.me/mirchinivizov', # Вместо ID можно добавить ссылку на канал

}


def make_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    # Добавление кнопки подписки на бота
    subscribe_bot_button = InlineKeyboardButton('Подписаться на бота 📝',
                                                url='https://t.me/OneGoroskope_bot')  # Замените на вашу ссылку
    keyboard.add(subscribe_bot_button)

    # Добавление кнопок подписки на каналы
    for channel_id, url in CHANNELS.items():
        button = InlineKeyboardButton('Подписаться на канал 📝', url=url)
        keyboard.add(button)

    # Добавление кнопки проверки подписки
    check_button = InlineKeyboardButton('💖 Я подписался(ась)', callback_data='check_subs')
    keyboard.add(check_button)

    return keyboard




@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    start_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton('🎥Все фильмы из ТикТока🎥', callback_data='check_channels')
    )

    photo_path = 'tiktok.jpg'  # Укажите здесь путь к файлу на вашем сервере
    photo = InputFile(path_or_bytesio=photo_path)

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo,
        caption="🥤Все фильмы из ТикТока\n\nЖми на кнопку, чтобы узнать названия фильмов ⤵️",
        reply_markup=start_keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'check_channels')
async def prompt_subscriptions(callback_query: types.CallbackQuery):
    # Сообщаем пользователю о необходимости подписки
    await callback_query.message.answer("📝 Для использования бота, вы должны быть подписаны на наши каналы:", reply_markup=make_subscription_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'check_subs')
async def process_check_subscription(callback_query: types.CallbackQuery):
    # Функция для проверки подписки пользователя
    user_subscribed = True
    for channel_id in CHANNELS:
        chat_member = await bot.get_chat_member(channel_id, callback_query.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            user_subscribed = False
            break

    if user_subscribed:
        await callback_query.message.answer("Доступ открыт!\nВсе фильмы из ТикТока⤵️: https://t.me/KinoAgent_007Insta")

    else:
        # Эта часть также отправит пользователю кнопку для подписки, если он не подписан на все каналы
        subscription_keyboard = make_subscription_keyboard()
        check_button = InlineKeyboardButton('❤ Я подписался(ась)', callback_data='check_subs')
        subscription_keyboard.add(check_button)
        await callback_query.message.answer("Пожалуйста, подпишитесь на все каналы перед тем как подтверждать.", reply_markup=subscription_keyboard)

    # Завершаем обработку обратного вызова
    await bot.answer_callback_query(callback_query.id)

# Остальная часть кода остаётся без изменений
# Добавляем состояния для диалога
class AdditionProcess(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_channel_url = State()


# Обработчик для команды начала добавления админом нового канала.
@dp.message_handler(commands=['addchannel'], state='*')
async def add_channel_start(message: types.Message):
    # Проверка, является ли пользователь одним из администраторов
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("У вас недостаточно прав для этой команды.")

    await message.answer("Введите ID канала:")
    await AdditionProcess.waiting_for_channel_id.set()


@dp.message_handler(state=AdditionProcess.waiting_for_channel_id)
async def add_channel_id(message: types.Message, state: FSMContext):
    # здесь можете проверить, действительно ли ID канала валиден
    async with state.proxy() as data:
        data['channel_id'] = message.text
    await message.answer("Теперь введите ссылку на канал:")
    await AdditionProcess.waiting_for_channel_url.set()


@dp.message_handler(state=AdditionProcess.waiting_for_channel_url)
async def add_channel_url(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['channel_url'] = message.text
        # Добавление нового канала в наш словарь (возможно, стоит сохранять его в БД или файл)
        CHANNELS[data['channel_id']] = data['channel_url']

    await message.answer("Канал успешно добавлен!")
    await state.finish()
class DeletionProcess(StatesGroup):
    waiting_for_channel_id_to_delete = State()

# Обработчик команды начала удаления канала админом
@dp.message_handler(commands=['delchannel'], state='*')
async def del_channel_start(message: types.Message):
    # Проверяем, является ли пользователь одним из администраторов
    if message.from_user.id not in ADMIN_IDS:
        await message.reply("У вас недостаточно прав для этой команды.")
        return

    await message.answer("Введите ID канала для удаления:")
    await DeletionProcess.waiting_for_channel_id_to_delete.set()

# Обработчик ввода ID канала для удаления
@dp.message_handler(state=DeletionProcess.waiting_for_channel_id_to_delete)
async def del_channel_id(message: types.Message, state: FSMContext):
    channel_id_to_delete = message.text.strip()

    if channel_id_to_delete in CHANNELS:
        del CHANNELS[channel_id_to_delete]  # Удаляем канал из словаря
        await message.answer("Канал удален из подписок.")
    else:
        await message.answer("Канала с таким ID нет в списке подписок.")

    await state.finish()

# Добавляем LoggingMiddleware чтобы видеть информацию о состоянии в логах бота
dp.middleware.setup(LoggingMiddleware())
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
