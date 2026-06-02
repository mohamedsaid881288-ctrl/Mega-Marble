"""
Utility functions for Mega A.R. GitHub App
"""

import os
import subprocess
import hashlib
import hmac
import json
import logging
from datetime import datetime
from pathlib import Path
from typing import Dict, List, Optional, Tuple

import torch
import librosa
import soundfile as sf

logger = logging.getLogger(__name__)


class AudioProcessor:
    """Handle audio file processing and enhancement"""
    
    @staticmethod
    def validate_audio_file(file_path: str, max_size: int) -> Tuple[bool, str]:
        """
        Validate audio file format and size
        
        Args:
            file_path: Path to audio file
            max_size: Maximum file size in bytes
            
        Returns:
            Tuple of (is_valid, message)
        """
        if not os.path.exists(file_path):
            return False, "File not found"
        
        file_size = os.path.getsize(file_path)
        if file_size > max_size:
            return False, f"File too large. Max: {max_size / (1024*1024):.0f}MB"
        
        _, ext = os.path.splitext(file_path)
        from config import Config
        if ext.lower() not in Config.SUPPORTED_EXTENSIONS:
            return False, f"Unsupported format: {ext}"
        
        return True, "Valid"
    
    @staticmethod
    def enhance_audio(input_path: str, output_path: str) -> bool:
        """
        Enhance audio with voice isolation and noise reduction using FFmpeg
        
        Applies:
        - Highpass filter (200Hz) to remove rumble
        - Speech normalization for balanced levels
        
        Args:
            input_path: Path to input audio
            output_path: Path to output audio
            
        Returns:
            Success status
        """
        try:
            ffmpeg_cmd = [
                "ffmpeg", "-y", "-i", input_path,
                "-af", "highpass=f=200, speechnorm=e=50:r=0.0001:l=1",
                "-ar", "16000", "-ac", "1", output_path
            ]
            
            result = subprocess.run(
                ffmpeg_cmd,
                capture_output=True,
                text=True,
                timeout=300
            )
            
            if result.returncode == 0:
                logger.info(f"Audio enhanced: {output_path}")
                return True
            else:
                logger.error(f"FFmpeg error: {result.stderr}")
                return False
                
        except Exception as e:
            logger.error(f"Audio enhancement failed: {str(e)}")
            return False
    
    @staticmethod
    def get_audio_duration(file_path: str) -> float:
        """Get audio file duration in seconds"""
        try:
            y, sr = librosa.load(file_path, sr=None)
            duration = librosa.get_duration(y=y, sr=sr)
            return duration
        except Exception as e:
            logger.error(f"Could not get duration: {str(e)}")
            return 0.0


class WebhookValidator:
    """Validate GitHub webhook signatures"""
    
    @staticmethod
    def verify_signature(payload: bytes, signature: str, secret: str) -> bool:
        """
        Verify GitHub webhook signature
        
        Args:
            payload: Raw request body
            signature: X-Hub-Signature-256 header value
            secret: Webhook secret
            
        Returns:
            True if signature is valid
        """
        if not signature:
            logger.warning("No signature provided")
            return False
        
        # Signature format: sha256=hexdigest
        if signature.startswith('sha256='):
            hash_alg = 'sha256'
            signature_value = signature[7:]
        else:
            logger.warning("Unknown signature algorithm")
            return False
        
        expected_signature = hmac.new(
            secret.encode(),
            payload,
            hashlib.sha256
        ).hexdigest()
        
        is_valid = hmac.compare_digest(expected_signature, signature_value)
        
        if not is_valid:
            logger.warning("Invalid webhook signature")
        
        return is_valid


