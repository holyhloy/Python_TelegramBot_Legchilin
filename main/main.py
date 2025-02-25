import datetime
import re

import telegram
import psycopg2
from psycopg2.extras import RealDictCursor
from telegram.ext import Updater, CommandHandler, MessageHandler, Filters
from secret import API_TOKEN


updater = Updater(token=API_TOKEN)

conn = psycopg2.connect(
    host='localhost',
    database='calendar',
    user='postgres',
    password='postgres'
)

cursor = conn.cursor()

class Calendar:
    def __init__(self, connection):
        self.conn = connection
        self.cursor = self.conn.cursor(cursor_factory=RealDictCursor)


    # Создать метод create_event
    def create_event(self, event_name, event_date, event_time, event_details, telegram_id):

        self.cursor.execute('''INSERT INTO events (name, date, time, details, telegram_id)
                            VALUES (%s, %s, %s, %s, %s);''',
                            (
                                event_name,
                                event_date,
                                event_time,
                                event_details,
                                telegram_id)
                            )
        self.conn.commit()
        # return 'Событие создано!'


    def read_event(self, event_name):
        self.cursor.execute('SELECT name, date, time, details FROM events WHERE name = %s', (event_name,))
        event = self.cursor.fetchall()
        return event


    def edit_event(self, event_name, event_date, event_time, event_details) -> None:

        self.cursor.execute('''UPDATE events SET name = %s,
                            date = %s, time = %s, details = %s
                            WHERE name = %s''',
                            (
                                event_name,
                                event_date,
                                event_time,
                                event_details,
                                event_name
                            ))
        self.conn.commit()


    def delete_event(self, event_name):

        self.cursor.execute('DELETE FROM events WHERE name = %s', (event_name,))
        self.conn.commit()


    def display_events(self, telegram_id):
        self.cursor.execute('SELECT name, date, time, details FROM events WHERE telegram_id = %s', (telegram_id,))
        events = self.cursor.fetchall()
        return events

calendar = Calendar(conn)

cursor.execute("""
        CREATE TABLE IF NOT EXISTS events (
            id serial PRIMARY KEY,
            name text NOT NULL,
            date date NOT NULL,
            time time NOT NULL,
            details text,
            telegram_id int NOT NULL
        );
        """)
conn.commit()

def event_create_handler(update, context):
    try:

        message = update.message.text
        event =  re.search(' ([A-я0-9]+) (\d*).(\d*).(\d*).(\d*).(\d*) ([A-я0-9]+.+)', message)

        event_name = event.group(1)
        event_date = datetime.date(int(event.group(2)), int(event.group(3)), int(event.group(4)))
        event_time = datetime.time(int(event.group(5)), int(event.group(6)))
        event_details = event.group(7)
        telegram_id = update.message.chat_id

        calendar.create_event(event_name, event_date, event_time, event_details, telegram_id)

        context.bot.send_message(chat_id=update.message.chat_id,
                                    text=f"Событие {event_name} создано.")
    except Exception as err:

        context.bot.send_message(chat_id=update.message.chat_id, text=f"При создании события произошла ошибка. {err}")


updater.dispatcher.add_handler(CommandHandler('create_event', event_create_handler))


def read_event_handler(update, context):
    try:

        event_name = update.message.text[12:]
        event_str = ''

        event = calendar.read_event(event_name)

        for dict_row in event:
            event_str += '\n'
            for k, v in dict_row.items():
                event_str += f'{k}: {v}\n'

        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f"Информация о событии '{event_name}':\n{event_str}")
    except Exception as err:

        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f"При чтении события произошла ошибка: {err}")


updater.dispatcher.add_handler(CommandHandler('read_event', read_event_handler))


def edit_event_handler(update, context):
    try:

        message = update.message.text
        event = re.search(' ([A-я0-9]+) (\d*).(\d*).(\d*).(\d*).(\d*) ([A-я0-9]+.+)', message)

        event_name = event.group(1)
        event_date = datetime.date(int(event.group(2)), int(event.group(3)), int(event.group(4)))
        event_time = datetime.time(int(event.group(5)), int(event.group(6)))
        event_details = event.group(7)

        calendar.edit_event(event_name, event_date, event_time, event_details)

        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f"Событие {event_name} отредактировано.")
    except Exception as err:

        context.bot.send_message(chat_id=update.message.chat_id, text=f"При редактировании события произошла ошибка {err}")


updater.dispatcher.add_handler(CommandHandler('edit_event', edit_event_handler))


def delete_event_handler(update, context):
    try:

        event_name = update.message.text[14:]
        calendar.delete_event(event_name)
        context.bot.send_message(chat_id=update.message.chat_id,
                                 text=f"Событие {event_name} удалено.")
    except Exception as err:

        context.bot.send_message(chat_id=update.message.chat_id, text=f"При удалении события произошла ошибка {err}")


updater.dispatcher.add_handler(CommandHandler('delete_event', delete_event_handler))


def display_events_handler(update, context):
    try:

        events_str = ''
        telegram_id = update.message.chat_id
        events = calendar.display_events(telegram_id)
        for dict_row in events:
            events_str += '\n'
            for k, v in dict_row.items():
                events_str += f'{k}: {v}\n'
        context.bot.send_message(chat_id=update.message.chat_id, text=f"Список событий пользователя {telegram_id}:\n{events_str}")

    except Exception as err:

        context.bot.send_message(chat_id=update.message.chat_id, text=f"При отображении событий произошла ошибка. {err}")


updater.dispatcher.add_handler(CommandHandler('display_events', display_events_handler))


def main():
    updater.start_polling()


main()
