#Chien Kai Wang, Brian Wan, William Chen
#TCP CHAT CLIENT

import pyaudio
import sys
import socket
import select
import time
from array import array
from struct import pack

msgType = 0 
check = 0
receive = 0

ALPHA_LOWER = ['a', 'b', 'c', 'd', 'e', 'f', 'g', ' ', 'h', 'i', 'j', 'k', 'l', 'm', 'n', 'o', 'p', 'q', 'r', 's', 't', 'u', 'v', 'w', 'x', 'y', 'z']
ALPHA_UPPER = ['A', 'B', 'C', 'D', 'E', 'F', 'G', 'H', 'I', 'J', 'K', 'L', 'M', 'N', 'O', 'P', 'Q', 'R', 'S', 'T', 'U', 'V', 'W', 'X', 'Y', 'Z']
SUB_CIPHER = [('1','5'), (',','\''), ('.','"'), (';','<'), ('"','>'), (':','?'), ('<','/'), ('>',';'), ('/',','), ('?','.'), ('2','`'), ('3','-'), ('4','~'), ('5','1'), ('[','|'), (']','\\'), ('\\','{'), ('}','['), ('{',']'), ('|','}'), ('6','0'), ('7','='), ('8','2'), ('9','6'), ('0','8'), ('-','9'), ('=','7'), ('!','#'), ('@','*'), ('#','!'), ('$','^'), ('%','('), ('^','&'), ('&','+'), ('*',')'), ('(','%'), (')','_'), ('_','@'), ('+','$'), ('~', '4'), ('`', '3')]
NEW_CIPHER = {}

#receive data
def MsgRec(s, x):
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

    # Decrypt the message, preserving the prefix
    i = 0
    for c in msg:
        if c == ']':
            break
        i = i+1
    if x == 0:
        dmsg = decrypt_sub(msg[i+2:])
        msg = msg[:i+2]
        msg = msg + dmsg

    return msg

#send data
def MsgSend(clientsocket, msg, x):
    if x == 0:
        msg = encrypt_sub(msg)
    msgTypeSend = str(msgType)
    length = str(len(msg))
    while(len(length) < 111):
        length = '0' + length
    try: 
        clientsocket.sendall(msgTypeSend)
        clientsocket.sendall(length)
        clientsocket.sendall(msg)
    except socket.error:
        print >> sys.stderr,'ERROR: Failed to send message. Terminating.'
        sys.exit()

def encrypt_sub(message):
    encrypted = ''
    for c in message:
        if c in NEW_CIPHER:
            encrypted = encrypted + NEW_CIPHER[c]
        else:
            encrypted = encrypted + c
    return encrypted

def decrypt_sub(message):
    # Invert the Cipher to get the decryptions
    inverted = {}
    for key, value in NEW_CIPHER.items():
        inverted[value] = key

    # Decrypt it
    decrypted = ''
    for c in message:
        if c in NEW_CIPHER:
            decrypted = decrypted + inverted[c]
        else:
            decrypted = decrypted + c
    return decrypted

def chat_client():
    global msgType
    global check
    global receive 
    if len(sys.argv) != 2:
        print >> sys.stderr,'Invalid number of args. Terminating'
        sys.exit()

    host = sys.argv[1]
    #port = int(sys.argv[2])

    # Set up the Substitution Cipher password
    print 'Rearrange the words for your password'
    print '"TV quiz drag cox blew JFK nymphs"'
    password = sys.stdin.readline()

    if len(password.replace(' ', '')) != 27:
        print >> sys.stderr,'Invalid password. You included an extra character or forgot one. Terminating'
        sys.exit()

    # Scramble the Preset Subtitution Cipher
    i = 0
    j = 38
    for tuple in SUB_CIPHER:
        NEW_CIPHER[SUB_CIPHER[i][0]] = SUB_CIPHER[j][1]
        i = i + 1
        j = j - 1

    # Build the Substitution cipher
    password = password.lower()
    password = password.replace(' ', '')
    password = password.replace('\n', '')
    password = password + ' '
    j = 15
    for i in range(0, 27):
        NEW_CIPHER[ALPHA_LOWER[i]] = password[i]
    for i in range(25, -1, -1):
        NEW_CIPHER[ALPHA_UPPER[i]] = password[i].upper()
        j = j+1
    NEW_CIPHER['\n'] = '\n'

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
                    data = MsgRec(sock, 0)
                    #if data.strip() != '[audio]' : 
                    if '[audio]' not in data:
                        sys.stdout.write("\r" + '[Guest]'+data)
                        sys.stdout.write('[Local] '); sys.stdout.flush()     
                    else:
                        receive = 1
                        check = 1 
                        break
                else :
                    if msgType == 0: #text
                        msg = sys.stdin.readline() #read a line from the client
                        #if msg.strip() == '[audio]':
                        if '[audio]' in msg:
                            msgType = 1
                        MsgSend(s,msg, 0)    #send using the send function 
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
                datastream = MsgRec(s, 1)
                if 'endofaudio' in datastream:
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
                    MsgSend(s,datastreamSend, 1)
                    if silent:
                        countSilent += 1 
                    if countSilent > 40:
                        MsgSend(s,'endofaudio', 1)
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

def is_silent (sendData):
    return max(sendData) < 600 

if __name__ == "__main__":

    sys.exit(chat_client())

