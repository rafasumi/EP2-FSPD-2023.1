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
    if len(argv) < 2:
        usage()

    args = argv[1].split(':')
    addr = args[0]
    port = int(args[1])

    channel = grpc.insecure_channel(f'{addr}:{port}')
    stub = int_pb2_grpc.IntegrationStub(channel)

    for line in stdin:
        # Remove espaços e quebras de linha do começo e final da string
        line = line.strip()

        line = line.split(',')
        command = line[0]
        if command == 'C':
            key = int(line[1])

            response = stub.search(int_pb2.SearchRequest(key=key))
            if response.name == 'ND':
                print(response.name)
            else:
                dir_channel = grpc.insecure_channel(f'{response.name}:{response.port}')
                dir_stub = dir_pb2_grpc.DirectoryStub(dir_channel)

                dir_response = dir_stub.search(dir_pb2.SearchRequest(key=key))

                dir_channel.close()
                
                print('{},{:7.4}'.format(dir_response.desc, dir_response.val))
        elif command == 'T':
            response = stub.finish(int_pb2.FinishRequest())
            print(response.num_keys)
        else:
            continue

    # Ao final o cliente pode fechar o canal para o servidor.
    channel.close()


if __name__ == '__main__':
    run()
