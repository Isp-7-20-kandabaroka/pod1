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
    '-1001735601596': {
        'url': 'https://t.me/mirchinivizov',
        'clicks': 0,
        'order': 2,
        'bot_members': 0  # Изначально количество подписчиков от бота равно 0
    },
    # Другие каналы
}
successful_checks = 0

next_channel_order = 2

def make_subscription_keyboard():
    keyboard = InlineKeyboardMarkup(row_width=1)

    subscribe_bot_button = InlineKeyboardButton('Подписаться на канал 1 📝', url='https://t.me/OneGoroskope_bot')
    keyboard.add(subscribe_bot_button)

    # Sort channels by their order before adding them to the keyboard
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

    photo_path = 'images/tiktok.jpg'  # Укажите здесь путь к файлу на вашем сервере
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
    global successful_checks  # Используем глобальную переменную внутри функции

    # Считаем количество каналов
    channels_count = len(CHANNELS)

    # Функция для проверки подписки пользователя
    user_subscribed = True
    for channel_id in CHANNELS:
        chat_member = await bot.get_chat_member(channel_id, callback_query.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            user_subscribed = False
            break

    if user_subscribed:
        successful_checks += channels_count  # Увеличиваем счетчик на количество каналов
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


@dp.callback_query_handler(lambda c: c.data == 'check_subs')
async def process_check_subscription(callback_query: types.CallbackQuery):
    global successful_checks  # Используй глобальную переменную внутри функции

    # Проверяем статус подписки пользователя на все каналы
    user_subscribed = True
    for channel_id in CHANNELS:
        chat_member = await bot.get_chat_member(channel_id, callback_query.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            user_subscribed = False
            break

    if user_subscribed:

        CHANNELS['bot_members'] += 1  # Увеличиваем счетчик подписчиков от бота на 1
        channels_count = len(CHANNELS)  # Считаем количество каналов
        successful_checks += 1  # Увеличиваем счетчик на 1


        await callback_query.message.answer(f"Поздравляем! Вы подписаны на все {channels_count} каналов.")
    else:
        await callback_query.message.answer("Пожалуйста, подпишитесь на все каналы перед подтверждением.")

    # Завершаем обработку обратного вызова
    await bot.answer_callback_query(callback_query.id)



# Обработчик для команды начала добавления админом нового канала.
@dp.message_handler(commands=['addchannel'], state='*')
async def add_channel_start(message: types.Message):
    if message.from_user.id not in ADMIN_IDS:
        return await message.reply("У вас недостаточно прав для этой команды.")
    await message.answer("Введите ID канала:")
    await AdditionProcess.waiting_for_channel_id.set()

@dp.message_handler(state=AdditionProcess.waiting_for_channel_id)
async def add_channel_id(message: types.Message, state: FSMContext):
    async with state.proxy() as data:
        data['channel_id'] = message.text.strip()
    await message.answer("Введите URL канала:")
    await AdditionProcess.next()

@dp.message_handler(state=AdditionProcess.waiting_for_channel_url)
async def add_channel_url(message: types.Message, state: FSMContext):
    global next_channel_order
    # Увеличивать next_channel_order нужно только после добавления данных,
    # чтобы исключить повторение order.
    async with state.proxy() as data:
        data['channel_url'] = message.text
    next_channel_order += 1
    CHANNELS[data['channel_id']] = {
        'url': data['channel_url'],
        'clicks': 0,
        'order': next_channel_order,
        'bot_members': 0  # Изначально количество подписчиков от бота равно 0
    }
    await message.answer(f"Канал успешно добавлен под номером {next_channel_order}!")
    await state.finish()



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

@dp.message_handler(commands=['stat'])
async def show_stats(message: types.Message):
    stats_message = "Статистика подписок:\n\n"
    for channel_id, details in CHANNELS.items():
        # Получаем информацию о количестве подписчиков для каждого канала
        chat_member_count = await bot.get_chat_members_count(channel_id)
        bot_member_count = details['bot_members']  # Количество подписчиков от бота из словаря

        channel_name = details.get('name', 'Канал неизвестен')

        # Добавляем информацию о канале в сообщение со статистикой
        stats_message += f"{channel_name}: {chat_member_count} подписчиков, от бота: {successful_checks} подписчиков\n"

    await message.answer(stats_message)



dp.middleware.setup(LoggingMiddleware())
if __name__ == '__main__':
    executor.start_polling(dp, skip_updates=True)
