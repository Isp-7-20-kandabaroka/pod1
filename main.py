
from aiogram import Bot, Dispatcher, executor, types
from aiogram.types import InlineKeyboardButton, InlineKeyboardMarkup, InputFile
from aiogram.dispatcher import FSMContext
from aiogram.dispatcher.filters.state import State, StatesGroup
from aiogram.contrib.middlewares.logging import LoggingMiddleware
from aiogram.contrib.fsm_storage.memory import MemoryStorage

TOKEN = "6855767476:AAGB9oVSxHlFe0-2uli8ITEDF-xHHn1Fekg"
bot = Bot(token=TOKEN)
storage = MemoryStorage()  # создаем MemoryStorage для FSM
dp = Dispatcher(bot, storage=storage)  # назначаем хранилище для диспетчера

ADMIN_IDS = [448076215, 6165219675, 713476634]
CHANNELS = {
    '-1001735601596': {
        'url': 'https://t.me/mirchinivizov',
        'order': 2,
        'bot_members': 0
    },
    # Другие каналы
}
successful_checks = 0

next_channel_order = 2

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
    global successful_checks

    channels_count = len(CHANNELS)

    user_subscribed = True
    for channel_id in CHANNELS:
        chat_member = await bot.get_chat_member(channel_id, callback_query.from_user.id)
        if chat_member.status not in ['member', 'administrator', 'creator']:
            user_subscribed = False
            break
    if user_subscribed:
        if successful_checks < channels_count:
            successful_checks += 1
        await callback_query.message.answer("Доступ открыт!\nВсе фильмы из ТикТока⤵️: https://t.me/KinoAgent_007Insta")
    else:
        subscription_keyboard = make_subscription_keyboard()
        check_button = InlineKeyboardButton('❤ Я подписался(ась)', callback_data='check_subs')
        subscription_keyboard.add(check_button)
        await callback_query.message.answer("Пожалуйста, подпишитесь на все каналы перед тем как подтверждать.",
                                            reply_markup=subscription_keyboard)

    await bot.answer_callback_query(callback_query.id)

class AdditionProcess(StatesGroup):
    waiting_for_channel_id = State()
    waiting_for_channel_url = State()

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
    async with state.proxy() as data:
        data['channel_url'] = message.text
    next_channel_order += 1
    CHANNELS[data['channel_id']] = {
        'url': data['channel_url'],
        'order': next_channel_order,
        'bot_members': 0
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



async def on_startup(dp):
    # Вывести информацию об успешном запуске в консоль
    print("Бот запущен и работает!")

    # Отправить сообщение об успешном запуске бота в чат администратора
    for admin_id in ADMIN_IDS:
        try:
            await bot.send_message(chat_id=admin_id, text='Бот запущен и работает!')
        except Exception as e:
            print(f"Ошибка при отправке сообщения в чат {admin_id}: {e}")

if __name__ == '__main__':
    # Устанавливаем обработчик запуска бота
    dp.middleware.setup(LoggingMiddleware())

    # Запускаем бота в бесконечном цикле с передачей on_startup
    executor.start_polling(dp, on_startup=on_startup, on_shutdown=None)
