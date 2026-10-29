import pika

url = "amqp://guest:guest@localhost"
param = pika.URLParameters(url)
cnn = pika.BlockingConnection(parameters=param)
ch = cnn.channel()
ch.queue_declare(queue='test')
print('Server is ready.')
count = 0
try:
    while True:
        input("Press ENTER to send a message...")
        count += 1
        ch.basic_publish('', 'test', f'Enviando msg {count}')
except KeyboardInterrupt:
    pass
ch.close()
