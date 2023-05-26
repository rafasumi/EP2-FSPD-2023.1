from threading import Event
from concurrent import futures
from sys import stderr, argv
from socket import gethostname

import grpc
import dir_pb2
import dir_pb2_grpc
import int_pb2
import int_pb2_grpc


class Directory(dir_pb2_grpc.DirectoryServicer):
    def __init__(self, port, finish_event):
        self.server_dict = {}
        self.name = gethostname()
        self.port = port
        self.finish_event = finish_event

    def insert(self, request, context):
        ret_val = 0
        if request.key in self.server_dict:
            ret_val = 1

        self.server_dict[request.key] = {'desc': request.desc, 'val': request.val}

        return dir_pb2.InsertReply(ret_val=ret_val)

    def search(self, request, context):
        desc = ''
        val = 0.0
        if request.key in self.server_dict:
            desc = self.server_dict[request.key].get('desc')
            val = self.server_dict[request.key].get('val')

        return dir_pb2.SearchReply(desc=desc, val=val)

    def register(self, request, context):
        channel = grpc.insecure_channel(f'{request.name}:{request.port}')
        stub = int_pb2_grpc.IntegrationStub(channel)

        keys = list(self.server_dict.keys())
        response = stub.register(int_pb2.RegisterRequest(name=self.name, port=self.port, keys=keys))

        channel.close()

        return dir_pb2.RegisterReply(ret_val=response.ret_val)

    def finish(self, request, context):
        self.finish_event.set()
        return dir_pb2.FinishReply(num_keys=len(self.server_dict))


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

    dir_pb2_grpc.add_DirectoryServicer_to_server(Directory(port, finish_event), server)

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
