# import assemblyai as aai





# aai.settings.api_key = "1ddb585475224ff8b3ec00d230c12373"
# transcriber = aai.Transcriber()

# transcript = transcriber.transcribe("NHC_conversation.mp3")
# # transcript = transcriber.transcribe("./my-local-audio-file.wav")

# print(transcript.text)



# import streamlit as st
# import assemblyai as aai

# # Set the AssemblyAI API key
# aai.settings.api_key = "1ddb585475224ff8b3ec00d230c12373"
# transcriber = aai.Transcriber()

# st.title("Live Audio Transcription")

# uploaded_file = st.file_uploader("Upload an audio file (.mp3, .wav)", type=["mp3", "wav"])

# if uploaded_file is not None:
#     st.audio(uploaded_file, format='audio/ogg', start_time=0)
#     st.write("Transcription:")

#     # Transcribe the entire file
#     transcript = transcriber.transcribe(uploaded_file)
#     st.write(transcript.text)
import openai
import speech_recognition as sr
import pyttsx3
import os
from dotenv import load_dotenv
import json
from pydub import AudioSegment

# Load environment variables from .env file
load_dotenv()

# File containing the assistant's personality description
personality = "p.txt"

# Use Whisper for speech recognition
usewhisper = True

# Get the OpenAI API key from environment variables
key = os.getenv('OPENAI_API_KEY')

# Set up OpenAI API key
openai.api_key = key

# Load the assistant's personality from the file
with open(personality, "r") as file:
    mode = file.read()
messages = [{"role": "system", "content": f"{mode}"}]

# pyttsx3 setup with error handling
try:
    engine = pyttsx3.init()
    voices = engine.getProperty('voices')
    engine.setProperty('voice', voices[1].id)  # 0 for male, 1 for female
except Exception as e:
    print(f"Error initializing pyttsx3: {e}")
    engine = None

# Speech recognition setup
r = sr.Recognizer()
mic = sr.Microphone(device_index=0)
r.dynamic_energy_threshold = False
r.energy_threshold = 400

# Function to transcribe audio using Whisper
def whisper(audio):
    audio_file_path = 'speech.wav'
    # Convert audio to WAV using pydub
    sound = AudioSegment.from_file_using_temporary_files(audio)
    sound.export(audio_file_path, format="wav")
    
    with open(audio_file_path, 'rb') as speech:
        wcompletion = openai.Audio.transcribe(
            model="whisper-1",
            file=speech
        )
    user_input = wcompletion['text']
    print(user_input)
    return user_input

# Function to save conversation to a file
def save_conversation(save_foldername):
    os.makedirs(save_foldername, exist_ok=True)
    base_filename = 'conversation'
    suffix = 0
    filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.txt')

    while os.path.exists(filename):
        suffix += 1
        filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.txt')

    with open(filename, 'w') as file:
        json.dump(messages, file, indent=4)

    return suffix

# Function to save in-progress conversation to a file
def save_inprogress(suffix, save_foldername):
    os.makedirs(save_foldername, exist_ok=True)
    base_filename = 'conversation'
    filename = os.path.join(save_foldername, f'{base_filename}_{suffix}.txt')

    with open(filename, 'w') as file:
        json.dump(messages, file, indent=4)

# Get the script's directory and set up folder paths
script_dir = os.path.dirname(os.path.abspath(__file__))
foldername = "voice_assistant"
save_foldername = os.path.join(script_dir, f"conversations/{foldername}")
suffix = save_conversation(save_foldername)

# Main loop for the conversation
while True:
    with mic as source:
        print("\nListening...")
        r.adjust_for_ambient_noise(source, duration=0.5)
        try:
            audio = r.listen(source)
        except Exception as e:
            print(f"Error capturing audio: {e}")
            continue

        try:
            if usewhisper:
                user_input = whisper(audio)
            else:
                user_input = r.recognize_google(audio)
        except sr.UnknownValueError:
            print("Google Speech Recognition could not understand audio")
            continue
        except sr.RequestError as e:
            print(f"Could not request results from Google Speech Recognition service; {e}")
            continue
        except Exception as e:
            print(f"Unexpected error: {e}")
            continue

    messages.append({"role": "user", "content": user_input})

    completion = openai.ChatCompletion.create(
        model="gpt-3.5-turbo-0301",
        messages=messages,
        temperature=0.8
    )    

    response = completion.choices[0].message.content
    messages.append({"role": "assistant", "content": response})
    print(f"\n{response}\n")
    save_inprogress(suffix, save_foldername)
    
    if engine:
        engine.say(response)
        engine.runAndWait()
