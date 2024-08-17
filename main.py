from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from db import add, select_reminder, delete_reminder, add_user, select_user, delete_user
from settings import BOT_NAME, BOT_TOKEN, PROXY, ADMIN_ID

if not PROXY:
    client = Client(name=BOT_NAME, bot_token=BOT_TOKEN)
else:
    client = Client(name=BOT_NAME, bot_token=BOT_TOKEN, proxy=PROXY)
add_user(ADMIN_ID)
scheduler = BackgroundScheduler()
no_limit = datetime(9999, 12, 31, 23, 59, 59)


class Account:
    def __init__(self):
        self.send_status = 0
        self.mode = None
        self.start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        self.end = no_limit
        self.msg = ''
        self.repeat = 'Never'
        self.destination = 'here'
        self.messages = dict()


home_key = [[InlineKeyboardButton('add Reminder', 'ar')], [InlineKeyboardButton('delete Reminder', 'dr')],
            [InlineKeyboardButton('add user', 'au'), InlineKeyboardButton('delete user', 'du')]]
chatId_account = dict()


@client.on_message()
def handle_message(bot: Client, message: Message):
    whitelist = select_user()
    chat_id = message.chat.id
    if (message.from_user.id,) not in whitelist:
        if message.text.startswith('/') or message.reply_to_message.from_user.is_self:
            bot_username = bot.get_me().username
            bot.send_message(chat_id,
                             f"@{message.from_user.username}, You don't have access in Symmio Reminder for this chat!\n"
                             f"(check @{bot_username})")
            try:
                bot.send_message(message.from_user.id,
                                 f"@{message.from_user.username} to get access in Symmio Reminder forward this message to admin"
                                 f"\nUserID: `{message.from_user.id}`")
            except errors.exceptions.bad_request_400.PeerIdInvalid:
                bot.send_message(chat_id,
                                 f"{message.from_user.username}! first start bot in @{bot_username} then /start again in this chat!")
        return
    if chat_id not in chatId_account:
        chatId_account[chat_id] = Account()
    if message.text:
        chat = chatId_account[chat_id]
        status = chat.send_status
        if message.text.startswith('/start'):
            chatId_account[chat_id].mode = None
            chatId_account[chat_id].start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0,
                                                                                          microsecond=0)
            chatId_account[chat_id].end = no_limit
            chatId_account[chat_id].msg = ''
            chatId_account[chat_id].repeat = 'Never'
            chatId_account[chat_id].destination = 'here'
            if chat_id == message.from_user.id:
                bot.send_message(chat_id, 'Welcome to Symmio Reminder', reply_markup=InlineKeyboardMarkup(home_key))
            else:
                bot.send_message(chat_id, 'Symmio Reminder start working')
        elif status == 'm':
            chatId_account[chat_id].msg = message.text
            end_date = 'No limit' if chat.end == no_limit else chat.end
            bot.send_message(chat_id, f'Add new Reminder\nYour message:\n\n{chatId_account[chat_id].msg}',
                             reply_markup=InlineKeyboardMarkup(
                                 [[InlineKeyboardButton(f'edit message', 'm'),
                                   InlineKeyboardButton(f'destination: {chat.destination}', 'dst')],
                                  [InlineKeyboardButton(f'start date: {chat.start}', 'sd'),
                                   InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                                  [InlineKeyboardButton(f'repeat: {chat.repeat}', 'r'),
                                   InlineKeyboardButton('Submit', 's')]]))
        elif status in ['year', 'month', 'day', 'hour', 'minute', 'second']:
            x = message.text
            if x.isdigit():
                e = 2
                while e:
                    try:
                        setattr(chatId_account[chat_id], chat.mode,
                                getattr(chat, chat.mode).replace(**{status: int(x)}))
                        e = False
                    except ValueError:
                        e -= 1
                        setattr(chatId_account[chat_id], chat.mode, getattr(chat, chat.mode) - timedelta(days=1))
                nl = [InlineKeyboardButton('No limit', 'nl')] if chat.mode == 'end' else []
                date = getattr(chatId_account[chat_id], chat.mode)
                bot.send_message(chat_id, f'{chat.mode} date changed successfully!',
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton(f'year: {date.year}', 'year'),
                                       InlineKeyboardButton(f'month: {date.month}', 'month'),
                                       InlineKeyboardButton(f'day: {date.day}', 'day')],
                                      [InlineKeyboardButton(f'hour: {date.hour}', 'hour'),
                                       InlineKeyboardButton(f'minute: {date.minute}', 'minute'),
                                       InlineKeyboardButton(f'second: {date.second}', 'second')],
                                      nl + [InlineKeyboardButton('back to reminder', 'b')]]))
            else:
                bot.send_message(chat_id, 'invalid message')
        elif status in ['days', 'hours', 'minutes', 'weeks']:
            x = message.text
            if x.isdigit():
                repeat = chatId_account[chat_id].repeat = f'every {x} {status}'
                end_date = 'No limit' if chat.end == no_limit else chat.end
                bot.send_message(chat_id,
                                 f'*** Reminder ***\nYour message:\n\n{chat.msg}',
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton(f'edit message', 'm'),
                                       InlineKeyboardButton(f'destination: {chat.destination}', 'dst')],
                                      [InlineKeyboardButton(f'start date: {chat.start}', 'sd'),
                                       InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                                      [InlineKeyboardButton(f'repeat: {repeat}', 'r'),
                                       InlineKeyboardButton('Submit', 's')]]))
            else:
                bot.send_message(chat_id, 'invalid message')
        elif status == 'dr':
            x = message.text
            if x.isdigit() or (x[0] == '-' and x[1:].isdigit()):
                messages = select_reminder(x)
                chatId_account[chat_id].destination = x
            else:
                messages = select_reminder(chat_id)
                chatId_account[chat_id].destination = chat_id
            all_rem = ''
            for i in messages:
                all_rem += f'ID: `{i[1]}` msg: {i[2]} start: {i[3]} end: {i[4] if i[4] != no_limit else "No limit"} repeat: {i[5]}\n'
            all_rem += '\nenter ID to delete reminder:'
            bot.send_message(chat_id, all_rem)
            chatId_account[chat_id].send_status = 'd'
            return
        elif status == 'd':
            x = message.text
            if x.isdigit() or (x[0] == '-' and x[1:].isdigit()):
                dst = chat_id if chat.destination == 'here' else int(chat.destination)
                if not delete_rem(dst, x):
                    bot.send_message(chat_id, "Reminder deleted successfully!",
                                     reply_markup=InlineKeyboardMarkup(home_key))
                else:
                    bot.send_message(chat_id, "Doesn't Exist!", reply_markup=InlineKeyboardMarkup(home_key))
        elif status == 'au':
            x = message.text
            if x.isdigit() or (x[0] == '-' and x[1:].isdigit()):
                try:
                    bot.send_message(x, 'You have been granted access!')
                    add_user(x)
                    bot.send_message(chat_id, 'User added successfully!', reply_markup=InlineKeyboardMarkup(home_key))
                except errors.exceptions.bad_request_400.PeerIdInvalid:
                    bot.send_message(chat_id, 'User not found!', reply_markup=InlineKeyboardMarkup(home_key))
        elif status == 'du':
            x = message.text
            if x.isdigit() or (x[0] == '-' and x[1:].isdigit()):
                try:
                    bot.send_message(x, 'Your access has been revoked!')
                    delete_user(x)
                    bot.send_message(chat_id, 'User deleted successfully!', reply_markup=InlineKeyboardMarkup(home_key))
                except errors.exceptions.bad_request_400.PeerIdInvalid:
                    bot.send_message(chat_id, 'User not found!', reply_markup=InlineKeyboardMarkup(home_key))
        elif status == 'dst':
            x = message.text.lower()
            if x == 'here' or x.isdigit() or (x[0] == '-' and x[1:].isdigit()):
                if x == 'here':
                    chatId_account[chat_id].destination = 'here'
                else:
                    chatId_account[chat_id].destination = int(x)
                end_date = 'No limit' if chat.end == no_limit else chat.end
                bot.send_message(chat_id, f'*** Reminder ***\nYour message:\n\n{chat.msg}',
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton(f'edit message', 'm'),
                                       InlineKeyboardButton(f'destination: {chat.destination}', 'dst')],
                                      [InlineKeyboardButton(f'start date: {chat.start}', 'sd'),
                                       InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                                      [InlineKeyboardButton(f'repeat: {chat.repeat}', 'r'),
                                       InlineKeyboardButton('Submit', 's')]]))
        else:
            try:
                if message.reply_to_message.from_user.is_self:
                    bot.send_message(chat_id, 'invalid message')
            except AttributeError:
                pass
        chatId_account[chat_id].send_status = 0


