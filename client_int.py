"""Arquivo que implementa o cliente para o servidor de integração"""

from __future__ import print_function
from sys import stdin, stderr, argv

import grpc
import int_pb2
import int_pb2_grpc
import dir_pb2
import dir_pb2_grpc


def usage():
    print(f'Usage: {argv[0]} <address:port>', file=stderr)
    print(f'Example: {argv[0]} localhost:5555', file=stderr)
    exit(1)


def run():
    if len(argv) != 2:
        usage()

    args = argv[1].split(':')
    addr = args[0]
    port = int(args[1])

    # Abre canal de comunicação com o servidor e inicializa o stub.
    channel = grpc.insecure_channel(f'{addr}:{port}')
    stub = int_pb2_grpc.IntegrationStub(channel)

    # Lê todas as linhas na entrada padrão, até encontrar EOF.
    for line in stdin:
        # Remove espaços e quebras de linha do começo e final da string
        line = line.strip()

        # Transforma string de entrada em uma lista com os parâmetros passados,
        # assumindo que estão separados por vírgula.
        line = line.split(',')

        command = line[0]
        if command == 'C':
            key = int(line[1])

            response = stub.search(int_pb2.SearchRequest(key=key))
            if response.name == 'ND':
                # Chave não foi encontrada em nenhum servidor registrado no
                # servidor de integração.
                print(response.name)
            else:
                # Abre canal de comunicação com o servidor de diretórios, a
                # a partir do nome e do porto retornados pelo servidor de
                # integração.
                dir_channel = grpc.insecure_channel(f'{response.name}:{response.port}')
                dir_stub = dir_pb2_grpc.DirectoryStub(dir_channel)

                # Realiza a busca pela chave no diretório de integração.
                dir_response = dir_stub.search(dir_pb2.SearchRequest(key=key))

                # Fecha o canal após o procedimento de busca.
                dir_channel.close()

                print('{},{:7.4}'.format(dir_response.desc, dir_response.val))
        elif command == 'T':
            response = stub.finish(int_pb2.FinishRequest())
            print(response.num_keys)
        else:
            # Comando inválido é ignorado.
            continue

    # Ao final o cliente pode fechar o canal para o servidor.
    channel.close()


if __name__ == '__main__':
    run()
