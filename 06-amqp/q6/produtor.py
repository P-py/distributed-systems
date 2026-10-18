import argparse
import itertools
import random

from broker import connect

EXCHANGE = "Notifier"

BINDINGS = {
    "marketing": "notification.marketing.message",
    "support_new": "notification.support.new_member",
    "messages": "notification.*.message",
    "notifications": "notification.#",
}

ROUTING_KEYS = [
    "notification.marketing.action",
    "notification.marketing.query",
    "notification.marketing.message",
    "notification.support.new_ticket",
    "notification.support.new_member",
    "notification.support.message",
]


def setup(channel):
    channel.exchange_declare(EXCHANGE, "topic")
    for queue, binding_key in BINDINGS.items():
        channel.queue_declare(queue=queue)
        channel.queue_bind(queue, EXCHANGE, binding_key)


def main():
    parser = argparse.ArgumentParser()
    parser.add_argument("-r", "--rounds", type=int, default=1)
    args = parser.parse_args()

    connection, channel = connect()
    setup(channel)
    counter = itertools.count(1)
    for _ in range(args.rounds):
        for key in random.sample(ROUTING_KEYS, len(ROUTING_KEYS)):
            body = f"mensagem {next(counter)}"
            channel.basic_publish(exchange=EXCHANGE, routing_key=key, body=body)
            print(f"Enviada [{key}] {body}")
    connection.close()


if __name__ == "__main__":
    main()
