import csv,collections,glob,sys
sys.argv=['x','anas1.ydr']
from db import *
from decks import deck, COM, byid as byid2
TY={1:'Dragon',2:'Zombie',3:'Fiend',4:'Pyro',6:'Rock',7:'Machine',8:'Fish',9:'Dinosaur',10:'Insect',11:'Beast',12:'Beast-Warrior',13:'Plant',14:'Aqua',15:'Warrior',16:'Winged Beast',17:'Fairy',18:'Spellcaster',19:'Thunder',20:'Reptile'}
import os,struct
ixb=open('card_indxeng.bin','rb').read(); dd=open('card_desceng.bin','rb').read()
def D(i):
    o=struct.unpack_from('<I',ixb,i*4)[0]
    o&=0x00ffffff
    if (o>>16)==0x20: o&=0xffff
    return dd[o:dd.index(bytes([0]),o)].decode('latin1').strip()
os.makedirs(r'C:/Users/ahmed/OneDrive/Desktop/joey_assistant/data',exist_ok=True)
w=csv.writer(open(r'C:/Users/ahmed/OneDrive/Desktop/joey_assistant/data/cards_all.csv','w',newline='',encoding='utf8'))
w.writerow(['deck_id','name','level','attribute','type','atk','def','passcode','description'])
rows=0
for i in range(1,1115):
    c=card(i); b=p[i*4:i*4+4]; v=b[2]|b[3]<<8; fl=v&15
    mon = c['type'] in TY
    atk=(b[1]+256*(fl&3))*5; df=b[0]*10
    w.writerow([c['id'],c['name'],c['lv'] if mon else '',ATTR.get(c['attr'],'') if mon else '',TY.get(c['type'],'') ,atk if mon else '',df if mon else '',c['pass_'],D(i)]); rows+=1
print(rows)
out=['# My decks (decoded from the .ydc files in the Common folder)\n','Names come from the game\'s own data.dat card table. Spell/Trap rows are plain names.\n']
for f in sorted(glob.glob(COM+'*.ydc')):
    out.append(f'\n## {os.path.basename(f)}')
    for nm,part in zip(('Main','Fusion','Side'),deck(f)):
        c=collections.Counter(part)
        out.append(f'- **{nm} ({len(part)})**: '+'; '.join(f"{v}x {byid2.get(k,'?'+str(k))}" for k,v in sorted(c.items(),key=lambda x:-x[1])))
open(r'C:/Users/ahmed/OneDrive/Desktop/joey_assistant/knowledge/04_my_decks.md','w',encoding='utf8').write('\n'.join(out)+'\n')