class TimeFormatter:
    """Format time values for display"""
    
    @staticmethod
    def seconds_to_mmss(seconds: float) -> str:
        """Convert seconds to MM:SS format"""
        minutes = int(seconds // 60)
        secs = int(seconds % 60)
        return f"{minutes:02d}:{secs:02d}"
    
    @staticmethod
    def seconds_to_hmmss(seconds: float) -> str:
        """Convert seconds to H:MM:SS format"""
        hours = int(seconds // 3600)
        minutes = int((seconds % 3600) // 60)
        secs = int(seconds % 60)
        return f"{hours}:{minutes:02d}:{secs:02d}"


class FileManager:
    """Manage temporary and output files"""
    
    @staticmethod
    def cleanup_temp_files(*file_paths: str) -> None:
        """Remove temporary files"""
        for file_path in file_paths:
            try:
                if os.path.exists(file_path):
                    os.remove(file_path)
                    logger.info(f"Cleaned up: {file_path}")
            except Exception as e:
                logger.error(f"Failed to delete {file_path}: {str(e)}")
    
    @staticmethod
    def ensure_directory(dir_path: str) -> bool:
        """Ensure directory exists"""
        try:
            os.makedirs(dir_path, exist_ok=True)
            return True
        except Exception as e:
            logger.error(f"Failed to create directory {dir_path}: {str(e)}")
            return False
    
    @staticmethod
    def get_safe_filename(filename: str) -> str:
        """
        Convert filename to filesystem-safe format
        
        Args:
            filename: Original filename
            
        Returns:
            Safe filename
        """
        import re
        # Remove special characters
        safe_name = re.sub(r'[^\w\s.-]', '', filename)
        # Replace spaces with underscores
        safe_name = re.sub(r'\s+', '_', safe_name)
        return safe_name


class TranscriptionFormatter:
    """Format transcription results"""
    
    @staticmethod
    def format_for_excel(segments: List[Dict]) -> List[Dict]:
        """
        Format transcription segments for Excel export
        
        Args:
            segments: List of transcription segments
            
        Returns:
            Formatted data for DataFrame
        """
        excel_data = []
        for segment in segments:
            excel_data.append({
                'Start Time': TimeFormatter.seconds_to_mmss(segment.get('start', 0)),
                'End Time': TimeFormatter.seconds_to_mmss(segment.get('end', 0)),
                'Speaker': segment.get('speaker', 'UNKNOWN'),
                'Text': segment.get('text', '').strip()
            })
        return excel_data
    
    @staticmethod
    def format_for_github_comment(segments: List[Dict], 
                                 file_name: str,
                                 quality: str,
                                 duration: float) -> str:
        """
        Format transcription results for GitHub comment
        
        Args:
            segments: List of transcription segments
            file_name: Original audio file name
            quality: Quality level used
            duration: Audio duration in seconds
            
        Returns:
            Formatted markdown comment
        """
        comment = f"""## 🎙️ Mega A.R. Transcription Results

**File:** `{file_name}`  
**Quality:** `{quality}`  
**Duration:** `{TimeFormatter.seconds_to_hmmss(duration)}`  
**Timestamp:** `{datetime.now().strftime('%Y-%m-%d %H:%M:%S')}`

---

### Transcription

| Start | End | Speaker | Text |
|-------|-----|---------|------|
"""
        
        for segment in segments:
            start = TimeFormatter.seconds_to_mmss(segment.get('start', 0))
            end = TimeFormatter.seconds_to_mmss(segment.get('end', 0))
            speaker = segment.get('speaker', 'UNKNOWN')
            text = segment.get('text', '').strip()
            
            # Escape pipe characters in text
            text = text.replace('|', '\\|')
            
            comment += f"| {start} | {end} | {speaker} | {text} |\n"
        
        comment += f"\n---\n*Generated by Mega A.R. v1.0*"
        
        return comment


def setup_logging(log_level: str = 'INFO') -> logging.Logger:
    """Setup logging configuration"""
    logging.basicConfig(
        level=log_level,
        format='%(asctime)s - %(name)s - %(levelname)s - %(message)s'
    )
    return logging.getLogger(__name__)


def cleanup_gpu_memory():
    """Clean up GPU memory"""
    if torch.cuda.is_available():
        torch.cuda.empty_cache()
        logger.info("GPU memory cleaned")