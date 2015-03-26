#!/usr/bin/env python
import pyaudio
import socket
import sys
import time
from array import array
from struct import pack
from multiprocessing import Process

# Pyaudio Initialization
chunk = 1024
FORMAT = pyaudio.paInt16
CHANNELS = 1
RATE = 10240
backlog = 5

THRESHOLD = 5

# Function Definitions

def is_silent(snd_data):
    #return True of below silent threshold
    return max(snd_data) < THRESHOLD

def audioSend(stream):
    # Main Functionality
    while 1:
        data = array('h', stream.read(chunk))
        silent = is_silent(data)
        
        if silent:
            count_silent += 1
    
        if count_silent > 65:
            print 'stop'
            break   #when silent counter hits 30, close connection
    
        s.send(data)
        #s.recv(size)

def audioRecv(stream):
    while 1:
        data = stream.recv(size)
        if data:
            #print 'receiving!'
            # Write data to pyaudio stream
            stream.write(data)  # Stream the received audio data

# Set up the pyaudio streams
pSend = pyaudio.PyAudio()
streamSend = pSend.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                input = True,
                frames_per_buffer = chunk)

pRecv = pyaudio.PyAudio();
streamRecv = pRecv.open(format = FORMAT,
                channels = CHANNELS,
                rate = RATE,
                output = True)

# Socket Initialization
size = 1024

# Parameters to start server
print 'Enter the desired Server Port'
portRecv = int(sys.stdin.readline())

socketRecv = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socketRecv.bind(('',portRecv))
socketRecv.listen(backlog)

print 'Server Started!'

# Parameters to connect to recipient
print 'Enter the IP of the recipient'
hostSend = sys.stdin.readline()

print 'Enter the port number'
portSend = int(sys.stdin.readline())

print 'Trying to connect to ' + hostSend + ' ' + str(portSend)

socketSend = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
socketSend.connect(('',9000))

print 'Press enter to start VOIP'
sys.stdin.readline()

# Start all the processes
procRecv = Process(target = audioRecv, args = (streamRecv,))
procSend = Process(target = audioSend, args = (streamSend,))
procRecv.daemon = True
procSend.daemon = True
procRecv.start()
procSend.start()

#need a silent counter or else connection will close immediately
r = array('h')
count_silent = 0



socketRecv.close()
socketSend.close()
streamSend.close()
streamRecv.close()
pSend.terminate()
pRecv.terminate()
