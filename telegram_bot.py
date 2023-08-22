import os
import re

import telebot

from downloader import start_download_operation, delete_files
from database_operations import (initialize_user_operation, add_total_downloads, is_limit_reached,
                                 find_restriction_date, restriction_message_creator)
from telegram_bot_messages import *

# load_dotenv() function is called while importing first functions from downloader
# so no need to call it again.
TELEBOT_API_TOKEN = os.getenv('TELEBOT_API_TOKEN')

bot = telebot.TeleBot(TELEBOT_API_TOKEN)

print('Telegram bot SpotyGo is now running.')


# Next comes Telegram bot functionality
@bot.message_handler(commands=['start'])
def send_welcome_message(message):
    """Sends message in response to /start command"""

    user_name = message.chat.username
    if user_name:
        reply_message = f'Hello, @{user_name}!\n\n{welcome_message}'
    else:
        reply_message = welcome_message

    bot.reply_to(message, reply_message)


@bot.message_handler(commands=['help'])
def send_help_message(message):
    """Sends message in response to /help command"""

    bot.reply_to(message, help_message)


@bot.message_handler(func=lambda message: True)
def handle_messages(message):
    """ Handles any onther message sent by user

    If the message is correct url link, starts downloading songs and sends zip file to user
    """

    chat_id = message.chat.id

    if message.entities:
        url_entities = [entity for entity in message.entities if entity.type == 'url']
        if len(url_entities) == 1:
            url = message.text
            playlsit_id_pattern = r'https://open.spotify.com/(playlist|album)/([a-zA-Z0-9]{22})'
            match = re.search(playlsit_id_pattern, url)
            if match:
                playlist_type = match.group(1)
                playlist_id = match.group(2)
                bot.send_message(chat_id, initialize_message)
                print('Initialized operation with chat_id: ', chat_id)
                if initialize_user_operation(chat_id=chat_id):
                    try:
                        start_download_operation(playlist_id, playlist_type)

                        with open(f'./Downloads/{playlist_id}/{playlist_id}.zip', mode='rb') as file:
                            bot.send_document(chat_id, file)

                        bot.send_message(chat_id, successful_download_message)
                        add_total_downloads(chat_id=chat_id)
                        is_limit_reached(chat_id=chat_id)
                    except Exception as error:
                        print('Error when downloading and sending file', error)
                        bot.send_message(chat_id, 'Sorry, there was an error. The file is too big to send')
                    finally:
                        delete_files(f'./Downloads/{playlist_id}')
                else:
                    restriction_date = find_restriction_date(chat_id=chat_id)
                    msg = restriction_message_creator(username=message.chat.username,
                                                      restriction_date=restriction_date,
                                                      message_body=restriction_message)
                    bot.send_message(chat_id, msg)
            else:
                bot.send_message(chat_id, error_incorrect_link_message)
        elif len(url_entities) > 1:
            bot.send_message(chat_id, error_one_link_message)
    else:
        bot.send_message(chat_id, error_no_link_message)
    print('Ended operation with chat_id: ', chat_id)


if __name__ == '__main__':
    bot.infinity_polling()
