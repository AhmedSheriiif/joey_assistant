import struct
p=open('card_prop.bin','rb').read(); n=open('nameeng.bin','rb').read()
ps=open('card_pass.bin','rb').read()
names=[n[i*64:(i+1)*64].split(b'\0')[0].decode('latin1').strip() for i in range(1115)]
desc=open('card_desceng.bin','rb').read().split(b'\0')
import re
t=open('list_card.txt','rb').read().decode('latin1')
m=re.findall(r'//\t(.*?)\r?\n//\t(\d+):\[(\d+)\]',t)
cid={int(i):int(c) for _,i,c in m}  # idx -> deck id
ATTR={1:'Light',2:'Dark',3:'Water',4:'Fire',5:'Earth',6:'Wind',7:'Divine'}
TYPE={1:'Dragon',2:'Spellcaster',3:'Fiend',4:'Pyro',7:'Machine',8:'Fish',11:'Beast',12:'Beast-Warrior',13:'Plant',14:'Aqua',15:'Warrior',16:'Winged Beast',17:'Fairy',19:'Thunder',20:'Reptile'}
def card(i):
    b=p[i*4:i*4+4]; v=b[2]|b[3]<<8
    return dict(idx=i,id=cid.get(i),name=names[i],atk=b[1]*5,df=b[0]*10,lv=(v>>9)&15,attr=v>>13,type=(v&0x1ff)>>4,flags=v&15,raw=b.hex(),pass_=struct.unpack_from('<I',ps,i*4)[0])
if __name__=='__main__':
    import sys
    for nm in ['Insect Queen','Mad Sword Beast','Red-Moon Baby','Stone Ogre Grotto','Empress Mantis','Alpha the Magnet Warrior','Beta the Magnet Warrior','The Legendary Fisherman','Polymerization','Monster Reborn','Mirror Force','Scapegoat','Jinzo','Sangan','Baby Dragon','Gemini Elf','Magician of Black Chaos','Alligator\'s Sword Dragon','Giant Rat','Dark Hole','Heavy Storm','Torrential Tribute','Call Of The Haunted','Yami','Premature Burial']:
        i=names.index(nm); c=card(i); print(c, len(desc))
