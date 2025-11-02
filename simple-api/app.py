from flask import Flask, jsonify, request
import os
import logging
import sys

# Configure logging
logging.basicConfig(
    level=logging.INFO,
    format='%(asctime)s - %(name)s - %(levelname)s - %(message)s',
    handlers=[
        logging.StreamHandler(sys.stdout)
    ]
)

app = Flask(__name__)
logger = logging.getLogger(__name__)

@app.route('/')
def hello():
    """Root endpoint - returns a welcome message"""
    logger.info("Root endpoint accessed")
    return jsonify({
        'message': 'Welcome to Simple API!',
        'version': '1.0',
        'endpoints': ['/health', '/info', '/echo']
    })

@app.route('/health')
def health():
    """Health check endpoint"""
    logger.info("Health check endpoint accessed")
    return jsonify({'status': 'healthy'}), 200

@app.route('/info')
def info():
    """Returns application information"""
    logger.info("Info endpoint accessed")
    return jsonify({
        'app': 'simple-api',
        'version': '1.0',
        'environment': os.getenv('ENVIRONMENT', 'development'),
        'port': os.getenv('PORT', '8080')
    })

@app.route('/echo', methods=['GET', 'POST'])
def echo():
    """Echo endpoint - returns the request data"""
    logger.info(f"Echo endpoint accessed with method: {request.method}")
    if request.method == 'POST':
        return jsonify({
            'method': 'POST',
            'data': request.get_json() if request.is_json else request.form.to_dict(),
            'headers': dict(request.headers)
        })
    else:
        return jsonify({
            'method': 'GET',
            'args': request.args.to_dict(),
            'headers': dict(request.headers)
        })

if __name__ == '__main__':
    port = int(os.getenv('PORT', 8080))
    logger.info(f"Starting Flask app on 0.0.0.0:{port}")
    app.run(host='0.0.0.0', port=port)
