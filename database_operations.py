import os
from datetime import datetime
from abc import ABC

import sshtunnel
import MySQLdb


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
    """
    Base abstract class for database operations.

    This class enforces a contract for creating connection, cursor, and chat_id attributes.

    Args:
        connection: A database connection object.
        cursor: A database cursor object.
        chat_id: The chat_id associated with the operations.
    """
    def __init__(self, connection, cursor, chat_id):
        self._connection = connection
        self._cursor = cursor
        self._chat_id = chat_id


class GetDataOperations(DatabaseOperations):
    """
    Class for database data retrieval operations.

    This class provides methods for retrieving data from the database with built-in exception handling.

    Inherits from:
        DatabaseOperations
    """

    @staticmethod
    def select_excpetions_handler(func):
        """Decorator for handling exceptions when executing select methods."""

        def wrapper(*args, **kwargs):
            try:
                return func(*args, **kwargs)
            except MySQLdb.Error as db_error:
                print('Database operation exception occured during select operation. Error: ', db_error)
            except Exception as other_error:
                print('Other exception occured during select operation. Error: ', other_error)
            return None
        return wrapper

    @select_excpetions_handler
    def chatid_exists(self):
        """Check if the chat_id exists in the database.

        This method executes a SQL query to check the existence of a chat_id in the 'users' table.
        """
        query = 'SELECT EXISTS (SELECT 1 FROM users WHERE chat_id = %s)'
        self._cursor.execute(query, (self._chat_id,))
        result = self._cursor.fetchone()[0]
        return result

    @select_excpetions_handler
    def get_downloads_number(self):
        """Get downloads number of chat_id from the database.

        This method executes a SQL query to get the downloads value from 'users' table,
        for a concrete given chat_id.
        """
        query = 'SELECT downloads FROM users WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        result = self._cursor.fetchone()[0]
        return result

    @select_excpetions_handler
    def get_restriction_date(self):
        """Get restriction date of chat_id from the database.

        This method executes a SQL query to get the restriction date from 'users' table,
        for a concrete given chat_id.
        """
        query = 'SELECT date_of_restriction FROM users WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        result = self._cursor.fetchone()[0]
        return result


class ModifyDataOperations(DatabaseOperations):
    """A class for database modification operations with exception handling.

    This class provides methods for modifying data in the database with built-in exception handling.
    If an exception occurs during the execution of these methods, a rollback is performed to maintain
    data consistency.

    Inherits from:
        DatabaseOperations
    """
    @staticmethod
    def modify_excpetions_handler(func):
        """Decorator for handling exceptions when executing insert/modify methods.
        In case of exception, rollback is performed.
        """
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
        """Adds the chat_id value to the database.

        This method executes a SQL query to insert new chat_id value to the 'users' table,
        where chat_id is Primary Key. So the new row will be created.
        """
        query = 'INSERT INTO users (chat_id) VALUES (%s)'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def add_downloads(self):
        """Adds the downloads value to the database for chat_id.

        This method executes a SQL query to update downloads value in the 'users' table,
        for a concrete chat_id. By default, downloads is 0.
        """
        query = 'UPDATE users SET downloads = CASE WHEN downloads IS NULL THEN 1 ELSE downloads ' \
                '+ 1 END WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def add_total_downloads(self):
        """Adds the total_downloads value to the database for chat_id.

        This method executes a SQL query to update total_downloads value in the 'users' table,
        for a concrete chat_id. By default, total_downloads is 0.
        """
        query = 'UPDATE users SET total_downloads = CASE WHEN total_downloads IS NULL THEN 1 ELSE total_downloads ' \
                '+ 1 END WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def add_restriction_date(self, date_of_restriction):
        """Adds the restriction_date value to the database for chat_id.

        This method executes a SQL query to update restriction_date value in the 'users' table,
        for a concrete chat_id. By default, restriction_date is Null.
        """
        query = 'UPDATE users SET date_of_restriction = %s WHERE chat_id = %s'
        self._cursor.execute(query, (date_of_restriction, self._chat_id))
        self._connection.commit()

    @modify_excpetions_handler
    def clear_downloads(self):
        """Clears the downloads value of the database for chat_id.

        This method executes a SQL query to set downloads value to default in the 'users' table,
        for a concrete chat_id. By default, downloads is 0.
        """
        query = 'UPDATE users SET downloads = DEFAULT WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()

    @modify_excpetions_handler
    def clear_restriction_date(self):
        """Clears the restriction_date value of the database for chat_id.

        This method executes a SQL query to set restriction_date value to default in the 'users' table,
        for a concrete chat_id. By default, restriction_date is Null.
        """
        query = 'UPDATE users SET date_of_restriction = DEFAULT WHERE chat_id = %s'
        self._cursor.execute(query, (self._chat_id,))
        self._connection.commit()


