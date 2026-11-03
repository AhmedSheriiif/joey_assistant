import re,struct,glob,collections,sys
t=open('list_card.txt','rb').read().decode('latin1')
m=re.findall(r'//\t(.*?)\r?\n//\t(\d+):\[(\d+)\]',t)
byid={int(i):n for n,idx,i in m}; byidx={int(idx):n for n,idx,i in m}
print(len(m))
COM=r'C:/Users/ahmed/AppData/Roaming/Yu-Gi-Oh! Power of Chaos Common/'
def deck(p):
    d=open(p,'rb').read(); p=8; out=[]
    while p+2<=len(d):
        n=struct.unpack_from('<H',d,p)[0]; p+=2
        out.append(struct.unpack_from('<%dH'%n,d,p)); p+=2*n
    return out
if __name__=='__main__':
    for f in sorted(glob.glob(COM+'*.ydc')):
        print('==',f.split('/')[-1])
        for nm,part in zip(('main','fusion','side'),deck(f)):
            c=collections.Counter(part)
            print(' ',nm,len(part),'; '.join(f"{v}x {byid.get(k,'?'+str(k))}" for k,v in sorted(c.items(),key=lambda x:-x[1])))
