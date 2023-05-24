from threading import Event
from concurrent import futures
from sys import stderr, argv

import grpc
import dir_pb2
import dir_pb2_grpc


class Directory(dir_pb2_grpc.DirectoryServicer):
    def __init__(self, finish_event):
        self.server_dict = {}
        self.finish_event = finish_event

    def insert(self, request, context):
        ret_val = 0
        if request.key in self.server_dict:
            ret_val = 1

        self.server_dict[request.key] = {
            'desc': request.desc, 'val': request.val}

        return dir_pb2.InsertReply(ret_val=ret_val)

    def search(self, request, context):
        desc = ''
        val = 0.0
        if request.key in self.server_dict:
            desc = self.server_dict[request.key].get('desc')
            val = self.server_dict[request.key].get('val')

        return dir_pb2.SearchReply(desc=desc, val=val)
    
    def register(self, request, context):
        pass

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

    finish_event = Event()
    dir_pb2_grpc.add_DirectoryServicer_to_server(Directory(finish_event), server)

    server.add_insecure_port(f'localhost:{port}')

    server.start()
    finish_event.wait()
    server.stop(1)


if __name__ == '__main__':
    serve()
