#!/usr/bin/env python3
"""Make a store release of the ICO PS5 app from tools/package-ps5.py's app-only stage.

  dist/release/<TITLE>.zip            the <TITLE>/ app folder at the top of the
                                      archive, as ProsperoStore and RecompStore
                                      install it; no game data
  dist/release/ICO-PS5-<version>-third-party-source.tar.xz
                                      the GPL parts' source at the pinned revisions
  dist/release/release.json           hashes, revisions and what was checked

It refuses uncommitted changes, a --devtools build, a stage that differs from
its receipt, and any game data in the stage. --allow-dirty makes a trial
release for checking the steps; its files are named -dirty and are not for
publishing.
"""
import argparse,hashlib,json,shutil,subprocess,tarfile,tempfile,time,zipfile
from pathlib import Path
from ps5_provenance import source_identity
ROOT=Path(__file__).resolve().parent.parent
LOCK=json.loads((ROOT/'port/ps5/dependencies.json').read_text())
TITLE=LOCK['title_id']
# The app may hold only these: the program, its runtime module, the tile's
# metadata and art, and the licences. Anything else (an archive of game data,
# a disc image, a stray file) stops the release.
ALLOWED=('eboot.bin','sce_module/libc.prx','sce_sys/','licenses/')
GPL_SOURCES={'PS5_Vulkan':('https://github.com/mihawk-99/PS5_Vulkan.git',LOCK['sources']['PS5_Vulkan']),
             'PS5_PayloadSDK':('https://github.com/mihawk-99/PS5_PayloadSDK.git',LOCK['PS5_PayloadSDK']),
             'PS5_Mesa':('https://github.com/mihawk-99/PS5_Mesa.git',LOCK['PS5_Mesa'])}
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def git(*args,cwd=ROOT):return subprocess.check_output(['git',*map(str,args)],cwd=cwd,text=True).strip()
def checkout(name,url,rev,cache):
 """A clean tree of url at rev under cache/name (fetched once)."""
 dst=cache/name
 if not (dst/'.git').exists():
  dst.mkdir(parents=True,exist_ok=True)
  subprocess.run(['git','init','-q',dst],check=True);subprocess.run(['git','-C',dst,'remote','add','origin',url],check=True)
 if subprocess.run(['git','-C',dst,'cat-file','-e',rev+'^{commit}'],capture_output=True).returncode!=0:
  subprocess.run(['git','-C',dst,'fetch','-q','--depth','1','origin',rev],check=True)
 return dst
