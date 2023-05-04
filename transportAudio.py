import os
from multiprocessing import Process
import time

def run(quic_path, remote_ip="127.0.0.1", remote_port="1114", local_port="1114"):
    def quic_server(path, port="1114"):
        os.chdir(path)
        print("quic_server is open!")
        os.system("./server 0.0.0.0 "+ port + " > /dev/null")

    def quic_client(path, ip="127.0.0.1", port="1114"):
        os.chdir(path)
        print("quic_client is open!")
        os.system("./client " + ip + " " + port + " > /dev/null")

    v_path = quic_path
    p_quic_server_v = Process(target=quic_server, args=(v_path, local_port,))
    p_quic_client_v = Process(target=quic_client, args=(v_path, remote_ip, remote_port,))



    p_quic_server_v.start()


    p_quic_client_v.start()

