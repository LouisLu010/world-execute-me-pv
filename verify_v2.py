"""Regression checks for message continuity, critic timing, image provenance and vision motion."""
import hashlib
import json
import math
from pathlib import Path
import numpy as np
from PIL import Image
import brand
import chat_flow as chat
import vision_sequence as vision
from render import frame,FRAMES
from visual import FPS,ROOT,RASTER_SCALE,pixel_box


def verify():
    data=brand.ASSET.read_bytes()
    blob=hashlib.sha1(b'blob '+str(len(data)).encode()+b'\0'+data).hexdigest()
    assert blob=='78caf4fa20ffb0ae8ebefd74408871c11c1c7fd2',blob
    # 64 patches reconstruct every original source pixel without changing the artwork.
    source=brand.source();joined=Image.new('RGBA',source.size)
    size=source.width//8
    for i in range(64):
        joined.paste(brand.patch_tile(i,size),(i%8*size,i//8*size))
    assert joined.tobytes()==source.tobytes()
    assert brand.patch_features().shape==(64,8)
    assert np.isfinite(brand.patch_features()).all()
    messages=chat.messages()
    assert all(a.start<b.start for a,b in zip(messages,messages[1:]))
    for m in messages:
        if m.strike is not None:
            assert m.start+m.duration<m.strike
            assert chat.visible_count(m,m.strike)==len(m.text)
    scrolls=[chat.layout(n/FPS)[1] for n in range(math.ceil(103.03*FPS))]
    diffs=np.diff(scrolls)
    assert diffs.min()>-1e-8
    assert diffs.max()<16,(diffs.min(),diffs.max())
    samples=set()
    for m in messages+chat.final_messages():
        samples.update([round(m.start*FPS)+1,round((m.start+m.duration)*FPS)])
        if m.strike is not None:
            samples.update([round(m.strike*FPS),round((m.strike+.35)*FPS)])
    for boundary in [88.34,90.54,93.34,96.44,99.44,103.03]:
        samples.update([max(0,math.ceil(boundary*FPS)-1),math.ceil(boundary*FPS),math.ceil((boundary+.42)*FPS)])
    for n in sorted(samples):
        im=frame(n)
        assert im.size==(1920*RASTER_SCALE,1080*RASTER_SCALE)
    # Measure the transcript body, deliberately excluding avatars, footers and cursor UI.
    changes=[]
    for t in [20.9,24.9,45.1,47.3,48.6,55.9,74.4,81.95,89.0,100.2,181.15]:
        box=pixel_box((65,275,550,695))
        a=np.asarray(frame(round(t*FPS)).crop(box)).astype(np.int16)
        b=np.asarray(frame(round((t+.12)*FPS)).crop(box)).astype(np.int16)
        delta=float(np.abs(a-b).mean())
        assert delta>.015,(t,delta)
        changes.append({'time':t,'body_motion_difference':delta})
    n=round(49.7*FPS)
    expected=frame(n).tobytes();frame(round(98*FPS))
    assert frame(n).tobytes()==expected
    result={'status':'passed','source_logo_git_blob':blob,'patch_reconstruction_exact':True,
            'messages':len(messages),'critic_rounds':len(chat.TRAINING),'rendered_event_frames':len(samples),
            'max_scroll_pixels_per_frame':float(diffs.max()),'left_body_motion':changes,
            'native_raster_scale':RASTER_SCALE,'deterministic':True}
    name='v2_animation_review'+('_4k' if RASTER_SCALE==2 else '')+'.json'
    (ROOT/'out'/name).write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':verify()
