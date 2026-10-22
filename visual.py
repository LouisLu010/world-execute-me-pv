"""Original cinematic TUI primitives. Every frame is addressed by soundtrack time."""
from __future__ import annotations

import math
import os
from functools import lru_cache
from pathlib import Path

import numpy as np
from PIL import Image, ImageChops, ImageDraw, ImageFilter, ImageFont

ROOT = Path(__file__).resolve().parent
W, H, FPS = 1920, 1080, 60
# Layout remains in the original design coordinates; rasterisation is resolution-aware.
RASTER_SCALE = int(os.environ.get('GPT_PV_RASTER_SCALE', '1'))
if RASTER_SCALE not in (1, 2):
    raise ValueError('GPT_PV_RASTER_SCALE must be 1 (1080p) or 2 (native 4K)')
BG = (6, 11, 18)
WHITE = (227, 240, 235)
MINT = (127, 233, 207)
AMBER = (246, 187, 108)
RED = (255, 93, 85)
DIM = (126, 145, 164)
FAINT = (39, 57, 76)
BLUE = (132, 190, 255)


def clamp(x, a=0., b=1.):
    return max(a, min(b, x))


def ease(x):
    x = clamp(x)
    return x * x * (3 - 2 * x)


def out(x):
    return 1 - (1 - clamp(x)) ** 3


def mix(a, b, t):
    return tuple(int(x + (y - x) * clamp(t)) for x, y in zip(a, b))


def col(c, a=1.):
    return tuple(int(v * clamp(a)) for v in c)


def pixel_box(box):
    return tuple(round(value*RASTER_SCALE) for value in box)


def new_surface(color=BG):
    return Image.new('RGB', (W*RASTER_SCALE, H*RASTER_SCALE), color)


def has_cjk(value):
    return any('\u2e80' <= ch <= '\u9fff' or '\uff00' <= ch <= '\uffef' for ch in value)


@lru_cache(2048)
def wrap_text(value, size, max_width):
    f = font(size, cjk=has_cjk(value))
    lines=[]
    for paragraph in str(value).split('\n'):
        if not paragraph:
            lines.append('')
            continue
        pieces=list(paragraph) if has_cjk(paragraph) else paragraph.split(' ')
        joiner='' if has_cjk(paragraph) else ' '
        line=''
        for piece in pieces:
            candidate=line+joiner+piece if line else piece
            if line and f.getlength(candidate)>max_width:
                lines.append(line)
                line=piece
            else:
                line=candidate
        if line:
            lines.append(line)
    return lines


@lru_cache(128)
def font(size, bold=False, cjk=False):
    if cjk:
        local = ROOT / "assets/fonts/NotoSansCJKsc-Regular.otf"
        path = local if local.exists() else Path("/usr/share/fonts/opentype/noto/NotoSansCJK-Regular.ttc")
        return ImageFont.truetype(str(path), size, index=2 if path.suffix == ".ttc" else 0)
    name="DejaVuSansMono" + ("-Bold" if bold else "") + ".ttf"
    local=ROOT / "assets/fonts" / name
    return ImageFont.truetype(str(local if local.exists() else Path("/usr/share/fonts/truetype/dejavu") / name), size)


@lru_cache(4096)
def text_tile(value, size, bold, cjk):
    f = font(size, bold, cjk)
    box = f.getbbox(value or " ")
    width = max(1, int(f.getlength(value)))
    tile = Image.new("L", (width + 6, size * 2 + 8))
    ImageDraw.Draw(tile).text((3, 2 - box[1]), value, font=f, fill=255)
    return tile.crop((0, 0, width + 6, max(4, box[3] - box[1] + 6)))


