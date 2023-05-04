import numpy as np
import pyaudio
import time
from multiprocessing import Queue, Process
from pydub import AudioSegment
from io import BytesIO


sample_rate=48000
chunk_size=960


p = pyaudio.PyAudio()

def find_audio_input_device_index(p, target_device_name="ROCCAT Khan AIMO"):
    num_devices = p.get_device_count()
    


    for i in range(num_devices):
        device_info = p.get_device_info_by_index(i)
        #print(device_info)
        device_name = device_info.get("name")
        if device_name and target_device_name in device_name and device_info["maxInputChannels"] > 0:
            return i
    return None



def from_audio_stream(q_output,sample_rate=sample_rate, channels=1):

    audio_device_index = find_audio_input_device_index(p)
    #audio_device_index=5
    try:
        audio_format = pyaudio.paInt16
        
        device_info = p.get_device_info_by_index(audio_device_index)

        if sample_rate is None:
            sample_rate = int(device_info["defaultSampleRate"])

        print("Start recording!")

        stream = p.open(format=audio_format,
                       channels=channels,
                       rate=sample_rate,
                       input=True,
                       input_device_index=audio_device_index,
                       frames_per_buffer=chunk_size)
        

        while True:
            data = stream.read(chunk_size, exception_on_overflow=False)
            #print(" data: ",len(data))
            audio_data = np.frombuffer(data, dtype=np.int16)
            #print(" audio_data: ",len(audio_data))

            q_output.put(audio_data)
            #q_output.put(data)
            


        stream.stop_stream()
        stream.close()
        p.terminate()
        print("Finish recording!")
        
        return audio_segment
    except Exception as e:
        print(f"Error in from_audio_stream: {e}")


    