@client.on_callback_query()
def handle_callback_query(bot: Client, query: CallbackQuery):
    whitelist = select_user()
    chat_id = query.message.chat.id
    msg_id = query.message.id
    if (query.from_user.id,) not in whitelist:
        bot_username = bot.get_me().username
        bot.send_message(chat_id,
                         f"@{query.from_user.username} You don't have access in Symmio Reminder for this chat!\n"
                         f"(check @{bot_username})")
        try:
            bot.send_message(query.from_user.id,
                             f"{query.from_user.username} to get access in Symmio Reminder forward this message to admin"
                             f"\nUserID: `{query.from_user.id}`")
        except errors.exceptions.bad_request_400.PeerIdInvalid:
            bot.send_message(chat_id,
                             f"{query.from_user.username}! first start bot in @{bot_username} then /start again in this chat!")
        return
    if chat_id not in chatId_account:
        chatId_account[chat_id] = Account()
    chatId_account[chat_id].send_status = query.data
    chat = chatId_account[chat_id]
    status = chat.send_status
    if status == 'ar':
        chatId_account[chat_id].send_status = 'm'
        bot.edit_message_text(chat_id, message_id=msg_id, text='enter your message: ')
    elif status == 'dr':
        chat_ids = ''
        for c_id in {rec[0] for rec in select_reminder()}:
            chat_ids += f'{bot.get_chat(c_id).title}: `{c_id}`\n'
        bot.edit_message_text(chat_id, message_id=msg_id, text=chat_ids + 'enter another ChatID or "here": ')
    elif status == 'm':
        bot.edit_message_text(chat_id, message_id=msg_id, text='enter your new message: ')
    elif status in ['sd', 'ed']:
        if status == 'sd':
            chatId_account[chat_id].mode = 'start'
            nl = []
        else:
            chatId_account[chat_id].mode = 'end'
            nl = [InlineKeyboardButton('No limit', 'nl')]
        date = getattr(chat, chatId_account[chat_id].mode)
        bot.edit_message_text(chat_id, message_id=msg_id, text=f'edit {chatId_account[chat_id].mode} date: ',
                              reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'year: {date.year}', 'year'),
                                                                  InlineKeyboardButton(f'month: {date.month}', 'month'),
                                                                  InlineKeyboardButton(f'day: {date.day}', 'day')],
                                                                 [InlineKeyboardButton(f'hour: {date.hour}', 'hour'),
                                                                  InlineKeyboardButton(f'minute: {date.minute}',
                                                                                       'minute'),
                                                                  InlineKeyboardButton(f'second: {date.second}',
                                                                                       'second')],
                                                                 nl + [InlineKeyboardButton('back to reminder', 'b')]]))
    elif status in ['year', 'month', 'day', 'hour', 'minute', 'second']:
        bot.edit_message_text(chat_id, message_id=msg_id, text=f'enter new {status}:')
    elif status == 'nl':
        chatId_account[chat_id].end = no_limit
    elif status in ['b', 'n']:
        if status == 'n':
            chatId_account[chat_id].repeat = 'Never'
        end_date = 'No limit' if chat.end == no_limit else chat.end
        bot.edit_message_text(chat_id, message_id=msg_id, text=f'*** Reminder ***\nYour message:\n\n{chat.msg}',
                              reply_markup=InlineKeyboardMarkup(
                                  [[InlineKeyboardButton(f'edit message', 'm'),
                                    InlineKeyboardButton(f'destination: {chat.destination}', 'dst')],
                                   [InlineKeyboardButton(f'start date: {chat.start}', 'sd'),
                                    InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                                   [InlineKeyboardButton(f'repeat: {chatId_account[chat_id].repeat}', 'r'),
                                    InlineKeyboardButton('Submit', 's')]]))
    elif status == 'r':
        bot.edit_message_text(chat_id, message_id=msg_id, text=f'Repeat by N ?:',
                              reply_markup=InlineKeyboardMarkup(
                                  [[InlineKeyboardButton('Minutes', 'minutes'), InlineKeyboardButton('Hours', 'hours')],
                                   [InlineKeyboardButton('Days', 'days'), InlineKeyboardButton('Weeks', 'weeks')],
                                   [InlineKeyboardButton('Never', 'n')]]))
    elif status in ['days', 'hours', 'minutes', 'weeks']:
        bot.edit_message_text(chat_id, message_id=msg_id, text=f'Repeat every ? {status}')
    elif status == 's':
        msg_id = query.message.id
        dst = chat_id if chat.destination == 'here' else int(chat.destination)
        add(dst, str(msg_id) + str(chat_id), chat.msg, chat.start, chat.end, chat.repeat)
        bot.edit_message_text(chat_id, message_id=msg_id, text='Reminder added successfully',
                              reply_markup=InlineKeyboardMarkup(home_key))
        repeat = chat.repeat.split()
        if len(repeat) == 3:
            chatId_account[dst].messages[f'{msg_id}{chat_id}'] = scheduler.add_job(send_msg, trigger='interval',
                                                                                   args=[dst, chat.msg],
                                                                                   start_date=chat.start,
                                                                                   end_date=chat.end,
                                                                                   **{repeat[2]: int(repeat[1])})
        else:
            chatId_account[dst].messages[f'{msg_id}{chat_id}'] = scheduler.add_job(no_repeat, trigger='interval',
                                                                                   args=[dst, chat.msg,
                                                                                         f'{msg_id}{chat_id}'],
                                                                                   start_date=chat.start)
        chatId_account[chat_id].msg = ''
        chatId_account[chat_id].start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        chatId_account[chat_id].end = no_limit
        chatId_account[chat_id].repeat = 'Never'
        chatId_account[chat_id].destination = 'here'
    elif status in ['au', 'du']:
        users = ''
        if status == 'du':
            for user in whitelist:
                users += f'@{bot.get_users(user[0]).username}: `{user[0]}`\n'
        bot.edit_message_text(chat_id, message_id=msg_id, text=users + 'enter UserID:')
    elif status == 'dst':
        bot.edit_message_text(chat_id, message_id=msg_id, text='enter ChatID or "here": ')
    else:
        chatId_account[chat_id].send_status = 0


def no_repeat(chatId, msg, msgId):
    client.send_message(chatId, msg)
    chatId_account[chatId].messages[msgId].remove()
    del chatId_account[chatId].messages[msgId]
    delete_reminder(chatId, msgId)


def send_msg(chatId, msg):
    client.send_message(chatId, msg)


def delete_rem(chatId, msgId):
    try:
        chatId_account[chatId].messages[msgId].remove()
        del chatId_account[chatId].messages[msgId]
        delete_reminder(chatId, msgId)
    except KeyError:
        return 1


for rec in select_reminder():
    repeat = rec[5].split()
    if len(repeat) == 3:
        if datetime.now() <= rec[4]:
            if rec[0] not in chatId_account:
                chatId_account[rec[0]] = Account()
            chatId_account[rec[0]].messages[rec[1]] = scheduler.add_job(send_msg, trigger='interval',
                                                                        args=[rec[0], rec[2]], start_date=rec[3],
                                                                        end_date=rec[4], **{repeat[2]: int(repeat[1])})
        else:
            delete_reminder(rec[0], rec[1])
    else:
        if datetime.now() <= rec[3]:
            if rec[0] not in chatId_account:
                chatId_account[rec[0]] = Account()
            chatId_account[rec[0]].messages[rec[1]] = scheduler.add_job(no_repeat, trigger='interval',
                                                                        args=[rec[0], rec[2], rec[1]],
                                                                        start_date=rec[3])
        else:
            delete_reminder(rec[0], rec[1])

scheduler.start()
client.run()
