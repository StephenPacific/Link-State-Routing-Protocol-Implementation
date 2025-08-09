#coding: utf-8
from socket import *
import sys
import random
import time
from datetime import datetime
#Define connection (socket) parameters
#Address + Port no
#Server would be running on the same host as Client
serverhost = sys.argv[1]
serverPort = int(sys.argv[2])

clientSocket = socket(AF_INET, SOCK_DGRAM)
random_start = random.randrange(10000,20000)
clientSocket.settimeout(0.6)
waittime_list =[]

for i in range(random_start,random_start+20):
    message = f"PING {i} {datetime.now()} \r\n".encode()
    clientSocket.sendto(message, (serverhost, serverPort))
    start = time.time()
    waittime = 'timed out'
    while True:
        try:
            receive_message = clientSocket.recv(1024)
            if len(receive_message) > 0 :
                waittime = f"{round((time.time() - start)* 1000)} "
                waittime_list.append(int(waittime))
                print(f"ping to {serverhost}, seq = {i}, rtt = {waittime}ms" )
                break
            else:
                print(f"Received empty message")
        except timeout as e:
            print(f"ping to {serverhost}, seq = {i}, timeout")
            break
avg_list = sum(waittime_list)/len(waittime_list)
print(f"max:{max(waittime_list)} ms")
print(f"min:{min(waittime_list)} ms")
print(f"average:{avg_list} ms")


clientSocket.close()
# Close the socket


