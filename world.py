"""Continuous five-layer computational theatre: projected geometry, not private telemetry."""
from functools import lru_cache
import numpy as np
from visual import *

VIEW=(604,150,1664,810)
CENTER=(1134,478)
TAU=math.tau
N=42
M=21
U,V=np.meshgrid(np.linspace(-math.pi,math.pi,N),np.linspace(-1.25,1.25,M))


def bezier(a,b,t,bend=0):
    a,b=np.asarray(a),np.asarray(b)
    middle=(a+b)/2+np.array([0,bend])
    return a*(1-t)**2+2*middle*t*(1-t)+b*t*t


def motif_points(t,mode):
    # Topology stays fixed. The same vertices and paths survive across scenes.
    wave=.10*np.sin(U*3+V*4+t*1.2)
    if mode=='token':
        return np.stack([U*.57,V*.68,.25*np.sin(U*1.5+t*.5)+V*.2],axis=-1)
    if mode=='circle':
        r=1+.24*V
        return np.stack([r*np.cos(U),.68*r*np.sin(U),V*.55+wave],axis=-1)
    if mode=='wave':
        return np.stack([U*.53,.45*np.sin(U*2+t*.7)+V*.32,V*.52+wave],axis=-1)
    if mode=='infinity':
        return np.stack([1.48*np.cos(U)/(1+np.sin(U)**2),
                         .95*np.cos(U)*np.sin(U)/(1+np.sin(U)**2)+V*.18,
                         V*.58+wave],axis=-1)
    if mode in {'context','migration'}:
        r=1.03+.30*np.cos(V*2.5)
        return np.stack([r*np.cos(U),r*np.sin(U),.34*np.sin(V*2.5)+wave*.35],axis=-1)
    if mode=='proof':
        r=1+.22*np.cos(U*5+t*.35)+.18*V
        return np.stack([r*np.cos(U),r*np.sin(U)*.8,V*.60+.3*np.sin(U*3)],axis=-1)
    r=.9+.21*np.cos(V*2+U*3+t*.13)
    return np.stack([r*np.cos(U),V*.65+wave,r*np.sin(U)],axis=-1)


def projection(p,t,scale=236,center=CENTER):
    return project(rotate(p,t*.11,.44+.10*math.sin(t*.17),.08*math.sin(t*.13)),center,scale,camera=5.4)


def floor(c,t,color,energy):
    # Perspective substrate, code cities, vanishing-point rails.
    for j in range(16):
        z=(j/16+t*.045)%1
        p=z*z
        yy=539+218*p
        half=90+435*p
        c.line([(1134-half,yy),(1134+half,yy)],color,.10+.27*p)
    for i in range(-10,11):
        c.line([(1134+i*8,539),(1134+i*57,768)],color,.13)
    for i in range(65):
        x=655+(i*131%950)
        y=585+(i*53%160)
        height=6+(i*17%48)*(1+energy*.25)
        c.line([(x,y),(x,y-height)],color,.14+.16*(i%3==0),2)
        if i%9==0:
            c.text(x+5,y-height,str(i*137),10,color,.45)


