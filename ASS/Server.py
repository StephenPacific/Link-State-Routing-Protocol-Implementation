import sys
import os
from socket import *
import threading 
import json
import hashlib
import time

router = {}
package = {}
info = [] # with id
graph = [] # donot include id
last_active = {} 

def initialize(filename):
    key = os.path.basename(filename).split('config')[1].split('.')[0]
    router[key] = []
    with open(filename) as f:
        next(f)
        for line in f:
            parts = line.strip().split()
            router[key].append(parts)
    data_str = json.dumps(router, sort_keys=True)
    package['id'] = hashlib.sha256(data_str.encode()).hexdigest()
    package['message'] = router
    info.append(package)
    graph.append(router)
    # print(info)

def flooding(udp,router):
    while True:
        result = json.dumps(info).encode()
        for neighbors in router.values():
            for neighbor in neighbors:
                neighbor_port = int(neighbor[2])  
                udp.sendto(result, ("127.0.0.1", neighbor_port))
        time.sleep(5)

def listening(udp,info):
    while True:
        data, addr = udp.recvfrom(1024)  # We could get the info and addr from the receive message.
        Received = data.decode()  
        received_data = json.loads(Received)
        for i in received_data:
            received_id = i['id']  
            received_message = i['message']
            idExist = False
            for j in info:
                if received_id == j['id']:
                    idExist = True
                    break
            if not idExist:
                info.append(i)
                graph.append(received_message)
        
def findLost():
    while True:
        time.sleep(3)
        checkRouter = os.path.basename(filename).split('config')[1].split('.')[0]
        directly_connected_routers = []
        for item in info:
            if checkRouter in item['message']:
                for neighbor in item['message'][checkRouter]:
                    directly_connected_routers.append(neighbor[0])

        print(f"Routers directly connected to {checkRouter}: {directly_connected_routers}")
        # print(info)



# def dijkstra_algorithm(graph, start):
#     shortest_distances = {node: float('infinity') for node in graph}
#     shortest_distances[start] = 0
#     previous_nodes = {}
#     unvisited_nodes = set(graph)

#     while unvisited_nodes:
#         current_node = min(unvisited_nodes, key=lambda node: shortest_distances[node])
#         unvisited_nodes.remove(current_node)

#         for neighbour, weight in graph[current_node].items():
#             distance = shortest_distances[current_node] + weight
#             if distance < shortest_distances[neighbour]:
#                 shortest_distances[neighbour] = distance
#                 previous_nodes[neighbour] = current_node

#     return previous_nodes, shortest_distances

# def reconstruct_path(previous_nodes, start, end):
#     path = []
#     current = end
#     while current != start:
#         path.append(current)
#         current = previous_nodes[current]
#     path.append(start)
#     return path[::-1]

# def dijikstra():
#     while True:
#         time.sleep(15)
#         currentGraph = {}
#         for weight in graph:
#             for node, edges in weight.items():
#                 currentGraph[node] = {edge[0]: float(edge[1]) for edge in edges}
#         start_router = os.path.basename(filename).split('config')[1].split('.')[0]
#         print(f"I am router {start_router}")  
#         print("-----Router Path and least Cost-----")

#         routes_info = []
#         for node in currentGraph:
#             if node != start_router:  
#                 previous_nodes, shortest_distances = dijkstra_algorithm(currentGraph, start_router)
#                 path = reconstruct_path(previous_nodes, start_router, node)
#                 routes_info.append((node, ''.join(path), shortest_distances[node]))

#         routes_info.sort(key=lambda x: x[0])
#         for route in routes_info:
#             print(f"Least cost path to router {route[0]}: {route[1]} and the cost is {route[2]}")


if __name__ == '__main__':
    serverPort = int(sys.argv[1])
    IP = "127.0.0.1"
    udp = socket(AF_INET, SOCK_DGRAM)
    udp.bind((IP, serverPort))
    filename = sys.argv[2]
    print(f"I am router {os.path.basename(filename).split('config')[1].split('.')[0]}")
    thread = threading.Thread(target=flooding)
    initialize(filename)
    flood_thread = threading.Thread(target=flooding, args=(udp, router))
    listen_thread = threading.Thread(target=listening, args=(udp,info))
    findLost_thread = threading.Thread(target=findLost)
    # dijikstra_thread = threading.Thread(target=dijikstra)
    flood_thread.start()
    listen_thread.start()
    findLost_thread.start()
    # dijikstra_thread.start()

    flood_thread.join()
    listen_thread.join()
    findLost_thread.join()
    # dijikstra_thread.join()
