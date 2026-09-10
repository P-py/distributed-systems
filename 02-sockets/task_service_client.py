import xmlrpc.client

HOST = 'localhost'
PORT = 50007

def fmt(moment):
    return moment.strftime('%d/%m/%Y %H:%M:%S') if moment else '-'

def show(label, tasks):
    print(f'\n{label} ({len(tasks)} tarefa(s))')
    for task in tasks:
        status = 'finalizada' if task['finished_at'] else 'aberta'
        print(f"  #{task['id']:<3} {task['title']:<24} {status:<11}"
              f" criada: {fmt(task['created_at'])}"
              f" | fim: {fmt(task['finished_at'])}")
        if task['description']:
            print(f"      {task['description']}")

def check(label, condition):
    print(f'  [{"OK" if condition else "FALHOU"}] {label}')
    return condition

with xmlrpc.client.ServerProxy(f'http://{HOST}:{PORT}/',
                               allow_none=True, use_datetime=True) as proxy:
    print('métodos expostos:', proxy.system.listMethods())

    created = [
        proxy.create_task('Estudar sockets', 'Rever o backlog do listen() e o accept()'),
        proxy.create_task('Escrever o relatório', 'Documentar os módulos do 02-sockets'),
        proxy.create_task('Revisar o XML-RPC'),
    ]
    created_ids = [task['id'] for task in created]
    print(f'\ncriadas as tarefas {created_ids}')

    every = proxy.list_all()
    show('TODAS', every)

    target = created_ids[1]
    finished = proxy.finish_task(target)
    print(f"\nfinalizada a tarefa #{finished['id']} em {fmt(finished['finished_at'])}")

    done = proxy.list_done()
    show('FINALIZADAS', done)

    opened = proxy.list_open()
    show('ABERTAS', opened)

    print('\nvalidação:')
    ok = True
    ok &= check('as 3 tarefas criadas aparecem em list_all',
                set(created_ids) <= {task['id'] for task in every})
    ok &= check('a tarefa finalizada aparece em list_done',
                target in {task['id'] for task in done})
    ok &= check('a tarefa finalizada sumiu de list_open',
                target not in {task['id'] for task in opened})
    ok &= check('as outras 2 continuam abertas',
                {created_ids[0], created_ids[2]} <= {task['id'] for task in opened})
    ok &= check('list_all == list_open + list_done',
                len(every) == len(opened) + len(done))
    ok &= check('toda tarefa tem id, título, criação, término e descrição',
                all(set(task) == {'id', 'title', 'created_at', 'finished_at',
                                  'description'} for task in every))

    for label, call, args in (
        ('descrição acima de 500 caracteres', proxy.create_task, ('Excede', 'x' * 501)),
        ('finalizar tarefa inexistente', proxy.finish_task, (999999,)),
        ('finalizar tarefa já finalizada', proxy.finish_task, (target,)),
    ):
        try:
            call(*args)
            ok &= check(f'{label} é recusada', False)
        except xmlrpc.client.Fault as fault:
            ok &= check(f'{label} -> Fault {fault.faultCode}: {fault.faultString}', True)

    print('\nresultado:', 'interface validada' if ok else 'há falhas na interface')
