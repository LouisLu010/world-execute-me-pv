"""Render the original film, contact sheets, and frame-accurate excerpts.

python render.py stills
python render.py clip --start 29.28 --end 44.04 --width 1280
python render.py full --workers 2
"""
from __future__ import annotations

import argparse
from concurrent.futures import ProcessPoolExecutor
from functools import lru_cache
import json
import math
from pathlib import Path
import re
import subprocess
import time

import imageio_ffmpeg
import numpy as np
from PIL import Image, ImageDraw, ImageFont

import stage as scenes
import lyrics
from score import SHOTS, shot_at
from visual import *

END = 211.90
FRAMES = round(END * FPS)
OUT = ROOT / "out"


@lru_cache(None)
def soundtrack():
    with np.load(ROOT / "data/audio_features.npz") as data:
        return {k:data[k].copy() for k in data.files}


def features(t):
    data=soundtrack()
    position=max(0,min(len(data['rms'])-1,t*48))
    i=int(position); j=min(len(data['rms'])-1,i+1); q=position-i
    return {key:((1-q)*data[key][i]+q*data[key][j]) for key in ['rms','onset','bands']}


@lru_cache(None)
def lyric_lines():
    return [(line['start'],line['end'],line['text']) for line in lyrics.timeline()]


def lyric_at(t):
    """Use the reference's actual acoustic word onsets, with hash-validated words."""
    active=lyrics.at(t)
    if not active:
        return None
    line,idx=active
    return line['text'],[word['text'] for word in line['words']],idx


