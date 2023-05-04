import sys, getopt
from multiprocessing import Queue, Process
import time
import os
import sounddevice as sd
import numpy as np
import pyaudio
# lib
import ingestAudio
import encodingAudio
import pipeIOAudio
import transportAudio
import renderAudio
os.environ['SDL_AUDIODRIVER'] = 'pulseaudio'



def run_audio_system(mode="run", remote_ip="127.0.0.1", remote_port="1114", local_port="1114"):
    print("run_audio_system is open!")
    # data
    q_send_ingest_encoding = Queue()
    q_send_encoding_pipe = Queue()
    q_receive_pipe_decoding = Queue()
    q_receive_decoding_render = Queue()

    test=Queue()

    pipe_path = "quic_0421/build"
    svideopipe_path = "quic_0421/build/svideopipe"
    cvideopipe_path = "quic_0421/build/cvideopipe"
    # 创建管道
    if not os.path.exists(svideopipe_path):
        os.mkfifo(svideopipe_path)
    
    if not os.path.exists(cvideopipe_path):
        os.mkfifo(cvideopipe_path)

    # process
    processes = []

   
    p_ingest = Process(target=ingestAudio.from_audio_stream, args=(q_send_ingest_encoding, ingestAudio.sample_rate,1))
    processes.append(p_ingest)
    p_encoding = Process(target=encodingAudio.encodeAudio, args=(q_send_ingest_encoding, q_send_encoding_pipe,test))
    processes.append(p_encoding)
    if mode == "noFIFO":
        print("noFIFO is open!")
        p_pipe = Process(target=pipeIOAudio.test_noFIFO_audio, args=(q_send_encoding_pipe, q_receive_pipe_decoding,))
        processes.append(p_pipe)
    else:
        p_asend_pipe = Process(target=pipeIOAudio.write_audio, args=(q_send_encoding_pipe, svideopipe_path,))
        p_transport = Process(target=transportAudio.run, args=(pipe_path, remote_ip, remote_port, local_port,))
        p_areceive_pipe = Process(target=pipeIOAudio.read_audio, args=(q_receive_pipe_decoding, cvideopipe_path,))

        
        processes.append(p_asend_pipe)
        processes.append(p_transport)
        processes.append(p_areceive_pipe)
        

    p_decoding = Process(target=encodingAudio.decodeAudio, args=(q_receive_pipe_decoding, q_receive_decoding_render,test,))
    processes.append(p_decoding)
    p_render = Process(target=renderAudio.playAudio, args=(q_send_ingest_encoding,))
    processes.append(p_render)

    






    for process in processes:
        process.start()


    for process in processes:
        process.join(1)

        

def test_ingest_audio():
    p_ingest = Process(target=ingestAudio.test_from_audio_stream)
    p_ingest.start()
    p_ingest.join()

def test_encoding_audio():
    p_encoding = Process(target=encodingAudio.testEncoding)
    p_encoding.start()
    p_encoding.join()

def test_pipe_audio():
    p_pipe = Process(target=pipeIOAudio.test_pipeIOAudio)
    p_pipe.start()
    p_pipe.join() 

def test_render_audio():
    p_render = Process(target=renderAudio.test_audio_to_file_or_play)
    p_render.start()
    p_render.join() 

if __name__ == "__main__":
    remote_ip = "0.0.0.0"
    remote_port = "1114"
    local_port = "1114"
    test_flag = False

    # input
    opts, _ = getopt.getopt(sys.argv[1:], "t:", ["test=", "remote_ip=", "remote_port=", "local_port="])

    if opts:
        # load paras
        for o, a in opts:
            if o in ("--remote_ip"):
                remote_ip = a
            if o in ("--remote_port"):
                remote_port = a
            if o in ("--local_port"):
                local_port = a
        # test
        for o, a in opts:
            if o in ("-t", "--test"):
                test_flag = True
                if a == "ingest_audio":
                    test_ingest_audio()
                elif a == "encoding_audio":
                    test_encoding_audio()
                elif a == "pipe_audio":
                    test_pipe_audio()
                elif a == "render_audio":
                    test_render_audio()
                elif a == "noFIFO":
                    run_audio_system(mode="noFIFO", remote_ip=remote_ip, remote_port=remote_port, local_port=local_port)
            else:
                test_flag = False
        if not test_flag:
            run_audio_system(mode="run", remote_ip=remote_ip, remote_port=remote_port, local_port=local_port)
    else:
        print("Error: no params. Use --test to enter test mode. Add --remote_ip to enter run mode.")

