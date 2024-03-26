import sys
import os
import json

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
        
        return (part.strip(), content[index + 1:])

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

        if parts[0].startswith('(FROM '):
            source = parts[0].split('(FROM ')[1].removesuffix(')')
        else:
            print('Invalid format')

        if parts[1].startswith('(NUM '):
            num = parts[1].split('(NUM ')[1].removesuffix(')')
        else:
            print('Invalid format')

        if parts[2].startswith('(TO '):
            destination = parts[2].split('(TO ')[1].removesuffix(')')
        else:
            print('Invalid format')

        if parts[3].startswith('(TEXT '):
            text = parts[3].split('(TEXT ')[1].removesuffix(')')
            text = text.replace(' (QUOTE ', "'")
            text = text.replace(')', '')
            text = text.replace('\n', '')
            text = text.replace('  ', ' ')
            text = text.replace('  ', ' ')
        else:
            print('Invalid format')

        if parts[4].startswith('(TIMES '):
            times = parts[4].split('(TIMES ')[1].removesuffix(')')
            times = list([float(time) for time in times.split(' ')])
        else:
            print('Invalid format')

        if len(parts) > 5:
            for part in parts[6:]:
                if part.startswith('(COMMENT '):
                    comment = part.split('(COMMENT ')[1].removesuffix(')')
                    comments.append(comment)
                else:
                    print('Invalid format')
        
        return Exchange(source, destination, num, text, times, comments)

    def __repr__(self) -> str:
        return f'''Exchange {{
    from: "{self.source}",
    num: "{self.num}",
    to: "{self.destination}",
    text: "{self.text}",
    times: {self.times}
}}'''


class Transcript:
    def __init__(self, tape_header: str, comments: list[str], exchanges):
        self.tape_header = tape_header
        self.comments = comments
        self.exchanges = exchanges

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
        with open(path, 'r') as f:
            tape_header_line = f.readline()
            tape_header = tape_header_line.split('"')[1]
            tape_tail = ''

            exchanges = []
            comments = []

            rest = f.read()

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
                    print(exchange)
                    exchanges.append(exchange)
                    if len(exchanges) >= 2:
                        exit(1)
                elif item.startswith('((TAPE-TAIL'):
                    tape_tail = item.split('"')[1]
                else:
                    print(item)

def main():
    if len(sys.argv) > 1:
        base_path = sys.argv[1]

        transcripts = []

        for entry in os.scandir(base_path):
            transcript = Transcript.parse_from_file(entry.path)
            transcripts.append(transcript)
            break

    else:
        print('This script takes the argument of the transcript base path')

if __name__ == '__main__':
    main()
