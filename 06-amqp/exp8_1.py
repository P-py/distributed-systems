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
    channel.queue_declare(queue='greetings')
    channel.queue_declare(queue='greeter')
    return connection, channel


def send_to_queue(channel, routing_key, body):
    channel.basic_publish(
        exchange='',
        routing_key=routing_key,
        body=body
    )
    print(f"Message sent to {routing_key}#{body}")


def producer():
    connection, channel = connect()
    send_to_queue(channel, 'greetings', 'Hello!')
    send_to_queue(channel, 'greetings', 'Good morning!')
    send_to_queue(channel, 'greeter', 'Greetings!')
    try:
        connection.close()
        print("Connection closed")
    except Exception as e:
        print(f"Error: #{e}")


def callback(ch, method, properties, body):
    print(f"Received #{ body }")


def consumer():
    connection, channel = connect()
    channel.basic_consume("greetings", callback, auto_ack=True)
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
    if args.prod:
        producer()
    else:
        consumer()
