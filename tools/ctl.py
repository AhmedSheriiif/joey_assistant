import json,struct,sys,os
sys.path.insert(0,'.')
from replay_decks import read_replay
decks,ev=read_replay(sys.argv[1])
for snap in sys.argv[2:]:
    data=open(snap,'rb').read(); print('==',os.path.basename(snap))
    for li in (0,1):
        for part in range(3):
            ids=decks[li][part]
            if len(ids)<4: continue
            for w,tag in((2,'<H'),(4,'<I')):
                for n in (len(ids),8):
                    pat=b''.join(struct.pack(tag,x) for x in ids[:n])
                    print('list',li,'part',part,'w',w,'first',n,'hits',data.count(pat))
