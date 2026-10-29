/* ICO PS5, MIT. Real SDL audio conversion/thread with mocked AudioOut. */
#include <SDL3/SDL.h>
#include <stdatomic.h>
#include <stdint.h>
#include <assert.h>
#include <stdio.h>
static atomic_int outputs,nonzero,closed,fail_open;
int sceAudioOutInit(void){return 0;}
int sceAudioOutOpen(int u,int t,int i,unsigned frames,unsigned rate,unsigned format)
{
 assert(u==255&&t==0&&i==0&&frames==256&&rate==48000&&format==1);
 return atomic_load(&fail_open)?-1:19;
}
int sceAudioOutOutput(int h,const void *p)
{
 assert(h==19);
 if(p){const int16_t *samples=p;for(int i=0;i<512;i++)if(samples[i]){atomic_fetch_add(&nonzero,1);break;}
 atomic_fetch_add(&outputs,1);SDL_DelayNS(5333333);}
 return 0;
}
int sceAudioOutClose(int h){assert(h==19);atomic_fetch_add(&closed,1);return 0;}
int main(void)
{
 SDL_SetHint(SDL_HINT_AUDIO_DRIVER,"ps5");assert(SDL_Init(SDL_INIT_AUDIO));
 SDL_AudioSpec want={SDL_AUDIO_F32,1,44100};
 SDL_AudioStream *s=SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,&want,NULL,NULL);assert(s);
 float samples[22050];for(int i=0;i<22050;i++)samples[i]=(i%80<40)?.25f:-.25f;
 assert(SDL_PutAudioStreamData(s,samples,sizeof(samples)));assert(SDL_ResumeAudioStreamDevice(s));
 SDL_Delay(150);assert(atomic_load(&outputs)>4);assert(atomic_load(&nonzero)>2);
 Uint64 closing=SDL_GetTicks();SDL_DestroyAudioStream(s);assert(SDL_GetTicks()-closing<1000);assert(atomic_load(&closed)==1);
 atomic_store(&fail_open,1);s=SDL_OpenAudioDeviceStream(SDL_AUDIO_DEVICE_DEFAULT_PLAYBACK,&want,NULL,NULL);assert(!s);
 assert(atomic_load(&closed)==1);SDL_Quit();
 puts("PS5 audio: 44.1 kHz float mono -> 48 kHz S16 stereo, playback, shutdown and open failure passed");return 0;
}
