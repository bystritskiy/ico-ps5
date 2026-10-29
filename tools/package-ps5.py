#!/usr/bin/env python3
"""Convert, sign, stage and roundtrip-verify the ICO PS5 application."""
import argparse,hashlib,json,os,re,shutil,subprocess,tempfile
from pathlib import Path
from ps5_provenance import source_identity
ROOT=Path(__file__).resolve().parent.parent
TITLE='PPSA99030'
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def inventory(p):
 return {x.relative_to(p).as_posix():{'size':x.stat().st_size,'sha256':sha(x)} for x in sorted(p.rglob('*')) if x.is_file()}
def run(cmd,log=None):
 if log:
  with log.open('w') as out:subprocess.run(list(map(str,cmd)),stdout=out,stderr=subprocess.STDOUT,check=True)
  return log.read_text(errors='replace')
 return subprocess.check_output(list(map(str,cmd)),text=True)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--native-tool',type=Path,default=ROOT/'build/ps5/ps5-native-tool')
 p.add_argument('--llvm-bin',type=Path,default=Path('/opt/homebrew/opt/llvm@18/bin'))
 p.add_argument('--game',type=Path,help='Verified ico.o2r, for a private package')
 p.add_argument('--pack-python',type=Path,help='Python with MkPFS 1.1.0')
 a=p.parse_args();identity=source_identity()
 if json.loads((ROOT/'build/ps5/build-source.json').read_text())!=identity:raise ValueError('Sources differ from the linked build; run tools/build-ps5.py')
 native=a.native_tool.resolve();llvm=a.llvm_bin.resolve()
 linked=ROOT/'build/ps5/linked';vk=ROOT/'build/deps/PS5_Vulkan';sdk=vk/'.deps/native/ps5-payload-sdk'
 lock=json.loads((ROOT/'port/ps5/dependencies.json').read_text())
 app=ROOT/'dist'/('with-game' if a.game else 'app')/TITLE;app.mkdir(parents=True,exist_ok=True)
 if not a.game and (app/'ico.o2r').exists():raise ValueError('Unexpected game in app-only stage')
 symbols=run([llvm/'llvm-readelf','--dyn-syms','--wide',linked/'llvm-pie.elf'])
 exports=[x for x in symbols.splitlines() if re.search(r'\b(?:GLOBAL|WEAK)\b',x) and ' UND ' not in x]
 if exports:raise ValueError('Unexpected ELF exports: '+repr(exports[:5]))
 if sha(vk/'runtime/libc.prx')!=lock['runtime']['libc_sha256']:raise ValueError('Runtime hash mismatch')
 run([native,'link','--in',linked/'llvm-pie.elf','--out',linked/'eboot.elf','--stub-dir',sdk/'target/lib','--stub',linked/'stubs/libSceAgc.so','--stub',linked/'stubs/libSceAgcDriver.so','--module-sdk','0x02000009','--companion-sdk','0x08050001','--file-name','eboot.elf'],linked/'convert.log')
 run([native,'self','--sign','--in',linked/'eboot.elf','--out',app/'eboot.bin','--magic','0x1D3D154F'],linked/'sign.log')
 (app/'sce_module').mkdir(exist_ok=True);shutil.copyfile(vk/'runtime/libc.prx',app/'sce_module/libc.prx')
 for f in [app/'eboot.bin',app/'sce_module/libc.prx']:
  result=run([native,'self','--inspect','--file',f]);(linked/(f.name+'-inspect.txt')).write_text(result)
  if 'integrity: valid' not in result:raise ValueError('Invalid FSELF '+str(f))
 shutil.copytree(ROOT/'port/ps5/sce_sys',app/'sce_sys',dirs_exist_ok=True)
 param=json.loads((app/'sce_sys/param.json').read_text())
 if param['titleId']!=TITLE or param['contentVersion']!=lock['ps5_content_version']:raise ValueError('Metadata mismatch')
 licenses=app/'licenses';licenses.mkdir(exist_ok=True)
 for source,name in [(ROOT/'LICENSE','ico-pc-MIT.txt'),(ROOT/'docs/THIRD_PARTY.md','ico-pc-third-party.md'),(ROOT/'port/ps5/NOTICE.md','PS5-Port-NOTICE.md'),(ROOT/'port/ps5/dependencies.json','dependencies.json'),(vk/'LICENSE','PS5-Vulkan-GPL.txt'),(vk/'NOTICE.md','PS5-Vulkan-NOTICE.md'),(ROOT/'build/deps/sdl3/LICENSE.txt','SDL3-zlib.txt'),(ROOT/'build/deps/libmpeg2/LICENSE','libmpeg2-Apache.txt'),(ROOT/'build/deps/libchdr/LICENSE.txt','libchdr-BSD.txt')]:shutil.copyfile(source,licenses/name)
 for source in sorted((ROOT/'port/assets/fonts').glob('*.txt')):
  shutil.copyfile(source,licenses/('font-'+source.name))
 for source in sorted((ROOT/'port/third_party').glob('*/LICENSE')):
  shutil.copyfile(source,licenses/(source.parent.name+'-LICENSE.txt'))
 if a.game:
  facts=json.loads((ROOT/'build/validation/game-data.json').read_text())
  if sha(a.game)!=facts['archive_sha256']:raise ValueError('Unverified game archive')
  shutil.copyfile(a.game,app/'ico.o2r')
 expected=inventory(app)
 result={'source':identity,'title_id':TITLE,'version':param['contentVersion'],'console_tested':False,'game_included':bool(a.game),'fself_integrity':'valid','linked_elf_sha256':sha(linked/'llvm-pie.elf'),'imports':re.findall(r'\bUND[ \t]+(\S+)',symbols),'files':expected}
 if a.pack_python:
  dest=ROOT/'dist'/('ICO-PS5-'+TITLE+('-with-game' if a.game else '-app')+'.ffpfsc')
  with tempfile.TemporaryDirectory(prefix='ico-pack-',dir=ROOT/'build/ps5') as tmp:
   tmp=Path(tmp);packed=tmp/'game.ffpfsc';unpacked=tmp/'unpacked'
   run([a.pack_python,'-m','mkpfs','pack','folder','--verify',app,packed],linked/'pack.log')
   run([a.pack_python,'-m','mkpfs','unpack','--deep',packed,unpacked],linked/'unpack.log')
   if inventory(unpacked)!=expected:raise ValueError('FFPFSC roundtrip mismatch')
   os.replace(packed,dest)
  result['package']={'path':str(dest.relative_to(ROOT)),'size':dest.stat().st_size,'sha256':sha(dest),'roundtrip_files':len(expected)}
 receipt=app.parent/'verification.json';receipt.write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps({k:v for k,v in result.items() if k not in ['files','imports']},indent=2))
if __name__=='__main__':main()