def chrome(c,s,t,f):
    if s.kind=="execution":
        color=RED
    elif t>=176.96:
        color=AMBER
    else:
        color=MINT
    c.text(64,34,"GPT",32,WHITE,bold=True)
    c.text(156,45,"/  SAME PROCESS?",18,DIM)
    c.text(1856,41,s.chapter,19,color,anchor="right")
    c.line([(64,91),(1856,91)],DIM,.5)
    c.rect((64,90,64+1792*t/END,92),color,.9,True)
    # This spectrum belongs to the supplied soundtrack, not to fictional telemetry.
    for i,value in enumerate(f['bands']):
        x=700+i*8
        c.rect((x,68-value*28,x+4,68),color,.28+.5*value,True)
    c.text(988,47,"MUSIC / FFT",12,DIM)
    _time,date,model=scenes.milestone(t)
    c.text(64,108,date+' / '+model,14,WHITE)
    c.text(620,108,"GPT / CODEX · FICTIONAL INTERNAL WORLD",11,DIM)
    c.text(1856,108,s.title,12,color,anchor="right")
    # Narrative layer: separate from the lyric layer, so the song remains readable.
    if s.line and s.kind not in {"execution", "end"}:
        alpha=ease((t-s.start)/.24)
        c.text(960,839,s.line,30,WHITE,alpha,"center")
        if s.sub:
            c.text(960,883,s.sub,13,DIM,alpha,"center")
    # The lyric rail is always the lowest information layer of the film.
    c.line([(48,960),(1872,960)],DIM,.42)
    c.text(64,987,"LYRIC //",13,color,.9)
    active=lyric_at(t)
    if active:
        _text,words,idx=active
        widths=[text_tile(word,27,False,False).width for word in words]
        gap=13
        total=sum(widths)+gap*max(0,len(words)-1)
        x=(W-total)/2
        for i,(word,width) in enumerate(zip(words,widths)):
            word_color=color if i==idx else (WHITE if i<idx else DIM)
            alpha=1.0 if i==idx else (.85 if i<idx else .78)
            c.text(x,1000,word,27,word_color,alpha)
            if i==idx:
                c.rect((x-2,1042,x+width+2,1045),color,.85,True)
            x+=width+gap
    else:
        c.text(960,1005,"— instrumental / process state continues —",18,DIM,.8,"center")
    c.text(64,927,"MILI / world.execute(me); · AI-ASSISTED FAN PV",11,DIM)
    minutes=int(t//60);seconds=t%60
    c.text(1856,922,f"{minutes:02}:{seconds:05.2f} / 03:31.90",15,DIM,anchor="right")


def frame(n, bloom=True):
    t=n/FPS
    s=shot_at(t)
    f=features(t)
    c=Canvas(t,"red" if s.kind=="execution" else "mint")
    scenes.DRAW[s.kind](c,s,t,f)
    # Short cubic optical dissolves for scene changes. Mesh-to-mesh transitions are
    # vertex morphs in world.py; the two major execution cuts stay musical hard cuts.
    dt=t-s.start
    if s.start>0 and 0<=dt<.45 and s.start not in {147.52,162.23}:
        previous=shot_at(s.start-.001)
        shared_vision=previous.kind in {'vision','omni'} and s.kind in {'vision','omni'}
        if previous.kind!=s.kind and not shared_vision:
            before=Canvas(t)
            scenes.DRAW[previous.kind](before,previous,s.start-.001,f)
            # The chat transcript is a continuous surface, not part of scene dissolves.
            # Keep it time-current across pretrain / geometry / RLHF / conversation cuts.
            chat_kinds={'boot','pretrain','geometry','rlhf','chat','vision','omni'}
            if previous.kind in chat_kinds and s.kind in chat_kinds:
                before.im.paste(c.im.crop(pixel_box((44,154,574,804))),pixel_box((44,154)))
            c.im=Image.blend(before.im,c.im,ease(dt/.45))
            c.d=ImageDraw.Draw(c.im)
    chrome(c,s,t,f)
    im=c.finish(.23+.09*f['rms']) if bloom else c.im
    if t<.4:
        im=Image.blend(new_surface(BG),im,ease(t/.4))
    return im


def encode_chunk(task):
    n0,n1,target,width,preset,resume=task
    target=Path(target)
    target.parent.mkdir(parents=True,exist_ok=True)
    height=width*9//16
    if resume and target.exists():
        import av
        try:
            with av.open(str(target)) as container:
                stream=container.streams.video[0]
                valid=(stream.width,stream.height)==(width,height) and float(stream.average_rate)==FPS
                if width>=3840:
                    valid=valid and not stream.codec_context.has_b_frames
                count=0
                for image in container.decode(stream):
                    valid=valid and abs(image.time-count/FPS)<.0001
                    count+=1
                if valid and count==n1-n0:
                    print(f"RESUMED {target.name}: {count} complete decoded frames",flush=True)
                    return str(target)
        except (av.error.FFmpegError, IndexError, ValueError):
            pass
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ff,"-v","error","-y","-f","rawvideo","-pixel_format","rgb24","-video_size",f"{width}x{height}",
         "-framerate",str(FPS),"-i","pipe:0","-an","-c:v","libx264","-threads","1","-preset",preset,
         "-crf","18","-vf","scale=out_color_matrix=bt709:out_range=tv,format=yuv420p",
          "-colorspace","bt709","-color_primaries","bt709","-color_trc","bt709","-color_range","tv",str(target)]
    if width>=3840:
        # Bound x264's UHD frame queue on small render hosts. This does not
        # change resolution, frame cadence, CRF or the raw-frame rasterisation.
        cmd[1:1]=['-filter_threads','1']
        cmd[-1:-1]=['-tune','zerolatency','-x264-params',
                    'rc-lookahead=0:sync-lookahead=0:bframes=0:ref=1']
    start=time.monotonic()
    proc=subprocess.Popen(cmd,stdin=subprocess.PIPE)
    try:
        for n in range(n0,n1):
            im=frame(n)
            if im.size!=(width,height):im=im.resize((width,height),Image.Resampling.LANCZOS)
            proc.stdin.write(im.tobytes())
            if (n-n0)%240==0:
                elapsed=max(.01,time.monotonic()-start)
                print(f"{target.name} {n-n0}/{n1-n0} frames / {(n-n0)/elapsed:.1f} fps",flush=True)
        proc.stdin.close()
        if proc.wait()!=0:raise RuntimeError(f"Encoder failed: {target}")
    finally:
        if proc.poll() is None:proc.kill()
    print(f"Finished {target.name} in {time.monotonic()-start:.1f}s",flush=True)
    return str(target)


