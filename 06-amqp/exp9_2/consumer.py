import json
import pika
import uuid

class BasicMathRpcClient:
    def __init__(self):
        url_param = pika.URLParameters("amqp://guest:guest@localhost")
        self.connection = pika.BlockingConnection(parameters=url_param)
        self.channel = self.connection.channel()

        result = self.channel.queue_declare(queue='', exclusive=True)
        
        self.callback_queue = result.method.queue
        self.channel.basic_consume(
            queue=self.callback_queue,
            on_message_callback=self.on_response,
            auto_ack=True)
        self.response = None
        self.corr_id = None

    def on_response(self, ch, method, props, body):
        if self.corr_id == props.correlation_id:
            r = json.loads(body)['result']
            self.response = r

    def add(self, a, b):
        req = json.dumps(dict(method='add', arg1=a, arg2=b))
        self.__call(req)
        return self.response

    def sub(self, a, b):
        req = json.dumps(dict(method='sub', arg1=a, arg2=b))
        self.__call(req)
        return self.response

    def mul(self, a, b):
        req = json.dumps(dict(method='mul', arg1=a, arg2=b))
        self.__call(req)
        return self.response

    def div(self, a, b):
        req = json.dumps(dict(method='div', arg1=a, arg2=b))
        self.__call(req)
        return self.response

    def __call(self, req):
        self.response = None
        self.corr_id = str(uuid.uuid4())
        self.channel.basic_publish(
            exchange='',
            routing_key='rpc_queue',
            properties=pika.BasicProperties(
                reply_to=self.callback_queue,
                correlation_id=self.corr_id),
            body=req)
        while self.response is None:
            self.connection.process_data_events(time_limit=None)


if __name__ == '__main__':
    rpc = BasicMathRpcClient()

    print(f"add(6, 3) = {rpc.add(6, 3)}")
    print(f"sub(6, 3) = {rpc.sub(6, 3)}")
    print(f"mul(6, 3) = {rpc.mul(6, 3)}")
    print(f"div(6, 3) = {rpc.div(6, 3)}")
    print(f"div(1, 0) = {rpc.div(1, 0)}")
    
    rpc.connection.close()
