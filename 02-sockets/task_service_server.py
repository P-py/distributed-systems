from datetime import datetime
from itertools import count
from xmlrpc.client import Fault
from xmlrpc.server import SimpleXMLRPCServer

HOST = 'localhost'
PORT = 50007
DESCRIPTION_LIMIT = 500

INVALID_TITLE = 100
INVALID_DESCRIPTION = 101
DESCRIPTION_TOO_LONG = 102
TASK_NOT_FOUND = 404
TASK_ALREADY_DONE = 409

tasks = {}
ids = count(1)

def create_task(title, description=''):
    """Cria uma tarefa aberta e devolve o registro criado."""
    if not isinstance(title, str) or not title.strip():
        raise Fault(INVALID_TITLE, 'o título é obrigatório')
    if not isinstance(description, str):
        raise Fault(INVALID_DESCRIPTION, 'a descrição deve ser uma string')
    if len(description) > DESCRIPTION_LIMIT:
        raise Fault(DESCRIPTION_TOO_LONG,
                    f'a descrição excede {DESCRIPTION_LIMIT} caracteres '
                    f'(recebidos: {len(description)})')

    task_id = next(ids)
    tasks[task_id] = {
        'id': task_id,
        'title': title.strip(),
        'created_at': datetime.now(),
        'finished_at': None,
        'description': description,
    }
    print(f'[create] #{task_id} {title!r}')
    return tasks[task_id]

def finish_task(task_id):
    """Finaliza a tarefa do id informado e devolve o registro atualizado."""
    task = tasks.get(task_id)
    if task is None:
        raise Fault(TASK_NOT_FOUND, f'tarefa #{task_id} não encontrada')
    if task['finished_at'] is not None:
        raise Fault(TASK_ALREADY_DONE, f'tarefa #{task_id} já foi finalizada')

    task['finished_at'] = datetime.now()
    print(f'[finish] #{task_id}')
    return task

def list_all():
    """Lista todas as tarefas."""
    return list(tasks.values())

def list_open():
    """Lista apenas as tarefas em aberto."""
    return [task for task in tasks.values() if task['finished_at'] is None]

def list_done():
    """Lista apenas as tarefas finalizadas."""
    return [task for task in tasks.values() if task['finished_at'] is not None]

if __name__ == '__main__':
    with SimpleXMLRPCServer((HOST, PORT), allow_none=True) as server:
        server.register_introspection_functions()
        for function in (create_task, finish_task, list_all, list_open, list_done):
            server.register_function(function)

        print(f'Lista de tarefas em http://{HOST}:{PORT}/ (Ctrl-C para encerrar)')
        try:
            server.serve_forever()
        except KeyboardInterrupt:
            print('Exiting')
