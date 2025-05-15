import pyttsx3
from pathlib import Path

# Path to existing sentences.txt file
sentences_file = Path("sentences.txt")

# Directory to save audio files
output_dir = Path("output")
output_dir.mkdir(exist_ok=True)

# Read sentences from existing file
sentences = [line.strip() for line in sentences_file.read_text(encoding="utf-8").splitlines() if line.strip()]

# Initialize pyttsx3 engine
engine = pyttsx3.init()

def save_audio(text, output_file):
    engine.save_to_file(text, str(output_file))
    engine.runAndWait()
    print(f"Saved: {output_file}")

# Generate audio for each sentence
for i, sentence in enumerate(sentences, start=1):
    audio_path = output_dir / f"sentence_{i}.wav"
    save_audio(sentence, audio_path)
