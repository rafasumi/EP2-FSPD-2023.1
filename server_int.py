from threading import Event
from concurrent import futures
from sys import stderr, argv

import grpc
import int_pb2
import int_pb2_grpc


class Integration(int_pb2_grpc.IntegrationServicer):
    def __init__(self, finish_event):
        self.server_dict = {}
        self.finish_event = finish_event

    def register(self, request, context):
        try:
            for key in request.keys:
                self.server_dict[key] = {'name': request.name, 'port': request.port}

            return int_pb2.RegisterReply(ret_val=len(request.keys))
        except:
            return int_pb2.RegisterReply(ret_val=0)

    def search(self, request, context):
        name = 'ND'
        port = 0
        if request.key in self.server_dict:
            name = self.server_dict[request.key].get('name')
            port = self.server_dict[request.key].get('port')

        return int_pb2.SearchReply(name=name, port=port)

    def finish(self, request, context):
        self.finish_event.set()
        return int_pb2.FinishReply(num_keys=len(self.server_dict))


def usage():
    print(f'Usage: {argv[0]} <port>', file=stderr)
    print(f'Example: {argv[0]} 5555', file=stderr)
    exit(1)


def serve():
    if len(argv) < 2:
        usage()

    port = int(argv[1])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Usado para determinar quando o servidor deve parar de executar. Optei por
    # usar um Event ao invés de uma variável de condição, pois não há nenhuma
    # trava mutex associada.
    finish_event = Event()

    int_pb2_grpc.add_IntegrationServicer_to_server(Integration(finish_event), server)

    # O endereço 0.0.0.0 permite fazer o "bind" para todos os endereços
    # disponíveis na interface de rede.
    server.add_insecure_port(f'0.0.0.0:{port}')

    server.start()

    # Espera até que o evento "finish_event" seja ativado e encerra a execução
    # do servidor depois disso.
    finish_event.wait()
    server.stop(None)


if __name__ == '__main__':
    serve()
