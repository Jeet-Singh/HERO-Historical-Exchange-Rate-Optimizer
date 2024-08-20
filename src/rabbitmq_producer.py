import pika
import requests
import json
import time
import os

API_KEY = 'rHA3DChPyh4W1Xj2D905oTs192RRG8rC'
BASE_URL = 'https://api.currencybeacon.com/v1/convert'
CURRENCIES = ['USD', 'JPY']

def fetch_hourly_rate(from_currency, to_currency):
    params = {
        'from': from_currency,
        'to': to_currency,
        'amount': 1,
        'api_key': API_KEY
    }
    response = requests.get(BASE_URL, params=params)
    data = response.json()

    if response.status_code == 200 and data.get('success'):
        return {
            'from_currency': from_currency,
            'to_currency': to_currency,
            'rate': data['result']['amount'],
            'timestamp': time.time()
        }
    else:
        return None

def send_message(rate_data):
    rabbitmq_url = os.getenv('CLOUDAMQP_URL', 'amqp://localhost')
    params = pika.URLParameters(rabbitmq_url)
    rabbitmq_connection = pika.BlockingConnection(params)
    channel = rabbitmq_connection.channel()
    channel.queue_declare(queue='exchange_rate_queue', durable=True)

    message = json.dumps(rate_data)
    channel.basic_publish(
        exchange='',
        routing_key='exchange_rate_queue',
        body=message,
        properties=pika.BasicProperties(
            delivery_mode=2,  # Make the message persistent
        ))
    rabbitmq_connection.close()

if __name__ == "__main__": 
    while True:
        for from_currency in CURRENCIES:
            for to_currency in CURRENCIES:
                if from_currency != to_currency:
                    rate_data = fetch_hourly_rate(from_currency, to_currency)
                    if rate_data:
                        send_message(rate_data)
        time.sleep(3600)  # Wait for an hour before sending the next batch
