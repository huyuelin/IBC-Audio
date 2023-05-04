import os
import sys
import time
import numpy as np
from multiprocessing import Process, Queue
import ingestAudio 
import encodingAudio
import pipeIOAudio
import renderAudio
import shutil


def write_audio(q_send_encoding_pipe, pipe_path):
    f_v = os.open(pipe_path, os.O_WRONLY)
    print("send open1", time.time(), flush=True)
    noteForWrite=0
    #wait for data
    while True:

        noteForWrite+=1
        #print("start write:",time.time())
        encoded_audio_data = q_send_encoding_pipe.get()
        #print("send!!!", len(encoded_audio_data), encoded_audio_data)
        encoded_audio_data = encoded_audio_data.tobytes()
        encoded_audio_data = encoded_audio_data+b'\x0f\x0f'
        
        
        os.write(f_v, encoded_audio_data)
        
    print("send close1", time.time(), flush=True)
    print("noteForWrite=", noteForWrite)
    os.write(f_v, "end".encode("utf-8")+b'\x0f\x0f')
    return


def read_audio(q_output, pipe_path):
    f_v = os.open(pipe_path, os.O_RDONLY)
    s=b''
    while True:
        while not (b'\x0f\x0f' in s):
            s += os.read(f_v, 1024)
        if s == "end".encode("utf-8")+b'\x0f\x0f':
            break
        
        index = s.find(b'\x0f\x0f')
        tmp = s[:index]
        tmp=np.frombuffer(tmp, dtype=np.uint8)
        #print("receive!!!", len(tmp), tmp)

        q_output.put(tmp)
        s = s[index+2:]
    print("receive close1", time.time(), flush=True)
    return

            
def test_noFIFO_audio(q_input, q_output):
    while True:
        q_output.put(q_input.get())

