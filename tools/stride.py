import json,struct,sys,os
sys.path.insert(0,'.')
from hands import initial_libraries
from replay_decks import read_replay
import numpy as np
rep=sys.argv[1]; d=open(rep,'rb').read()
seed=struct.unpack_from('<I',d,24)[0]; f20=struct.unpack_from('<I',d,20)[0]
decks,ev=read_replay(rep); libs=initial_libraries(decks,seed,1 if f20 else 0)
for snap in sys.argv[2:]:
    data=open(snap,'rb').read(); regions=json.load(open(snap[:-4]+'.json'))
    def where(i):
        for b,s,p in regions:
            if p<=i<p+s: return b+i-p
    a=np.frombuffer(data,dtype=np.uint8)
    print('==',os.path.basename(snap),len(data)//1e6)
    for label,lib in libs.items():
        ids=lib[:5]
        for w in (2,4):
            # candidates for first id
            dt='<u2' if w==2 else '<u4'
            n=(len(data)//w)
            for al in range(w):
                v=np.frombuffer(data[al:al+(len(data)-al)//w*w],dtype=dt)
                c=np.nonzero(v==ids[0])[0]
                for stride in range(1,65):
                    ok=c.copy()
                    for k in range(1,5):
                        ok=ok[(ok+k*stride<len(v))]
                        ok=ok[v[ok+k*stride]==ids[k]]
                        if not len(ok): break
                    for o in ok[:3]:
                        print(label,'hand5 w',w,'stride(units)',stride,hex(where(al+o*w)))