@lru_cache(2048)
def raster_text_tile(value, size, bold, cjk):
    if RASTER_SCALE==1:
        return text_tile(value,size,bold,cjk)
    scale=RASTER_SCALE
    f=font(size*scale,bold,cjk)
    box=f.getbbox(value or ' ')
    width=max(1,math.ceil(f.getlength(value)))
    tile=Image.new('L',(width+6*scale,max(4*scale,box[3]-box[1]+6*scale)))
    ImageDraw.Draw(tile).text((3*scale,2*scale-box[1]),value,font=f,fill=255)
    return tile


@lru_cache(8)
def background(palette="mint"):
    if RASTER_SCALE>1:
        # Broadcast one row/column at a time to avoid the large np.mgrid allocations
        # that would otherwise make parallel native 4K rendering memory-heavy.
        sw,sh=W*RASTER_SCALE,H*RASTER_SCALE
        x=np.arange(sw,dtype=np.float32)[None,:]/RASTER_SCALE
        y=np.arange(sh,dtype=np.float32)[:,None]/RASTER_SCALE
        r=((x-W*.52)/(W*.65))**2+((y-H*.42)/(H*.72))**2
        gl=np.maximum(0,1-r)**2
        base=(6,10,16) if palette!='red' else (14,7,11)
        tint=(3,8,11) if palette!='red' else (12,3,4)
        a=np.empty((sh,sw,3),dtype=np.uint8)
        for k in range(3):
            a[:,:,k]=np.clip(base[k]+gl*tint[k],0,255)
        for offset in range(RASTER_SCALE):
            a[offset::4*RASTER_SCALE]=(a[offset::4*RASTER_SCALE]*.92).astype(np.uint8)
        im=Image.fromarray(a)
        d=ImageDraw.Draw(im)
        dot=(22,36,44) if palette!='red' else (39,22,27)
        for xx in range(64,W,48):
            for yy in range(132,852,48):
                d.rectangle(pixel_box((xx,yy,xx+.5,yy+.5)),fill=dot)
        return im
    y, x = np.mgrid[0:H, 0:W]
    r = ((x - W * .52) / (W * .65)) ** 2 + ((y - H * .42) / (H * .72)) ** 2
    gl = np.maximum(0, 1 - r) ** 2
    a = np.zeros((H, W, 3), dtype=np.uint8)
    base = (6, 10, 16) if palette != "red" else (14, 7, 11)
    tint = (3, 8, 11) if palette != "red" else (12, 3, 4)
    for k in range(3):
        a[:, :, k] = np.clip(base[k] + gl * tint[k], 0, 255)
    a[::4] = (a[::4] * .92).astype(np.uint8)
    im = Image.fromarray(a)
    d = ImageDraw.Draw(im)
    for xx in range(64, W, 48):
        for yy in range(132, 852, 48):
            d.point((xx, yy), fill=(22, 36, 44) if palette != "red" else (39, 22, 27))
    return im


