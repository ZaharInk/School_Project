import telebot
from telebot.types import InlineKeyboardMarkup, InlineKeyboardButton, Message, CallbackQuery, BotCommand
from telebot.formatting import escape_html
import json
from security import *
from database import *

with open('config.json', 'r') as file:
    config = json.load(file)

bot = telebot.TeleBot(config['token'])

commands = {'/start': 'Регистрация', '/menu': 'Меню', '/help': 'Справочная информация',
            '/auth': 'Авторизация', '/quit': 'Выход'}


def setup_commands():
    user_commands = [BotCommand(command=c, description=d) for c, d in commands.items()]
    bot.set_my_commands(user_commands)


status = {}
active = {}
reg_attemps = {}


def check_status(msg: Message):
    return bool(status.get(msg.from_user.id, False))


keys = {}
info = {'credentials': ['Название', 'Идентификатор пользователя', 'Пароль'],
        'card': ['Название', 'Номер карты', 'Срок действия', 'CVV', 'Держателя карты'],
        'address': ['Название', 'Город', 'Адрес', 'Квартиру', 'Телефон'],
        'note': ['Название', 'Примечание']}


@bot.message_handler(commands=['start'])
def start(msg: Message):
    bot.send_message(msg.chat.id, 'Здравствуйте! Меня зовут SecretPass, я персональный менеджер паролей')
    if check_user(msg.from_user.id):
        bot.send_message(msg.chat.id, 'Вы уже зарегистрированы, воспользуйтесь командой /menu')
    else:
        active[msg.from_user.id] = True
        bot.send_message(msg.chat.id, 'Придумайте мастер-пароль:')
        bot.register_next_step_handler(msg, register)


def register(msg: Message):
    pwd = msg.text
    special = "!@#$%^&*()_+=-[]{}\\|;:'\",.<>/?`~"
    if len(pwd) >= 12 and any(c.isupper() for c in pwd) and any(c.islower() for c in pwd) and any(
            c.isdigit() for c in pwd) and any(c in special for c in pwd):
        salt = generate_salt()
        create_user(msg.from_user.id, bcrypt_hash(pwd), salt)
        keys[msg.from_user.id] = generate_key(pwd, salt)
        status[msg.from_user.id] = True
        active[msg.from_user.id] = False
        bot.delete_message(msg.chat.id, msg.message_id)
        bot.send_message(msg.chat.id, 'Данные занесены в базу, воспользуйтесь командой /menu')
    else:
        bot.send_message(msg.chat.id, 'Пароль небезопасен, требования доступны по команде /help')


@bot.message_handler(commands=['menu'])
def menu(msg: Message):
    if check_status(msg):
        kb = InlineKeyboardMarkup()
        kb.row(InlineKeyboardButton('Сохранить данные', callback_data='menu_save'))
        kb.row(InlineKeyboardButton('Прочитать данные', callback_data='menu_read'))
        kb.row(InlineKeyboardButton('Справочная информация', callback_data='help'))
        bot.send_message(msg.chat.id, 'Выбери, что тебе нужно', reply_markup=kb)
    else:
        bot.send_message(msg.chat.id, 'Вы не авторизованы, воспользуйтесь командой /auth')


@bot.message_handler(commands=['auth'])
def auth(msg: Message):
    if get_data(msg.from_user.id) is not None:
        if not bool(status.get(msg.from_user.id, False)):
            active[msg.from_user.id] = True
            reg_attemps[msg.from_user.id] = 3
            bot.send_message(msg.chat.id, 'Отправьте мастер-пароль:')
            bot.register_next_step_handler(msg, authorization)
        else:
            bot.send_message(msg.chat.id, 'Вы уже авторизованы')
    else:
        bot.send_message(msg.chat.id, 'Вы ещё не зарегистрированы, воспользуйтесь командой /start')


def authorization(msg: Message):
    if not msg.text:
        reg_attemps[msg.from_user.id] -= 1
        bot.send_message(msg.chat.id, 'Пароль должен быть текстовым.')
        if reg_attemps[msg.from_user.id] > 0:
            bot.send_message(msg.chat.id, 'Попробуйте ещё раз:')
            bot.register_next_step_handler(msg, authorization)
            return
        return
    user_data = get_data(msg.from_user.id)
    if bcrypt_check(msg.text, user_data[0]):
        keys[msg.from_user.id] = generate_key(msg.text, user_data[1])
        status[msg.from_user.id] = True
        active[msg.from_user.id] = False
        bot.delete_message(msg.chat.id, msg.message_id)
        bot.send_message(msg.chat.id, 'Вы успешно авторизованы')
    else:
        reg_attemps[msg.from_user.id] -= 1
        bot.send_message(msg.chat.id, 'Неверный пароль')
        if reg_attemps[msg.from_user.id] > 0:
            bot.send_message(msg.chat.id, 'Попробуйте ещё раз:')
            bot.register_next_step_handler(msg, authorization)


