import sys
import os
from socket import *
import threading 
import json
import hashlib
import time
import heapq


router = {}
package = {}
info = [] # with id
lastreceivedTime = {}

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


def flooding(udp, router, info):
    while True:
        current_time = int(time.time())
        own_id = info[0]['id'] if info else None
        if own_id:
            for node_info in info:
                if node_info['id'] == own_id:
                    node_info['timestamp'] = current_time
            data_to_send = json.dumps({"info": info}).encode()
            for neighbors in router.values():
                for neighbor in neighbors:
                    neighbor_port = int(neighbor[2])
                    udp.sendto(data_to_send, ("127.0.0.1", neighbor_port))

        time.sleep(1)
           
def listening(udp, info):
    while True:
        data, addr = udp.recvfrom(4096)
        received_data = json.loads(data.decode())
        actual_info = received_data["info"]

        for received_node in actual_info:
            received_id = received_node['id']
            received_timestamp = received_node['timestamp']
            
            local_node = next((item for item in info if item['id'] == received_id), None)
                
            if local_node:
                if local_node['timestamp'] < received_timestamp:
                    local_node.update(received_node)
            else:
                info.append(received_node)
                
def build_graph_from_info(info):
    graph = {}
    current_time = int(time.time()) - 3

    active_nodes = set()
    for item in info:
        if item['timestamp'] >= current_time or item == info[0]:
            active_nodes.update(item['message'].keys())
    for item in info:
        node_id = list(item['message'].keys())[0] 
        if node_id in active_nodes:
            connections = item['message'][node_id]
            graph[node_id] = {conn[0]: float(conn[1]) for conn in connections if conn[0] in active_nodes}

    return graph



def dijkstra_algorithm(info, start):
    filtered_graph = build_graph_from_info(info)
    paths = {node: [] for node in filtered_graph}
    priority_queue = [(0, start)]
    distances = {node: float('inf') for node in filtered_graph}  
    distances[start] = 0

    while priority_queue:
        curr_dist, curr_node = heapq.heappop(priority_queue)

        if curr_dist <= distances[curr_node]:
            for neighbor, cost in filtered_graph[curr_node].items():
                distance = curr_dist + cost

                if distance < distances.get(neighbor, float('inf')): 
                    paths[neighbor] = paths[curr_node] + [curr_node]
                    distances[neighbor] = distance
                    heapq.heappush(priority_queue, (distance, neighbor))

    return distances, paths

def dijkstra(info):
    while True:
        time.sleep(30)  
        start_router = os.path.basename(filename).split('config')[1].split('.')[0]
        distances, paths = dijkstra_algorithm(info, start_router)

        print(f"I am router {start_router}")

        sorted_nodes = sorted(distances.keys())

        for node in sorted_nodes:
            if node != start_router:
                path_str = ''.join(paths[node] + [node])
                distance_str = "{:.1f}".format(distances[node])
                print(f"Least cost path to router {node}: {path_str} and the cost is {distance_str}")
        
if __name__ == '__main__':
    serverPort = int(sys.argv[2])
    IP = "127.0.0.1"
    udp = socket(AF_INET, SOCK_DGRAM)
    udp.bind((IP, serverPort))
    filename = sys.argv[3]
    routerId = sys.argv[1]
    thread = threading.Thread(target=flooding)
    initialize(filename)
    flood_thread = threading.Thread(target=flooding, args=(udp, router,info,))
    listen_thread = threading.Thread(target=listening, args=(udp,info,))
    dijikstra_thread = threading.Thread(target=dijkstra,args=(info,))
    flood_thread.start()
    listen_thread.start()
    dijikstra_thread.start()

    flood_thread.join()
    listen_thread.join()
    dijikstra_thread.join()
