"""
Core transcription module for Mega A.R. GitHub App
Handles WhisperX transcription, alignment, and diarization
"""

import os
import logging
import gc
import torch
from typing import Dict, List, Optional
from dataclasses import dataclass

import whisperx
import pandas as pd

from config import Config
from utils import (
    AudioProcessor, FileManager, TimeFormatter,
    TranscriptionFormatter, cleanup_gpu_memory
)

logger = logging.getLogger(__name__)


@dataclass
class TranscriptionResult:
    """Data class for transcription results"""
    segments: List[Dict]
    language: str
    duration: float
    confidence: float
    model_used: str


class TranscriptionPipeline:
    """Manage the complete transcription pipeline"""
    
    def __init__(self, config: Optional[Dict] = None):
        """
        Initialize transcription pipeline
        
        Args:
            config: Configuration override
        """
        self.config = config or self._get_default_config()
        self.models = {}
        self._load_models()
    
    def _get_default_config(self) -> Dict:
        """Get default configuration from Config class"""
        return {
            'device': Config.DEVICE,
            'batch_size': Config.BATCH_SIZE,
            'compute_type': Config.COMPUTE_TYPE,
            'language': Config.LANGUAGE_CODE,
            'initial_prompt': Config.INITIAL_PROMPT,
            'hf_token': Config.HF_TOKEN
        }
    
    def _load_models(self) -> None:
        """Load WhisperX models"""
        try:
            logger.info("Loading WhisperX models...")
            
            # Load ASR model
            model_name = Config.QUALITY_MODELS[Config.DEFAULT_QUALITY]
            self.models['asr'] = whisperx.load_model(
                model_name,
                self.config['device'],
                compute_type=self.config['compute_type'],
                asr_options={
                    "initial_prompt": self.config['initial_prompt'],
                    "language": self.config['language']
                }
            )
            logger.info(f"ASR model loaded: {model_name}")
            
            # Load alignment model
            self.models['align_model'], self.models['metadata'] = whisperx.load_align_model(
                language_code=self.config['language'],
                device=self.config['device']
            )
            logger.info("Alignment model loaded")
            
            # Load diarization model
            self.models['diarize'] = whisperx.DiarizationPipeline(
                use_auth_token=self.config['hf_token'],
                device=self.config['device']
            )
            logger.info("Diarization model loaded")
            
        except Exception as e:
            logger.error(f"Failed to load models: {str(e)}")
            raise
    
    def transcribe(self, audio_path: str, quality: str = 'high') -> Optional[TranscriptionResult]:
        """
        Transcribe audio file with full pipeline
        
        Args:
            audio_path: Path to audio file
            quality: Quality level (low, medium, high, ultra)
            
        Returns:
            TranscriptionResult or None if failed
        """
        try:
            # 1. Load and validate audio
            logger.info(f"Starting transcription: {audio_path}")
            is_valid, msg = AudioProcessor.validate_audio_file(
                audio_path,
                Config.MAX_FILE_SIZE
            )
            
            if not is_valid:
                logger.error(f"Invalid audio file: {msg}")
                return None
            
            # 2. Enhance audio
            enhanced_audio_path = audio_path.replace('.wav', '_enhanced.wav')
            if not AudioProcessor.enhance_audio(audio_path, enhanced_audio_path):
                logger.error("Audio enhancement failed")
                return None
            
            # 3. Load enhanced audio
            audio = whisperx.load_audio(enhanced_audio_path)
            audio_duration = len(audio) / 16000  # Assuming 16kHz sample rate
            logger.info(f"Audio loaded. Duration: {TimeFormatter.seconds_to_hmmss(audio_duration)}")
            
            # 4. Transcribe
            logger.info("Running ASR transcription...")
            asr_result = self.models['asr'].transcribe(
                audio,
                batch_size=self.config['batch_size'],
                language=self.config['language']
            )
            
            # 5. Align
            logger.info("Aligning transcription...")
            aligned_result = whisperx.align(
                asr_result["segments"],
                self.models['align_model'],
                self.models['metadata'],
                audio,
                self.config['device'],
                return_char_alignments=False
            )
            
            # 6. Diarize (speaker identification)
            logger.info("Performing speaker diarization...")
            diarize_segments = self.models['diarize'](audio)
            
            # 7. Assign speakers to segments
            final_result = whisperx.assign_word_speakers(
                diarize_segments,
                aligned_result
            )
            
            # 8. Extract segments
            segments = final_result.get('segments', [])
            logger.info(f"Transcription complete. Segments: {len(segments)}")
            
            # 9. Cleanup
            FileManager.cleanup_temp_files(enhanced_audio_path)
            cleanup_gpu_memory()
            
            # Return result
            return TranscriptionResult(
                segments=segments,
                language=self.config['language'],
                duration=audio_duration,
                confidence=self._calculate_confidence(segments),
                model_used=Config.QUALITY_MODELS[quality]
            )
            
        except Exception as e:
            logger.error(f"Transcription failed: {str(e)}")
            cleanup_gpu_memory()
            return None
    
    @staticmethod
    def _calculate_confidence(segments: List[Dict]) -> float:
        """Calculate average confidence from segments"""
        if not segments:
            return 0.0
        
        confidences = [seg.get('confidence', 0.9) for seg in segments if 'confidence' in seg]
        if confidences:
            return sum(confidences) / len(confidences)
        return 0.9  # Default if no confidence scores available
    
    def export_to_excel(self, segments: List[Dict], output_path: str) -> bool:
        """
        Export transcription to Excel file
        
        Args:
            segments: Transcription segments
            output_path: Path to save Excel file
            
        Returns:
            Success status
        """
        try:
            data = TranscriptionFormatter.format_for_excel(segments)
            df = pd.DataFrame(data)
            df.to_excel(output_path, index=False)
            logger.info(f"Excel file saved: {output_path}")
            return True
        except Exception as e:
            logger.error(f"Failed to export Excel: {str(e)}")
            return False
    
    def cleanup(self) -> None:
        """Cleanup and free memory"""
        try:
            self.models.clear()
            cleanup_gpu_memory()
            gc.collect()
            logger.info("Pipeline cleanup complete")
        except Exception as e:
            logger.error(f"Cleanup error: {str(e)}")


