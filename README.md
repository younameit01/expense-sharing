Welcome to the Expense Sharing Web Application! This README will guide you through the process of setting up and running the server locally, as well as performing necessary database migrations.

## Prerequisites

Before you begin, ensure you have met the following requirements:

- [Python](https://www.python.org/downloads/) (version 3.6 or higher)
- [Pip](https://pip.pypa.io/en/stable/installation/) (Python package manager)
- MySQL Server (for the database)

## Installation

1. Clone the repository:

   ```
   git clone https://github.com/younameit01/expense-sharing.git
   cd expense-sharing
2. Create a Python virtual environment (recommended):
    ``````
    python -m venv venv
    source venv/bin/activate

3. Install the required Python packages:
    ```
    pip install -r requirements.txt

## Configuration

```
Configure environment variables by editing config.py file in the project root.
```

## Database Migration
Before running the server, you need to apply database migrations to create the necessary database tables. Make sure your MySQL server is running.

1. Run the following commands to perform database migrations: \
    `Create Initial Migration Folder:` 
    ```
    flask db init
    ```
    `Create Migration Script From Database Changes`
    ```
    flask db migrate
    ```
    `Apply Migration Script Created`
    ```
    flask db upgrade
    ```
    This will create the database tables based on the models defined in the application.

## Running the Server
1. Start the Flask server:
    ```
    flask run
    ```
    By default, the server will run at http://127.0.0.1:5000. You can access the API at this URL.


