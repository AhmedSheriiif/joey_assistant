import json,struct,sys,os
sys.path.insert(0,'.')
import numpy as np
from hands import initial_libraries
from replay_decks import read_replay
rep=sys.argv[1]; snap=sys.argv[2]
d=open(rep,'rb').read(); seed=struct.unpack_from('<I',d,24)[0]; f20=struct.unpack_from('<I',d,20)[0]
decks,ev=read_replay(rep); libs=initial_libraries(decks,seed,1 if f20 else 0)
data=open(snap,'rb').read(); regions=json.load(open(snap[:-4]+'.json'))
def where(i):
    for b,s,p in regions:
        if p<=i<p+s: return b+i-p
for label,lib in libs.items():
    hand=lib[:5]; print(label,'hand',hand,'uniq',len(set(hand)))
    for w,dt in((2,'<u2'),(4,'<u4')):
        for al in range(w):
            v=np.frombuffer(data[al:al+(len(data)-al)//w*w],dtype=dt)
            pos=[np.nonzero(v==h)[0] for h in set(hand)]
            allp=np.sort(np.concatenate(pos)); 
            win=128//w*2
            best=[]
            for i,p in enumerate(allp):
                j=np.searchsorted(allp,p+win)
                ids={int(v[q]) for q in allp[i:j]}
                if len(ids&set(hand))>=min(4,len(set(hand))): best.append(p)
            if best: print(' w',w,'al',al,'windows',len(best),[hex(where(al+int(b)*w)) for b in best[:6]])
