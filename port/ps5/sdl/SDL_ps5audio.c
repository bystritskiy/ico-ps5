/*
  Simple DirectMedia Layer
  Copyright (C) 1997-2026 Sam Lantinga <slouken@libsdl.org>

  This software is provided 'as-is', without any express or implied
  warranty.  In no event will the authors be held liable for any damages
  arising from the use of this software.

  Permission is granted to anyone to use this software for any purpose,
  including commercial applications, and to alter it and redistribute it
  freely, subject to the following restrictions:

  1. The origin of this software must not be misrepresented; you must not
     claim that you wrote the original software. If you use this software
     in a product, an acknowledgment in the product documentation would be
     appreciated but is not required.
  2. Altered source versions must be plainly marked as such, and must not be
     misrepresented as being the original software.
  3. This notice may not be removed or altered from any source distribution.
*/
/* Altered for ICO PS5: native AudioOut, SDL conversion and callback thread. */
#include "SDL_internal.h"
#include "../SDL_sysaudio.h"
#include "SDL_dummyaudio.h"
extern int sceAudioOutInit(void);
extern int sceAudioOutOpen(int,int,int,unsigned,unsigned,unsigned);
extern int sceAudioOutOutput(int,const void *);
extern int sceAudioOutClose(int);
static bool PS5_Open(SDL_AudioDevice *device)
{
    if(device->recording)return SDL_SetError("PS5 recording unavailable");
    device->hidden=SDL_calloc(1,sizeof(*device->hidden));
    if(!device->hidden)return false;
    device->hidden->handle=-1;
    device->spec.format=SDL_AUDIO_S16;
    device->spec.channels=2;device->spec.freq=48000;device->sample_frames=256;
    SDL_UpdatedAudioDeviceFormat(device);
    device->hidden->mixbuf=SDL_aligned_alloc(64,device->buffer_size);
    if(!device->hidden->mixbuf)return false;
    sceAudioOutInit();
    device->hidden->handle=sceAudioOutOpen(255,0,0,256,48000,1);
    if(device->hidden->handle<0)return SDL_SetError("sceAudioOutOpen: 0x%x",device->hidden->handle);
    SDL_memset(device->hidden->mixbuf,0,device->buffer_size);return true;
}
static void PS5_Close(SDL_AudioDevice *device)
{
    if(!device->hidden)return;
    if(device->hidden->handle>=0){sceAudioOutOutput(device->hidden->handle,NULL);sceAudioOutClose(device->hidden->handle);}
    SDL_aligned_free(device->hidden->mixbuf);SDL_free(device->hidden);device->hidden=NULL;
}
/* WaitDevice runs outside SDL's device lock. AudioOut blocks on the device
 * clock; blocking in PlayDevice would starve stream writes and shutdown. */
static bool PS5_Wait(SDL_AudioDevice *device)
{
    int rc=sceAudioOutOutput(device->hidden->handle,device->hidden->mixbuf);
    return rc>=0?true:SDL_SetError("sceAudioOutOutput: 0x%x",rc);
}
static bool PS5_Play(SDL_AudioDevice *device,const Uint8 *buffer,int length)
{
    if(buffer!=device->hidden->mixbuf)SDL_memcpy(device->hidden->mixbuf,buffer,length);
    return true;
}
static Uint8 *PS5_Buffer(SDL_AudioDevice *device,int *size){*size=device->buffer_size;return device->hidden->mixbuf;}
static bool PS5_Init(SDL_AudioDriverImpl *impl)
{
    impl->OpenDevice=PS5_Open;impl->CloseDevice=PS5_Close;
    impl->WaitDevice=PS5_Wait;impl->PlayDevice=PS5_Play;impl->GetDeviceBuf=PS5_Buffer;
    impl->OnlyHasDefaultPlaybackDevice=true;return true;
}
AudioBootStrap DUMMYAUDIO_bootstrap={"ps5","PS5 AudioOut",PS5_Init,false,false};
