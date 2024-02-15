
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = "6882073553:AAHRPI4Ii5El8--oXskqD6XbQJ0IwPNscPM"
bot = Bot(token=TOKEN)
storage = MemoryStorage()
dp = Dispatcher(bot, storage=storage)


ADMIN_IDS = [448076215, 6165219675, 713476634]
CHANNELS = {
    '-1001735601596': {
        'url': 'https://t.me/pokupka_na_vb',
        'order': 2,
        'bot_members': {}
    },
    # Другие каналы
}

next_channel_order = 2

user_subscription_checks = {}

def make_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    subscribe_bot_button = InlineKeyboardButton('Подписаться на канал 1 📝', url='https://t.me/OneGoroskope_bot')
    keyboard.add(subscribe_bot_button)

    # Сортируем каналы по их порядку перед добавлением их в клавиатуру
    sorted_channels = sorted(CHANNELS.items(), key=lambda item: item[1]['order'])
    for channel_id, details in sorted_channels:
        button = InlineKeyboardButton(f'Подписаться на канал {details["order"]} 📝', url=details['url'],
                                      callback_data=f'subscribe_channel_{channel_id}')
        keyboard.add(button)

    check_button = InlineKeyboardButton('💖 Я подписался(ась)', callback_data='check_subs')
    keyboard.add(check_button)

    return keyboard

@dp.message_handler(commands=['start'])
async def send_welcome(message: types.Message):
    username = message.from_user.first_name
    welcome_text = f"Добро пожаловать, {username} ❤️" if username else "Добро пожаловать!"
    await bot.send_message(chat_id=message.chat.id, text=welcome_text)
    start_keyboard = InlineKeyboardMarkup().add(
        InlineKeyboardButton('🎥Все фильмы из ТикТока🎥', callback_data='check_channels')
    )

    photo_path = 'tiktok.jpg'
    photo = InputFile(path_or_bytesio=photo_path)

    await bot.send_photo(
        chat_id=message.chat.id,
        photo=photo,
        caption="🥤Все фильмы из ТикТока\n\nЖми на кнопку, чтобы узнать названия фильмов ⤵️",
        reply_markup=start_keyboard
    )

@dp.callback_query_handler(lambda c: c.data == 'check_channels')
async def prompt_subscriptions(callback_query: types.CallbackQuery):
    await callback_query.message.answer("📝 Для использования бота, вы должны быть подписаны на наши каналы:",
                                        reply_markup=make_subscription_keyboard())

