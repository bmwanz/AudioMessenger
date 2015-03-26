#Chien Kai Wang, Brian Wan, William Chen
#TCP CHAT CLIENT


#CITATION:
#http://www.bogotobogo.com/python/python_network_programming_tcp_server_client_chat_server_chat_client_select.php
#by K Hong 

import pyaudio
import sys
import socket
import select
import time
import pickle

from array import array
from struct import pack
from Crypto.PublicKey import RSA
from Crypto.Hash import MD5
from Crypto.Util import randpool

msgType = 0 
check = 0
receive = 0

#receive data and decrypt
def MsgRec(s, key):
    msgType = int(s.recv(1))
    length = int(s.recv(111))
    msg = ''

    if(length < 1024): 
        msg = s.recv(1024)
    else:
        left = length % 1024 
        while(length >= 1024):
            msg = msg + s.recv(1024)
            length = length - 1024
        msg = msg + s.recv(left)

    encoded = pickle.loads(msg)

    decoded = key.decrypt(msg)
    return decoded

#send and encrypt data
def MsgSend(clientsocket, msg, key):
    encoded = key.encrypt(msg, 32)
    
    msgTypeSend = str(msgType)
    length = str(len(encoded))
    while(len(length) < 111):
        length = '0' + length
    try: 
        clientsocket.sendall(msgTypeSend)
        clientsocket.sendall(length)
        clientsocket.sendall(pickle.dumps(encoded))
    except socket.error:
        print >> sys.stderr,'ERROR: Failed to send message. Terminating.'
        sys.exit()
 
def chat_client():
    global msgType
    global check
    global receive 
    if len(sys.argv) != 2:
        print >> sys.stderr,'Invalid number of args. Terminating'
        sys.exit()

    # Create the RSA key
    rand = randpool.RandomPool()
    RSAKey = RSA.generate(1024, rand.get_bytes)
    RSAPubKey = RSAKey.publickey()

    host = sys.argv[1]
    #port = int(sys.argv[2])

    s = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
     
    try:
        s.connect((host, 9001))
    except Exception, e:
        if(e.errno == -2):
            print >> sys.stderr,'ERROR: Could not connect to server. Terminating.'
        elif(e.errno == 111):
            print >> sys.stderr,'ERROR: Invalid port. Terminating.'
        else:
            print >> sys.stderr,e
        sys.exit()

    print 'Connected'

    receivedKey = s.recv(2048)
    publickey = pickle.loads(receivedKey)
    print publickey

    s.sendall(pickle.dumps(RSAPubKey))

    sys.stdout.write('[Local] '); sys.stdout.flush()
     
    p = pyaudio.PyAudio()
    r = array('h')
    countSilent = 0
    
    while 1:
        socket_list = [sys.stdin, s]
         
        # chooses inputs
        if check == 0 :
            read_sock, write_sock, err_sock = select.select(socket_list , [], [])
            for sock in read_sock:             
                if sock == s:
                    data = MsgRec(sock, RSAKey)
                    if data.strip() != '[audio]' : 
                        sys.stdout.write("\r" + '[Guest] '+data)
                        sys.stdout.write('[Local] '); sys.stdout.flush()     
                    else:
                        receive = 1
                        check = 1 
                        break
                else :
                    if msgType == 0: #text
                        msg = sys.stdin.readline() #read a line from the client
                        if msg.strip() == '[audio]':
                            msgType = 1
                        MsgSend(s,msg, publickey)    #send using the send function
                        sys.stdout.write('[Local] '); sys.stdout.flush() 
                    else : #audio
                        countSilent = 0
                        receive = 2 
                        check = 1
                        break
        if receive == 1 : 
            stream = p.open(format = pyaudio.paInt16,
                            channels = 1,
                            rate = 44100,
                            output = True)
            sys.stdout.write('\nGuest is Talking ...\n'); sys.stdout.flush()
            while 1:
                datastream = MsgRec(s, RSAKey)
                #if datastream.strip() == 'endofaudio' :
                if 'endofaudio' in datastream :
                    check = 0
                    receive = 0
                    msgType = 0
                    sys.stdout.write('\nGuest is Done Talking!\n'); sys.stdout.flush()
                    break
                if datastream:
                    stream.write(datastream)
        elif receive == 2:
            stream = p.open(format = pyaudio.paInt16,
                            channels = 1,
                            rate = 44100,
                            input = True, 
                            frames_per_buffer = 8192)
            try:
                while 1:
                    datastreamSend = stream.read(8192)
                    dataTest = array('h',datastreamSend)
                    silent = is_silent(dataTest)
                    MsgSend(s,datastreamSend, publickey)
                    if silent:
                        countSilent += 1 
                    if countSilent > 40:
                        MsgSend(s,'endofaudio', publickey)
                        msgType = 0
                        check = 0
                        receive = 0 
                        #MsgSend(s,'endofaudio')
                        break
                    
                    #MsgSend(s,datastreamSend)
                    
                '''
                datastreamSend = stream.read(8192)
                MsgSend(s,datastreamSend)
                '''
            except IOError:
                print 'warning: dropped frame'
            #triggerMsg = sys.stdin.readline() 

            #MsgSend(s,datastreamsend)

def is_silent (sendData):
    return max(sendData) < 600 

if __name__ == "__main__":

    sys.exit(chat_client())

