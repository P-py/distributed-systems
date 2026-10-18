import pika

URL = "amqp://guest:guest@localhost:5672/"


def connect():
    connection = pika.BlockingConnection(pika.URLParameters(URL))
    return connection, connection.channel()


def consume(queue):
    connection, channel = connect()
    channel.queue_declare(queue=queue)

    def callback(ch, method, properties, body):
        print(f"[{queue}] {method.routing_key}: {body.decode()}")

    channel.basic_consume(queue, callback, auto_ack=True)
    print(f"Aguardando mensagens em '{queue}'. Para sair, pressione CTRL+C")
    try:
        channel.start_consuming()
    except KeyboardInterrupt:
        print("\nEncerrando")
    connection.close()
