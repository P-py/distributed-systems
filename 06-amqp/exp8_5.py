import argparse
import os
import sys

import pika

URL = "amqp://guest:guest@localhost:5672/"


def connect():
    params = pika.URLParameters(URL)
    connection = pika.BlockingConnection(params)
    channel = connection.channel()
    print("Channel over a connection created")
    channel.queue_declare(queue='Fila1')
    channel.queue_declare(queue='Fila2')
    return connection, channel


def send_to_exchange(exchange, routing_key, body):
    channel.basic_publish(
        exchange=exchange,
        routing_key=routing_key,
        body=body
    )
    print(f"Message sent to exchange{exchange}#{body}")


def producer():
    channel.exchange_declare("Greetings", "direct")
    channel.queue_bind("Fila1", "Greetings", "greeting")
    channel.exchange_declare("ToAll", "fanout")
    channel.queue_bind("Fila1", "ToAll")
    channel.queue_bind("Fila2", "ToAll")
    send_to_exchange("Greetings", "greeting", "Hello My Friend!")
    send_to_exchange("Greetings", "helo", "Hello Friendo")
    send_to_exchange("ToAll", "", "Hello Everyone!")
    try:
        connection.close()
        print("Connection closed")
    except Exception as e:
        print(f"Error: #{e}")


def callback1(ch, method, properties, body):
    print(f"Received on Fila1#{ body }")


def callback2(ch, method, properties, body):
    print(f"Received on Fila2#{ body }")


def consumer():
    channel.basic_consume("Fila1", callback1, auto_ack=True)
    channel.basic_consume("Fila2", callback2, auto_ack=True)
    try:
        print("\nWaiting for messages. To exit press CTRL+C \n")
        channel.start_consuming()
    except Exception as e:
        print(f"Error: #{e}")
        try:
            sys.exit(0)
        except SystemExit:
            os._exit(0)


if __name__ == '__main__':
    parser = argparse.ArgumentParser()
    parser.add_argument('--prod', action='store_true')
    args = parser.parse_args()
    connection, channel = connect()
    if args.prod:
        producer()
    else:
        consumer()
