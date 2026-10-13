import random
import time
import zmq

context = zmq.Context()

sender = context.socket(zmq.PUSH)
sender.bind("tcp://localhost:5557")

sink = context.socket(zmq.PUSH)
sink.connect("tcp://localhost:5558")

print("Pressione Enter quando os workers estiverem prontos: ")
_ = input()
print("Enviando as tarefas aos workers...")

sink.send(b'0')

random.seed()

total_msec = 0
for task_nbr in range(100):
    workload = random.randint(1, 100)
    total_msec += workload
    sender.send_string(f"{workload}")

print(f"Custo total esperado: {total_msec} ms")

time.sleep(1)
