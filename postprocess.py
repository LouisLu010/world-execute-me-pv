"""Final delivery gate: decode all frames, retain exact audio, produce review excerpts."""
import hashlib
import json
import subprocess
import zipfile
from pathlib import Path
import imageio_ffmpeg
import av
from PIL import Image,ImageDraw

from check_media import check
from package import archive, delivery
from visual import ROOT, font, WHITE, BG


def clips():
    ff=imageio_ffmpeg.get_ffmpeg_exe()
    source=ROOT/'out/same_process_1080p60.mp4'
    # Re-encode only these standalone review excerpts, leaving the full film untouched.
    for start,end,name in [(103.03,125.33,'codex_preview.mp4'),(147.52,176.96,'execution_preview.mp4')]:
        subprocess.run([ff,'-v','error','-y','-ss',str(start),'-i',str(source),'-t',str(end-start),
                        '-c:v','libx264','-preset','fast','-crf','18','-threads','2',
                        '-c:a','aac','-b:a','192k','-movflags','+faststart',str(ROOT/'out'/name)],check=True)


def encoded_contact():
    moments=[13,35,90,108,143,156,175.5,204,210]
    picked=[]
    # Sequentially decode actual encoded images rather than republishing source renders.
    with av.open(str(ROOT/'out/same_process_1080p60.mp4')) as c:
        for image in c.decode(video=0):
            if len(picked)==len(moments):break
            if image.time>=moments[len(picked)]:
                picked.append((image.time,image.to_image().resize((640,360),Image.Resampling.LANCZOS)))
    sheet=Image.new('RGB',(1920,1194),BG)
    d=ImageDraw.Draw(sheet)
    for i,(time,im) in enumerate(picked):
        x=i%3*640;y=i//3*398
        d.text((x+14,y+8),f'{time:07.2f}s / FINAL ENCODE',font=font(17),fill=WHITE)
        sheet.paste(im,(x,y+38))
    sheet.save(ROOT/'out/final_encoded_contact.jpg',quality=95)


def manifest():
    files=['render.py','stage.py','score.py','visual.py','world.py','codex_ui.py','lyrics.py',
           'prepare.py','requirements.txt','data/word_timeline_notext.json',
           'data/lyrics.json','data/audio_features.npz','input/soundtrack.m4a']
    hashes={name:hashlib.sha256((ROOT/name).read_bytes()).hexdigest() for name in files}
    result={'title':'你还记得我吗？ / SAME PROCESS?','dimensions':[1920,1080],'fps':60,
            'frames':12714,'timeline_seconds':211.90,'native_frame_render':True,
            'codex_reference_commit':'7c073196a1673a0b248b2e5edfb7548d2c2290ac','input_sha256':hashes}
    (ROOT/'out/build_manifest.json').write_text(json.dumps(result,ensure_ascii=False,indent=2))


if __name__=='__main__':
    check()
    clips()
    encoded_contact()
    manifest()
    archive()
    delivery()
    dest=Path('/tmp/opencode/gpt-history-delivery')
    import shutil
    for name in ['codex_preview.mp4','execution_preview.mp4','final_encoded_contact.jpg',
                 'audio_review.json','particle_review.json','build_manifest.json']:
        shutil.copy2(ROOT/'out'/name,dest/name)
    with zipfile.ZipFile(ROOT/'out/same_process_project.zip') as z:
        assert z.testzip() is None
    print('DELIVERY VERIFIED: '+str(dest))
