#!/usr/bin/env python3
"""Build the native PS5 libraries and link the complete ICO application."""
import argparse,json,subprocess
from ps5_provenance import source_identity
from pathlib import Path
ROOT=Path(__file__).resolve().parent.parent
def run(*args):subprocess.run(list(map(str,args)),check=True,cwd=ROOT)
def main():
 p=argparse.ArgumentParser(description=__doc__)
 p.add_argument('--llvm-bin',type=Path,default=Path('/opt/homebrew/opt/llvm@18/bin'))
 p.add_argument('--jobs',type=int,default=8)
 p.add_argument('--builder-image',default='ico-ps5-builder:local')
 p.add_argument('--devtools',action='store_true',help='DevLoop capture and the menu-less texture export (never a release)')
 a=p.parse_args();identity=source_identity();sdk=ROOT/'build/deps/PS5_Vulkan/.deps/native/ps5-payload-sdk'
 common=['-G','Ninja','-DCMAKE_TOOLCHAIN_FILE='+str(ROOT/'port/ps5/cmake/ps5.cmake'),'-DCMAKE_C_COMPILER='+str(a.llvm_bin/'clang'),'-DPS5_PAYLOAD_SDK='+str(sdk),'-DCMAKE_BUILD_TYPE=Release']
 options=['SDL_STATIC=ON','SDL_SHARED=OFF','SDL_UNIX_CONSOLE_BUILD=ON','SDL_X11=OFF','SDL_WAYLAND=OFF','SDL_KMSDRM=OFF','SDL_OPENGL=OFF','SDL_OPENGLES=OFF','SDL_VULKAN=ON','SDL_OFFSCREEN=ON','SDL_HIDAPI=OFF','SDL_JOYSTICK=ON','SDL_VIRTUAL_JOYSTICK=ON','SDL_AUDIO=ON','SDL_DUMMYAUDIO=ON','SDL_HAPTIC=OFF','SDL_SENSOR=OFF','SDL_OSS=OFF','SDL_TEST_LIBRARY=OFF','SDL_TESTS=OFF','SDL_EXAMPLES=OFF','LIBC_HAS_WCSNLEN=OFF','LIBC_HAS_WCSLCPY=OFF','LIBC_HAS_WCSLCAT=OFF']
 run('python3',ROOT/'tools/prepare-ps5-sdl.py',ROOT/'build/deps/sdl3')
 run('cmake','-S',ROOT/'build/deps/sdl3','-B',ROOT/'build/ps5/sdl3',*common,*['-D'+o for o in options])
 run('cmake','--build',ROOT/'build/ps5/sdl3','-j',a.jobs)
 options=['ICO_VERSION_LABEL=v0.10.0','ICO_HEADLESS=OFF','ICO_LINK_EXE=ON','ICO_DEPS_DIR='+str(ROOT/'build/deps'),'SDL3_DIR='+str(ROOT/'build/ps5/sdl3'),'ICO_DXC='+str(ROOT/'build/deps/dxc/dxc'),'ICO_RHI_MOLTENVK=OFF','ICO_RHI_OPENGL=OFF','ICO_SHADERS_DXIL=OFF','ICO_SHADERS_GLSL=OFF','ICO_SHADERS_D3D11_CHECK=OFF','ICO_PS5_DEVTOOLS='+('ON' if a.devtools else 'OFF')]
 run('cmake','-S',ROOT,'-B',ROOT/'build/ps5/game',*common,*['-D'+o for o in options])
 run('cmake','--build',ROOT/'build/ps5/game','--target','ico_pc','-j',a.jobs)
 run('docker','run','--rm','-v',str(ROOT)+':'+str(ROOT),'-w',ROOT,'-e','ICO_COMPILER_RT='+str(ROOT/'build/deps/compiler-rt/libclang_rt.builtins-x86_64.a'),a.builder_image,'bash','tools/link-ps5.sh')
 if source_identity()!=identity:raise RuntimeError('Sources changed during the build; build again')
 (ROOT/'build/ps5/build-source.json').write_text(json.dumps(dict(identity,devtools=a.devtools),indent=2)+'\n')
if __name__=='__main__':main()
