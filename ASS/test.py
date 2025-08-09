# coding=utf-8
import math
import sys
import socket
import time
import threading
import heapq


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


class ProtocolPackage:
    def __init__(self, id='', port=0, timestamp=0, node_num=0, nodes=None):
        if nodes is None:
            nodes = dict()
        self.id = id
        self.port = port
        self.timestamp = timestamp
        self.node_num = node_num
        self.nodes = nodes


def package_encode(package_):
    # head
    str_to_encode = f'{package_.id} {package_.port} {package_.timestamp} {package_.node_num}\n'
    # body
    str_to_encode += '\n'.join(
        f"{k1} {k2} {v2[0]} {v2[1]}" for k1, v1 in package_.nodes.items() for k2, v2 in v1.items())
    return str_to_encode.encode('utf-8')


def package_decode(bytes_):
    strs = bytes_.decode('utf-8').split('\n')
    h = strs[0].split(' ')  # header
    body = strs[1:]  # body

    packages = ProtocolPackage()
    packages.id, packages.port, packages.timestamp, packages.node_num = h[0], int(h[1]), int(h[2]), int(h[3])

    payload = {}
    for item in body:
        if len(item) > 0:
            item_sp = item.split(' ')
            key1, key2, value = item_sp[0], item_sp[1], (float(item_sp[2]), int(item_sp[3]))
            payload.setdefault(key1, {})[key2] = value

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
        neighbor_node_ = {R_ID: neighbor_node.get(R_ID)}
        for failed_node in fail_nodes:
            neighbor_node_[failed_node] = {}
        package_ = ProtocolPackage()
        package_.id = R_ID
        package_.port = R_PORT
        package_.timestamp = int(round(time.time() * 1000))
        package_.node_num = int(neighbor_node_num)
        package_.nodes = neighbor_node_

        self_neighbor = neighbor_node[R_ID]
        for neighbor_id, neighbor_info in self_neighbor.items():
            destination_address = (R_HOST, neighbor_info[1])
            udp_socket.sendto(package_encode(package_), destination_address)
        time.sleep(UPDATE_INTERVAL)


def listen_thr_handle():
    global neighbor_node
    server_socket = socket.socket(socket.AF_INET, socket.SOCK_DGRAM)
    server_socket.bind((R_HOST, R_PORT))

    while True:
        data, client_address = server_socket.recvfrom(1024)  # Recv data use udp
        package_ = package_decode(data)

        for fail_node in fail_nodes:
            del neighbor_node.get(R_ID)[fail_node]
        fail_nodes.clear()

        for k, v in package_.nodes.items():
            neighbor_node[k] = v if len(v) != 0 else {}
        for k, v in neighbor_node.items():
            if neighbor_node[k] == {}:
                del neighbor_node[k]

        self_neighbor = neighbor_node.get(R_ID)
        package_r_id = package_.id

        if package_r_id not in send_record or send_record[package_r_id] < package_.timestamp:
            send_record[package_r_id] = package_.timestamp
            [udp_socket.sendto(data, (R_HOST, v[1])) for k, v in self_neighbor.items() if k != package_r_id]

        if R_ID in package_.nodes[package_r_id]:
            new_neighbor_info = (package_.nodes[package_r_id][R_ID][0], package_.port)
            self_neighbor[package_r_id] = new_neighbor_info


def dijkstra(graph, start):
    paths = {node: [] for node in graph}
    priority_queue = [(0, start)]
    dists = {node: float('inf') for node in graph}
    dists[start] = 0

    while priority_queue:
        curr_dist, curr_node = heapq.heappop(priority_queue)

        if curr_dist <= dists[curr_node]:
            for neighbor, cost in graph[curr_node].items():
                distance = curr_dist + cost[0] if isinstance(cost, tuple) else curr_dist + cost

                if distance < dists[neighbor]:
                    paths[neighbor] = paths[curr_node] + [curr_node]
                    dists[neighbor] = distance
                    heapq.heappush(priority_queue, (distance, neighbor))

    return dists, paths


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
    wait_cycle = 3
    while True:
        neighbors = neighbor_node.get(R_ID)
        for node_id, _ in neighbors.items():
            if send_record.get(node_id) is None:
                fail_nodes.append(node_id)
            elif wait_cycle * UPDATE_INTERVAL * 1000 < (int(round(time.time() * 1000)) - send_record.get(node_id)):
                fail_nodes.append(node_id)
        time.sleep(UPDATE_INTERVAL)


if __name__ == '__main__':
    if len(sys.argv) > 3:
        R_ID = sys.argv[1]
        R_PORT = sys.argv[2]
        CONFIG_PATH = sys.argv[3]
    else:
        print("Please enter <router id> <router_port> <config_file>")
    R_PORT = int(R_PORT)

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

    lazy_time_seconds = 20
    time.sleep(lazy_time_seconds)  # lazy start
    find_fail_node_thr.start()