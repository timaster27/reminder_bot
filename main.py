import time
from datetime import datetime, timedelta

from apscheduler.schedulers.background import BackgroundScheduler
from pyrogram import Client, errors
from pyrogram.types import Message, InlineKeyboardMarkup, InlineKeyboardButton, CallbackQuery

from config import BOT_NAME, BOT_TOKEN, API_ID, API_HASH, PROXY, CHAT_ID
from db import add, select, delete, add_user, select_user

client = Client(name=BOT_NAME, bot_token=BOT_TOKEN, api_id=API_ID, api_hash=API_HASH, proxy=PROXY)
scheduler = BackgroundScheduler()
add_user(CHAT_ID, CHAT_ID)


class Account:
    def __init__(self):
        self.send_status = 0
        self.mode = None
        self.start = (datetime.now() + timedelta(hours=1)).replace(minute=0, second=0, microsecond=0)
        self.end = datetime(9999, 12, 31, 23, 59, 59)
        self.reminder = dict(message='', start=self.start, end=self.end, repeat='Never')
        self.messages = dict()


home_key = [[InlineKeyboardButton('add Reminder', 'a')], [InlineKeyboardButton('delete', 'd')],
            [InlineKeyboardButton('add user', 'u')]]
chatId_account = dict()


@client.on_message()
def handle_message(bot: Client, message: Message):
    whitelist = select_user()
    chat_id = message.chat.id
    if (message.from_user.id, chat_id) not in whitelist:
        bot.send_message(chat_id,
                         f"You ({message.from_user.username}) don't have access in Symmio Reminder for this chat!\n"
                         f"(check PV)")
        try:
            bot.send_message(message.from_user.id,
                             f"{message.from_user.username} to get access in Symmio Reminder forward this message to admin"
                             f"\nUserID: {message.from_user.id}  and ChatID: {chat_id}")
        except errors.exceptions.bad_request_400.PeerIdInvalid:
            bot.send_message(chat_id,
                             f"{message.from_user.username}! first start bot in your PV then /start again in this chat!")
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
            chatId_account[chat_id].reminder = dict(message='', start=chatId_account[chat_id].start,
                                                    end=chat.end, repeat='Never')
            bot.send_message(chat_id, 'Welcome to Symmio Reminder', reply_markup=InlineKeyboardMarkup(home_key))
        elif status == 'm':
            chatId_account[chat_id].reminder["message"] = message.text
            end_date = 'No limit' if chat.reminder["end"] == chat.end else chat.reminder["end"]
            bot.send_message(chat_id,
                             f'Add new Reminder\nYour message:\n\n{chatId_account[chat_id].reminder["message"]}',
                             reply_markup=InlineKeyboardMarkup(
                                 [[InlineKeyboardButton(f'edit message', 'm')],
                                  [InlineKeyboardButton(f'start date: {chat.reminder["start"]}', 'sd'),
                                   InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                                  [InlineKeyboardButton(f'repeat: {chat.reminder["repeat"]}', 'r'),
                                   InlineKeyboardButton('Submit', 's')]]))
        elif status in ['year', 'month', 'day', 'hour', 'minute', 'second']:
            x = message.text
            if x.isdigit():
                e = 2
                while e:
                    try:
                        chatId_account[chat_id].reminder[chat.mode] = chatId_account[chat_id].reminder[
                            chat.mode].replace(**{status: int(x)})
                        e = False
                    except ValueError:
                        e -= 1
                        chatId_account[chat_id].reminder[chat.mode] -= timedelta(days=1)
                nl = [InlineKeyboardButton('No limit', 'nl')] if chat.mode == 'end' else []
                date = chatId_account[chat_id].reminder[chat.mode]
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
                repeat = chatId_account[chat_id].reminder['repeat'] = f'every {x} {status}'
                end_date = 'No limit' if chat.reminder["end"] == chat.end else chat.reminder["end"]
                bot.send_message(chat_id,
                                 f'*** Reminder ***\nYour message:\n\n{chat.reminder["message"]}',
                                 reply_markup=InlineKeyboardMarkup(
                                     [[InlineKeyboardButton(f'edit message', 'm')],
                                      [InlineKeyboardButton(f'start date: {chat.reminder["start"]}', 'sd'),
                                       InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                                      [InlineKeyboardButton(f'repeat: {repeat}', 'r'),
                                       InlineKeyboardButton('Submit', 's')]]))
            else:
                bot.send_message(chat_id, 'invalid message')
        elif status == 'd':
            x = message.text
            if x.isdigit() or (x[0] == '-' and x[1:].isdigit()):
                delete_reminder(chat_id, int(x))
                bot.send_message(chat_id, 'Reminder deleted successfully!', reply_markup=InlineKeyboardMarkup(home_key))
        elif status == 'u':
            x = message.text.split()
            if (x[0].isdigit() or (x[0][0] == '-' and x[0][1:].isdigit())) and (
                    x[1].isdigit() or (x[1][0] == '-' and x[1][1:].isdigit())):
                add_user(x[0], x[1])
                bot.send_message(x[0], 'You got access in a chat!')
                bot.send_message(chat_id, 'User added successfully!', reply_markup=InlineKeyboardMarkup(home_key))
        else:
            bot.send_message(chat_id, 'invalid message')
        chatId_account[chat_id].send_status = 0


@client.on_callback_query()
def handle_callback_query(bot: Client, query: CallbackQuery):
    whitelist = select_user()
    chat_id = query.message.chat.id
    if (query.from_user.id, chat_id) not in whitelist:
        bot.send_message(chat_id,
                         f"You ({query.from_user.username}) don't have access in Symmio Reminder for this chat!\n"
                         f"(check PV)")
        try:
            bot.send_message(query.from_user.id,
                             f"{query.from_user.username} to get access in Symmio Reminder forward this message to admin"
                             f"\nUserID: {query.from_user.id}  and ChatID: {chat_id}")
        except errors.exceptions.bad_request_400.PeerIdInvalid:
            bot.send_message(chat_id,
                             f"{query.from_user.username}! first start bot in your PV then /start again in this chat!")
        return
    if chat_id not in chatId_account:
        chatId_account[chat_id] = Account()
    chatId_account[chat_id].send_status = query.data
    chat = chatId_account[chat_id]
    status = chat.send_status
    if status == 'a':
        chatId_account[chat_id].send_status = 'm'
        bot.send_message(chat_id, 'enter your message: ')
    elif status == 'd':
        messages = select(chat_id)
        all_rem = ''
        for i in messages:
            all_rem += f'ID:{i[1]} msg:{i[2]} start:{i[3]} end:{i[4]} repeat:{i[5]}\n'
        all_rem += 'enter ID to delete reminder:'
        bot.send_message(chat_id, all_rem)
    elif status == 'm':
        bot.send_message(chat_id, 'enter your new message: ')
    elif status in ['sd', 'ed']:
        if status == 'sd':
            chatId_account[chat_id].mode = 'start'
            nl = []
        else:
            chatId_account[chat_id].mode = 'end'
            nl = [InlineKeyboardButton('No limit', 'nl')]
        date = chat.reminder[chatId_account[chat_id].mode]
        bot.send_message(chat_id, f'edit {chatId_account[chat_id].mode} date: ',
                         reply_markup=InlineKeyboardMarkup([[InlineKeyboardButton(f'year: {date.year}', 'year'),
                                                             InlineKeyboardButton(f'month: {date.month}', 'month'),
                                                             InlineKeyboardButton(f'day: {date.day}', 'day')],
                                                            [InlineKeyboardButton(f'hour: {date.hour}', 'hour'),
                                                             InlineKeyboardButton(f'minute: {date.minute}', 'minute'),
                                                             InlineKeyboardButton(f'second: {date.second}', 'second')],
                                                            nl + [InlineKeyboardButton('back to reminder', 'b')]]))
    elif status in ['year', 'month', 'day', 'hour', 'minute', 'second']:
        bot.send_message(chat_id, f'enter new {status}')
    elif status == 'nl':
        chatId_account[chat_id].reminder['end'] = chat.end
    elif status in ['b', 'n']:
        if status == 'n':
            chatId_account[chat_id].reminder["repeat"] = 'Never'
        end_date = 'No limit' if chat.reminder["end"] == chat.end else chat.reminder["end"]
        bot.send_message(chat_id, f'*** Reminder ***\nYour message:\n\n{chat.reminder["message"]}',
                         reply_markup=InlineKeyboardMarkup(
                             [[InlineKeyboardButton(f'edit message', 'm')],
                              [InlineKeyboardButton(f'start date: {chat.reminder["start"]}', 'sd'),
                               InlineKeyboardButton(f'end date: {end_date}', 'ed')],
                              [InlineKeyboardButton(f'repeat: {chatId_account[chat_id].reminder["repeat"]}', 'r'),
                               InlineKeyboardButton('Submit', 's')]]))
    elif status == 'r':
        bot.send_message(chat_id, f'Repeat by N _____:',
                         reply_markup=InlineKeyboardMarkup(
                             [[InlineKeyboardButton('Minutes', 'minutes'), InlineKeyboardButton('Hours', 'hours')],
                              [InlineKeyboardButton('Days', 'days'), InlineKeyboardButton('Weeks', 'weeks')],
                              [InlineKeyboardButton('Never', 'n')]]))
    elif status in ['days', 'hours', 'minutes', 'weeks']:
        bot.send_message(chat_id, f'Repeat every ?? {status}')
    elif status == 's':
        msg_id = query.message.id
        add(chat_id, msg_id, chat.reminder['message'], chat.reminder['start'], chat.reminder['end'],
            chat.reminder['repeat'])
        bot.send_message(chat_id, 'Reminder added successfully', reply_markup=InlineKeyboardMarkup(home_key))
        repeat = chat.reminder['repeat'].split()
        if len(repeat) == 3:
            chatId_account[chat_id].messages[msg_id] = scheduler.add_job(send_msg, trigger='interval',
                                                                         args=[chat_id, chat.reminder['message']],
                                                                         start_date=chat.reminder['start'],
                                                                         end_date=chat.reminder['end'],
                                                                         **{repeat[2]: int(repeat[1])})
        else:
            chatId_account[chat_id].messages[msg_id] = scheduler.add_job(no_repeat, trigger='interval',
                                                                         args=[chat_id, chat.reminder['message'],
                                                                               msg_id],
                                                                         start_date=chat.reminder['start'])
        chatId_account[chat_id].reminder = dict(message='', start=chat.start, end=chat.end, repeat='Never')
    elif status == 'u':
        bot.send_message(chat_id, 'enter UserID and ChatID with a space seperator:')
    else:
        chatId_account[chat_id].send_status = 0


async def main():
    async with client:
        while True:
            await client.get_me()
            time.sleep(10)


def no_repeat(chatId, msg, msgId):
    client.send_message(chatId, msg)
    chatId_account[chatId].messages[msgId].remove()
    del chatId_account[chatId].messages[msgId]
    delete(chatId, msgId)


def send_msg(chatId, msg):
    client.send_message(chatId, msg)


def delete_reminder(chatId, msgId):
    chatId_account[chatId].messages[msgId].remove()
    del chatId_account[chatId].messages[msgId]
    delete(chatId, msgId)


for rec in select():
    repeat = rec[5].split()
    if len(repeat) == 3:
        if datetime.now() <= rec[4]:
            if rec[0] not in chatId_account:
                chatId_account[rec[0]] = Account()
            chatId_account[rec[0]].messages[rec[1]] = scheduler.add_job(send_msg, trigger='interval',
                                                                        args=[rec[0], rec[2]], start_date=rec[3],
                                                                        end_date=rec[4], **{repeat[2]: int(repeat[1])})
        else:
            delete(rec[0], rec[1])
    else:
        if datetime.now() <= rec[3]:
            if rec[0] not in chatId_account:
                chatId_account[rec[0]] = Account()
            chatId_account[rec[0]].messages[rec[1]] = scheduler.add_job(no_repeat, trigger='interval',
                                                                        args=[rec[0], rec[2], rec[1]],
                                                                        start_date=rec[3])
        else:
            delete(rec[0], rec[1])

scheduler.start()
client.run(main())
