"""Arquivo que implementa o servidor de diretórios"""

from threading import Event
from concurrent import futures
from sys import stderr, argv
from socket import getfqdn

import grpc
import dir_pb2
import dir_pb2_grpc
import int_pb2
import int_pb2_grpc


class Directory(dir_pb2_grpc.DirectoryServicer):
    def __init__(self, port, finish_event):
        self.server_dict = {}  # Dicionário que armazena as chaves e valores.
        self.name = getfqdn()  # Nome "completo" do servidor.
        self.port = port  # Porto onde está executando o servidor.
        self.finish_event = finish_event  # Evento que controla o fim da execução do servidor.

    # Implementação do procedimento de inserção
    def insert(self, request, context):
        ret_val = 0
        if request.key in self.server_dict:
            # Caso em que a chave já existia no dicionário
            ret_val = 1

        # Armazena os valores no dicionário em outro dicionário, que tem as chaves
        # 'desc' e 'val'.
        self.server_dict[request.key] = {'desc': request.desc, 'val': request.val}

        return dir_pb2.InsertReply(ret_val=ret_val)

    # Implementação do procedimento de consulta
    def search(self, request, context):
        desc = ''
        val = 0.0
        if request.key in self.server_dict:
            # Se a chave está no dicionário, busca os valores de 'desc' e 'val'
            # associados a ela.
            desc = self.server_dict[request.key].get('desc')
            val = self.server_dict[request.key].get('val')

        return dir_pb2.SearchReply(desc=desc, val=val)

    # Implementação do procedimento de registro
    def register(self, request, context):
        # Abre um canal de comunicação com o servidor de integração, considerando
        # o nome e o porto passados como parâmetros.
        channel = grpc.insecure_channel(f'{request.name}:{request.port}')
        stub = int_pb2_grpc.IntegrationStub(channel)

        keys = list(self.server_dict.keys())
        response = stub.register(int_pb2.RegisterRequest(name=self.name, port=self.port, keys=keys))

        # Fecha o canal com o servidor de integração após chamar o procedimento de
        # registro.
        channel.close()

        return dir_pb2.RegisterReply(ret_val=response.ret_val)

    # Implementação do procedimento de término
    def finish(self, request, context):
        self.finish_event.set()
        return dir_pb2.FinishReply(num_keys=len(self.server_dict))


def usage():
    print(f'Usage: {argv[0]} <port>', file=stderr)
    print(f'Example: {argv[0]} 5555', file=stderr)
    exit(1)


def serve():
    if len(argv) != 2:
        usage()

    port = int(argv[1])

    server = grpc.server(futures.ThreadPoolExecutor(max_workers=10))

    # Evento usado para determinar quando o servidor deve parar de executar.
    # Optei por usar um Event ao invés de uma variável de condição, pois não há
    # nenhuma trava mutex associada a essa condição.
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
