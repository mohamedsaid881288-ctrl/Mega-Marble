# 🎙️ Mega A.R. - Arabic Audio Transcription System

A powerful GitHub App that transcribes audio files in multiple formats into Arabic with the highest accuracy and multiple quality settings using WhisperX with speaker diarization.

## ✨ Features

- **Multi-Format Support**: MP3, M4A, AMR, WAV, AAC
- **Advanced Arabic Transcription**: WhisperX Large-V3 model optimized for Arabic
- **Speaker Diarization**: Identify and label different speakers automatically
- **Quality Settings**: Low, Medium, High, Ultra modes
- **Alignment Technology**: Precise word-level timing alignment
- **Far-Field Enhancement**: Handles noisy, multi-speaker environments
- **Excel Export**: Organized transcription with timestamps and speakers
- **GitHub Integration**: Seamless PR and Issue integration

## 🚀 Quick Start

### Prerequisites
- Python 3.8+
- CUDA-compatible GPU (recommended)
- FFmpeg installed
- Hugging Face API token (for diarization)

### Installation

```bash
git clone https://github.com/mohamedsaid881288-ctrl/Mega-Marble.git
cd Mega-Marble
pip install -r requirements.txt
```

### Configuration

Create a `.env` file:
```
GITHUB_APP_ID=your_app_id
GITHUB_PRIVATE_KEY=your_private_key
WEBHOOK_SECRET=mega_ar_webhook_secret_2024
HF_TOKEN=hf_your_hugging_face_token
DEVICE=cuda
BATCH_SIZE=4
COMPUTE_TYPE=float16
```

### Run the Application

```bash
python app.py
```

## 📋 How It Works

1. **Audio Upload**: Users add audio files to GitHub Issues/PRs
2. **Webhook Trigger**: App receives GitHub event
3. **Audio Processing**: FFmpeg enhances audio with voice isolation
4. **Transcription**: WhisperX transcribes with Arabic language model
5. **Alignment**: Word-level timing alignment
6. **Diarization**: Speaker identification and labeling
7. **Export**: Results exported to Excel with timestamps
8. **Post Results**: Comment posted to GitHub with results

## 🎚️ Quality Settings

| Setting | Speed | Accuracy | Model | Use Case |
|---------|-------|----------|-------|----------|
| Low | Very Fast | 85% | base | Quick reviews |
| Medium | Fast | 92% | small | Daily use |
| High | Normal | 96% | medium | Production |
| Ultra | Slow | 99% | large-v3 | Critical content |

## 📊 Supported Arabic Dialects

- Modern Standard Arabic (MSA)
- Egyptian Arabic
- Levantine Arabic
- Gulf Arabic
- Moroccan Arabic
- Saudi Arabic

## 🔧 API Endpoints

- `POST /webhook` - GitHub webhook handler
- `POST /api/transcribe` - Manual transcription
- `GET /api/status/{file_id}` - Check transcription status
- `GET /api/formats` - Supported audio formats

## 💻 Technology Stack

- **WhisperX**: Advanced speech recognition
- **Pyannote.audio**: Speaker diarization
- **FFmpeg**: Audio processing & enhancement
- **PyGithub**: GitHub API integration
- **Pandas**: Data organization
- **Torch**: Deep learning backend

## 📝 Usage Examples

### In GitHub Issues/PRs

```
@mega-ar transcribe audio.wav quality:high
```

### Automatic Processing
Simply attach an audio file and the app will automatically:
1. Download the audio
2. Enhance and process it
3. Transcribe with speaker labels
4. Post results as a comment

## 🎯 Sample Output

```
| Start Time | End Time | Speaker | Text |
|-----------|----------|---------|------|
| 00:00 | 00:05 | SPEAKER_00 | السلام عليكم ورحمة الله وبركاته |
| 00:05 | 00:12 | SPEAKER_01 | وعليكم السلام ورحمة الله وبركاته |
| 00:12 | 00:20 | SPEAKER_00 | كيف حالك اليوم؟ |
```

## 🔐 Security

- Webhook signature verification
- GitHub App authentication
- Secure token storage
- File cleanup after processing

## 📄 License

MIT License - See LICENSE file

## 🤝 Contributing

Contributions welcome! Please submit PRs with:
- Clear description of changes
- Test cases
- Updated documentation

## 📞 Support

Create an issue for bugs, feature requests, or questions.

---

**Crafted with ❤️ for the Arabic community | Mega A.R. v1.0**