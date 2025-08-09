from socket import *
import sys
import os

def processRequest(requestSocket):
    receiveData = requestSocket.recv(1024)
    print(f'The receive data is {receiveData}')
    
    receiveDataSplit = receiveData.split()
    print(receiveDataSplit)
    requestFile = receiveDataSplit[1][1:]
        
    if not os.path.isfile(requestFile):
        message = 'HTTP/1.1 404 Not Found\r\nContent-Type: text/html\r\n\r\n<html><p>404 Not Found</p></html>'
        requestSocket.send(message.encode())
    else:
        response = 'HTTP/1.1 200 OK\r\n'
        if 'myimage.png' in str(requestFile):
            response += 'Content-Type: image/png\r\n\r\n'
        elif 'index.html' in str(requestFile):
            response += 'Content-Type: text/html\r\n\r\n'
            
        requestSocket.send(response.encode())

        with open(requestFile, 'rb') as file:
            fileData = file.read()
            requestSocket.send(fileData)

    requestSocket.close()


if __name__ == "__main__":
    serverSocket = socket(AF_INET, SOCK_STREAM)
    serverSocket.bind(('localhost', int(sys.argv[1])))
    serverSocket.listen(1)
    print("The server is ready to receive")

    while True:
        requestSocket, _ = serverSocket.accept()
        processRequest(requestSocket)

    serverSocket.close()
