#!/usr/bin/env python3
"""Fetch pinned ICO dependencies and reuse a verified public PS5 RADV SDK cache.

--runtime-cache points to a PS5_Vulkan checkout built by its tools/build-radv.sh.
The source cache is only read; the project receives its own installed copy.
"""
import argparse,hashlib,json,shutil,subprocess,urllib.request
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
URLS={'sdl3':'https://github.com/libsdl-org/SDL.git','volk':'https://github.com/zeux/volk.git','vulkan-headers':'https://github.com/KhronosGroup/Vulkan-Headers.git','libmpeg2':'https://android.googlesource.com/platform/external/libmpeg2','libchdr':'https://github.com/rtissera/libchdr.git','PS5_Vulkan':'https://github.com/mihawk-99/PS5_Vulkan.git'}
def run(args):subprocess.run(list(map(str,args)),check=True,cwd=ROOT)
def sha(p):
 h=hashlib.sha256()
 with p.open('rb') as f:
  for b in iter(lambda:f.read(1048576),b''):h.update(b)
 return h.hexdigest()
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--runtime-cache',type=Path,required=True)
 p.add_argument('--compiler-rt',type=Path,required=True)
 p.add_argument('--llvm-bin',type=Path,default=Path('/opt/homebrew/opt/llvm@18/bin'))
 p.add_argument('--dxc-archive',type=Path)
 p.add_argument('--build-images',action='store_true')
 a=p.parse_args();cache=a.runtime_cache.resolve();lock=json.loads((ROOT/'port/ps5/dependencies.json').read_text());deps=ROOT/'build/deps';deps.mkdir(parents=True,exist_ok=True)
 for name,rev in lock['sources'].items():
  dst=deps/name
  if dst.is_symlink():raise ValueError('Expected independent dependency folder: '+str(dst))
  if not dst.exists():
   run(['git','init',dst]);run(['git','-C',dst,'remote','add','origin',URLS[name]])
   run(['git','-C',dst,'fetch','--depth','1','origin',rev]);run(['git','-C',dst,'checkout','--detach','FETCH_HEAD'])
  got=subprocess.check_output(['git','-C',str(dst),'rev-parse','HEAD'],text=True).strip()
  if got!=rev:raise ValueError(name+' differs from pin')
 vk=deps/'PS5_Vulkan';runtime=lock['runtime']
 src=cache/'.deps/native/radv-release/lib/libvulkan_radeon.ps5.a'
 if sha(src)!=runtime['radv_sha256'] or sha(cache/'runtime/libc.prx')!=runtime['libc_sha256']:raise ValueError('Unexpected PS5 runtime cache')
 if sha(a.compiler_rt)!=runtime['builtins_sha256']:raise ValueError('Unexpected compiler-rt')
 if cache!=vk:
  shutil.copytree(cache/'.deps/native',vk/'.deps/native',symlinks=False,dirs_exist_ok=True)
  shutil.copyfile(cache/'runtime/libc.prx',vk/'runtime/libc.prx')
 (deps/'compiler-rt').mkdir(exist_ok=True);shutil.copyfile(a.compiler_rt,deps/'compiler-rt/libclang_rt.builtins-x86_64.a') if a.compiler_rt.resolve()!=deps/'compiler-rt/libclang_rt.builtins-x86_64.a' else None
 # macOS iconv's EUC-JP roundtrip can change C backslash escapes. Restore
 # original Git blobs with Python's codec; never overwrite modified files.
 for line in (ROOT/'.gitattributes').read_text().splitlines():
  if line.endswith(' working-tree-encoding=EUC-JP'):
   name=line.split()[0];expected=subprocess.check_output(['git','show',lock['upstream']+':'+name],cwd=ROOT).decode('utf8').encode('euc_jp');path=ROOT/name
   if path.read_bytes()!=expected:
    # Refuse real edits; allow only Git's platform checkout conversion.
    clean=subprocess.check_output(['git','diff','--',name],cwd=ROOT)
    if clean and b'\xef\xbc\xbc' not in clean:raise ValueError('Modified game source: '+name)
    path.write_bytes(expected)
 run(['python3',ROOT/'tools/prepare-ps5-sdl.py',deps/'sdl3'])
 dxc=deps/'dxc';dxc.mkdir(exist_ok=True);archive=dxc/'dxc.tar.gz'
 if a.dxc_archive:
  if a.dxc_archive.resolve()!=archive:shutil.copyfile(a.dxc_archive,archive)
 elif not archive.exists():urllib.request.urlretrieve('https://github.com/microsoft/DirectXShaderCompiler/releases/download/v1.9.2609/linux_dxc_2026_09_28.x86_x64.tar.gz',archive)
 if sha(archive)!=lock['dxc']['archive_sha256']:raise ValueError('DXC archive hash mismatch')
 shutil.copyfile(ROOT/'port/ps5/Dockerfile.dxc',dxc/'Dockerfile')
 wrapper=dxc/'dxc'
 import shlex
 wrapper.write_text('#!/bin/sh\nexec docker run --rm --platform linux/amd64 -v '+shlex.quote(str(ROOT)+':'+str(ROOT))+' -w "$PWD" ico-ps5-dxc:local "$@"\n');wrapper.chmod(0o755)
 if a.build_images:
  run(['docker','build','-t','ico-ps5-dxc:local',dxc])
  run(['docker','build','-t','ico-ps5-builder:local','-f',ROOT/'port/ps5/Dockerfile.builder',ROOT/'port/ps5'])
 n=vk/'tooling/native';tool=ROOT/'build/ps5/ps5-native-tool';tool.parent.mkdir(parents=True,exist_ok=True)
 run([a.llvm_bin/'clang++','-std=c++20','-O2',n/'native_app_builder.cpp',n/'self_container.cpp',n/'elf_object.cpp',n/'sce_module_writer.cpp','-lz','-o',tool])
 print('Pinned dependencies and native tool ready. Build commands: port/ps5/README.md')
if __name__=='__main__':main()