class Canvas:
    def __init__(self, t, palette="mint", color=None):
        self.t = t
        self.im = background(palette).copy() if color is None else new_surface(color)
        self.d = ImageDraw.Draw(self.im)

    def text(self, x, y, value, size=24, color=WHITE, alpha=1., anchor="left", bold=False, limit=None):
        value = str(value)
        if limit is not None:
            value = value[:max(0, int(limit))]
        if not value or alpha <= .005:
            return 0
        logical_width = text_tile(value, size, bold, has_cjk(value)).width
        tile = raster_text_tile(value, size, bold, has_cjk(value))
        if anchor == "center":
            x -= logical_width / 2
        elif anchor == "right":
            x -= logical_width
        self.im.paste(col(color, alpha), pixel_box((x,y)), tile)
        return logical_width

    def wrap(self, x, y, value, max_width, size=24, color=WHITE, alpha=1., leading=1.55):
        lines = wrap_text(value, size, max_width)
        for i, line in enumerate(lines):
            self.text(x, y+i*size*leading, line, size, color, alpha)
        return len(lines)*size*leading

    def line(self, pts, color=MINT, alpha=1., width=1):
        if len(pts) >= 2:
            self.d.line([pixel_box((x,y)) for x, y in pts], fill=col(color, alpha), width=width*RASTER_SCALE)

    def rect(self, box, color=MINT, alpha=1., fill=False, width=1):
        b = pixel_box(box)
        if b[2] < b[0] or b[3] < b[1]:
            return
        self.d.rectangle(b, fill=col(color, alpha) if fill else None,
                          outline=None if fill else col(color, alpha), width=width*RASTER_SCALE)

    def circle(self, x, y, r, color=MINT, alpha=1., fill=False, width=1):
        self.d.ellipse(pixel_box((x-r,y-r,x+r,y+r)),
                       fill=col(color, alpha) if fill else None,
                       outline=None if fill else col(color, alpha), width=width*RASTER_SCALE)

    def panel(self, box, label="", color=MINT, alpha=1.):
        x0, y0, x1, y1 = box
        self.rect(box, FAINT, alpha)
        for x, sx in [(x0, 1), (x1, -1)]:
            for y, sy in [(y0, 1), (y1, -1)]:
                self.line([(x+sx*18, y), (x, y), (x, y+sy*18)], color, alpha*.8, 2)
        if label:
            self.rect((x0+22, y0-12, x0+38+len(label)*11, y0+16), BG, 1, True)
            self.text(x0+30, y0-8, label, 17, color, alpha)

    def tag(self, x, y, value, color=MINT, size=18):
        width = text_tile(value, size, True, has_cjk(value)).width
        self.rect((x, y, x+width+24, y+size+20), color, .10, True)
        self.rect((x, y, x+3, y+size+20), color, .9, True)
        self.text(x+12, y+10, value, size, color, bold=True)
        return width+24

    def type(self, x, y, value, elapsed, speed=13, size=30, color=WHITE, anchor="left"):
        n = min(len(value), max(0, int(elapsed * speed)))
        tile = text_tile(value, size, False, has_cjk(value))
        start = x - tile.width/2 if anchor == "center" else x
        w = self.text(start, y, value[:n], size, color)
        if elapsed >= 0 and (n<len(value) or int(self.t*2)%2==0):
            self.rect((start+w+5, y+1, start+w+9, y+size), color, .9, True)

    def caption(self, line, sub="", alpha=1):
        if line:
            self.text(W/2, 858, line, 37, WHITE, alpha, "center")
        if sub:
            self.text(W/2, 916, sub, 17, DIM, alpha, "center")

    def finish(self, bloom=.26):
        # Quarter-resolution bloom keeps long offline renders CPU-friendly.
        sw,sh=self.im.size
        if RASTER_SCALE>1:
            # Only the low-frequency glow is evaluated at reduced resolution.
            # Main glyphs, masks, geometry and compositing stay at native 4K.
            tiny=self.im.reduce(4*RASTER_SCALE)
            threshold=tiny.point([max(0,v-65) for v in range(256)]*3)
            glow=threshold.filter(ImageFilter.GaussianBlur(3.2))
            glow=glow.point([int(v*bloom) for v in range(256)]*3)
            return ImageChops.add(self.im,glow.resize((sw,sh),Image.Resampling.BILINEAR))
        tiny = self.im.resize((sw//4, sh//4), Image.Resampling.BILINEAR)
        threshold = tiny.point([max(0, v-65) for v in range(256)]*3)
        blur = threshold.filter(ImageFilter.GaussianBlur(3.2*RASTER_SCALE)).resize((sw,sh), Image.Resampling.BILINEAR)
        return ImageChops.add(self.im, blur.point([int(v*bloom) for v in range(256)]*3))


def rotate(points, yaw=0., pitch=0., roll=0.):
    cy, sy, cp, sp, cr, sr = math.cos(yaw), math.sin(yaw), math.cos(pitch), math.sin(pitch), math.cos(roll), math.sin(roll)
    ry=np.array([[cy,0,sy],[0,1,0],[-sy,0,cy]])
    rx=np.array([[1,0,0],[0,cp,-sp],[0,sp,cp]])
    rz=np.array([[cr,-sr,0],[sr,cr,0],[0,0,1]])
    return np.asarray(points) @ (rz @ rx @ ry).T


def project(points, center=(960,475), scale=270, camera=4.5):
    p=np.asarray(points)
    denom=np.maximum(.5,camera+p[:,2])
    xy=p[:,:2] * (camera/denom[:,None])*scale
    xy[:,0]+=center[0]
    xy[:,1]+=center[1]
    return xy, p[:,2]


RNG = np.random.default_rng(130)
STAR = RNG.uniform([-3.3,-1.65,-1.3], [3.3,1.65,1.3], (650,3))
SPHERE = RNG.normal(size=(850,3))
SPHERE /= np.linalg.norm(SPHERE,axis=1)[:,None]


def field(c, t, strength=.35, center=(960,465), scale=240):
    p=rotate(STAR,t*.035,.16*math.sin(t*.11))
    xy,z=project(p,center,scale)
    for i in range(0,len(p),2):
        x,y=xy[i]
        if 70<x<1850 and 160<y<820:
            v=strength*(.45+.55*(z[i]+1.8)/3.6)
            c.rect((x,y,x+1+(i%7==0),y+1+(i%7==0)),MINT,v,True)


def orb(c,t,center=(960,470),radius=235,mode=0,alpha=1,color=MINT):
    theta=np.linspace(0,2*math.pi,181)
    yaw=t*.17
    for j in range(15):
        lat=-math.pi/2+(j+1)*math.pi/16
        wave=.07*np.sin(theta*5+t*1.4+j*.7) if mode==2 else 0
        p=np.stack([(math.cos(lat)+wave)*np.cos(theta),np.full_like(theta,math.sin(lat)),
                    (math.cos(lat)+wave)*np.sin(theta)],axis=1)
        p=rotate(p,yaw,.32,.12)
        xy,z=project(p,center,radius)
        c.line(xy,color,alpha*(.25+.4*(j%3==0)))
    for j in range(12):
        ang=j*math.pi/6
        p=np.stack([np.cos(theta)*math.cos(ang),np.sin(theta),np.cos(theta)*math.sin(ang)],axis=1)
        xy,z=project(rotate(p,yaw,.32,.12),center,radius)
        c.line(xy,color,alpha*.38)
    xy,z=project(rotate(SPHERE,yaw,.32,.12),center,radius)
    for i,(x,y) in enumerate(xy):
        if i%3==0:
            c.rect((x,y,x+2,y+2),color,alpha*(.2+.75*(z[i]+1)/2),True)


def waveform(c, box, t, color=AMBER, missing=.1366667, generated=False, gain=1, phase=0):
    x0,y0,x1,y1=box
    mid=(y0+y1)/2
    split=x0+(x1-x0)*(1-missing)
    c.line([(x0,mid),(x1,mid)],color,.18)
    c.line([(split,y0-12),(split,y1+12)],RED,.55)
    for x in range(int(x0),int(x1),5):
        u=(x-x0)/(x1-x0)
        envelope=(.15+.85*math.sin(u*math.pi*6.2+.3)**2)*(.3+.7*math.sin(u*math.pi*2.3)**2)
        amp=abs(math.sin(u*183+phase)*math.cos(u*73+phase*.4))*envelope*(y1-y0)*.46*gain
        if x<split:
            c.line([(x,mid-amp),(x,mid+amp)],color,.50+.45*math.sin(u*32)**2,2)
        elif generated:
            amp=(.15+abs(math.sin(u*155+phase+2))*.85)*(y1-y0)*.30*gain
            c.line([(x,mid-amp),(x,mid+amp)],MINT,.8,2)
        elif (x-int(split))%25<5:
            c.line([(x,y0+8),(x+6,y0+2)],RED,.35)
    return split


def door(c,center=(960,470),height=400,opening=.25,alpha=1,color=AMBER):
    x,y=center
    w=height*.42
    x0,y0=x-w/2,y-height/2
    x1,y1=x+w/2,y+height/2
    for k in range(16,0,-1):
        c.rect((x0-k,y0-k,x1+k,y1+k),color,alpha*.015)
    c.rect((x0,y0,x1,y1),color,alpha*.8,width=2)
    c.rect((x0+5,y0+5,x1-5,y1-4),color,alpha*.025,True)
    gap=w*opening
    c.d.polygon([(x1-gap,y0+gap*.2),(x1,y0),(x1,y1),(x1-gap,y1-gap*.08)],fill=col(color,alpha*.28))
    c.line([(x1-gap,y0+gap*.2),(x1-gap,y1-gap*.08)],color,alpha,3)
    c.line([(x0-120,y1+38),(x1+160,y1+38)],color,alpha*.13)
    c.d.polygon([(x1-gap,y1),(x1,y1),(x1+150,y1+100),(x0-100,y1+100)],fill=col(color,alpha*.065))
    c.circle(x1-gap-13,y+6,3,color,alpha,True)


def tunnel(c,t,color=MINT,center=(960,480),power=.6,broken=0):
    """A projected stack of computation planes, with packets travelling down its rails."""
    cx,cy=center
    for j in range(28):
        depth=(j/28+t*.095)%1
        q=depth**1.9
        rx=90+790*q;ry=65+255*q
        drift=math.sin(t*.24)*60*q
        x0,x1=cx-rx+drift,cx+rx+drift;y0,y1=cy-ry,cy+ry
        a=power*(.12+.62*q)
        if broken and j%16<broken:
            y0-=q*broken*3;y1+=q*broken*3
            a*=.3
        c.line([(x0,y0),(x1,y0),(x1,y1),(x0,y1),(x0,y0)],color,a)
        if j%3==0:
            for k in range(9):
                x=x0+(x1-x0)*k/8
                c.line([(x,y0),(x,y0+12+q*15)],color,a*.8)
            c.text(x0+12,y1-25,f"{j:02X}",12+int(q*6),color,a)
    for side in [-1,1]:
        for j in range(9):
            p=j/8
            a=(cx+side*90,cy-65+130*p)
            b=(cx+side*880,cy-320+640*p)
            c.line([a,b],color,power*.22)
            q=(t*.7+j*.173)%1
            x=a[0]+(b[0]-a[0])*q;y=a[1]+(b[1]-a[1])*q
            c.rect((x-3,y-2,x+8,y+2),color,power*.9,True)


def knot(c,t,center=(960,470),scale=170,color=MINT,alpha=.7):
    """A rotating trefoil of conditional paths; purely an authored geometric motif."""
    u=np.linspace(0,2*math.pi,240)
    for k in range(12):
        phase=k*2*math.pi/12
        r=.12
        p=np.stack([np.sin(u)+2*np.sin(2*u)+r*np.cos(phase)*np.cos(u),
                    np.cos(u)-2*np.cos(2*u)+r*np.cos(phase)*np.sin(u),
                    -np.sin(3*u)+r*np.sin(phase)],axis=1)
        p=rotate(p,t*.15,.55+math.sin(t*.09)*.2,.16)
        xy,z=project(p,center,scale,camera=6)
        xy-=np.asarray(center)
        xy*=min(1.,280/max(1.,np.max(abs(xy[:,1]))),720/max(1.,np.max(abs(xy[:,0]))))
        xy+=np.asarray(center)
        c.line(xy,color,alpha*(.25+.35*(k%3==0)),2 if k%3==0 else 1)
        for j in range(0,240,24):
            idx=(j+int(t*18))%240
            x,y=xy[idx]
            c.rect((x-2,y-2,x+2,y+2),color,alpha,True)
