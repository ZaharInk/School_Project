import sqlite3


def check_user(user_id):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    return cursor.execute(f'SELECT user_id FROM users WHERE user_id = {user_id}').fetchone()


def create_user(user_id, master_password, salt):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
    insert into users(user_id, master_password, salt)
    values(?, ?, ?)
    ''', (user_id, master_password, salt))
    conn.commit()


def get_data(user_id):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    return cursor.execute(f'SELECT master_password, salt FROM users WHERE user_id ={user_id}').fetchone()


def add_item(user_id, item, name, info):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
    insert into items(user_id, item, name, info)
    values(?, ?, ?, ?)
    ''', (user_id, item, name, info))
    conn.commit()


def get_items(user_id):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    return cursor.execute(f'SELECT id, item, name, info FROM items WHERE user_id = {user_id}').fetchall()


def get_item(user_id, id):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    return cursor.execute(f'SELECT id, item, name, info FROM items WHERE id = {id} AND user_id = {user_id}').fetchone()


def delete_item(user_id, id):
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    cursor.execute(f'DELETE FROM items WHERE id = {id} AND user_id = {user_id}')
    conn.commit()


if __name__ == '__main__':
    conn = sqlite3.connect('SecretPass.sqlite')
    cursor = conn.cursor()
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS users(
            user_id INTEGER PRIMARY KEY,
            master_password TEXT NOT NULL,
            salt TEXT NOT NULL
            )
        ''')
    cursor.execute('''
            CREATE TABLE IF NOT EXISTS items(
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            user_id INTEGER NOT NULL,
            item TEXT NOT NULL ,
            name TEXT NOT NULL,
            info BLOB NOT NULL,
            FOREIGN KEY (user_id) REFERENCES users (user_id) ON DELETE CASCADE
            )
        ''')
    cursor.close()
    conn.close()