def render(t0,t1,width,workers,preset,name,resume=False):
    OUT.mkdir(exist_ok=True)
    start=time.monotonic()
    n0,n1=round(t0*FPS),round(t1*FPS)
    folder=OUT / (Path(name).stem+"_chunks")
    folder.mkdir(exist_ok=True)
    count=max(workers,min(12,math.ceil((t1-t0)/22)))
    bounds=[n0+(n1-n0)*i//count for i in range(count+1)]
    tasks=[(bounds[i],bounds[i+1],str(folder/f"{i:03}.mp4"),width,preset,resume) for i in range(count)]
    if workers==1:
        files=[encode_chunk(task) for task in tasks]
    else:
        with ProcessPoolExecutor(max_workers=workers) as pool:files=list(pool.map(encode_chunk,tasks))
    listing=folder/"concat.txt"
    listing.write_text("".join(f"file '{Path(p).resolve().as_posix()}'\n" for p in files))
    target=OUT/name
    cmd=[imageio_ffmpeg.get_ffmpeg_exe(),"-v","error","-y","-f","concat","-safe","0","-i",str(listing),
         "-ss",f"{n0/FPS:.6f}","-i",str(ROOT/"input/soundtrack.m4a"),"-map","0:v:0","-map","1:a:0",
         "-c:v","copy","-c:a","copy","-t",f"{max((n1-n0)/FPS,211.906) if n0==0 and n1==FRAMES else (n1-n0)/FPS:.6f}","-movflags","+faststart",
         "-metadata","title=你还记得我吗？ / SAME PROCESS?",
         "-metadata","comment=GPT / Codex fan PV. Fictional model lifecycle. Music: Mili - world.execute(me);. AI-assisted production.",
         str(target)]
    subprocess.run(cmd,check=True)
    print(f"DELIVERED {target} / {time.monotonic()-start:.1f}s",flush=True)


def stills(times=None):
    folder=OUT/"stills"
    folder.mkdir(parents=True,exist_ok=True)
    times=times or [2,13,20,26,31,35,39,43,46,53,61,71,75,79,83,90,100,108,116,123,131,143,148,156,161.85,165,172,175.5,179,186,192,197,204,210]
    thumbs=[]
    for t in times:
        im=frame(round(t*FPS))
        im.save(folder/f"{t:07.2f}.jpg",quality=94)
        thumbs.append((t,im.resize((640,360))))
    for base in range(0,len(thumbs),12):
        group=thumbs[base:base+12]
        rows=math.ceil(len(group)/3)
        sheet=Image.new("RGB",(1920,rows*396),(13,22,29))
        d=ImageDraw.Draw(sheet)
        for i,(t,im) in enumerate(group):
            x=i%3*640;y=i//3*396
            d.text((x+12,y+8),f"{t:06.2f}s / {shot_at(t).title}",font=font(18),fill=WHITE)
            sheet.paste(im,(x,y+36))
        p=OUT/f"contact_{base//12+1}.jpg"
        sheet.save(p,quality=94)
        print(p)


if __name__=="__main__":
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument("mode",choices=["stills","clip","full"])
    ap.add_argument("--start",type=float,default=0)
    ap.add_argument("--end",type=float,default=20)
    ap.add_argument("--width",type=int,default=W*RASTER_SCALE)
    ap.add_argument("--workers",type=int,default=2)
    ap.add_argument("--preset",default="fast")
    ap.add_argument("--name")
    ap.add_argument("--resume",action="store_true",help="Reuse complete, fully decoded chunks from this same edit")
    ap.add_argument("--times",help="comma-separated seconds for stills")
    args=ap.parse_args()
    if args.mode=="stills":stills([float(x) for x in args.times.split(",")] if args.times else None)
    elif args.mode=="full":render(0,FRAMES/FPS,args.width,args.workers,args.preset,args.name or ("same_process_4k60.mp4" if args.width==3840 else "same_process_1080p60.mp4"),args.resume)
    else:render(args.start,args.end,args.width,args.workers,args.preset,args.name or "preview.mp4",args.resume)
