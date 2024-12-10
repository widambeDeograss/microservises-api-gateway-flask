import os
import logging
import requests
from flask import Flask, request, jsonify
from service_registry import ServiceRegistry

app = Flask(__name__)
service_registry = ServiceRegistry()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)


def route_request(service_name):
    """
    Route request to an available service instance
    :param service_name: Name of the target service
    :return: Response from the service
    """
    # Discover available service instances
    services = service_registry.discover_service(service_name)

    if not services:
        logger.warning(f"No services available for {service_name}")
        return jsonify({
            "status": "error",
            "message": f"No {service_name} services available",
            "available_services": list(services.keys()) if services else []
        }), 503

    # More robust load balancing with multiple attempts
    attempts = 3
    for _ in range(attempts):
        try:
            # Random service selection
            service_info = list(services.values())[0]
            service_url = f"http://{service_info['host']}:{service_info['port']}"

            # Preserve the original request path
            stripped_path = request.path.split(f"/{service_name}/")[-1] if f"/{service_name}/" in request.path else ""
            target_url = f"{service_url}/{stripped_path}".rstrip('/')

            logger.info(f"Routing request to: {target_url}")

            # Forward the request
            response = requests.request(
                method=request.method,
                url=target_url,
                headers={k: v for k, v in request.headers if k.lower() not in ['host', 'content-length']},
                data=request.get_data(),
                params=request.args,
                timeout=5  # Add timeout to prevent hanging
            )

            # Return the response from the service
            return (
                response.content,
                response.status_code,
                response.headers.items()
            )

        except requests.RequestException as e:
            logger.error(f"Service request failed: {e}")
            # Continue to next service if available
            continue

    # If all services fail
    return jsonify({
        "status": "error",
        "message": f"All {service_name} service instances are unavailable",
        "available_services": list(services.keys())
    }), 503


@app.route('/user-service/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/user-service/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def user_service(path):
    return route_request('user-service')


@app.route('/loan-service/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/loan-service/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def loan_service(path):
    return route_request('loan-service')


@app.route('/register', methods=['POST'])
def register_service():
    service_data = request.json
    service_registry.register_service(
        service_name=service_data['name'],
        host=service_data['host'],
        port=service_data['port'],
        metadata=service_data.get('metadata', {})
    )
    return jsonify({"status": "Service registered successfully"}), 201


@app.route('/unregister', methods=['POST'])
def unregister_service():
    service_data = request.json
    service_registry.deregister_service(service_data['name'], service_data['host'], service_data['port'])
    return jsonify({"status": "Service unregistered successfully"}), 200


if __name__ == '__main__':
    # Register services on startup
    service_registry.register_service(
        'user-service',
        os.getenv('USER_SERVICE_HOST', 'localhost'),
        int(os.getenv('USER_SERVICE_PORT', 8001))
    )
    service_registry.register_service(
        'loan-service',
        os.getenv('LOAN_SERVICE_HOST', 'localhost'),
        int(os.getenv('LOAN_SERVICE_PORT', 8002))
    )

    # Run the API Gateway
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('API_GATEWAY_PORT', 8000))
    )