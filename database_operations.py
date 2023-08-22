import os

import sshtunnel
import MySQLdb
from abc import ABC

# from dbconfig import config
from datetime import datetime


# ssh_host = config['ssh_host']
# ssh_port = config['ssh_port']
# ssh_user = config['ssh_user']
# ssh_pass = config['ssh_pass']
#
# host = config['host']
# user = config['user']
# password = config['password']
# db_name = config['database']
ssh_host = os.getenv('SSH_HOST')
ssh_port = os.getenv('SSH_PORT')
ssh_user = os.getenv('SSH_USER')
ssh_pass = os.getenv('SSH_PASS')

host = os.getenv('HOST')
user = os.getenv('USER')
password = os.getenv('PASSWORD')
db_name = os.getenv('DATABASE')

today = str(datetime.now().date())


class DatabaseOperations(ABC):

    def __init__(self, connection, cursor, chat_id):
        self._connection = connection
        self._cursor = cursor
        self._chat_id = chat_id


class GetDataOperations(DatabaseOperations):

    @staticmethod
    def select_excpetions_handler(func):
        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MySQLdb.Error as db_error:
                print('Database operation exception occured during select operation. Error: ', db_error)
            except Exception as other_error:
                print('Other exception occured during select operation. Error: ', other_error)
        return wrapper

    @select_excpetions_handler
    def chatid_exists(self):
        query = f'SELECT EXISTS (SELECT 1 FROM users WHERE chat_id = %s)'
        self._cursor.execute(query, (self._chat_id,))
        result = self._cursor.fetchone()[0]
        return result

    @select_excpetions_handler
    def get_downloads_number(self):
        query = f'SELECT downloads FROM users WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        result = self._cursor.fetchone()[0]
        return result

    @select_excpetions_handler
    def get_restriction_date(self):
        query = f'SELECT date_of_restriction FROM users WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        result = self._cursor.fetchone()[0]
        return result


class ModifyDataOperations(DatabaseOperations):

    @staticmethod
    def modify_excpetions_handler(func):
        def wrapper(self, *args, **kwargs):
            try:
                return func(self, *args, **kwargs)
            except MySQLdb.Error as db_error:
                print('Database operation error occured during modifying. Error: ', db_error)
                self._connection.rollback()
            except Exception as other_error:
                print('Other exception occured during modifying. Error: ', other_error)
                self._connection.rollback()
            return None

        return wrapper

    @modify_excpetions_handler
    def add_chat_id(self):
        query = f'INSERT INTO users (chat_id) VALUES (%s)'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def add_downloads(self):
        query = 'UPDATE users SET downloads = CASE WHEN downloads IS NULL THEN 1 ELSE downloads ' \
                '+ 1 END WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def add_total_downloads(self):
        query = 'UPDATE users SET total_downloads = CASE WHEN total_downloads IS NULL THEN 1 ELSE total_downloads ' \
                '+ 1 END WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def add_restriction_date(self, date_of_restriction):
        query = 'UPDATE users SET date_of_restriction = %s WHERE chat_id = %s'
        self._cursor.execute(query, (date_of_restriction, self._chat_id))
        self._connection.commit()

    @modify_excpetions_handler
    def clear_downloads(self):
        query = 'UPDATE users SET downloads = DEFAULT WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def clear_restriction_date(self):
        query = 'UPDATE users SET date_of_restriction = DEFAULT WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()


def connect_to_database():
    try:
        sshtunnel.SSH_TIMEOUT = 15.0
        sshtunnel.TUNNEL_TIMEOUT = 15.0
        tunnel = sshtunnel.SSHTunnelForwarder(
            ssh_host,
            ssh_username=ssh_user,
            ssh_password=ssh_pass,
            remote_bind_address=(host, 3306),)
        tunnel.start()
        try:
            db_connection = MySQLdb.connect(
                host='127.0.0.1',  # It's a local address for the SSH tunnel
                port=tunnel.local_bind_port,
                user=user,
                passwd=password,
                db=db_name,
                autocommit=False,
                connect_timeout=10
            )
            print('Connection: opened...')
            return [db_connection, tunnel]
        except (MySQLdb.Error, Exception) as e:
            print('Connection: unsuccessful. Error: ', e)
            tunnel.stop()
            return None
    except Exception as tunnel_error:
        print('Error while creating SSH tunnel. Error: ', tunnel_error)


