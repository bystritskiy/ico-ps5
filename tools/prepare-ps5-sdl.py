#!/usr/bin/env python3
"""Apply the ICO PS5 SDL adapters to pinned SDL 3.4.18 sources."""
from pathlib import Path
import subprocess,shutil,sys
root=Path(__file__).resolve().parent.parent
s=Path(sys.argv[1]).resolve()
if subprocess.check_output(['git','-C',str(s),'rev-parse','HEAD'],text=True).strip()!='829a65d769d935c4852f8159e964312c0957260a':
    raise SystemExit('Expected SDL release-3.4.18')
shutil.copyfile(root/'port/ps5/sdl/SDL_ps5vulkan.c',s/'src/video/offscreen/SDL_offscreenvulkan.c')
shutil.copyfile(root/'port/ps5/sdl/SDL_ps5audio.c',s/'src/audio/dummy/SDL_dummyaudio.c')
p=s/'src/audio/dummy/SDL_dummyaudio.h';t=p.read_text();t=t.replace('    Uint32 io_delay;', '    int handle;\n    Uint32 io_delay;') if 'int handle;' not in t else t;p.write_text(t)
p=s/'src/video/offscreen/SDL_offscreenvideo.c';t=p.read_text().replace('mode.w = 1024;','mode.w = 1920;').replace('mode.h = 768;','mode.h = 1080;');p.write_text(t)

p=s/"CMakeLists.txt";t=p.read_text().replace('dep_option(SDL_VIRTUAL_JOYSTICK    "Enable the virtual-joystick driver" ON SDL_HIDAPI OFF)', 'dep_option(SDL_VIRTUAL_JOYSTICK    "Enable the virtual-joystick driver" ON SDL_JOYSTICK OFF)');p.write_text(t)

p=s/"CMakeLists.txt";t=p.read_text().replace('if(FREEBSD OR NETBSD OR OPENBSD OR BSDI)','if((FREEBSD OR NETBSD OR OPENBSD OR BSDI) AND NOT ICO_PS5)');p.write_text(t)

# A console display always owns focus; offscreen has no window manager.
p=s/"src/video/offscreen/SDL_offscreenwindow.c";t=p.read_text()
if "ICO PS5: console focus" not in t:
 t=t.replace('#include "../SDL_sysvideo.h"','#include "../SDL_sysvideo.h"\n#include "../../events/SDL_keyboard_c.h"')
 t=t.replace('    return true;\n}', '    /* ICO PS5: console focus, no window manager. */\n    SDL_SetKeyboardFocus(window);\n    return true;\n}',1)
 p.write_text(t)

p=s/"CMakeLists.txt";t=p.read_text().replace('dep_option(SDL_HIDAPI_JOYSTICK     "Use HIDAPI for low level joystick drivers" ON SDL_JOYSTICK OFF)','dep_option(SDL_HIDAPI_JOYSTICK     "Use HIDAPI for low level joystick drivers" ON SDL_HIDAPI OFF)');p.write_text(t)
