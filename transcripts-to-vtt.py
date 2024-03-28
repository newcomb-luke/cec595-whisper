import sys
import os
import datetime


class Exchange:
    def __init__(self, source: str, destination: str, num: str, text: str, times: list[float], comments: list[str]):
        self.source = source
        self.destination = destination
        self.num = num
        self.text = text
        self.times = times
        self.comments = comments

    @staticmethod
    def _get_one_part(content: str):
        part = ''
        parens = 0
        just_started = True
        index = 0

        for c in content:
            if c == '(':
                parens += 1
            elif c == ')':
                parens -= 1

            part += c
            index += 1

            if not just_started and parens == 0:
                break
            
            just_started = False
        
        return (part.strip(), content[index + 1:].strip())

    @staticmethod
    def parse(raw: str):
        rest = raw.removeprefix('(')
        
        parts = []

        while rest.strip() != ')' and rest != '':
            part, rest = Exchange._get_one_part(rest)
            parts.append(part)

        source = None
        num = None
        destination = None
        text = None
        comments = []

        if parts[0].startswith('(FROM'):
            source = parts[0].split('(FROM')[1].removesuffix(')').strip()
        else:
            print(raw)
            print(f'Invalid format (expected FROM): {parts[0]}')

        if parts[1].startswith('(NUM'):
            num = parts[1].split('(NUM')[1].removesuffix(')').strip()
        else:
            # NUM is apparently optional
            num = 'none'
            parts.insert(1, '')

        if parts[2].startswith('(TO'):
            destination = parts[2].split('(TO')[1].removesuffix(')').strip()
        else:
            print(raw)
            print(f'Invalid format (expected TO): {parts[2]}')

        if parts[3].startswith('(TEXT'):
            text = parts[3].split('(TEXT')[1].removesuffix(')').strip()
            words = text.split()
            final_words = []
            do_quote = False

            for word in words:
                if do_quote:
                    final_words[-1] = final_words[-1] + "'" + word[:-1]
                    do_quote = False
                    continue
                if word == '(QUOTE':
                    do_quote = True
                else:
                    final_words.append(word)

            text = ' '.join(final_words).capitalize()
        else:
            print(raw)
            print(f'Invalid format (expected TEXT): {parts[3]}')
            exit(2)

        if parts[4].startswith('(TIMES '):
            times = parts[4].split('(TIMES ')[1].removesuffix(')').strip()
            times = list([float(time) for time in times.split()])
        else:
            print(raw)
            print(f'Invalid format (expected TIMES): {parts[4]}')
            exit(2)

        if len(parts) > 5:
            for part in parts[6:]:
                if part.startswith('(COMMENT'):
                    comment = part.split('(COMMENT')[1].removesuffix(')').strip()
                    comments.append(comment)
                else:
                    print(raw)
                    print(f'Invalid format: {part}')
                    exit(2)
        return Exchange(source, destination, num, text, times, comments)

    def __repr__(self) -> str:
        return f'''Exchange {{
    from: "{self.source}",
    num: "{self.num}",
    to: "{self.destination}",
    text: "{self.text}",
    times: {self.times}
}}'''

    def _time_to_vtt(self, time: float) -> str:
        hours, remainder = divmod(time, 3600.0)
        minutes, seconds = divmod(remainder, 60.0)
        return f'{int(hours):01}:{int(minutes):02}:{float(seconds):02.3f}'

    def to_vtt(self) -> str:
        start_time = self._time_to_vtt(self.times[0])
        end_time = self._time_to_vtt(self.times[1])
        return f'{start_time} --> {end_time}\n{self.text}\n\n'


class Transcript:
    def __init__(self, path: str, tape_header: str, comments: list[str], exchanges: list[Exchange], tape_tail: str):
        self.path = path
        self.tape_header = tape_header
        self.comments = comments
        self.exchanges = exchanges
        self.tape_tail = tape_tail

    @staticmethod
    def _get_one_item(content: str):
        item = ''
        parens = 0
        just_started = True
        index = 0

        for c in content:
            if just_started:
                if c == '' or c == '\n' or c == ' ' or c == '\r' or c == '\t':
                    index += 1
                    continue

            if c == '(':
                parens += 1
            elif c == ')':
                parens -= 1

            item += c
            index += 1

            if not just_started and parens == 0:
                break
            
            just_started = False
        
        return (item.strip(), content[index + 1:])


    @staticmethod
    def parse_from_file(path: str):
        print(f'Parsing: {path}')

        with open(path, 'r') as f:
            tape_header_line = f.readline()
            tape_header = tape_header_line.split('"')[1]
            tape_tail = ''

            exchanges = []
            comments = []

            uncommented = []

            for line in f.readlines():
                if not line.startswith(';'):
                    uncommented.append(line)

            rest = ''.join(uncommented)

            items = []

            while len(rest.strip()) > 0:
                item, rest = Transcript._get_one_item(rest)
                items.append(item)

            for item in items:
                if item.startswith('((COMMENT'):
                    comment = item.split('"')[1]
                    comments.append(comment)
                elif item.startswith('((FROM'):
                    exchange = Exchange.parse(item)
                    exchanges.append(exchange)
                elif item.startswith('((TAPE-TAIL'):
                    if '"' in item:
                        tape_tail = item.split('"')[1]
                    else:
                        tape_tail = item.split('TAPE-TAIL')[1].strip().replace(')', '')
                else:
                   print(f'Unrecognized data in transcript: {item}')

            return Transcript(path, tape_header, comments, exchanges, tape_tail)

    def _vtt_note(self, str) -> str:
        return f'NOTE\n{str}\n\n'

    def to_vtt(self) -> str:
        contents = 'WEBVTT\n\n'

        contents += self._vtt_note(self.tape_header)

        for exchange in self.exchanges:
            contents += exchange.to_vtt()

        contents += self._vtt_note(self.tape_tail)

        return contents


def main():
    if len(sys.argv) > 1:
        base_path = sys.argv[1]

        transcripts = []

        for entry in os.scandir(base_path):
            _, extension = os.path.splitext(entry.name)
            if extension == '.txt':
                transcript = Transcript.parse_from_file(entry.path)
                transcripts.append(transcript)

        for transcript in transcripts:
            filename, extension = os.path.splitext(transcript.path)

            vtt_path = filename + '.vtt'

            with open(vtt_path, 'w') as f:
                f.write(transcript.to_vtt())

    else:
        print('This script takes the argument of the transcript base path')

if __name__ == '__main__':
    main()