def modify_only_connection_handler(func):
    def wrapper(*args, **kwargs):
        start_connection = connect_to_database()
        connection = start_connection[0]
        tunnel = start_connection[1]
        cursor = connection.cursor()

        modify_data = ModifyDataOperations(connection=connection,
                                           cursor=cursor,
                                           *args, **kwargs)
        try:
            return func(modify_data=modify_data,
                        *args, **kwargs)
        except Exception as err:
            print('Error occured with database operation: ', err)
        finally:
            cursor.close()
            connection.close()
            tunnel.stop()
            print('Connection closed...')
    return wrapper


def get_only_connection_handler(func):
    def wrapper(*args, **kwargs):
        start_connection = connect_to_database()
        connection = start_connection[0]
        tunnel = start_connection[1]
        cursor = connection.cursor()

        get_data = GetDataOperations(connection=connection,
                                     cursor=cursor,
                                     *args, **kwargs)
        try:
            return func(get_data=get_data,
                        *args, **kwargs)
        except Exception as err:
            print('Error occured with get operation: ', err)
        finally:
            cursor.close()
            connection.close()
            tunnel.stop()
            print('Connection closed...')
    return wrapper


def double_connection_handler(func):
    def wrapper(*args, **kwargs):
        start_connection = connect_to_database()
        connection = start_connection[0]
        tunnel = start_connection[1]
        cursor = connection.cursor()

        get_data = GetDataOperations(connection=connection,
                                     cursor=cursor,
                                     *args, **kwargs)
        modify_data = ModifyDataOperations(connection=connection,
                                           cursor=cursor,
                                           *args, **kwargs)
        try:
            return func(get_data=get_data,
                        modify_data=modify_data,
                        *args, **kwargs)
        except Exception as err:
            print('Error occured with modify operation: ', err)
        finally:
            cursor.close()
            connection.close()
            tunnel.stop()
            print('Connection: closed...')
    return wrapper


@double_connection_handler
def initialize_user_operation(get_data, modify_data, chat_id) -> bool:
    """Function checks if user can proceed to download the songs.

    Checks if user's chat_id is in database, and adds it if not. Then checks if user has less than 2
    downloads completed. If false - checks his restriction date and compares to today date.
    If difference is 0 days, clears his restrictions. In other scenarios, return True.
    """

    try:
        chat_exists = get_data.chatid_exists()
        if chat_exists:
            its_downloads = get_data.get_downloads_number()
            if its_downloads >= 2:
                user_restriction_date = get_data.get_restriction_date()
                if user_restriction_date is not None:
                    restriction_date = str(user_restriction_date)
                    today_date = datetime.strptime(today, '%Y-%m-%d')
                    restricted_at_date = datetime.strptime(restriction_date, '%Y-%m-%d')
                    difference = today_date - restricted_at_date
                    difference_in_days = 7 - difference.days
                    if difference_in_days == 0:
                        modify_data.clear_restriction_date()
                        modify_data.clear_downloads()
                        return True
                    else:
                        return False
            else:
                return True
        else:
            modify_data.add_chat_id()
            return True
    except Exception as err:
        print('Error in initialization of user: ', err)


@modify_only_connection_handler
def add_total_downloads(modify_data, chat_id):
    """Adds + 1 to database columns (downloads) and (total_downloads)."""

    modify_data.add_total_downloads()


@double_connection_handler
def is_limit_reached(get_data, modify_data, chat_id):
    """Checks if user reached limit of downloads, and updates database if True."""

    modify_data.add_downloads()
    user_downloads = get_data.get_downloads_number()
    if user_downloads >= 2:
        utcdate = str(datetime.now().date())
        modify_data.add_restriction_date(date_of_restriction=utcdate)


@get_only_connection_handler
def find_restriction_date(get_data, chat_id) -> str:
    """Returns user restriction date as string."""
    restriction_date = get_data.get_restriction_date()
    if restriction_date is not None:
        return str(restriction_date)


def restriction_message_creator(username: str, restriction_date: str, message_body: str) -> str:
    """Creates a message string to be sent when user has active restriction."""
    start_part = f'Oh Lord, @{username}!\n\n'
    today_date = datetime.strptime(today, '%Y-%m-%d')
    restricted_at_date = datetime.strptime(restriction_date, '%Y-%m-%d')
    difference = today_date - restricted_at_date
    difference_in_days = 7 - difference.days
    end_part = f'Your access will be renewed in {difference_in_days} days.'
    if difference_in_days == 1:
        end_part = 'Your access will be renewed tomorrow.'
    final_msg = (start_part + message_body + end_part)
    return final_msg
