"""Native 3840x2160/60 export, followed by full decode and bit-exact audio verification.

python export_4k.py
python export_4k.py --resume
"""
from __future__ import annotations

import os
os.environ['GPT_PV_RASTER_SCALE']='2'

import argparse
import hashlib
import json
import math
from pathlib import Path
import shutil
import time
import gc

from PIL import Image,ImageDraw
import av
from render import frame,render,FRAMES,OUT
from score import SHOTS,HITS
from visual import ROOT,FPS,font,WHITE,BG,RASTER_SCALE
from check_media import check


def preflight(report_name='native_4k_preflight.json'):
    samples={0,FRAMES-1}
    for shot in SHOTS:
        samples.update([math.ceil(shot.start*FPS),math.ceil(shot.start*FPS)+15,
                        round((shot.start+shot.end)*FPS/2),math.ceil(shot.end*FPS)-1])
    samples.update(math.ceil(t*FPS) for t in HITS)
    for n in sorted(samples):
        image=frame(n)
        assert image.size==(3840,2160) and image.mode=='RGB',n
    expected=hashlib.sha256(frame(108*FPS).tobytes()).digest()
    frame(156*FPS)
    assert hashlib.sha256(frame(108*FPS).tobytes()).digest()==expected
    result={'status':'passed','resolution':[3840,2160],'native_raster_scale':RASTER_SCALE,
            'fps':FPS,'checked_frames':len(samples),'deterministic':True}
    (OUT/report_name).write_text(json.dumps(result,indent=2))
    print(json.dumps(result),flush=True)


def trim_preflight_memory():
    from visual import background,text_tile,raster_text_tile,wrap_text
    for fn in [background,text_tile,raster_text_tile,wrap_text]:
        fn.cache_clear()
    gc.collect()
    # Give the allocator's released 4K buffers back before fork/encoder startup.
    import ctypes
    libc=ctypes.CDLL(None)
    if hasattr(libc,'malloc_trim'):
        libc.malloc_trim(0)


def deliver(name='same_process_4k60.mp4'):
    target=OUT/name
    report_name='media_review_4k60.json' if name=='same_process_4k60.mp4' else target.stem+'_review.json'
    review=check(target,3840,2160,report_name)
    review['native_rasterization']=True
    with target.open('rb') as f:
        review['video_sha256']=hashlib.file_digest(f,'sha256').hexdigest()
    review['render_inputs_sha256']={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest()
        for name in ['render.py','visual.py','stage.py','world.py','codex_ui.py','lyrics.py','score.py',
                     'brand.py','chat_flow.py','vision_sequence.py','assets/brand/chatgpt-original.svg']}
    (OUT/report_name).write_text(json.dumps(review,indent=2))
    destination=Path('/tmp/opencode/gpt-history-delivery')
    destination.mkdir(exist_ok=True)
    shutil.copy2(target,destination/target.name)
    shutil.copy2(OUT/report_name,destination/report_name)
    # Decode one native-resolution still from the actual file as a useful quality sample.
    with av.open(str(target)) as video:
        video.seek(int(91.8*av.time_base))
        for image in video.decode(video=0):
            if image.time>=91.8:
                image.to_image().save(destination/(target.stem+'_frame.png'))
                break
    print('VERIFIED 4K DELIVERY: '+str(destination/target.name),flush=True)


if __name__=='__main__':
    parser=argparse.ArgumentParser(description=__doc__)
    parser.add_argument('--resume',action='store_true')
    parser.add_argument('--workers',type=int,default=1)
    parser.add_argument('--name',default='same_process_4k60.mp4')
    args=parser.parse_args()
    OUT.mkdir(exist_ok=True)
    preflight(Path(args.name).stem+'_preflight.json')
    trim_preflight_memory()
    render(0,FRAMES/FPS,3840,args.workers,'veryfast',args.name,args.resume)
    deliver(args.name)
