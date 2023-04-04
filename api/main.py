from flask import Flask, request
from pymysql import connect
from pymysql.cursors import DictCursor
from flask_restx import Api, Resource

app = Flask(__name__)
app.config['SECRET_KEY'] = 'supersecret'
api = Api(app)
API_KEY = "supersecret"

# Database connection parameters
db_config = {
    "host": "34.133.174.225",
    "user": "root",
    "password": "Kostenkele",
    "database": "main",
}

def init_app():
    try:
        # Call the get_db_connection() function to create the users table if it doesn't exist
        connection = get_db_connection()
        cursor = connection.cursor()
        create_users_table_query = """
        CREATE TABLE IF NOT EXISTS users (
            id INT AUTO_INCREMENT PRIMARY KEY,
            username VARCHAR(255) NOT NULL UNIQUE,
            password VARCHAR(255) NOT NULL
        );
        """
        cursor.execute(create_users_table_query)
        connection.commit()
        cursor.close()  # Close the cursor after executing the query
        connection.close()
        print("Users table created or already exists.")
    except Exception as e:
        print("Error while creating users table:", e)

def get_db_connection():
    connection = connect(**db_config)
    return connection

def fetch_data_from_db(query):
    connection = get_db_connection()
    cursor = connection.cursor(DictCursor)
    cursor.execute(query)
    data = cursor.fetchall()
    columns = [column[0] for column in cursor.description]
    connection.close()
    return {"data": data, "columns": columns}

class Articles(Resource):
    def get(self):
        api_key = request.headers.get("X-API-KEY")
        if not api_key or api_key != API_KEY:
            return {"error": "Invalid API key"}, 401

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM articles LIMIT 10000")
        articles = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]  # Get the column names
        connection.close()

        return {"data": articles, "columns": column_names}

class Transactions(Resource):
    def get(self):
        api_key = request.headers.get("X-API-KEY")
        if not api_key or api_key != API_KEY:
            return {"error": "Invalid API key"}, 401

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM transactions LIMIT 100000")
        transactions = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]  # Get the column names
        connection.close()

        return {"data": transactions, "columns": column_names}

class Customers(Resource):
    def get(self):
        api_key = request.headers.get("X-API-KEY")
        if not api_key or api_key != API_KEY:
            return {"error": "Invalid API key"}, 401

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM customers LIMIT 10000")
        customers = cursor.fetchall()
        column_names = [desc[0] for desc in cursor.description]  # Get the column names
        connection.close()

        return {"data": customers, "columns": column_names}

class UsersSignup(Resource):
    def post(self):
        api_key = request.headers.get("X-API-KEY")
        if not api_key or api_key != API_KEY:
            return {"error": "Invalid API key"}, 401

        data = request.get_json()
        new_username = data.get('username')
        new_password = data.get('password')

        # Validation and other operations like hashing the password should be done here

        connection = get_db_connection()
        cursor = connection.cursor()
        
        # Check if the username already exists
        cursor.execute("SELECT * FROM users WHERE username = %s", (new_username,))
        existing_user = cursor.fetchone()

        if not existing_user:
            cursor.execute("INSERT INTO users (username, password) VALUES (%s, %s)", (new_username, new_password))
            connection.commit()
            cursor.close()
            connection.close()
            return {"message": "User created successfully"}
        else:
            cursor.close()
            connection.close()
            return {"error": "Username already exists"}, 409


class UsersLogin(Resource):
    def post(self):
        api_key = request.headers.get("X-API-KEY")
        if not api_key or api_key != API_KEY:
            return {"error": "Invalid API key"}, 401

        data = request.get_json()
        username = data.get('username')
        password = data.get('password')

        connection = get_db_connection()
        cursor = connection.cursor()
        cursor.execute("SELECT * FROM users WHERE username = %s", (username,))
        user = cursor.fetchone()
        cursor.close()
        connection.close()

        if user and password == user[2]:
            # Replace this with a proper token generation process
            access_token = "your_access_token_here"
            return {"access_token": access_token}
        else:
            return {"error": "Username/password is incorrect"}, 401

api.add_resource(UsersSignup, "/api/users/signup")
api.add_resource(UsersLogin, "/api/users/login")
api.add_resource(Articles, "/api/articles")
api.add_resource(Transactions, "/api/transactions")
api.add_resource(Customers, "/api/customers")

if __name__ == "__main__":
    init_app() 
    app.run(debug=True, port=3010)