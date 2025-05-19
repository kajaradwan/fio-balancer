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

1. Create a config.yaml file with your hosts and IP addresses:
```yaml
hosts:
  - host1
  - host2
  - host3
  # Add more hosts as needed

ip_addresses:
  - 10.0.2.64
  - 10.0.2.65
  - 10.0.2.66
  # Add more IP addresses as needed

mount_base: /mnt
```

2. Run with clush:
```bash
clush -w node[1-13] "python3 fio_balancer.py --config config.yaml"
```

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