import pika
import json
import os
import psycopg2

DATABASE_URL = os.getenv('DATABASE_URL')

def get_db_connection():
    conn = psycopg2.connect(DATABASE_URL, sslmode='require')
    return conn

def save_rate_to_db(rate_data):
    conn = get_db_connection()
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO exchange_rates (from_currency, to_currency, rate, timestamp)
        VALUES (%s, %s, %s, to_timestamp(%s))
    """, (
        rate_data['from_currency'],
        rate_data['to_currency'],
        rate_data['rate'],
        rate_data['timestamp']
    ))

    conn.commit()
    cursor.close()
    conn.close()

def callback(ch, method, properties, body):
    rate_data = json.loads(body)
    save_rate_to_db(rate_data)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_messages():
    rabbitmq_url = os.getenv('CLOUDAMQP_URL', 'amqp://localhost')
    params = pika.URLParameters(rabbitmq_url)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    channel.queue_declare(queue='exchange_rate_queue', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='exchange_rate_queue', on_message_callback=callback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    consume_messages()
