"""Reconstruct the reference's actual word timing, with per-line hash validation."""
import bisect
import hashlib
import json
import re
from functools import lru_cache
from pathlib import Path

ROOT = Path(__file__).resolve().parent


@lru_cache(None)
def timeline():
    source = json.loads((ROOT/'data/lyrics.json').read_text())
    texts = []
    for line in source['syncedLyrics'].splitlines():
        match = re.match(r'\[\d+:\d+(?:\.\d+)?\]\s?(.*)', line)
        if match:
            texts.append(match[1].strip())
    data = json.loads((ROOT/'data/word_timeline_notext.json').read_text())
    patches = {p['line_id']: p['ops'] for p in data['patches']}
    restored = {}
    for meta in data['lines']:
        text = texts[meta['id']]
        for op in patches.get(meta['id'], []):
            assert op['op'] == 'reorder_words'
            words = text.split()
            text = ' '.join(words[i] for i in op['order'])
        assert hashlib.sha256(text.encode()).hexdigest() == meta['sha256'], meta['id']
        restored[meta['id']] = (text, meta['spans'])
    result = []
    for line in data['skeleton']['lines']:
        text, spans = restored[line['id']]
        words = []
        for word in data['skeleton']['words']:
            if word['line_id'] == line['id']:
                start, end = spans[word['word_index']]
                words.append(dict(text=text[start:end], start=word['start'], end=word['end']))
        assert len(words) == len(spans)
        result.append(dict(id=line['id'], text=text, start=line['start'],
                           end=line['display_end'], words=words))
    return result


def at(t):
    lines = timeline()
    index = bisect.bisect_right([line['start'] for line in lines], t)-1
    if index < 0 or t >= lines[index]['end']:
        return None
    line = lines[index]
    index = bisect.bisect_right([word['start'] for word in line['words']], t)-1
    return line, index
