import mysql.connector
from settings import take_sql_set
from werkzeug.security import generate_password_hash, check_password_hash


class request:
    def __init__(self):

        setings = take_sql_set()

        self.host= setings['host']
        self.user= setings['user']
        self.password= setings['password']
        self.database= setings['database']   

    def autorize(self, username, password):
        hash_password = generate_password_hash(password)

        conn = self.get_db_connection()

        cursor = conn.cursor(dictionary=True)
        cursor.execute("SELECT * FROM Users WHERE name = %s and password = %s", [username, hash_password])
        admin = cursor.fetchone()

        cursor.close()
        conn.close()

    def get_db_connection(self):

        conn = mysql.connector.connect(
            host=self.host,
            user=self.user,
            password=self.password,
            database=self.database
        )
        return conn





