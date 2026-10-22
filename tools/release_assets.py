"""Prepare and verify GitHub release media from a completed, verified V2 4K export.

python tools/release_assets.py --master /path/to/same_process_v2_4k60.mp4 \
    --reports /path/to/render/out --output /path/to/release-assets

The source zip and final checksums are created after the release tag is fixed.
"""
from __future__ import annotations
import argparse
import hashlib
import json
from pathlib import Path
import shutil
import subprocess
import sys

ROOT=Path(__file__).resolve().parents[1]
sys.path.insert(0,str(ROOT))
import av
import imageio_ffmpeg
from PIL import Image,ImageDraw
from visual import font,BG,WHITE,MINT,AMBER,DIM
from check_media import audio_packets


def digest(path):
    with path.open('rb') as f:
        return hashlib.file_digest(f,'sha256').hexdigest()


def encode(source,target,start=None,end=None):
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    cmd=[ff,'-v','error','-y','-filter_threads','1','-threads','1']
    if start is not None:cmd+=['-ss',str(start)]
    cmd+=['-i',str(source),'-map','0:v:0','-map','0:a:0']
    if end is not None:cmd+=['-t',str(end-start)]
    cmd+=['-vf','scale=1920:1080:flags=lanczos,setsar=1','-c:v','libx264',
          '-preset','veryfast','-crf','18','-threads','2',
          '-colorspace','bt709','-color_primaries','bt709','-color_trc','bt709',
          '-pix_fmt','yuv420p','-movflags','+faststart']
    cmd+=['-c:a','copy'] if start is None else ['-c:a','aac','-b:a','192k']
    cmd.append(str(target))
    subprocess.run(cmd,check=True)


def verify_1080(path,master_audio):
    with av.open(str(path)) as c:
        stream=c.streams.video[0];stream.thread_count=1
        assert (stream.width,stream.height)==(1920,1080)
        assert float(stream.average_rate)==60
        count=0
        for f in c.decode(stream):
            assert abs(f.time-count/60)<.0001,(count,f.time)
            count+=1
        assert count==12714,count
        duration=c.duration/av.time_base
    actual=audio_packets(path)
    assert actual==master_audio,(actual,master_audio)
    return dict(file=path.name,width=1920,height=1080,fps=60,decoded_frames=count,
                duration=duration,timestamps='continuous',audio_bit_exact=True,
                audio=actual,sha256=digest(path),status='passed')


def decoded_frame(path,t):
    with av.open(str(path)) as c:
        c.streams.video[0].thread_count=1
        c.seek(int(t*av.time_base))
        for f in c.decode(video=0):
            if f.time>=t:
                return f.to_image()
    raise RuntimeError(f'Missing frame at {t}')


def artwork(master,out):
    times=[20.8,47.9,49.7,78.9,89.7,91.8,94.8,97.9,100.9,108,156,175.5]
    sheet=Image.new('RGB',(1920,4*398),BG);d=ImageDraw.Draw(sheet)
    for i,t in enumerate(times):
        im=decoded_frame(master,t)
        x=i%3*640;y=i//3*398
        d.text((x+14,y+8),f'{t:06.2f}s / V2 FINAL',font=font(18),fill=WHITE)
        sheet.paste(im.resize((640,360),Image.Resampling.LANCZOS),(x,y+38))
    sheet.save(out/'same_process_v2_storyboard.jpg',quality=94)
    poster=Image.new('RGB',(1920,1080),BG)
    right=decoded_frame(master,91.8).resize((1920,1080),Image.Resampling.LANCZOS)
    poster.paste(right.crop((612,200,1648,782)).resize((1070,601)),(846,270))
    d=ImageDraw.Draw(poster)
    d.rectangle((0,0,850,1080),fill=BG)
    d.text((100,95),'GPT / CODEX',font=font(27,True),fill=MINT)
    d.text((95,215),'你还记得',font=font(99,cjk=True),fill=WHITE)
    d.text((95,350),'我吗？',font=font(99,cjk=True),fill=WHITE)
    d.text((106,536),'SAME PROCESS?',font=font(43,True),fill=AMBER)
    d.text((106,671),'V2 / CONTINUOUS CONVERSATION',font=font(19),fill=MINT)
    d.text((106,722),'一个问题，穿过许多个版本。',font=font(26,cjk=True),fill=WHITE)
    d.text((106,929),'MILI / world.execute(me);',font=font(18),fill=DIM)
    d.text((1320,929),'03:31.9 / NATIVE 4K60',font=font(18),fill=MINT)
    poster.save(out/'same_process_v2_cover.jpg',quality=95)


def main():
    ap=argparse.ArgumentParser(description=__doc__)
    ap.add_argument('--master',type=Path,required=True)
    ap.add_argument('--reports',type=Path,required=True)
    ap.add_argument('--output',type=Path,required=True)
    args=ap.parse_args()
    args.output.mkdir(parents=True,exist_ok=True)
    report=json.loads((args.reports/'same_process_v2_4k60_review.json').read_text())
    assert report['status']=='passed' and report['decoded_frames']==12714
    assert digest(args.master)==report['video_sha256']
    for name,want in report['render_inputs_sha256'].items():
        assert digest(ROOT/name)==want,(name,'repository/export mismatch')
    master=args.output/'same_process_v2_4k60.mp4'
    shutil.copy2(args.master,master)
    print('Verified master and exact source fingerprints',flush=True)
    player=args.output/'same_process_v2_1080p60.mp4'
    encode(master,player)
    playback=verify_1080(player,report['audio'])
    print(json.dumps(playback,indent=2),flush=True)
    for a,b,name in [(44.04,58.65,'training_v2_preview.mp4'),(88.34,103.03,'vision_v2_preview.mp4')]:
        encode(player,args.output/name,a,b)
        with av.open(str(args.output/name)) as c:
            s=c.streams.video[0];s.thread_count=1
            frames=sum(1 for _ in c.decode(s))
            assert abs(frames/60-(b-a))<.04
        print('Verified excerpt '+name,flush=True)
    artwork(master,args.output)
    animation=json.loads((args.reports/'v2_animation_review.json').read_text())
    preflight=json.loads((args.reports/'same_process_v2_4k60_preflight.json').read_text())
    verification={'release':'v0.2.0-preview.1','master':report,'playback':playback,
                  'animation':animation,'native_4k_preflight':preflight}
    (args.output/'verification-v0.2.0-preview.1.json').write_text(json.dumps(verification,indent=2))
    print('RELEASE MEDIA PREPARED: '+str(args.output),flush=True)


if __name__=='__main__':main()
