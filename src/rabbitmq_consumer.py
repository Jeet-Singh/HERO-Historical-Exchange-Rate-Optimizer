import pika
import sqlite3
import json

DB_PATH = 'exchange_rates.db'

def save_rate_to_db(rate_data):
    conn = sqlite3.connect(DB_PATH)
    cursor = conn.cursor()

    cursor.execute("""
        INSERT INTO exchange_rates (from_currency, to_currency, rate, timestamp)
        VALUES (?, ?, ?, datetime('now', 'unixepoch'))
    """, (
        rate_data['from_currency'],
        rate_data['to_currency'],
        rate_data['rate']
    ))

    conn.commit()
    cursor.close()
    conn.close()

def callback(ch, method, properties, body):
    rate_data = json.loads(body)
    save_rate_to_db(rate_data)
    ch.basic_ack(delivery_tag=method.delivery_tag)

def consume_messages():
    connection = pika.BlockingConnection(pika.ConnectionParameters('localhost'))
    channel = connection.channel()
    channel.queue_declare(queue='exchange_rate_queue', durable=True)

    channel.basic_qos(prefetch_count=1)
    channel.basic_consume(queue='exchange_rate_queue', on_message_callback=callback)

    print(" [*] Waiting for messages. To exit press CTRL+C")
    channel.start_consuming()

if __name__ == "__main__":
    consume_messages()