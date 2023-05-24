from __future__ import print_function
from sys import stdin, stderr, argv

import grpc
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
    stub = dir_pb2_grpc.DirectoryStub(channel)

    for line in stdin:
        line = line.split(',')
        command = line[0]
        if command == 'I':
            key = int(line[1])
            desc = line[2]
            val = float(line[3])

            response = stub.insert(
                dir_pb2.InsertRequest(key=key, desc=desc, val=val))
            print(response.ret_val)
        elif command == 'C':
            key = int(line[1])

            response = stub.search(dir_pb2.SearchRequest(key=key))
            if response.desc == '' and response.val == 0:
                print(-1)
            else:
                print(f'{response.desc},{response.val}')
        elif command == 'R':
            pass
        elif command == 'T':
            response = stub.finish(dir_pb2.FinishRequest())
            print(response.num_keys)
        else:
            continue

    # Ao final o cliente pode fechar o canal para o servidor.
    channel.close()


if __name__ == '__main__':
    run()
