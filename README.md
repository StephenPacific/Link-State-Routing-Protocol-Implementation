# Link-State-Routing-Protocol-Implementation

This project implements the **Link State Routing Protocol (LSR)** in Python, based on the UNSW COMP3331/9331 Computer Networks and Applications assignment specifications.

## Overview

* Simulates routers exchanging **link-state packets** over UDP.
* Builds a **global network topology** from received packets.
* Uses **Dijkstra’s algorithm** to compute least-cost paths.
* Periodically updates and broadcasts topology information.
* Detects and handles **node failures** (heartbeat mechanism).
* Restricts unnecessary link-state broadcasts.

## Folder Structure

```
project_root/ASS
├── Lsr.py                  # Main program (entry point)
├── utils/                  # Helper functions and modules
├── configs/                # Example configuration files
└── README.md
```

## Requirements

* Python **3.8+**
* Linux environment (tested on CSE lab machines)
* Only Python standard library (no external dependencies)

## Running the Program

### 1. Prepare configuration files

Each router has its own config file (e.g., `configA.txt`):

```
<number_of_neighbours>
<NEIGHBOUR_ID> <LINK_COST> <NEIGHBOUR_PORT>
```

Example `configA.txt`:

```
2
B 6.5 5001
C 2.2 5002
```

### 2. Start routers

Open one terminal per router and run:

```bash
python3 Lsr.py A 5000 configs/configA.txt
python3 Lsr.py B 5001 configs/configB.txt
python3 Lsr.py C 5002 configs/configC.txt
```

### 3. View output

After `ROUTE_UPDATE_INTERVAL` seconds (default **30s**), each router prints:

```
I am Router A
Least cost path to router C: AC and the cost is 2.2
Least cost path to router B: AB and the cost is 6.5
```

### 4. Simulate node failures

* Stop a router with `CTRL+C`.
* After \~60s (two route update intervals), other routers will exclude the failed node from their paths.

## Notes

* The configuration files used for actual testing are **private**.
* The code runs all routers on a single machine, each listening on a different UDP port.
