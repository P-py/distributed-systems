import pika

url = "amqp://guest:guest@localhost"
param = pika.URLParameters(url)
cnn = pika.BlockingConnection(parameters=param)
ch = cnn.channel()

def OnMessage(ch, method, properties, body):
    print(f"Received: {str(body)}.")
    input("Press ENTER to acknoledge the message.")
    ch.basic_ack(delivery_tag=method.delivery_tag)

ch.basic_consume(queue='test', on_message_callback=OnMessage) # auto_ack=False
ch.queue_declare(queue='test')
print('Consumer ready, waiting for messages...')
try:
    ch.start_consuming()
except KeyboardInterrupt:
    pass
ch.close()
