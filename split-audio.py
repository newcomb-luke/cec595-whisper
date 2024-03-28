import sys
import os
from pydub import AudioSegment


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


def main():
    if len(sys.argv) > 1:
        base_path = sys.argv[1]

        audio_path = os.path.join(base_path, 'audio')
        transcripts_path = os.path.join(base_path, 'transcripts')

        audio_files = []
        transcript_files = []

        for file in os.scandir(audio_path):
            _, extension = os.path.splitext(file.name)

            if extension == '.wav':
                audio_files.append(file.path)

        for file in os.scandir(transcripts_path):
            _, extension = os.path.splitext(file.name)

            if extension == '.vtt':
                transcript_files.append(file.path)

        if len(transcript_files) == 0:
            print('Please run the transcripts-to-vtt.py file before this script')
            return
        
        matches = {}

        for file in audio_files:
            name, _ = os.path.splitext(os.path.split(file)[1])

            for transcript_file in transcript_files:
                if name in transcript_file:
                    matches[name] = { "audio": file, "transcript": transcript_file }

        for tape, data in matches.items():
            captions = parse_vtt(data['transcript'])

            sound = AudioSegment.from_wav(data['audio'])

            current = 1
            num_captions = len(captions)

            for caption in captions:
                start_millis = int(caption.start * 1000.0)
                end_millis = int(caption.end * 1000.0)

                section = sound[start_millis:end_millis]

                os.makedirs(f'/home/luke/split-test/{tape}', exist_ok=True)

                section.export(f'/home/luke/split-test/{tape}/part-{current}.mp3', format='mp3')

                print(f'{current} / {num_captions}', flush=True)

                current += 1

    else:
        print('This script requires the path to the atc0_*/data/ directory')

if __name__ == '__main__':
    main()
