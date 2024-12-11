import os
import etcd3
import json
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
            logging.basicConfig(level=logging.INFO,
                                format="%(asctime)s - %(name)s - %(levelname)s - %(message)s")
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

        try:
            self.client.put(service_key, json.dumps(service_info))
            self.logger.info(f"Registered service: {service_name} at {host}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to register service {service_name}: {e}")
            raise

    def discover_service(self, service_name: str) -> Dict[str, Any]:
        """
        Discover available instances of a service

        :param service_name: Name of the service to discover
        :return: Dictionary of available service instances
        """
        services = {}

        try:
            for result in self.client.get_prefix(f"/services/{service_name}"):
                key = result[1].key.decode('utf-8')
                value = json.loads(result[0].decode('utf-8'))
                services[key] = value

            if not services:
                self.logger.warning(f"No instances found for service: {service_name}")

            return services
        except Exception as e:
            self.logger.error(f"Failed to discover service {service_name}: {e}")
            raise

    def deregister_service(self, service_name: str, host: str, port: int):
        """
        Remove a service from the registry

        :param service_name: Name of the service
        :param host: Service host
        :param port: Service port
        """
        service_key = f"/services/{service_name}/{host}:{port}"

        try:
            self.client.delete(service_key)
            self.logger.info(f"Deregistered service: {service_name} at {host}:{port}")
        except Exception as e:
            self.logger.error(f"Failed to deregister service {service_name}: {e}")
            raise

    def list_all_services(self) -> Dict[str, Any]:
        """
        List all registered services in the registry

        :return: Dictionary of all services and their instances
        """
        services = {}

        try:
            for result in self.client.get_prefix("/services/"):
                key = result[1].key.decode('utf-8')
                value = json.loads(result[0].decode('utf-8'))
                services[key] = value

            return services
        except Exception as e:
            self.logger.error("Failed to list all services: {e}")
            raise

    def shutdown(self):
        """
        Gracefully shut down the service registry client
        """
        try:
            self.client.close()
            self.logger.info("Service registry client shut down")
        except Exception as e:
            self.logger.error(f"Failed to shut down the service registry client: {e}")
            raise


