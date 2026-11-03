from lz import *
import struct
def get(n):
    b,u=raw(n); return lzss(b,u,4078,32,0) if len(b)!=u else b
for n in ['card_desceng','card_indxeng','card_prop','card_pass','card_pack','card_id','card_intid','card_sorteng']:
    o=get('bin#'+chr(92)+n+'.bin'); open(n+'.bin','wb').write(o); print(n,len(o),o[:48].hex())
d=open('card_desceng.bin','rb').read(); print(d[:300])
i=open('card_indxeng.bin','rb').read(); print(struct.unpack('<16I',i[:64]))
