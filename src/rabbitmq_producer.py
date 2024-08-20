import pika
import json
import os
import requests
from datetime import datetime

# Define the list of currencies
CURRENCIES = ['USD', 'JPY', 'EUR', 'GBP', 'AUD', 'CAD']

RABBITMQ_URL = os.getenv('CLOUDAMQP_URL')
API_KEY = os.getenv('CURRENCY_API_KEY')
BASE_URL = 'https://api.currencybeacon.com/v1/convert'

def fetch_rate(from_currency, to_currency):
    params = {
        'from': from_currency,
        'to': to_currency,
        'amount': 1,
        'api_key': API_KEY
    }
    try:
        response = requests.get(BASE_URL, params=params)
        response.raise_for_status()
        data = response.json()
        return {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': data['response']['value'],
            'timestamp': datetime.now().timestamp()
        }
    except requests.exceptions.RequestException as e:
        print(f"Request error: {e}")
        return None

def publish_message(channel, message):
    channel.basic_publish(
        exchange='',
        routing_key='exchange_rate_queue',
        body=json.dumps(message),
        properties=pika.BasicProperties(
            delivery_mode=2,  # make message persistent
        ))

def main():
    params = pika.URLParameters(RABBITMQ_URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='exchange_rate_queue', durable=True)

    for from_currency in CURRENCIES:
        for to_currency in CURRENCIES:
            if from_currency != to_currency:
                rate_data = fetch_rate(from_currency, to_currency)
                if rate_data:
                    publish_message(channel, rate_data)
                    print(f"Published message: {rate_data}")

    connection.close()

if __name__ == "__main__":
    main()
