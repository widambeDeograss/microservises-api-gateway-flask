import os
import etcd3
import json
import time
import logging
from typing import Dict, Any


class ServiceRegistry:
    def __init__(self, host: str = None, port: int = None):
        """
        Initialize etcd client and service registry

        :param host: etcd server host
        :param port: etcd server port
        """
        # Use environment variables or default values
        self.etcd_host = host or os.getenv('ETCD_HOST', 'localhost')
        self.etcd_port = port or int(os.getenv('ETCD_PORT', 2379))

        try:
            self.client = etcd3.client(host=self.etcd_host, port=self.etcd_port)
            logging.basicConfig(level=logging.INFO)
            self.logger = logging.getLogger(__name__)
            self.logger.info(f"Connected to etcd at {self.etcd_host}:{self.etcd_port}")
        except Exception as e:
            logging.error(f"Failed to connect to etcd: {e}")
            raise

    def register_service(self, service_name: str, host: str, port: int, metadata: Dict[str, Any] = None):
        """
        Register a microservice in etcd

        :param service_name: Name of the service
        :param host: Service host
        :param port: Service port
        :param metadata: Additional service metadata
        """
        service_key = f"/services/{service_name}/{host}:{port}"
        service_info = {
            "name": service_name,
            "host": host,
            "port": port,
            "metadata": metadata or {},
            "last_heartbeat": time.time()
        }

        # Store service information with a lease for automatic expiration
        lease = self.client.lease(60)  # 60-second TTL
        self.client.put(service_key, json.dumps(service_info), lease=lease)

        self.logger.info(f"Registered service: {service_name} at {host}:{port}")

    def discover_service(self, service_name: str) -> Dict[str, Any]:
        """
        Discover available instances of a service

        :param service_name: Name of the service to discover
        :return: Dictionary of available service instances
        """
        services = {}
        for result in self.client.get_prefix(f"/services/{service_name}"):
            key = result[1].key.decode('utf-8')
            value = json.loads(result[0].decode('utf-8'))
            services[key] = value

        if not services:
            self.logger.warning(f"No instances found for service: {service_name}")

        return services

    def deregister_service(self, service_name: str, host: str, port: int):
        """
        Remove a service from the registry

        :param service_name: Name of the service
        :param host: Service host
        :param port: Service port
        """
        service_key = f"/services/{service_name}/{host}:{port}"
        self.client.delete(service_key)
        self.logger.info(f"Deregistered service: {service_name} at {host}:{port}")