class TranscriptionManager:
    """High-level transcription management"""
    
    def __init__(self):
        self.pipeline = TranscriptionPipeline()
    
    def process_audio_file(self, 
                          audio_path: str,
                          output_dir: str,
                          quality: str = 'high') -> Optional[Dict]:
        """
        Process audio file and generate transcription + Excel
        
        Args:
            audio_path: Path to audio file
            output_dir: Directory to save outputs
            quality: Quality level
            
        Returns:
            Dictionary with results or None
        """
        try:
            # Ensure output directory exists
            FileManager.ensure_directory(output_dir)
            
            # Get base filename
            base_name = os.path.splitext(os.path.basename(audio_path))[0]
            
            # Transcribe
            result = self.pipeline.transcribe(audio_path, quality)
            if not result:
                return None
            
            # Export to Excel
            excel_path = os.path.join(output_dir, f"{base_name}_transcribed.xlsx")
            self.pipeline.export_to_excel(result.segments, excel_path)
            
            # Format for GitHub
            github_comment = TranscriptionFormatter.format_for_github_comment(
                result.segments,
                os.path.basename(audio_path),
                quality,
                result.duration
            )
            
            return {
                'segments': result.segments,
                'excel_path': excel_path,
                'github_comment': github_comment,
                'duration': result.duration,
                'confidence': result.confidence,
                'model': result.model_used
            }
            
        except Exception as e:
            logger.error(f"Process audio file failed: {str(e)}")
            return None