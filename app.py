"""
Mega A.R. - Arabic Audio Transcription System
Main Flask application
"""

import os
import logging
import json
from datetime import datetime

from flask import Flask, request, jsonify
from dotenv import load_dotenv

from config import Config, get_config
from utils import setup_logging
from webhook_handler import GithubWebhookHandler

# Load environment variables
load_dotenv()

# Setup logging
logger = setup_logging(Config.LOG_LEVEL)

# Create Flask app
app = Flask(__name__)
app.config.from_object(get_config())

# Create directories
Config.create_directories()

# Initialize webhook handler
webhook_handler = GithubWebhookHandler(
    private_key=Config.GITHUB_PRIVATE_KEY,
    app_id=Config.GITHUB_APP_ID
)

logger.info("Mega A.R. GitHub App initialized")


# ============================================================================
# Health Check Endpoints
# ============================================================================

@app.route('/health', methods=['GET'])
def health_check():
    """Health check endpoint"""
    return jsonify({
        'status': 'healthy',
        'app': 'Mega A.R.',
        'timestamp': datetime.now().isoformat()
    }), 200


@app.route('/api/status', methods=['GET'])
def status():
    """Get application status"""
    return jsonify({
        'status': 'running',
        'name': 'Mega A.R. - Arabic Audio Transcription System',
        'version': '1.0.0',
        'device': Config.DEVICE,
        'default_quality': Config.DEFAULT_QUALITY,
        'supported_formats': list(Config.SUPPORTED_EXTENSIONS)
    }), 200


# ============================================================================
# Webhook Endpoint
# ============================================================================

@app.route('/webhook', methods=['POST'])
def github_webhook():
    """
    GitHub webhook endpoint
    
    Expects:
    - X-Hub-Signature-256: SHA256 signature
    - X-GitHub-Event: Event type
    """
    try:
        # Get signature
        signature = request.headers.get('X-Hub-Signature-256', '')
        
        # Get event type
        event_type = request.headers.get('X-GitHub-Event', 'unknown')
        
        # Get raw payload
        payload = request.get_data()
        
        # Validate signature
        if not GithubWebhookHandler.validate_webhook(
            payload,
            signature,
            Config.WEBHOOK_SECRET
        ):
            logger.warning("Invalid webhook signature")
            return jsonify({'error': 'Invalid signature'}), 401
        
        # Parse JSON payload
        payload_json = json.loads(payload)
        
        # Handle webhook
        success, message = webhook_handler.handle_webhook(event_type, payload_json)
        
        response = {
            'success': success,
            'event': event_type,
            'message': message,
            'timestamp': datetime.now().isoformat()
        }
        
        status_code = 200 if success else 400
        return jsonify(response), status_code
        
    except json.JSONDecodeError:
        logger.error("Invalid JSON in webhook payload")
        return jsonify({'error': 'Invalid JSON'}), 400
    except Exception as e:
        logger.error(f"Webhook error: {str(e)}")
        return jsonify({'error': str(e)}), 500


# ============================================================================
# API Endpoints
# ============================================================================

@app.route('/api/formats', methods=['GET'])
def get_supported_formats():
    """Get list of supported audio formats"""
    return jsonify({
        'formats': list(Config.SUPPORTED_EXTENSIONS),
        'max_file_size_mb': Config.MAX_FILE_SIZE / (1024 * 1024)
    }), 200


@app.route('/api/quality-levels', methods=['GET'])
def get_quality_levels():
    """Get available quality levels and settings"""
    quality_info = {
        'default': Config.DEFAULT_QUALITY,
        'available': {
            'low': {
                'model': Config.QUALITY_MODELS['low'],
                'speed': 'Very Fast',
                'accuracy': '85%',
                'use_case': 'Quick reviews'
            },
            'medium': {
                'model': Config.QUALITY_MODELS['medium'],
                'speed': 'Fast',
                'accuracy': '92%',
                'use_case': 'Daily use'
            },
            'high': {
                'model': Config.QUALITY_MODELS['high'],
                'speed': 'Normal',
                'accuracy': '96%',
                'use_case': 'Production'
            },
            'ultra': {
                'model': Config.QUALITY_MODELS['ultra'],
                'speed': 'Slow',
                'accuracy': '99%',
                'use_case': 'Critical content'
            }
        }
    }
    return jsonify(quality_info), 200


@app.route('/api/supported-languages', methods=['GET'])
def get_supported_languages():
    """Get supported languages and dialects"""
    languages = {
        'primary': 'ar',
        'dialects': [
            'Modern Standard Arabic (MSA)',
            'Egyptian Arabic',
            'Levantine Arabic',
            'Gulf Arabic',
            'Moroccan Arabic',
            'Saudi Arabic'
        ]
    }
    return jsonify(languages), 200


# ============================================================================
# Error Handlers
# ============================================================================

@app.errorhandler(404)
def not_found(error):
    """Handle 404 errors"""
    return jsonify({'error': 'Endpoint not found'}), 404


@app.errorhandler(500)
def internal_error(error):
    """Handle 500 errors"""
    logger.error(f"Internal server error: {str(error)}")
    return jsonify({'error': 'Internal server error'}), 500


# ============================================================================
# Startup and Shutdown
# ============================================================================

@app.before_request
def before_request():
    """Log incoming requests"""
    logger.debug(f"{request.method} {request.path}")


@app.after_request
def after_request(response):
    """Log response"""
    logger.debug(f"Response: {response.status_code}")
    return response


# ============================================================================
# Main
# ============================================================================

if __name__ == '__main__':
    logger.info(f"Starting Mega A.R. on {Config.HOST}:{Config.PORT}")
    logger.info(f"Debug: {Config.DEBUG}")
    logger.info(f"Device: {Config.DEVICE}")
    
    app.run(
        host=Config.HOST,
        port=Config.PORT,
        debug=Config.DEBUG,
        use_reloader=False
    )