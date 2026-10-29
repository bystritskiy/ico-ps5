#!/usr/bin/env python3
"""Import a user's PAL ISO through ico-pc's ELF and DATA.DF verification.

The PBPX menu repack contains an intact PAL game and a second data archive.
Only the temporary import copy selects the original PAL boot and data file.
"""
import argparse,hashlib,json,shutil,struct,subprocess
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
ELF_SHA1='da3644c54c26fe760f3b6a591a5fc2eab396ed2b'
def digest(path,kind='sha256'):
 h=hashlib.new(kind)
 with path.open('rb') as f:
  for b in iter(lambda:f.read(1024*1024),b''):h.update(b)
 return h.hexdigest()
def records(f,offset,size):
 f.seek(offset);data=f.read(size);pos=0
 while pos<len(data):
  n=data[pos]
  if not n:pos=(pos//2048+1)*2048;continue
  r=data[pos:pos+n]
  if len(r)!=n or n<34:raise ValueError('Invalid ISO directory')
  name=r[33:33+r[32]].split(b';')[0].decode('ascii')
  yield name,struct.unpack_from('<I',r,2)[0]*2048,struct.unpack_from('<I',r,10)[0],pos,n
  pos+=n
def normalize(src,dst):
 with src.open('rb') as f:
  f.seek(16*2048);pvd=f.read(2048)
  if pvd[:7]!=b'\x01CD001\x01':raise ValueError('Expected ISO9660 DVD image')
  root=struct.unpack_from('<I',pvd,158)[0]*2048;size=struct.unpack_from('<I',pvd,166)[0]
  entries={r[0]:r for r in records(f,root,size)}
  if 'SCES_507.60' not in entries:raise ValueError('Expected original SCES_507.60')
  _,off,n,*_=entries['SCES_507.60'];f.seek(off)
  if hashlib.sha1(f.read(n)).hexdigest()!=ELF_SHA1:raise ValueError('PAL ELF hash mismatch')
  _,cnf_off,cnf_n,*_=entries['SYSTEM.CNF'];f.seek(cnf_off);cnf=f.read(cnf_n)
  df_off,df_n=entries['DFDATAS'][1:3]
  extras=[r for r in records(f,df_off,df_n) if r[0]=='DATA.D2']
  patched=b'PBPX_955.06' in cnf
 shutil.copyfile(src,dst)
 with dst.open('r+b') as f:
  if patched:
   f.seek(cnf_off);f.write(cnf.replace(b'PBPX_955.06',b'SCES_507.60'))
  # The game uses DATA.DF. The menu's alternate DATA.D2 is not imported.
  for _,_,_,pos,n in sorted(extras,key=lambda r:r[3],reverse=True):
   f.seek(df_off);d=f.read(df_n);f.seek(df_off)
   f.write(d[:pos]+d[pos+n:]+bytes(n))
 return {'boot_menu_normalized':patched,'alternate_archives_omitted':len(extras),'elf_sha1':ELF_SHA1}
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('iso',type=Path);p.add_argument('--host-exe',type=Path,required=True)
 a=p.parse_args();iso=a.iso.resolve();exe=a.host_exe.resolve()
 work=ROOT/'build/inputs';work.mkdir(parents=True,exist_ok=True)
 validation=ROOT/'build/validation';validation.mkdir(parents=True,exist_ok=True)
 normalized=work/'Ico_PAL.import.iso';facts=normalize(iso,normalized)
 data=exe.parent/'ico.o2r'
 # The generated host build's folder is disposable, never a user's installation.
 if not exe.is_relative_to(ROOT/'build'):raise ValueError('Use a host executable under build/')
 if data.exists():data.rename(data.with_name('ico.previous.o2r'))
 (exe.parent/'ico-pc.ini').write_text('use_iso=0\n')
 with (validation/'host-run.log').open('w') as log:
  subprocess.run([str(exe),'--iso',str(normalized),'--ticks','300','--trace',str(validation/'host-trace.txt'),'--console'],stdout=log,stderr=subprocess.STDOUT,check=True)
 text=(validation/'host-run.log').read_text()
 if 'accepted by' not in text or '300 Main ticks' not in text:raise ValueError('Host import did not complete')
 out=ROOT/'build/game/ico.o2r';out.parent.mkdir(parents=True,exist_ok=True);shutil.copyfile(data,out)
 facts.update(input_name=iso.name,input_size=iso.stat().st_size,input_sha256=digest(iso),archive_size=out.stat().st_size,archive_sha256=digest(out),host_ticks=300,console_tested=False)
 (validation/'game-data.json').write_text(json.dumps(facts,indent=2)+'\n')
 print(json.dumps(facts,indent=2))
if __name__=='__main__':main()
