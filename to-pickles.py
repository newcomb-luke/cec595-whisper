import os
import pickle
from datasets import Dataset, Audio
from transformers import pipeline
from transformers import (
    AutomaticSpeechRecognitionPipeline,
    WhisperTimeStampLogitsProcessor,
    WhisperForConditionalGeneration,
    WhisperTokenizer,
    WhisperProcessor,
    WhisperFeatureExtractor
)

class Caption:
    def __init__(self, text: str, start: float, end: float):
        self.text = text
        self.start = start
        self.end = end

    def __repr__(self) -> str:
        return f'''Caption {{
    start: {self.start},
    end: {self.end},
    text: "{self.text}"
}}'''


def vtt_time_to_float(time: str) -> float:
    parts = time.split(':')
    hours = int(parts[0])
    minutes = int(parts[1])
    seconds = float(parts[2])

    return float(hours * 60 * 60) + float(minutes * 60) + seconds


def parse_vtt(path: str) -> list[Caption]:
    with open(path, 'r') as f:
        lines = list([l.strip() for l in f.readlines()])

        times = [0.0, 0.0]
        is_caption = False

        captions = []

        for line in lines:
            if is_caption:

                text = line.strip()

                captions.append(Caption(text, times[0], times[1]))

                is_caption = False
                continue

            if '-->' in line:
                vtt_times = line.split()
                vtt_start = vtt_times[0]
                vtt_end = vtt_times[2]

                times[0] = vtt_time_to_float(vtt_start)
                times[1] = vtt_time_to_float(vtt_end)

                is_caption = True

        return captions

def get_transcripts_from_airport(airport_directory: str):
    print(f'Getting transcript data from: {airport_directory}')
    
    transcripts_directory = os.path.join(airport_directory, 'data', 'transcripts')

    transcript_files = {}

    for file in os.scandir(transcripts_directory):
        name, extension = os.path.splitext(file.name)

        if extension == '.vtt':
            transcript_files[name] = [caption.text for caption in parse_vtt(file.path)]

    return transcript_files

def get_transcripts(data_directory: str):
    transcripts = {}
    
    for directory in os.scandir(data_directory):
        transcripts[directory.name] = get_transcripts_from_airport(directory.path)
    
    return transcripts

def get_audio_from_airport(airport_directory: str):
    print(f'Getting audio data from: {airport_directory}')

    audio_files = {}

    for directory in os.scandir(airport_directory):        
        files = []

        num_files = len(list(os.scandir(directory)))

        for i in range(num_files):
            files.append(os.path.join(directory, f'part-{i + 1}.mp3'))
        
        audio_files[directory.name] = files

    return audio_files

def get_audio(split_data_directory: str):
    audio = {}

    for directory in os.scandir(split_data_directory):
        audio[directory.name] = get_audio_from_airport(directory.path)

    return audio

def join_dicts(transcripts_dict, audio_dict):
    text = []
    audio = []
    
    for airport in transcripts_dict.keys():
        for log in transcripts_dict[airport].keys():
            for caption in transcripts_dict[airport][log]:
                text.append(caption)
            for audio_file in audio_dict[airport][log]:
                audio.append(audio_file)

    return {'text': text, 'audio': audio}

transcripts_directory = '~/data_asr/atc0_comp'
split_data_directory = '~/data_asr/split-data'

model_name = 'openai/whisper-medium'
language = 'English'
task = 'transcribe'

feature_extractor = WhisperFeatureExtractor.from_pretrained(model_name)
tokenizer = WhisperTokenizer.from_pretrained(model_name, language=language, task=task)

transcripts = get_transcripts(transcripts_directory)
audio = get_audio(split_data_directory)
data = join_dicts(transcripts, audio)

dataset = Dataset.from_dict(data).cast_column('audio', Audio(sampling_rate=16000)).filter(lambda e: '(unintelligible)' not in e['text'])

def prepare_dataset_saving(row):
    audio = row['audio']

    row['input_features'] = feature_extractor(audio['array'], sampling_rate=audio['sampling_rate']).input_features[0]

    row['labels'] = tokenizer(row['text']).input_ids

    return dict(row)

print(f'Total: {len(dataset)}')

for i, row in enumerate(dataset):
    prepared_row = prepare_dataset_saving(row)
    print(f'Row: {i}')
    with open(f'~/data_asr/pickled/{i}.pkl', 'wb') as f:
        pickle.dump(prepared_row, f, protocol=pickle.HIGHEST_PROTOCOL)
