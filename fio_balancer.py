#!/usr/bin/env python3

import argparse
import json
import os
import subprocess
from typing import List, Dict
import yaml
import socket

class FioBalancer:
    def __init__(self, hosts: List[str], ip_addresses: List[str], mount_base: str = "/mnt", total_threads: int = 8192):
        self.hosts = hosts
        self.ip_addresses = ip_addresses
        self.mount_base = mount_base
        self.shares = [f"mount{i}" for i in range(1, 9)]
        self.mounted_points = set()
        
        # Get current hostname
        self.current_host = socket.gethostname()
        
        # Calculate which IPs belong to this host
        self.host_ips = self._get_host_ips()

        self.total_threads = total_threads

    def _get_host_ips(self) -> List[str]:
        """Get the IPs that belong to the current host."""
        # Calculate how many IPs per host (8)
        ips_per_host = 8
        
        # Find this host's index
        try:
            host_index = self.hosts.index(self.current_host)
        except ValueError:
            print(f"Error: Current host {self.current_host} not found in host list")
            return []
        
        # Get the IPs for this host
        start_idx = host_index * ips_per_host
        return self.ip_addresses[start_idx:start_idx + ips_per_host]

    def _mount_point(self, ip: str, share: str) -> bool:
        """Mount a single IP address with a specific share."""
        mount_point = os.path.join(self.mount_base, ip)
        
        # Create mount point if it doesn't exist
        os.makedirs(mount_point, exist_ok=True)
        
        # Check if already mounted
        if os.path.ismount(mount_point):
            print(f"Mount point {mount_point} is already mounted")
            return True
            
        # Mount the IP with specific share
        cmd = f"mount -t nfs {ip}:/{share} {mount_point}"
        try:
            subprocess.run(cmd, shell=True, check=True)
            self.mounted_points.add(mount_point)
            print(f"Successfully mounted {ip}:/{share} at {mount_point}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error mounting {ip}:/{share} at {mount_point}: {e}")
            return False

    def _unmount_point(self, mount_point: str) -> bool:
        """Unmount a single mount point."""
        if not os.path.ismount(mount_point):
            print(f"Mount point {mount_point} is not mounted")
            return True
            
        try:
            subprocess.run(f"umount {mount_point}", shell=True, check=True)
            self.mounted_points.remove(mount_point)
            print(f"Successfully unmounted {mount_point}")
            return True
        except subprocess.CalledProcessError as e:
            print(f"Error unmounting {mount_point}: {e}")
            return False

    def _mount_all(self) -> bool:
        """Mount all IPs for this host."""
        success = True
        for i, ip in enumerate(self.host_ips):
            # Use the corresponding share for this IP (mount1 through mount8)
            share = self.shares[i]
            if not self._mount_point(ip, share):
                success = False
        return success

    def _unmount_all(self) -> bool:
        """Unmount all IPs for this host."""
        success = True
        for ip in self.host_ips:
            mount_point = os.path.join(self.mount_base, ip)
            if not self._unmount_point(mount_point):
                success = False
        return success

    def _generate_fio_config(self, mount_point: str) -> str:
        """Generate FIO configuration for a specific mount point."""
        # Create the output directory structure
        output_dir = os.path.join(mount_point, "fio", self.current_host)
        os.makedirs(output_dir, exist_ok=True)

        # Calculate threads per mount point to achieve ~8192 total threads
        # 8192 threads / 13 hosts / 8 mount points = ~79 threads per mount point
        threads_per_mount = 79

        config = {
            "global": {
                "ioengine": "libaio",
                "direct": 1,
                "size": "1g",
                "runtime": 60,
                "time_based": 1,
                "group_reporting": 1,
                "numa_mem_policy": "local",
                "numjobs": threads_per_mount,
                "iodepth": 16,
                "bs": "2m"
            },
            "jobs": [
                {
                    "name": "testSequentialReads",
                    "rw": "randread",
                    "opendir": output_dir
                },
                {
                    "name": "testSequentialWrites",
                    "rw": "randwrite",
                    "opendir": output_dir
                }
            ]
        }
        return json.dumps(config, indent=2)

    def run(self):
        """Run FIO tests for this host's IPs."""
        print(f"Running on host {self.current_host}")
        print(f"Assigned IPs: {self.host_ips}")
        
        # Mount all IPs for this host
        if not self._mount_all():
            print(f"Failed to mount all IPs for {self.current_host}")
            return

        try:
            for ip in self.host_ips:
                mount_point = os.path.join(self.mount_base, ip)
                config = self._generate_fio_config(mount_point)
                
                # Create config file
                config_file = f"/tmp/fio_config_{ip}.json"
                with open(config_file, 'w') as f:
                    f.write(config)
                
                # Run FIO
                cmd = f"fio {config_file}"
                try:
                    subprocess.run(cmd, shell=True, check=True)
                except subprocess.CalledProcessError as e:
                    print(f"Error running FIO on {self.current_host} for {ip}: {e}")
                finally:
                    os.remove(config_file)
        finally:
            # Unmount all IPs for this host
            self._unmount_all()

def main():
    parser = argparse.ArgumentParser(description='Run FIO tests on this host')
    parser.add_argument('--hosts', nargs='+', required=True, help='List of all hostnames')
    parser.add_argument('--ips', nargs='+', required=True, help='List of all IP addresses')
    parser.add_argument('--mount-base', default='/mnt', help='Base mount point directory')
    parser.add_argument('--total-threads', type=int, default=8192, help='Total number of threads to distribute (default: 8192)')
    parser.add_argument('--config', help='YAML configuration file (alternative to command line arguments)')
    
    args = parser.parse_args()
    
    if args.config:
        with open(args.config, 'r') as f:
            config = yaml.safe_load(f)
            hosts = config['hosts']
            ips = config['ip_addresses']
            mount_base = config.get('mount_base', '/mnt')
    else:
        hosts = args.hosts
        ips = args.ips
        mount_base = args.mount_base

    balancer = FioBalancer(
        hosts=hosts,
        ip_addresses=ips,
        mount_base=mount_base,
        total_threads=args.total_threads
    )
    balancer.run()

if __name__ == '__main__':
    main() 