import os
import re

import telebot

from downloader import start_download_operation, delete_files
from database_operations import (connect_to_database, close_connection, initialize_user_operation,
                                 add_total_downloads, is_limit_reached,
                                 find_restriction_date, restriction_message_creator)
from telegram_bot_messages import my_messages


TELEBOT_API_TOKEN = os.getenv('TELEBOT_API_TOKEN')
bot = telebot.TeleBot(TELEBOT_API_TOKEN)


print('Telegram bot SpotyGo is now running.')


# Next comes Telegram bot functionality
@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    """Sends message in response to /start command"""

    user_name = message.chat.username
    if user_name:
        reply_message = f'Hello, @{user_name}!\n\n{my_messages["welcome_message"]}'
    else:
        reply_message = my_messages['welcome_message']

    bot.reply_to(message, reply_message)


@bot.message_handler(commands=['help'])
def send_help_message(message):
    """Sends message in response to /help command"""

    bot.reply_to(message, my_messages['help_message'])


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """ Handles any onther message sent by user

    If the message is correct url link, starts downloading songs and sends zip file to user.
    """
    chat_id = message.chat.id
    print('Initialized process with chat_id: ', chat_id)
    if message.entities:
        url_entities = [entity for entity in message.entities if entity.type == 'url']
        if len(url_entities) == 1:
            url = message.text
            playlsit_id_pattern = r'https://open.spotify.com/(playlist|album)/([a-zA-Z0-9]{22})'
            match = re.search(playlsit_id_pattern, url)
            if match:
                playlist_type = match.group(1)
                playlist_id = match.group(2)
                bot.send_message(chat_id, my_messages['initialize_message'])
                conn = connect_to_database()  # returns list-> [connection, tunnel, cursor()]
                if initialize_user_operation(connection=conn, chat_id=chat_id):
                    try:
                        add_total_downloads(connection=conn, chat_id=chat_id)
                        is_limit_reached(connection=conn, chat_id=chat_id)

                        start_download_operation(playlist_id, playlist_type)

                        with open(f'./Downloads/archives/{playlist_id}.zip', mode='rb') as file:
                            bot.send_document(chat_id, file)

                        bot.send_message(chat_id, my_messages['successful_download_message'])

                    except Exception as error:
                        print('Error when downloading and sending file', error)
                        bot.send_message(chat_id, my_messages['file_error_message'])
                    finally:
                        delete_files(playlist_id)
                        close_connection(connection=conn)
                else:
                    restriction_date = find_restriction_date(connection=conn, chat_id=chat_id)
                    restriction_message = restriction_message_creator(username=message.chat.username,
                                                                      restriction_date=restriction_date,
                                                                      message_body=my_messages['restriction_message'])
                    bot.reply_to(message, restriction_message)
                    close_connection(connection=conn)
            else:
                bot.send_message(chat_id, my_messages['error_incorrect_link_message'])
        elif len(url_entities) > 1:
            bot.send_message(chat_id, my_messages['error_one_link_message'])
    else:
        bot.send_message(chat_id, my_messages['error_no_link_message'])
    print('End of process with chat_id: ', chat_id)


if __name__ == '__main__':
    bot.infinity_polling()