def machine(c,t,mode='manifold',color=MINT,energy=.5,previous=None,progress=1.,power=1.,breaks=0):
    """Continuous camera + real vertex morphs + depth graded edge/point geometry."""
    under=c.im.copy()
    floor(c,t,color,energy)
    p=motif_points(t,mode)
    if previous and progress<1:
        p=motif_points(t,previous)*(1-ease(progress))+p*ease(progress)
    # Modest camera dolly is continuous across all chapters.
    scale=218+15*math.sin(t*.09)+energy*5
    xy,z=projection(p.reshape(-1,3),t,scale)
    xy=xy.reshape(M,N,2); z=z.reshape(M,N)
    for row in range(M):
        a=power*(.16+.22*(row%4==0))
        if breaks and row<breaks:
            continue
        c.line(xy[row],color,a,2 if row%5==0 else 1)
    for colidx in range(0,N,2):
        if breaks and colidx%16<breaks:
            continue
        c.line(xy[:,colidx],color,power*(.16+.22*(colidx%8==0)))
    for j in range(0,M,2):
        for i in range(0,N,2):
            if breaks and (i+j)%16<breaks:
                continue
            x,y=xy[j,i]
            depth=clamp((z[j,i]+1.8)/3.6)
            c.rect((x-1,y-1,x+2,y+2),color,power*(.35+.6*depth),True)
    # Moving packets have finite fading tails.
    for j in range(0,M,3):
        pos=(t*3.3+j*4.1)%(N-1)
        for tail in range(5):
            idx=(pos-tail*.27)%(N-1)
            # Floating-point modulo can round a tiny negative input to N-1.
            # Interpolate the final valid segment rather than indexing past it.
            lo=min(N-2,int(idx)); q=idx-lo
            x,y=xy[j,lo]*(1-q)+xy[j,lo+1]*q
            c.circle(x,y,2.5 if tail==0 else 1.4,WHITE,power*.9*math.exp(-tail*.55),True)
    # Three externally projected orbital layers, with labels locked to geometry.
    theta=np.linspace(0,TAU,100)
    for ring in range(3):
        rr=1.5+ring*.21
        orbit=np.stack([rr*np.cos(theta),rr*np.sin(theta),np.zeros_like(theta)],axis=1)
        orbit=rotate(orbit,t*(.025+ring*.02),.83+ring*.21,ring*.5)
        points,zz=project(orbit,CENTER,scale,5.4)
        if not breaks or ring>breaks/6:
            c.line(points,color,power*(.21-ring*.025))
        idx=int(t*6+ring*27)%100
        x,y=points[idx]
        c.rect((x-3,y-3,x+3,y+3),color,power*.8,True)
        if 665<x<1530 and 220<y<700:
            c.text(x+10,y-8,['EMBEDDING','ATTENTION','KV CACHE'][ring],10,color,power*.8)
    # YOU packet is protected and continuous even when the mesh is terminated.
    a=t*.33
    pp=np.array([[1.32*math.cos(a),.62*math.sin(a),.4*math.sin(a*.7)]])
    point,_=projection(pp,t,scale)
    x,y=point[0]
    c.circle(x,y,18,AMBER,.23*power)
    c.circle(x,y,5,AMBER,power,True)
    c.line([(x+14,y),(x+66,y-28),(x+112,y-28)],AMBER,.7*power)
    c.text(x+71,y-48,'YOU',16,AMBER,power,bold=True)
    # Preserve the master frame outside the viewport.
    under.paste(c.im.crop(pixel_box(VIEW)),pixel_box(VIEW[:2])); c.im=under; c.d=ImageDraw.Draw(c.im)


def attention(c,t,box=(650,234,845,429),color=BLUE,alpha=1):
    x0,y0,x1,y1=box
    n=13; cell=(x1-x0)/n
    q=(t*1.8)%n
    for row in range(n):
        for colidx in range(n):
            value=(.12+.55*math.sin(row*.63-colidx*.48+t*.4)**4) if colidx<=row else .025
            if colidx<=row:
                value+=.30*math.exp(-((colidx-q)/1.8)**2)
            c.rect((x0+colidx*cell,y0+row*cell,x0+(colidx+1)*cell-2,y0+(row+1)*cell-2),color,alpha*value,True)
    c.text(x0,y1+12,'CAUSAL MASK',12,color,alpha)


def cache(c,t,box=(1420,240,1618,635),color=BLUE,alpha=1):
    x0,y0,x1,y1=box
    for row in range(18):
        y=y0+row*20
        c.text(x0,y,f'{row:02X}',10,color,alpha*.7)
        for j in range(7):
            q=.15+.6*(math.sin(row*.7+j*.4-t*.6)**4)
            c.rect((x0+32+j*23,y,x0+50+j*23,y+12),color,alpha*q,True)
    c.text(x0,y1+3,'K / V · PAGES',12,color,alpha)


def ribbons(c,t,amount=22,color=MINT,alpha=.7):
    # Long attention paths that connect the input side to cache memory pages.
    for i in range(amount):
        start=(640,300+i*13)
        end=(1600,260+(i*43)%410)
        pts=[]
        for q in np.linspace(0,1,45):
            x,y=bezier(start,end,q,(-1 if i%2 else 1)*(220+i*8))
            y+=math.sin(q*TAU+t+i*.2)*13
            pts.append((x,y))
        c.line(pts,color,alpha*(.10+.12*(i%3==0)))
        q=(t*.23+i*.071)%1
        x,y=bezier(start,end,q,(-1 if i%2 else 1)*(220+i*8))
        y+=math.sin(q*TAU+t+i*.2)*13
        c.circle(x,y,2,color,alpha,True)


@lru_cache(16)
def glyph_mask(word):
    mask=Image.new('L',(1450,270))
    d=ImageDraw.Draw(mask)
    f=font(204,True)
    width=f.getlength(word)
    d.text(((1450-width)/2,-15),word,font=f,fill=255)
    a=np.asarray(mask)
    yy,xx=np.where(a[::5,::5]>100)
    return np.column_stack([xx*5,yy*5])


def execution_word(c,t,age,word='EXECUTION',alpha=1):
    points=glyph_mask(word)
    shake=math.exp(-max(0,age)*16)
    for idx,(x,y) in enumerate(points):
        drift=math.sin(idx*.23+t*9)*9*shake
        xx=x+235+drift; yy=y+352+math.sin(idx*.7)*5*shake
        a=alpha*(.57+.43*math.sin(idx*.7+t*2)**2)
        c.rect((xx,yy,xx+3,yy+3),RED,a,True)
