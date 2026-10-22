"""The real OpenAI/ChatGPT knot artwork, from the recorded SVG distribution.

The vector path is unmodified. CairoSVG renders its transparent white form;
the same image is used for the avatar and the vision-stage example.
"""
from functools import lru_cache
from io import BytesIO
import xml.etree.ElementTree as ET
import numpy as np
from PIL import Image
from visual import ROOT, RASTER_SCALE, pixel_box, clamp

ASSET=ROOT/'assets/brand/chatgpt-original.svg'


@lru_cache(1)
def source():
    cached=ROOT/'assets/brand/chatgpt-white-1536.png'
    if cached.exists():
        return Image.open(cached).convert('RGBA')
    import cairosvg
    svg=ET.fromstring(ASSET.read_bytes())
    svg.set('color','#ffffff')
    data=cairosvg.svg2png(bytestring=ET.tostring(svg),output_width=1536,output_height=1536)
    return Image.open(BytesIO(data)).convert('RGBA')


@lru_cache(160)
def icon(size):
    return source().resize((size,size),Image.Resampling.LANCZOS)


def draw(c,cx,cy,size,alpha=1):
    if alpha<=0:return
    tile=icon(max(1,round(size*RASTER_SCALE)))
    mask=tile.getchannel('A')
    if alpha<.999:mask=mask.point([round(i*clamp(alpha)) for i in range(256)])
    c.im.paste((255,255,255),pixel_box((cx-size/2,cy-size/2)),mask)


@lru_cache(512)
def patch_tile(index,size,grid=8):
    image=source();w=image.width//grid
    x=index%grid*w;y=index//grid*w
    tile=image.crop((x,y,x+w,y+w))
    return tile.resize((size,size),Image.Resampling.LANCZOS)


@lru_cache(1)
def patch_features():
    """Measured image features for the diagram; not proprietary learned embeddings."""
    a=np.asarray(source().getchannel('A').resize((256,256),Image.Resampling.LANCZOS),dtype=float)/255
    result=[]
    for i in range(64):
        x=i%8*32;y=i//8*32;p=a[y:y+32,x:x+32]
        dx=np.abs(np.diff(p,axis=1));dy=np.abs(np.diff(p,axis=0))
        result.append([float(p.mean()),float(p.std()),float(dx.mean()*8),float(dy.mean()*8),
                       float(p[:16].mean()),float(p[16:].mean()),float(p[:,:16].mean()),float(p[:,16:].mean())])
    return np.clip(np.array(result),0,1)