def main():
 p=argparse.ArgumentParser(description=__doc__,formatter_class=argparse.RawDescriptionHelpFormatter)
 p.add_argument('--allow-dirty',action='store_true',help='a trial release of uncommitted changes, never published')
 a=p.parse_args()
 identity=source_identity()
 dirty=bool(git('status','--porcelain','--untracked-files=normal'))
 if dirty and not a.allow_dirty:raise SystemExit('Commit the changes first (git status is not clean)')
 receipt=json.loads((ROOT/'dist/app/verification.json').read_text())
 if receipt['source']!=identity:raise SystemExit('dist/app is from other sources: run tools/build-ps5.py and tools/package-ps5.py')
 if receipt.get('devtools'):raise SystemExit('dist/app is a --devtools build: build again without it')
 if receipt['game_included']:raise SystemExit('dist/app holds game data')
 app=ROOT/'dist/app'/TITLE
 files={x.relative_to(app).as_posix():x for x in sorted(app.rglob('*')) if x.is_file() and x.name!='.DS_Store'}
 stray=[n for n in files if not any(n==r or (r.endswith('/') and n.startswith(r)) for r in ALLOWED)]
 if stray:raise SystemExit('Not allowed in a release: '+', '.join(stray))
 for n,x in files.items():
  want=receipt['files'].get(n)
  if want is None or want['sha256']!=sha(x):raise SystemExit('The stage differs from its receipt: '+n)
 if set(receipt['files'])!=set(files):raise SystemExit('The stage lacks files its receipt lists')
 param=json.loads((app/'sce_sys/param.json').read_text())
 if param['titleId']!=TITLE or param['contentVersion']!=LOCK['ps5_content_version']:raise SystemExit('param.json disagrees with dependencies.json')
 version=param['contentVersion'];suffix='-dirty' if dirty else ''
 out=ROOT/'dist/release';out.mkdir(parents=True,exist_ok=True)
 # The zip: sorted names, one fixed time stamp, so a rebuild of the same
 # stage gives the same bytes.
 zpath=out/(TITLE+suffix+'.zip');stamp=(2026,1,1,0,0,0)
 with zipfile.ZipFile(zpath,'w',zipfile.ZIP_DEFLATED,compresslevel=9) as z:
  for n,x in files.items():
   info=zipfile.ZipInfo(TITLE+'/'+n,stamp);info.compress_type=zipfile.ZIP_DEFLATED;info.external_attr=0o644<<16
   z.writestr(info,x.read_bytes())
 with zipfile.ZipFile(zpath) as z:
  names=z.namelist()
  if any(not n.startswith(TITLE+'/') for n in names) or TITLE+'/eboot.bin' not in names or TITLE+'/sce_sys/param.json' not in names:
   raise SystemExit('Unexpected zip layout')
  for n in names:
   if hashlib.sha256(z.read(n)).hexdigest()!=receipt['files'][n[len(TITLE)+1:]]['sha256']:raise SystemExit('Zip roundtrip mismatch: '+n)
 # The GPL parts' source: the forks at the pinned revisions, as git archives.
 name='ICO-PS5-'+version+suffix+'-third-party-source'
 cache=ROOT/'build/release-sources';revisions={}
 with tempfile.TemporaryDirectory(prefix='ico-src-',dir=ROOT/'build') as tmp:
  stage=Path(tmp)/name;stage.mkdir()
  for repo,(url,rev) in GPL_SOURCES.items():
   src=checkout(repo,url,rev,cache)
   tar=Path(tmp)/(repo+'.tar')
   subprocess.run(['git','-C',src,'archive','--format=tar','--prefix='+repo+'/','-o',tar,rev],check=True)
   with tarfile.open(tar) as t:t.extractall(stage,filter='data')
   (stage/repo/'REVISION').write_text(rev+'\n');revisions[repo]=rev
  shutil.copyfile(ROOT/'port/ps5/dependencies.json',stage/'dependencies.json')
  (stage/'README.txt').write_text(
   'Source code of the GPL parts of the ICO PS5 app '+version+'.\n\n'
   'PS5_Vulkan/      github.com/mihawk-99/PS5_Vulkan: the app CRT, link recipe,\n'
   '                 ps5-native-tool and libc.prx (GPL-3.0-or-later)\n'
   'PS5_PayloadSDK/  github.com/mihawk-99/PS5_PayloadSDK: the payload SDK with the PS5\n'
   '                 platform layer (GPL-3.0-or-later; include/freebsd: BSD)\n'
   'PS5_Mesa/        github.com/mihawk-99/PS5_Mesa: Mesa with RADV\'s PS5 winsys (MIT and\n'
   '                 others, its docs/license.rst)\n\n'
   'Each REVISION names the commit; dependencies.json pins every input. The port\'s own\n'
   'source is the repository and commit '+identity['commit']+'; port/ps5/README.md builds it.\n')
  spath=out/(name+'.tar.xz')
  # macOS writes .DS_Store and ._ files into folders on external drives
  junk=lambda i:None if Path(i.name).name=='.DS_Store' or Path(i.name).name.startswith('._') else i
  with tarfile.open(spath,'w:xz') as t:t.add(stage,arcname=name,filter=junk)
 result={'title_id':TITLE,'version':version,'dirty':dirty,'source':identity,'zip':{'path':str(zpath.relative_to(ROOT)),'size':zpath.stat().st_size,'sha256':sha(zpath),'files':len(names)},
  'third_party_source':{'path':str(spath.relative_to(ROOT)),'size':spath.stat().st_size,'sha256':sha(spath),'revisions':revisions},
  'eboot_sha256':receipt['files']['eboot.bin']['sha256'],'game_included':False,'console_tested':receipt.get('console_tested',False),
  'made':time.strftime('%Y-%m-%dT%H:%M:%SZ',time.gmtime())}
 (out/('release'+suffix+'.json')).write_text(json.dumps(result,indent=2)+'\n')
 print(json.dumps(result,indent=2))
if __name__=='__main__':main()
