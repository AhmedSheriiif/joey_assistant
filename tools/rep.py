import struct,sys,re,collections
from db import names,cid
t=open('list_card.txt','rb').read().decode('latin1')
m=re.findall(r'//\t(.*?)\r?\n//\t(\d+):\[(\d+)\]',t)
byid={int(c):n for n,i,c in m}
COM='C:/Users/ahmed/AppData/Roaming/Yu-Gi-Oh! Power of Chaos Common/'
def lists(d,p):
    out=[]
    for _ in range(3):
        n=struct.unpack_from('<H',d,p)[0]; p+=2
        out.append(struct.unpack_from('<%dH'%n,d,p)); p+=2*n
    return out,p
f=sys.argv[1]
d=open(COM+f,'rb').read()
print(len(d),d[:4],d[4:12].hex(),struct.unpack_from('<IIII',d,12),d[12:28].hex())
p=28
print(d[28:44].hex())
L1,p=lists(d,28)
print('P1',[len(x) for x in L1],'ends',p)
L2,p2=lists(d,p)
print('P2',[len(x) for x in L2],'ends',p2)
for nm,L in (('P1',L1),('P2',L2)):
    c=collections.Counter(L[0]); print(nm,'main:', '; '.join(f'{v}x {byid.get(k,k)}' for k,v in sorted(c.items(),key=lambda x:-x[1])))
print('rest',len(d)-p2, d[p2:p2+120].hex())
print('=== log')
n=struct.unpack_from('<I',d,p2)[0]; q=p2+4
rec=[struct.unpack_from('<II',d,q+8*i) for i in range((len(d)-q)//8)]
print('count field',n,'records',len(rec),'tail bytes',(len(d)-q)%8)
print(' '.join(f'{a:x}:{b:x}' for a,b in rec[:70]))
print(collections.Counter(a&0xffff for a,b in rec).most_common(25))
