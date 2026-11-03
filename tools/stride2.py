import json,struct,sys
sys.path.insert(0,'.')
import numpy as np
from hands import initial_libraries
from replay_decks import read_replay
rep=sys.argv[1]; snap=sys.argv[2]
d=open(rep,'rb').read(); seed=struct.unpack_from('<I',d,24)[0]
decks,ev=read_replay(rep); libs=initial_libraries(decks,seed,0)
data=open(snap,'rb').read(); regions=json.load(open(snap[:-4]+'.json'))
def where(i):
    for b,s,p in regions:
        if p<=i<p+s: return b+i-p
for label,lib in libs.items():
  for N in (5,):
    ids=lib[:N]
    for w,dt in((2,'<u2'),(4,'<u4')):
      for al in range(0,w):
        v=np.frombuffer(data[al:al+(len(data)-al)//w*w],dtype=dt)
        c=np.nonzero(v==ids[0])[0]
        for stride in range(1,2049):
            ok=c
            for k in range(1,N):
                ok=ok[ok+k*stride<len(v)]
                ok=ok[v[ok+k*stride]==ids[k]]
                if not len(ok): break
            for o in ok[:2]: print(label,'w',w,'stride bytes',stride*w,hex(where(al+int(o)*w)))
print('done')
