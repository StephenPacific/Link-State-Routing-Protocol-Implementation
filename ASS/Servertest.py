import sys
import os
from socket import *
import threading 
import json
import hashlib
import time
import heapq


info_lock = threading.Lock()
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
        
# def listening(udp, info):
#     while True:
#         data, addr = udp.recvfrom(4096)
#         received_data = json.loads(data.decode())
#         actual_info = received_data["info"]

#         for received_node in actual_info:
#             received_id = received_node['id']
#             received_timestamp = received_node['timestamp']
            
#             # 检查并更新本地信息
#             local_node = next((item for item in info if item['id'] == received_id), None)
#             if local_node is None or local_node['timestamp'] < received_timestamp:
#                 # 更新或添加节点信息
#                 if local_node:
#                     local_node.update(received_node)
#                 else:
#                     info.append(received_node)

#         # print("receive_data", received_data)
        
def listening(udp, info):
    while True:
        data, addr = udp.recvfrom(4096)
        received_data = json.loads(data.decode())
        actual_info = received_data["info"]

        # print("info",info)    
        for received_node in actual_info:
            received_id = received_node['id']
            received_timestamp = received_node['timestamp']
            
            local_node = next((item for item in info if item['id'] == received_id), None)
                
            if local_node:
                
                if local_node['timestamp'] < received_timestamp:
                    local_node.update(received_node)
            else:
                info.append(received_node)

        
def findLost(info):
    while True:
        time.sleep(3)
        current_time = int(time.time())
        ids_to_remove = []

        for item in info:
            time_diff = current_time - item['timestamp']
            if time_diff > 3:
                ids_to_remove.append(item['id'])
        print("need to remove",ids_to_remove)
        info[:] = [item for item in info if item['id'] not in ids_to_remove]

# def findLost(info):
#     while True:
#         time.sleep(3)  # 定时检查
#         current_time = int(time.time())
#         # 选出所有活跃的节点
#         active_nodes = [item for item in info if current_time - item['timestamp'] <= 3]  # 假设3秒为不活跃阈值
#         # 更新info列表为只包含活跃的节点
#         print("activeNode",active_nodes)
#         info[:] = active_nodes
#         # info[:] = [item for item in info if current_time - item['timestamp'] <= 3]


def build_graph_from_info(info):
    print("Current info:", info)  # 打印当前的info列表
    graph = {}
    alive = []
    for item in info:
        if isinstance(item, dict) and 'message' in item and isinstance(item['message'], dict):
            for node, connections in item['message'].items():
                graph[node] = {conn[0]: float(conn[1]) for conn in connections}
        else:
            print("Warning: Unexpected item format in info:", item)
    for i in graph:
        alive.append(i)

    # 过滤图中的节点和连接，只保留活着的节点
    filtered_graph = {node: {neigh: cost for neigh, cost in connections.items() if neigh in alive} 
                      for node, connections in graph.items() if node in alive}

    # print("Built graph:", filtered_graph)  # 打印构建的graph
    # print("Alive nodes:", alive)
    return filtered_graph

def dijkstra_algorithm(info, start):
    filtered_graph = build_graph_from_info(info)
    paths = {node: [] for node in filtered_graph}
    priority_queue = [(0, start)]
    distances = {node: float('inf') for node in filtered_graph}  # 初始化 distances，确保每个节点都有条目
    distances[start] = 0

    while priority_queue:
        curr_dist, curr_node = heapq.heappop(priority_queue)

        if curr_dist <= distances[curr_node]:
            for neighbor, cost in filtered_graph[curr_node].items():
                distance = curr_dist + cost

                if distance < distances.get(neighbor, float('inf')):  # 使用 .get() 以防止 KeyError
                    paths[neighbor] = paths[curr_node] + [curr_node]
                    distances[neighbor] = distance
                    heapq.heappush(priority_queue, (distance, neighbor))

    return distances, paths

def format_dijkstra_output(info):
    while True:  # 添加循环以定期计算和输出
        time.sleep(15)  # 等待 15 秒后重新计算
        start_router = os.path.basename(filename).split('config')[1].split('.')[0]
        distances, paths = dijkstra_algorithm(info, start_router)

        print(f"I am router {start_router}")
        print("-----Router Path and least Cost-----")
        for node, distance in distances.items():
            if node != start_router:
                path_str = ''.join(paths[node] + [node])
                print(f"Least cost path to router {node}: {path_str} and the cost is {distance}")
        
if __name__ == '__main__':
    serverPort = int(sys.argv[1])
    IP = "127.0.0.1"
    udp = socket(AF_INET, SOCK_DGRAM)
    udp.bind((IP, serverPort))
    filename = sys.argv[2]
    print(f"I am router {os.path.basename(filename).split('config')[1].split('.')[0]}")
    thread = threading.Thread(target=flooding)
    initialize(filename)
    flood_thread = threading.Thread(target=flooding, args=(udp, router,info,))
    listen_thread = threading.Thread(target=listening, args=(udp,info,))
    findLost_thread = threading.Thread(target=findLost,args=(info,))
    dijikstra_thread = threading.Thread(target=format_dijkstra_output,args=(info,))
    flood_thread.start()
    listen_thread.start()
    findLost_thread.start()
    dijikstra_thread.start()

    flood_thread.join()
    listen_thread.join()
    findLost_thread.join()
    dijikstra_thread.join()
