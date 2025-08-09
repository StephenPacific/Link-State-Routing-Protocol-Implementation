# coding=utf-8
import math
import sys
import socket
import time
import threading
import heapq
from dataclasses import dataclass, field


R_ID = 'A'
R_HOST = '127.0.0.1'
R_PORT = 5000
CONFIG_PATH = 'configA.txt'

UPDATE_INTERVAL = 1
ROUTER_UPDATE_INTERVAL = 30

udp_socket = None
neighbor_node_num = 0
neighbor_node = {}
fail_nodes = []
send_record = {}


@dataclass
class ProtocolPackage:
    id: str = field(default='')
    port: int = field(default=0)
    timestamp: int = field(default=0)
    node_num: int = field(default=0)
    nodes: dict = field(default_factory=dict)


def package_encode(package_):
    # head
    str_to_encode = f'{package_.id} {package_.port} {package_.timestamp} {package_.node_num}\n'
    # body
    for k1, v1 in package_.nodes.items():
        for k2, v2 in v1.items():
            str_to_encode += f"{k1} {k2} {v2[0]} {v2[1]}\n"
    return str_to_encode.encode('utf-8')


def package_decode(bytes_):
    strs = bytes_.decode('utf-8').split('\n')
    h = strs[0].split(' ')  # header
    body = strs[1:]

    packages = ProtocolPackage()
    packages.id = h[0]
    packages.port = int(h[1])
    packages.timestamp = int(h[2])
    packages.node_num = int(h[3])

    payload = {}
    for item in body:
        if len(item) > 0:
            item_sp = item.split(' ')
            key1 = item_sp[0]
            key2 = item_sp[1]
            value = (float(item_sp[2]), int(item_sp[3]))
            if payload.get(key1) is None:
                payload[key1] = {key2: value}
            else:
                payload[key1][key2] = value
    packages.nodes = payload
    return packages


def init_from_config(path):
    global neighbor_node_num
    with open(path, 'r') as f:
        lines = f.readlines()
        neighbor_node_num = int(lines[0].strip())
        node_info = lines[1:]
        for line in node_info:
            if neighbor_node.get(R_ID) is None:
                neighbor_node[R_ID] = {}
            line_sp = line.strip().split(' ')
            neighbor_node[R_ID][line_sp[0]] = (float(line_sp[1]), int(line_sp[2]))


def broadcast_thr_handle():
    while True:
        neighbor_node_ = {R_ID: neighbor_node[R_ID]}
        for i in fail_nodes:
            neighbor_node_[i] = {}
        package_ = ProtocolPackage()
        package_.id = R_ID
        package_.port = R_PORT
        package_.timestamp = int(round(time.time() * 1000))
        package_.node_num = int(neighbor_node_num)

        self_neighbor = neighbor_node[R_ID]
        package_.nodes = neighbor_node_
        for _, v in self_neighbor.items():
            udp_socket.sendto(package_encode(package_), (R_HOST, v[1]))
        time.sleep(UPDATE_INTERVAL)


def listen_thr_handle():
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((R_HOST, R_PORT))

    while True:
        data, client_address = server_socket.recvfrom(1024)  # Recv data use udp
        package_ = package_decode(data)

        self_neighbor = neighbor_node.get(R_ID)
        self_neighbor = {key: value for key, value in self_neighbor.items() if key not in fail_nodes}
        fail_nodes.clear()

        for k, v in package_.nodes.items():
            if len(v) == 0:
                del neighbor_node[k]
            else:
                neighbor_node[k] = v
        package_r_id = package_.id
        if R_ID in package_.nodes[package_r_id]:
            self_neighbor[package_r_id] = (package_.nodes[package_r_id][R_ID][0], package_.port)

        if package_r_id not in send_record or send_record[package_r_id] < package_.timestamp:
            send_record[package_r_id] = package_.timestamp
            [udp_socket.sendto(data, (R_HOST, v[1])) for k, v in self_neighbor.items() if k != package_r_id]


def dijkstra(graph, start):
    distances = {node: float('infinity') for node in graph}
    distances[start] = 0
    paths = {node: [] for node in graph}
    priority_queue = [(0, start)]

    while priority_queue:
        curr_dist, curr_node = heapq.heappop(priority_queue)

        if curr_dist > distances[curr_node]:
            continue

        for neighbor, weight in graph[curr_node].items():
            distance = curr_dist + weight[0] if isinstance(weight, tuple) else curr_dist + weight

            if distance < distances[neighbor]:
                distances[neighbor] = distance
                paths[neighbor] = paths[curr_node] + [curr_node]
                heapq.heappush(priority_queue, (distance, neighbor))

    return distances, paths


def min_path_handle():
    while True:
        time.sleep(ROUTER_UPDATE_INTERVAL)
        try:
            distances, paths = dijkstra(neighbor_node, R_ID)
            for node in distances:
                path_str = "".join(paths[node] + [node])
                distance = distances[node]
                if not node == R_ID and not math.isinf(distance):
                    print(f"Least cost path to router {node}: {path_str} and the cost is {round(distance, 2)}")
            print('')
        except Exception as e:
            print(e)


def find_fail_node():
    time.sleep(3)  # lazy start

    while True:
        time.sleep(UPDATE_INTERVAL)
        self_neighbors = neighbor_node.get(R_ID)
        for k, v in self_neighbors.items():
            if send_record.get(k) is None or (int(round(time.time() * 1000)) - send_record.get(k)) > 3 * UPDATE_INTERVAL * 1000 :
                fail_nodes.append(k)


if __name__ == '__main__':
    if len(sys.argv) == 4:
        R_ID = sys.argv[1]
        R_PORT = int(sys.argv[2])
        CONFIG_PATH = sys.argv[3]
    else:
        print("Please enter <router id> <router_port> <config_file>")

    try:
        init_from_config(CONFIG_PATH)
        udp_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    except Exception as e:
        print("Start Fail Cause: ")
        print(e)

    print(f"I am router {R_ID}")
    # ------- Start Threads -------
    broadcast_thr = threading.Thread(target=broadcast_thr_handle)
    listen_thr = threading.Thread(target=listen_thr_handle)
    dijkstra_thr = threading.Thread(target=min_path_handle)
    find_fail_node_thr = threading.Thread(target=find_fail_node)

    broadcast_thr.start()
    listen_thr.start()
    dijkstra_thr.start()
    find_fail_node_thr.start()