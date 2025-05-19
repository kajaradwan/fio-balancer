# FIO Balancer

A Python script for distributing FIO workloads across multiple hosts and mount points. The script is designed to work with clush for parallel execution across multiple nodes.

## Features

- Distributes FIO workloads across multiple hosts
- Automatically mounts and unmounts NFS shares
- Creates separate directories for each host in each share
- Configurable number of threads and I/O parameters
- Works with clush for parallel execution

## Requirements

- Python 3.x
- FIO
- NFS client
- clush (for parallel execution)

## Installation

1. Clone the repository:
```bash
git clone https://github.com/kajaradwan/fio-balancer.git
cd fio-balancer
```

2. Install Python dependencies:
```bash
pip install -r requirements.txt
```

## Usage

1. Create a `config.yaml` file with your configuration:
```yaml
hosts:
  - node1
  - node2
  # ... add all your nodes
ip_addresses:
  - 192.168.1.1
  - 192.168.1.2
  # ... add all your IPs
mount_base: /mnt
```

2. Run the script using `clush` to distribute across all nodes:
```bash
clush -w node[1-13] python3 fio_balancer.py --config config.yaml
```

3. Run on a single node with default thread count (8192):
```bash
python3 fio_balancer.py --hosts node1 --ips 192.168.1.1 192.168.1.2 192.168.1.3 192.168.1.4 192.168.1.5 192.168.1.6 192.168.1.7 192.168.1.8
```

4. Run on a single node with reduced thread count (e.g., 1024 threads):
```bash
python3 fio_balancer.py --hosts node1 --ips 192.168.1.1 192.168.1.2 192.168.1.3 192.168.1.4 192.168.1.5 192.168.1.6 192.168.1.7 192.168.1.8 --total-threads 1024
```

Note: When running on a single node, you need to provide all 8 IP addresses for that node. The script will automatically mount the appropriate share (mount1 through mount8) for each IP.

## Configuration

The script uses the following FIO parameters:
- Block size: 2MB
- I/O depth: 16
- Threads per mount point: 79
- Runtime: 60 seconds
- Direct I/O: enabled
- NUMA memory policy: local

## License

MIT License 
MIT License 