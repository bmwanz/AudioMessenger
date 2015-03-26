#Chien Kai Wang, Brian Wan, William Chen
# TCP Chat Server

msgType = 0

#receive data
def MsgSend(clientsocket, msg):
    msgTypeSend = str(msgType)
    length = str(len(msg))
    while(len(length) < 111):
        length = '0' + length
    try: 
        clientsocket.sendall(msgTypeSend)
        clientsocket.sendall(length)
        clientsocket.sendall(msg)
    except socket.error:
        #print 'ERROR: Failed to send message. Terminating.'
        if clientsocket in SOCKET_LIST:
            SOCKET_LIST.remove(clientsocket)
        sys.exit()

#send data
def MsgRec(s):
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
    return msg 

import pyaudio
import sys
import socket
import select

host = '' 
SOCKET_LIST = [] 
port = 9001

def chat_server():

    server_socket = socket.socket(socket.AF_INET, socket.SOCK_STREAM)
    server_socket.setsockopt(socket.SOL_SOCKET, socket.SO_REUSEADDR, 1)
    try:
        server_socket.bind((host, port))
    except socket.error:
        print 'ERROR: Could not bind to port. Terminating.'
        sys.exit()
    SOCKET_LIST.append(server_socket)
    print 'Chat Online!'
    
    p= pyaudio.PyAudio()
    stream = p.open(format = pyaudio.paInt16,
                channels = 1,
                rate = 10240,
                    output = True)
    
    server_socket.listen(5)
    checkAudio = 0
    while 1:

        #chooses the ready-to-use input stream 
        read_sock, write_sock, err_sock = select.select(SOCKET_LIST,[],[],0)
      
        for sock in read_sock:
            #new chat client 
            if sock == server_socket: 
                sockfd, addr = server_socket.accept()
                SOCKET_LIST.append(sockfd)
                print "Client (%s, %s) Joins the Chat" % addr
                 
                sendtochat(server_socket, sockfd, "[%s:%s] Joins the Chat\n" % addr)
             
            #chat message from one of the clients 
            else:
                try:
                    # receive data using the function 
                    data = MsgRec(sock)
                    if data : #socket is valid
                        if checkAudio == 0:
                            if data.strip() != '[audio]' :
                                checkAudio = 0
                            else :
                                checkAudio = 1
                        if checkAudio == 0:
                            sendtochat(server_socket, sock, "\r" + '[' + str(sock.getpeername()) + '] ' + data)
                        else :
                            print '7'
                            sendtochat(server_socket,sock,data)
                    else: #broken socket
                        print '8'
                        if sock in SOCKET_LIST:
                            print '9'
                            SOCKET_LIST.remove(sock)
                        sendtochat(server_socket, sock, "Client (%s, %s) is off\n" % addr) 
                except:
                    continue

    server_socket.close()
    
# send message to the chat room
def sendtochat (server_socket, sock, message):
    for socket in SOCKET_LIST:
        if socket != server_socket and socket != sock :
            MsgSend(socket,message)
            #socket.send(message)

if __name__ == "__main__":

    sys.exit(chat_server())         
