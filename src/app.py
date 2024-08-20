import os
import psycopg2
import requests
import json
from flask import Flask, render_template, jsonify, request
from datetime import datetime, timedelta

app = Flask(__name__)

# Database URL from Heroku environment variable
DATABASE_URL = os.getenv('DATABASE_URL')
API_KEY = 'rHA3DChPyh4W1Xj2D905oTs192RRG8rC'
BASE_URL = 'https://api.currencybeacon.com/v1/convert'
currencies = ['USD', 'JPY', 'INR', 'AUD', 'GBP', 'HKD']

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def create_database():
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        CREATE TABLE IF NOT EXISTS exchange_rates (
            id SERIAL PRIMARY KEY,
            from_currency TEXT,
            to_currency TEXT,
            rate REAL,
            timestamp TIMESTAMPTZ
        );
    """)
    conn.commit()
    cursor.close()
    conn.close()
    print("Database and table ensured to exist.")

def get_latest_rate(from_currency, to_currency):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        SELECT rate FROM exchange_rates
        WHERE from_currency = %s AND to_currency = %s
        ORDER BY timestamp DESC LIMIT 1
    """, (from_currency, to_currency))

    rate = cursor.fetchone()
    cursor.close()
    conn.close()

    return rate[0] if rate else None

def fetch_and_store_historical_data():
    conn = get_db_connection()
    cursor = conn.cursor()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    for from_currency in currencies:
        for to_currency in currencies:
            if from_currency != to_currency:
                date = start_date
                while date <= end_date:
                    rate_data = fetch_rate(from_currency, to_currency, date)
                    if rate_data:
                        cursor.execute("""
                            INSERT INTO exchange_rates (from_currency, to_currency, rate, timestamp)
                            VALUES (%s, %s, %s, %s)
                        """, (
                            from_currency,
                            to_currency,
                            rate_data['rate'],
                            rate_data['timestamp']
                        ))
                    date += timedelta(days=1)
    
    conn.commit()
    cursor.close()
    conn.close()
    print("Historical data fetched and stored.")

def fetch_rate(from_currency, to_currency, date):
    params = {
        'from': from_currency,
        'to': to_currency,
        'amount': 1,
        'api_key': API_KEY,
        'date': date.strftime('%Y-%m-%d')
    }
    try:
        response = requests.get(BASE_URL, params=params)
        data = response.json()
        response = requests.get(url, headers=headers)
        response.raise_for_status()  # Raises HTTPError for bad responses
        # Print response text for debugging
        print(response.text)
        data = response.json()
        return {
                'rate': data['result']['amount'],
                'timestamp': date.strftime('%Y-%m-%d %H:%M:%S')}
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
    except requests.exceptions.JSONDecodeError as e:
        print(f"JSON decode error: {e}")
       
      

@app.route('/')
def index():
    return render_template('index.html', currencies=currencies)

@app.route('/convert', methods=['POST'])
def convert():
    from_currency = request.form.get('from_currency')
    to_currency = request.form.get('to_currency')

    rate = get_latest_rate(from_currency, to_currency)

    if rate:
        return jsonify({
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': rate,
            'success': True
        })
    else:
        return jsonify({
            'success': False,
            'error': 'Rate not available. Please try again later.'
        })

@app.route('/chart')
def chart():
    from_currency = request.args.get('from_currency')
    to_currency = request.args.get('to_currency')

    conn = get_db_connection()
    cursor = conn.cursor()

    end_date = datetime.now()
    start_date = end_date - timedelta(days=90)

    cursor.execute("""
        SELECT rate, timestamp FROM exchange_rates
        WHERE from_currency = %s AND to_currency = %s
        AND timestamp BETWEEN %s AND %s
        ORDER BY timestamp
    """, (from_currency, to_currency, start_date, end_date))

    data = cursor.fetchall()
    cursor.close()
    conn.close()

    if not data:
        return jsonify({'success': False, 'error': 'No historical data found.'})

    dates, rates = zip(*data)
    moving_avg = calculate_moving_average(rates)

    return jsonify({
        'success': True,
        'dates': [d[0] for d in data],  # Convert datetime to string
        'rates': rates,
        'moving_avg': moving_avg
    })

def calculate_moving_average(rates, window_size=7):
    if len(rates) < window_size:
        return [None] * len(rates)
    
    moving_avg = []
    for i in range(len(rates)):
        if i < window_size - 1:
            moving_avg.append(None)
        else:
            avg = sum(rates[i-window_size+1:i+1]) / window_size
            moving_avg.append(avg)
    return moving_avg

if __name__ == '__main__':
    create_database()  # Ensure the PostgreSQL database and table exist
    
    # Check if the database is empty and populate with historical data if needed
    conn = get_db_connection()
    cursor = conn.cursor()
    cursor.execute("SELECT COUNT(*) FROM exchange_rates")
    count = cursor.fetchone()[0]
    conn.close()

    if count == 0:
        fetch_and_store_historical_data()
    
    app.run(debug=True)
