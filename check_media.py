"""Decode every finished frame and compare the supplied audio packets bit for bit."""
import hashlib
import json
import av
from render import FRAMES
from visual import ROOT,W,H,FPS


def audio_packets(path):
    digest=hashlib.sha256();count=0
    with av.open(str(path)) as source:
        for packet in source.demux(source.streams.audio[0]):
            if packet.size:
                digest.update(bytes(packet));count+=1
    return {'packets':count,'sha256':digest.hexdigest()}


def check(path=None, width=W, height=H, report_name='media_review.json'):
    path=path or ROOT/'out/same_process_1080p60.mp4'
    with av.open(str(path)) as video:
        stream=video.streams.video[0]
        assert (stream.width,stream.height)==(width,height)
        assert float(stream.average_rate)==FPS
        duration=video.duration/av.time_base
        count=0
        for frame in video.decode(stream):
            assert abs(frame.time-count/FPS)<.0001,(count,frame.time)
            count+=1
        assert count==FRAMES,(count,FRAMES)
    source=audio_packets(ROOT/'input/soundtrack.m4a')
    result=audio_packets(path)
    assert result==source,(source,result)
    review={'file':path.name,'bytes':path.stat().st_size,'duration':duration,'width':width,'height':height,
            'fps':FPS,'decoded_frames':count,'timestamps':'continuous','audio_bit_exact':True,
            'audio':result,'status':'passed'}
    (ROOT/'out'/report_name).write_text(json.dumps(review,indent=2))
    print(json.dumps(review,indent=2))
    return review


if __name__=='__main__':
    check()