@dp.callback_query_handler(lambda c: c.data == 'check_subs')
async def process_check_subscription(callback_query: types.CallbackQuery):
    global next_channel_order

    if callback_query.from_user.id not in user_subscription_checks:
        user_subscription_checks[callback_query.from_user.id] = 0

    user_subscribed = True
    not_subscribed_channels = []  # Список для хранения каналов, на которые пользователь не подписан

    for channel_id, details in CHANNELS.items():
        chat_member = await bot.get_chat_member(channel_id, callback_query.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            user_subscribed = False
            not_subscribed_channels.append(details['url'])  # Добавляем URL канала в список

    total_channels = len(CHANNELS)  # Общее количество каналов

    if user_subscribed:
        # Если пользователь подписан на все каналы, добавляем общее количество каналов к его счетчику
        user_subscription_checks[callback_query.from_user.id] += total_channels
        await callback_query.message.answer("Доступ открыт!\nВсе фильмы из ТикТока⤵️: https://t.me/kinoAgent_007")
    else:
        # Формируем сообщение с предупреждением и кнопками для подписки
        warning_message = "Пожалуйста, подпишитесь на следующие каналы перед тем как подтверждать:\n" + "\n".join(not_subscribed_channels)
        await callback_query.message.answer(warning_message, reply_markup=make_subscription_keyboard())

    await bot.answer_callback_query(callback_query.id)

class AdditionProcess(StatesGroup):
    waiting_for_channel_id = State()  # Пользователь вводит ID канала
    waiting_for_channel_url = State()  # Пользователь вводит URL канала

@dp.message_handler(commands=['addchannel'], state='*')
async def add_channel_start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("У вас недостаточно прав для этой команды.")
    await AdditionProcess.waiting_for_channel_id.set()
    await message.answer("Введите ID канала:")

@dp.message_handler(state=AdditionProcess.waiting_for_channel_id)
async def add_channel_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['channel_id'] = message.text.strip()
    await AdditionProcess.next()  # Переход к следующему состоянию
    await message.answer("Введите URL канала:")


@dp.message_handler(state=AdditionProcess.waiting_for_channel_url)
async def add_channel_url(message: types.Message, state: FSMContext):
    global next_channel_order
    async with state.proxy() as data:
        data['channel_url'] = message.text

    # Находим максимальный order среди существующих каналов и устанавливаем next_channel_order на один больше
    if CHANNELS:  # Проверяем, не пуст ли словарь
        max_order = max(channel['order'] for channel in CHANNELS.values())
        next_channel_order = max_order + 1
    else:  # Если каналов ещё нет, начинаем с первого
        next_channel_order = 1

    channel_id = data['channel_id']
    CHANNELS[channel_id] = {
        'url': data['channel_url'],
        'order': next_channel_order,
        'bot_members': {}
    }
    # Теперь не нужно увеличивать next_channel_order, так как он уже был установлен правильно выше
    await message.answer(f"Канал успешно добавлен под номером {CHANNELS[channel_id]['order']}!")
    await state.finish()  # Завершение текущего состояния

class DeletionProcess(StatesGroup):
    waiting_for_channel_id_to_delete = State()

@dp.message_handler(commands=['delchannel'], state='*')
async def delete_channel_start(message: types.Message):
    # Проверка, является ли пользователь одним из администраторов
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("У вас недостаточно прав для этой команды.")

    await message.answer("Введите ID канала, чтобы удалить его:")
    await DeletionProcess.waiting_for_channel_id_to_delete.set()
# Обработчик команды начала удаления канала админом


@dp.message_handler(state=DeletionProcess.waiting_for_channel_id_to_delete)
async def del_channel_id(message: types.Message, state: FSMContext):
    global CHANNELS, next_channel_order  # Добавляем next_channel_order в глобальный контекст

    channel_id_to_delete = message.text.strip()

    if channel_id_to_delete in CHANNELS:
        removed_channel_order = CHANNELS[channel_id_to_delete]['order']
        del CHANNELS[channel_id_to_delete]

        # Уменьшаем `order` для следующих каналов.
        for channel_id, channel_info in CHANNELS.items():
            if channel_info['order'] > removed_channel_order:
                channel_info['order'] -= 1

        # Уменьшаем счетчик для следующего `order`, если удаляемый канал не был последним
        if removed_channel_order <= next_channel_order:
            next_channel_order -= 1

        await message.answer("Канал удален из подписок.")
    else:
        await message.answer("Канала с таким ID нет в списке подписок.")

    await state.finish()
 # Добавляем информацию о канале в сообщение со статистикой
@dp.message_handler(commands=['stat'])
async def show_stats(message: types.Message):
    # Проверка, является ли пользователь одним из администраторов
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("У вас недостаточно прав для выполнения этой команды.")

    total_subscribers = sum(user_subscription_checks.values())
    await message.answer(f"Подписчиков от бота: + {total_subscribers}")



async def on_startup(dp):
    # Устанавливаем MemoryStorage для хранения состояний FSM
    dp.middleware.setup(LoggingMiddleware())



if __name__ == '__main__':
    # Запускаем бота в бесконечном цикле с передачей on_startup
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=None)

if __name__ == '__main__':
    # Устанавливаем обработчик запуска бота
    dp.middleware.setup(LoggingMiddleware())

    # Запускаем бота в бесконечном цикле с передачей on_startup
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=None)
