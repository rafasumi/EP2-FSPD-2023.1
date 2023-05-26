DIR = dir.proto
INT = int.proto
DIR_STUBS = dir_pb2_grpc.py dir_pb2.py
INT_STUBS = int_pb2_grpc.py int_pb2.py

stubs: $(DIR_STUBS) $(INT_STUBS)

$(DIR_STUBS): $(DIR)
	@python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. $(DIR)

$(INT_STUBS): $(INT)
	@python3 -m grpc_tools.protoc -I. --python_out=. --grpc_python_out=. $(INT)

run_cli_dir: stubs
	@python3 client_dir.py $(arg)

run_serv_dir: stubs
	@python3 server_dir.py $(arg)

run_cli_int: stubs
	@python3 client_int.py $(arg)

run_serv_int: stubs
	@python3 server_int.py $(arg)

clean:
	@rm -f $(DIR_STUBS) $(INT_STUBS)