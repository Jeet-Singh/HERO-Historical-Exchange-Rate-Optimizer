import requests
import json
import sqlite3

API_KEY = 'rHA3DChPyh4W1Xj2D905oTs192RRG8rC'
BASE_URL = 'https://api.currencybeacon.com/v1'  


#create initial data tables if they do not exist yet.  TO-DO: Create proper primary key 
def create_table():
    try:
        conn = sqlite3.connect('currency_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            CREATE TABLE IF NOT EXISTS historical_data (
                date TEXT PRIMARY KEY,
                base_currency TEXT,
                target_currency TEXT,
                rate REAL
            )
        ''')
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"An error occurred while creating the table: {e}")


def insert_data(date, base_currency, target_currency, rate):
    try:
        conn = sqlite3.connect('currency_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            INSERT OR REPLACE INTO historical_data (date, base_currency, target_currency, rate)
            VALUES (?, ?, ?, ?)
        ''', (date, base_currency, target_currency, rate))
        
        conn.commit()
        conn.close()
    except Exception as e:
        print(f"An error occurred while inserting data: {e}")

def get_historical_data(base_currency, target_currency, start_date, end_date):
    try:
        url = f"{BASE_URL}/timeseries"
        params = {
            'api_key': API_KEY,
            'base': base_currency,
            'symbols': target_currency,
            'start_date': start_date,
            'end_date': end_date
        }

        response = requests.get(url, params=params)
        response.raise_for_status()
        return response.json()
    except Exception as e:
        print(f"An error occurred while fetching data: {e}")
        return None

def store_data(data, base_currency, target_currency):
    try:
        if data and 'response' in data:
            for date, rates in data['response'].items():
                rate = rates.get(target_currency)
                if rate is not None:
                    insert_data(date, base_currency, target_currency, rate)
            print("Data successfully inserted into the database.")
        else:
            print("No data to store.")
    except Exception as e:
        print(f"An error occurred while storing data: {e}")

def print_data():
    try:
        conn = sqlite3.connect('currency_data.db')
        cursor = conn.cursor()
        
        cursor.execute('''
            SELECT date, base_currency, target_currency, rate
            FROM historical_data
        ''')
        
        rows = cursor.fetchall()
        conn.close()
        
        if rows:
            print(f"{'Date':<12} {'Base Currency':<15} {'Target Currency':<15} {'Rate':<10}")
            print("-" * 52)
            for row in rows:
                print(f"{row[0]:<12} {row[1]:<15} {row[2]:<15} {row[3]:<10.4f}")
        else:
            print("No data available in the database.")
    except Exception as e:
        print(f"An error occurred while printing data: {e}")

def main():
    create_table()
    
    base_currency = 'USD'
    target_currency = 'AUD'
    start_date = '2023-08-08'
    end_date = '2023-10-08'
    
    try:
        data = get_historical_data(base_currency, target_currency, start_date, end_date)
        store_data(data, base_currency, target_currency)
        print_data()
    except Exception as e:
        print(f"An error occurred in the main function: {e}")

if __name__ == "__main__":
    main()