import numpy as np
from multiprocessing import Queue, Process
import ctypes
import datetime
import ingestAudio as ia
import pyaudio
import time

# 参数
chunk_size=ia.chunk_size
sample_rate_hz = ia.sample_rate

num_channels = 1
bitrate = 3200
enable_dtx = False
model_path_cstr = b"model_coeffs"

# Load the correct version of libstdc++.so.6
libstdcpp_path = "/usr/lib/x86_64-linux-gnu/libstdc++.so.6"
libstdcpp = ctypes.CDLL(libstdcpp_path, mode=ctypes.RTLD_GLOBAL)

# 加载共享库
liblyra_encoder = ctypes.CDLL("./liblyra_encoderhyl.so")
liblyra_decoder = ctypes.CDLL("./liblyra_decoderhyl.so")

# 定义函数参数类型和返回值类型
# For Encoder
liblyra_encoder.CreateLyraEncoder.argtypes = [
    ctypes.c_int,  # sample_rate_hz
    ctypes.c_int,  # num_channels
    ctypes.c_int,  # bitrate
    ctypes.c_bool,  # enable_dtx
    ctypes.c_char_p  # model_path_cstr
]
liblyra_encoder.CreateLyraEncoder.restype = ctypes.POINTER(ctypes.c_void_p)

liblyra_encoder.DestroyLyraEncoder.argtypes = [
    ctypes.POINTER(ctypes.c_void_p)  # encoder
]

liblyra_encoder.LyraEncode.argtypes = [
    ctypes.POINTER(ctypes.c_void_p),  # encoder
    ctypes.POINTER(ctypes.c_int16),  # audio
    ctypes.c_int,  # audio_length
    ctypes.POINTER(ctypes.c_uint8),  # output
    ctypes.POINTER(ctypes.c_int)  # output_length
]
liblyra_encoder.LyraEncode.restype = ctypes.c_bool

# For Decoder
liblyra_decoder.CreateLyraDecoder.argtypes = [
    ctypes.c_int,  # sample_rate_hz
    ctypes.c_int,  # num_channels
    ctypes.c_char_p  # model_path_cstr
]
liblyra_decoder.CreateLyraDecoder.restype = ctypes.POINTER(ctypes.c_void_p)

liblyra_decoder.DestroyLyraDecoder.argtypes = [
    ctypes.POINTER(ctypes.c_void_p)  # decoder
]

liblyra_decoder.LyraSetEncodedPacket.argtypes = [
    ctypes.POINTER(ctypes.c_void_p),  # decoder
    ctypes.POINTER(ctypes.c_uint8),  # encoded
    ctypes.c_int  # size
]
liblyra_decoder.LyraSetEncodedPacket.restype = ctypes.c_int


liblyra_decoder.LyraDecodeSamples.argtypes = [
    ctypes.POINTER(ctypes.c_void_p),  # decoder
    ctypes.c_int  # num_samples
]
liblyra_decoder.LyraDecodeSamples.restype = ctypes.POINTER(ctypes.c_int16)

liblyra_decoder.LyraFreeDecodedSamples.argtypes = [
    ctypes.POINTER(ctypes.c_int16)  # decoded_samples
]






# 新增 encodeAudio 函数
def encodeAudio(q_send_ingest_encoding, q_send_encoding_pipe,test):
    print("Start encoding!")
    # Initialize the Lyra encoder instance here
    encoder = liblyra_encoder.CreateLyraEncoder(sample_rate_hz, num_channels, bitrate, enable_dtx, model_path_cstr)

    noteForEncode=0
    while True:
        
        #print("start get encode:",time.time())
        input_audio = q_send_ingest_encoding.get()

        if noteForEncode==1:
            test.put(input_audio)

        #print("start encode:",time.time())
        audio_length = len(input_audio)
        output = np.zeros(256, dtype=np.uint8)
        output_length = ctypes.c_int(0)
        audio_ptr = input_audio.ctypes.data_as(ctypes.POINTER(ctypes.c_int16))
        output_ptr = output.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        success = liblyra_encoder.LyraEncode(encoder, audio_ptr, audio_length, output_ptr, ctypes.byref(output_length))
        #print("end encode:",time.time())
        if success:
            q_send_encoding_pipe.put(output[:output_length.value])
            noteForEncode+=1
            #print("noteForEncode is ", noteForEncode)
        

    # Destroy the encoder instance
    liblyra_encoder.DestroyLyraEncoder(encoder)
    print("Finsh encoding!")


# ... (之前的部分代码保持不变)

# 新增 decodeAudio 函数
def decodeAudio(q_receive_pipe_decoding, q_receive_decoding_render,test):
    # Initialize the Lyra decoder instance here
    decoder = liblyra_decoder.CreateLyraDecoder(sample_rate_hz, num_channels, model_path_cstr)

    
    noteFordecodeAudio=0

    print("Start decodeAudio!")
    while True:
        encoded_data = q_receive_pipe_decoding.get()
        
       
        #print("decoding now")
        
        encoded_data_ptr = encoded_data.ctypes.data_as(ctypes.POINTER(ctypes.c_uint8))
        encoded_size = encoded_data.size
        success = liblyra_decoder.LyraSetEncodedPacket(decoder, encoded_data_ptr, encoded_size)
        if not success:
            q_receive_decoding_render.put(bytes(chunk_size))
            noteFordecodeAudio+=1
            
        else:
            num_samples_to_decode = 960 # 根据您的需求调整
            decoded_samples_ptr = liblyra_decoder.LyraDecodeSamples(decoder, num_samples_to_decode)
            if not decoded_samples_ptr:
                #print("Error decoding samples")
                noteFordecodeAudio+=1
                q_receive_decoding_render.put(bytes(chunk_size).tobytes())
                
            else:
                decoded_samples = np.ctypeslib.as_array(decoded_samples_ptr, (num_samples_to_decode,)).copy()
                liblyra_decoder.LyraFreeDecodedSamples(decoded_samples_ptr)
                noteFordecodeAudio+=1
                #print("noteFordecodeAudio:",noteFordecodeAudio)

                q_receive_decoding_render.put(decoded_samples.tobytes())

                if noteFordecodeAudio==1:
                    test.put(decoded_samples)

                #print("decoded_samples:",len(decoded_samples))

    

    # Destroy the decoder instance
    liblyra_decoder.DestroyLyraDecoder(decoder)
    print("Finish decodeAudio!")




