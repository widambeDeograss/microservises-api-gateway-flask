import os
import logging
import requests
from flask import Flask, request, jsonify
from .service_registry import ServiceRegistry


app = Flask(__name__)
registry = ServiceRegistry()

# Configure logging
logging.basicConfig(level=logging.INFO)
logger = logging.getLogger(__name__)

def route_request(service_name, path):
    """
    Route request to an available service instance
    :param service_name: Name of the target service
    :param path: Request path
    :return: Response from the service
    """
    # Discover available service instances
    services = registry.discover_service(service_name)

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
            stripped_path = path if f"/{service_name}/" in request.path else request.path.split(f"/{service_name}/")[-1]
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

@app.route('/users/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/users/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def user_service(path):
    return route_request('users', path)

@app.route('/movies/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/movies/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def movie_service(path):
    return route_request('movies', path)

@app.route('/showtimes/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/showtimes/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def showtime_service(path):
    return route_request('showtimes', path)

@app.route('/bookings/', defaults={'path': ''}, methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
@app.route('/bookings/<path:path>', methods=['GET', 'POST', 'PUT', 'DELETE', 'PATCH'])
def booking_service(path):
    return route_request('bookings', path)

@app.route('/register', methods=['POST'])
def register_service():
    service_data = request.json
    registry.register_service(
        service_name=service_data['name'],
        host=service_data['host'],
        port=service_data['port'],
        metadata=service_data.get('metadata', {})
    )
    return jsonify({"status": "Service registered successfully"}), 201

@app.route('/unregister', methods=['POST'])
def unregister_service():
    service_data = request.json
    registry.deregister_service(service_data['name'], service_data['host'], service_data['port'])
    return jsonify({"status": "Service unregistered successfully"}), 200

if __name__ == '__main__':
    # Register services on startup
    registry.register_service(
        'users',
        os.getenv('USER_SERVICE_HOST', 'localhost'),
        int(os.getenv('USER_SERVICE_PORT', 5000))
    )
    registry.register_service(
        'movies',
        os.getenv('MOVIES_SERVICE_HOST', 'localhost'),
        int(os.getenv('MOVIES_SERVICE_PORT', 5001))
    )
    registry.register_service(
        'showtimes',
        os.getenv('SHOWTIMES_SERVICE_HOST', 'localhost'),
        int(os.getenv('SHOWTIMES_SERVICE_PORT', 5002))
    )
    registry.register_service(
        'bookings',
        os.getenv('BOOKINGS_SERVICE_HOST', 'localhost'),
        int(os.getenv('BOOKINGS_SERVICE_PORT', 5003))
    )

    # Run the API Gateway
    app.run(
        host='0.0.0.0',
        port=int(os.getenv('API_GATEWAY_PORT', 8000))
    )