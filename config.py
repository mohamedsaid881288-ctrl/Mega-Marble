"""
Configuration Management for Mega A.R. GitHub App
"""

import os
from dotenv import load_dotenv

load_dotenv()

class Config:
    """Base configuration"""
    
    # GitHub App Configuration
    GITHUB_APP_ID = os.getenv('GITHUB_APP_ID')
    GITHUB_PRIVATE_KEY = os.getenv('GITHUB_PRIVATE_KEY')
    WEBHOOK_SECRET = os.getenv('WEBHOOK_SECRET', 'mega_ar_webhook_secret_2024')
    
    # Hugging Face Token
    HF_TOKEN = os.getenv('HF_TOKEN')
    
    # Transcription Settings
    DEVICE = os.getenv('DEVICE', 'cuda')
    BATCH_SIZE = int(os.getenv('BATCH_SIZE', 4))
    COMPUTE_TYPE = os.getenv('COMPUTE_TYPE', 'float16')
    LANGUAGE_CODE = os.getenv('LANGUAGE_CODE', 'ar')
    
    # Quality Settings
    DEFAULT_QUALITY = os.getenv('DEFAULT_QUALITY', 'high')
    QUALITY_MODELS = {
        'low': os.getenv('LOW_QUALITY_MODEL', 'base'),
        'medium': os.getenv('MEDIUM_QUALITY_MODEL', 'small'),
        'high': os.getenv('HIGH_QUALITY_MODEL', 'medium'),
        'ultra': os.getenv('ULTRA_QUALITY_MODEL', 'large-v3')
    }
    
    # Server Configuration
    HOST = os.getenv('HOST', '0.0.0.0')
    PORT = int(os.getenv('PORT', 5000))
    DEBUG = os.getenv('DEBUG', 'False').lower() == 'true'
    
    # File Settings
    MAX_FILE_SIZE = int(os.getenv('MAX_FILE_SIZE', 500)) * 1024 * 1024  # Convert to bytes
    TEMP_DIR = os.getenv('TEMP_DIR', '/tmp/mega_ar')
    OUTPUT_DIR = os.getenv('OUTPUT_DIR', './transcriptions')
    SUPPORTED_EXTENSIONS = ('.mp3', '.m4a', '.amr', '.wav', '.aac', '.flac', '.ogg')
    
    # Initial Prompt for Arabic Context
    INITIAL_PROMPT = os.getenv(
        'INITIAL_PROMPT',
        'يا جماعة، موافقون، اعتراض، النصاب القانوني، ميزانية، محضر الجلسة، تصويت، العضو، رئيس مجلس الإدارة'
    )
    
    # Logging
    LOG_LEVEL = os.getenv('LOG_LEVEL', 'INFO')
    
    @staticmethod
    def create_directories():
        """Create necessary directories"""
        os.makedirs(Config.TEMP_DIR, exist_ok=True)
        os.makedirs(Config.OUTPUT_DIR, exist_ok=True)


class DevelopmentConfig(Config):
    """Development configuration"""
    DEBUG = True
    LOG_LEVEL = 'DEBUG'


class ProductionConfig(Config):
    """Production configuration"""
    DEBUG = False
    LOG_LEVEL = 'INFO'


class TestingConfig(Config):
    """Testing configuration"""
    TESTING = True
    DEBUG = True
    DEVICE = 'cpu'


def get_config():
    """Get configuration based on environment"""
    env = os.getenv('FLASK_ENV', 'production')
    
    if env == 'development':
        return DevelopmentConfig
    elif env == 'testing':
        return TestingConfig
    else:
        return ProductionConfig