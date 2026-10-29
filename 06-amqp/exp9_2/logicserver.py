import json
import pika

functions = {
    'add':lambda a,b: a+b,
    'sub':lambda a,b: a-b,
    'mul':lambda a,b: a*b,
    'div':lambda a,b: a/b
    }

def ProcessRpcRequest(ch, method, properties, body):
    req = json.loads(body)
    m = req['method']

    a1 = req['arg1']
    a2 = req['arg2']

    if m in functions:
        try:
            r = functions[m](a1, a2)
        except Exception as e:
            r = str(e)
    else:
        r = "invalid"

    res = json.dumps(dict(result=r))

    ch.basic_publish(exchange='',
                     routing_key=properties.reply_to,
                     properties=pika.BasicProperties(correlation_id=properties.correlation_id),
                     body=res)
    ch.basic_ack(delivery_tag=method.delivery_tag)

param = pika.URLParameters("amqp://guest:guest@localhost")
cnn = pika.BlockingConnection(parameters=param)

ch = cnn.channel()
ch.basic_qos(prefetch_count=1)
ch.queue_declare(queue='rpc_queue')
ch.basic_consume(queue='rpc_queue', on_message_callback=ProcessRpcRequest)

print('Server is ready.')

try:
    ch.start_consuming()
except KeyboardInterrupt:
    pass

ch.close()