# Functions fo connections handling
def connect_to_database() -> list:
    """Creates connection to database, by creating sshtunnel, db_conenction and cursor.

    It returns list, that consists of [db_connection, tunnel, cursor()].
    """
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
            return [db_connection, tunnel, db_connection.cursor()]
        except (MySQLdb.Error, Exception) as e:
            print('Connection: unsuccessful. Error: ', e)
            tunnel.stop()
            return None
    except Exception as tunnel_error:
        print('Error while creating SSH tunnel. Error: ', tunnel_error)


def close_connection(connection) -> None:
    """Closes sshtunnel, connection and cursor object.

    Takes list of these objects as a parameter."""
    try:
        connection[2].close()
        connection[0].close()
        connection[1].stop()
        print('Connection: closed...')
    except Exception as e:
        print('Connection was not closed properly: ', e)


# Decorators for database functions
def modify_only_operation_handler(func):
    """Decorator used to wrap functions which only modify database data.

    It returns function with passed ModifyDataOperations() object to it.
    """
    def wrapper(connection, *args, **kwargs):
        modify_data = ModifyDataOperations(connection=connection[0],
                                           cursor=connection[2],
                                           *args, **kwargs)
        try:
            return func(modify_data=modify_data,
                        *args, **kwargs)
        except Exception as err:
            print('Error occured with modify db operation: ', err)
    return wrapper


def get_only_operation_handler(func):
    """Decorator used to wrap functions which only get database data.

    It returns function with passed GetDataOperations() object to it.
    """
    def wrapper(connection, *args, **kwargs):
        get_data = GetDataOperations(connection=connection[0],
                                     cursor=connection[2],
                                     *args, **kwargs)
        try:
            return func(get_data=get_data,
                        *args, **kwargs)
        except Exception as err:
            print('Error occured with get db operation: ', err)
    return wrapper


def double_operation_handler(func):
    """Decorator used to wrap functions which bot get and modify database data.

    It returns function with passed ModifyDataOperations() and GetDataOperations() objects to it.
    """
    def wrapper(connection, *args, **kwargs):
        get_data = GetDataOperations(connection=connection[0],
                                     cursor=connection[2],
                                     *args, **kwargs)
        modify_data = ModifyDataOperations(connection=connection[0],
                                           cursor=connection[2],
                                           *args, **kwargs)
        try:
            return func(get_data=get_data,
                        modify_data=modify_data,
                        *args, **kwargs)
        except Exception as err:
            print('Error occured with double db operation: ', err)
    return wrapper


# Database functions block
@double_operation_handler
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


@double_operation_handler
def is_limit_reached(get_data, modify_data, chat_id) -> None:
    """Checks if user reached limit of downloads, and updates database if True."""

    modify_data.add_downloads()
    user_downloads = get_data.get_downloads_number()
    if user_downloads >= 2:
        utcdate = str(datetime.now().date())
        modify_data.add_restriction_date(date_of_restriction=utcdate)


@modify_only_operation_handler
def add_total_downloads(modify_data, chat_id) -> None:
    """Adds + 1 to database column total_downloads."""

    modify_data.add_total_downloads()


@get_only_operation_handler
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
