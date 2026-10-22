"""Preflight the musical edit, actual word alignment, boundary frames and determinism."""
import json
import math
import time
import numpy as np
import lyrics
from render import END, FRAMES, frame, soundtrack
from score import SHOTS, HITS, EXEC
from visual import ROOT, W, H, FPS, text_tile, has_cjk
import stage


def verify():
    start=time.monotonic()
    assert (W,H,FPS)==(1920,1080,60)
    assert SHOTS[0].start==0 and SHOTS[-1].end==END
    assert all(a.end==b.start for a,b in zip(SHOTS,SHOTS[1:]))
    assert all(s.start<s.end and s.kind in stage.DRAW for s in SHOTS)
    assert len(HITS)==len(EXEC)==16
    assert all(a<b for a,b in zip(HITS,HITS[1:]))
    assert all(np.isfinite(value).all() for value in soundtrack().values())
    aligned=lyrics.timeline()
    assert sum(len(line['words']) for line in aligned)==395
    assert all(word['start']<word['end'] for line in aligned for word in line['words'])
    for s in SHOTS:
        assert text_tile(s.line,30,False,has_cjk(s.line)).width<1780, s.title
    for line in aligned:
        assert sum(text_tile(w['text'],27,False,False).width+13 for w in line['words'])<1500, line['id']
    samples={0,FRAMES-1}
    for s in SHOTS:
        samples.update([math.ceil(s.start*FPS),math.ceil(s.start*FPS)+1,
                        round((s.start+s.end)*FPS/2),math.ceil(s.end*FPS)-1])
    for t in HITS:
        samples.update([math.floor(t*FPS),math.ceil(t*FPS),math.ceil(t*FPS)+12])
    for n in sorted(samples):
        im=frame(n)
        assert im.size==(W,H) and im.mode=='RGB'
        if n>30:
            assert np.asarray(im).max()>100, n
    # Out-of-order rendering must not change a frame in the process pool.
    expected=frame(10901).tobytes()
    frame(1403)
    assert frame(10901).tobytes()==expected
    # Consecutive 60 Hz frames in moving scenes must actually differ.
    changes=[]
    for t in [26.0,35.0,43.0,61.0,90.0,108.0,141.0]:
        n=round(t*FPS)
        a=np.asarray(frame(n))[240:700,850:1400].astype(np.int16)
        b=np.asarray(frame(n+1))[240:700,850:1400].astype(np.int16)
        value=float(np.abs(a-b).mean())
        assert value>.005, (t,value)
        changes.append({'time':t,'adjacent_frame_difference':value})
    result={'status':'passed','shots':len(SHOTS),'frames':FRAMES,'fps':FPS,'size':[W,H],
            'boundary_frames_rendered':len(samples),'word_alignment_lines':len(aligned),
            'word_alignment_words':395,'execution_hits':len(HITS),'deterministic':True,
            'motion_samples':changes,'seconds':round(time.monotonic()-start,2)}
    (ROOT/'out').mkdir(exist_ok=True)
    (ROOT/'out/review.json').write_text(json.dumps(result,indent=2))
    print(json.dumps(result,indent=2))


if __name__=='__main__':
    verify()
