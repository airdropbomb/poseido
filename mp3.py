import pyttsx3

# Initialize TTS engine
engine = pyttsx3.init()

# Get available voices
voices = engine.getProperty('voices')

# === Voice selection ===
# voices[0] -> usually male
# voices[1] -> usually female
# Change the index to choose your preferred voice
engine.setProperty('voice', voices[1].id)  # female voice example

# Speech rate (default ~200, lower = slower, higher = faster)
engine.setProperty('rate', 150)

# Read words from word.txt
with open("word.txt", "r", encoding="utf-8") as f:
    text = f.read()

# Save as MP3
engine.save_to_file(text, "words_voice.mp3")
engine.runAndWait()

print("MP3 file created successfully: words_voice.mp3")