@bot.message_handler(commands=['quit'])
def quit(msg: Message):
    if bool(status.get(msg.from_user.id, False)):
        del keys[msg.from_user.id]
        status[msg.from_user.id] = False
        bot.send_message(msg.chat.id, 'Вы успешно деавторизованы')
    else:
        bot.send_message(msg.chat.id, 'Вы уже деавторизованы')


@bot.message_handler(commands=['help'])
def help(msg: Message):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton('Требования к мастер-паролю', callback_data='help_pwd'))
    kb.row(InlineKeyboardButton('Связь с разработчиком', callback_data='help_contact'))
    bot.send_message(msg.chat.id, 'Чем могу помочь?', reply_markup=kb)


@bot.callback_query_handler(lambda call: True)
def callback(call: CallbackQuery):
    if active.get(call.from_user.id):
        bot.answer_callback_query(call.id, 'Завершите текущее взаимодействие')
        return
    if call.data == 'help':
        help(call.message)
    elif call.data.startswith('help'):
        _, var = call.data.split('_')
        if var == 'pwd':
            bot.send_message(call.message.chat.id,'Мастер-пароль должен:\nСодержать не менее 12 символов\nВключать в себя хотя бы 1 букву верхнего и нижнего регистра\nВключать в себя хотя бы 1 цифру и символ\n')
        elif var == 'contact':
            bot.send_message(call.message.chat.id, 'Разработчик: Захар\nЭлектронная почта: inkinzahar@gmail.com')
    elif call.from_user.id not in keys:
        bot.answer_callback_query(call.id, 'Сессия истекла. Воспользуйтесь командой /auth', show_alert=True)
        return
    elif call.data.startswith('menu'):
        _, var = call.data.split('_')
        if var == 'save':
            save(call.message)
        elif var == 'read':
            read(call.message, call.from_user.id)
    elif call.data.startswith('save'):
        active[call.from_user.id] = True
        _, item = call.data.split('_')
        bot.send_message(call.message.chat.id, 'Введите название:')
        bot.register_next_step_handler(call.message, save_item, call.from_user.id, info[item][:], item, {})
    elif call.data.startswith('read'):
        _, id = call.data.split('_')
        read_item(call.message, call.from_user.id, id)
    elif call.data.startswith('delete'):
        _, id = call.data.split('_')
        delete_item(call.from_user.id, id)
        bot.send_message(call.message.chat.id, 'Данные успешно удалены')


def save(msg: Message):
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton('Учётные данные', callback_data='save_credentials'))
    kb.row(InlineKeyboardButton('Карта', callback_data='save_card'))
    kb.row(InlineKeyboardButton('Адрес', callback_data='save_address'))
    kb.row(InlineKeyboardButton('Заметка', callback_data='save_note'))
    bot.send_message(msg.chat.id, 'Выберите тип сохраняемых данных:', reply_markup=kb)


def save_item(msg: Message, user_id, info, item, data):
    if not msg.text:
        bot.send_message(msg.chat.id, f'Ошибка, ожидался текст')
        bot.send_message(msg.chat.id, f'Введите {info[0].lower()}:')
        bot.register_next_step_handler(msg, save_item, user_id, info=info, item=item, data=data)
        return
    else:
        var = info.pop(0)
        data[var] = msg.text
    if info:
        bot.send_message(msg.chat.id, f'Введите {info[0].lower()}:')
        bot.register_next_step_handler(msg, save_item, user_id, info=info, item=item, data=data)
    else:
        key = keys[user_id]
        if not key:
            bot.send_message(msg.chat.id, "Сессия истекла. Воспользуйтесь командой /auth")
            return
        name = data.pop('Название', 'Без названия')
        add_item(user_id, item, encrypt_data(name, key), serialize_and_encrypt(data, key))
        bot.send_message(msg.chat.id, 'Данные успешно сохранены')
        active[user_id] = False


def read(msg: Message, user_id):
    kb = InlineKeyboardMarkup()
    if get_items(user_id):
        for item in get_items(user_id):
            kb.row(InlineKeyboardButton(f'{item[1].capitalize()}: {decrypt_data(item[2], keys[user_id])}', callback_data=f'read_{item[0]}'))
        bot.send_message(msg.chat.id, 'Выберите данные для просмотра:', reply_markup=kb)
    else:
        bot.send_message(msg.chat.id, 'Вы ещё не сохранили никаких данных')


def read_item(msg: Message, user_id, id):
    data_dict = get_item(user_id, id)
    info = "\n".join([f'{key}: <code>{escape_html(str(value))}</code>' for key, value in decrypt_and_deserialize(data_dict[3], keys[user_id]).items()])
    kb = InlineKeyboardMarkup()
    kb.row(InlineKeyboardButton('Стереть данные', callback_data=f'delete_{data_dict[0]}'))
    bot.send_message(msg.chat.id, f'{data_dict[1]}\nНазвание: {decrypt_data(data_dict[2], keys[user_id])}\n{info}', parse_mode='HTML', reply_markup=kb)


if __name__ == '__main__':
    setup_commands()
    bot.polling(True)
