/* ICO PS5 host, MIT. Public PayloadSDK exports, no Sony SDK. */
#include <SDL3/SDL.h>
#include <stdarg.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
#include "ps5_host.h"
#define DATA ICO_PS5_DATA_DIR
extern int ico_host_main(int, char **);
extern int sceSystemServiceHideSplashScreen(void);
extern int sceKernelSendNotificationRequest(int,void *,size_t,int);
void ico_ps5_notify(const char *text)
{
    struct {char reserved[45];char message[3075];} note={0};
    snprintf(note.message,sizeof(note.message),"ICO: %s",text);
    sceKernelSendNotificationRequest(0,&note,sizeof(note),0);
}
extern int scePthreadSetaffinity(pthread_t, uint64_t);
extern int sceUserServiceInitialize(const void *);
extern int sceUserServiceGetInitialUser(int *);
extern int scePadInit(void);
extern int scePadOpen(int,int,int,const void *);
extern int scePadGetHandle(int,int,int);
extern int scePadRead(int,void *,int);
extern int scePadClose(int);
extern int scePadSetVibration(int,const void *);
extern int scePadSetVibrationMode(int,int);
/* One sample as the console writes it: 120 bytes (PS5_Vulkan's recipe and
   PS5_DevilutionX's platform.c agree on the layout). */
typedef struct PadSample {
    uint32_t buttons;
    uint8_t lx,ly,rx,ry,l2,r2;
    uint8_t reserved[66];
    uint8_t connected; /* a bool, then padding */
    uint8_t connected_pad[3];
    uint64_t timestamp_us;
    uint8_t extension[16];
    uint8_t connected_count;
    uint8_t remaining[15];
} PadSample;
_Static_assert(sizeof(PadSample)==120,"libScePad samples are 120 bytes");
_Static_assert(offsetof(PadSample,connected)==0x4c,"connected at 0x4c");
void ico_ps5_image_dir(int k, char *out, size_t size)
{
    if(k==0)snprintf(out,size,"%s",DATA);
    else if(k==1)snprintf(out,size,"/data/ico");
    else if(k<10)snprintf(out,size,"/mnt/usb%d/ico",k-2);
    else snprintf(out,size,"/mnt/usb%d",k-10);
}
static void pad_log(const char *fmt, ...)
{
    FILE *f=fopen(DATA "/logs/pad.log","a");
    if(!f)return;
    va_list ap;va_start(ap,fmt);vfprintf(f,fmt,ap);va_end(ap);
    fputc('\n',f);fclose(f);
}
static SDL_Joystick *joystick;
static SDL_JoystickID virtual_id;
static int pad=-1, owned;
static Uint64 retry;
/* The latest sample of a connected pad. scePadRead returns only the samples
   since the last call, so a call that finds none keeps the buttons held. */
static PadSample last;
static int have_last;
static bool SDLCALL rumble(void *unused, Uint16 low, Uint16 high)
{
    (void)unused;
    uint8_t motors[2]={(uint8_t)(low>>8),(uint8_t)(high>>8)};
    return pad>=0 && scePadSetVibration(pad,motors)>=0;
}
static void close_pad(void)
{
    if (pad>=0) {rumble(NULL,0,0);if(owned)scePadClose(pad);}
    pad=-1;owned=0;have_last=0;
}
static Sint16 stick(uint8_t x)
{
    int value=(int)x-128;
    return (Sint16)(value<0 ? value*256 : value*32767/127);
}
static void SDLCALL update(void *unused)
{
    (void)unused;
    if(!joystick)return;
    if(pad<0 && SDL_GetTicks()>=retry) {
        retry=SDL_GetTicks()+1000;
        int user=-1;
        int urc=sceUserServiceGetInitialUser(&user);
        if(urc>=0) {
            int opened=scePadOpen(user,0,0,NULL);
            int got=opened;
            if(got<0)got=scePadGetHandle(user,0,0);
            pad=got;owned=opened>=0;
            if(pad>=0)scePadSetVibrationMode(pad,2);
            pad_log("open user=%d urc=0x%08x open=0x%08x get=0x%08x",user,(unsigned)urc,(unsigned)opened,(unsigned)got);
        } else {
            pad_log("user rc=0x%08x",(unsigned)urc);
        }
    }
    PadSample samples[64];
    int count=-1;
    if(pad>=0) {
        count=scePadRead(pad,samples,64);
        if(count<0){pad_log("read rc=0x%08x",(unsigned)count);close_pad();}
        else if(count>0) {
            /* the newest sample says whether the pad is still there */
            const PadSample *s=&samples[(count<64?count:64)-1];
            have_last=s->connected!=0;
            if(have_last)last=*s;
        }
    }
    PadSample d;
    if(have_last)d=last;
    else {memset(&d,0,sizeof(d));d.lx=d.ly=d.rx=d.ry=128;}
    {
        /* the log names each change of the pad's state, not every read */
        static int logged_pad=-2, logged_connected=-1;
        if(pad!=logged_pad || have_last!=logged_connected) {
            logged_pad=pad;logged_connected=have_last;
            pad_log("pad=%d owned=%d count=%d connected=%d",pad,owned,count,have_last);
        }
    }
    /* SDL's gamepad order: S E W N, Back (touchpad), Guide (the system's
       PS button), Start (Options), L3 R3, L1 R1, d-pad U D L R, Misc1 */
    const uint32_t bits[16]={0x4000,0x2000,0x8000,0x1000,0x100000,0,0x8,0x2,0x4,0x400,0x800,0x10,0x40,0x80,0x20,0};
    for(int i=0;i<16;i++)SDL_SetJoystickVirtualButton(joystick,i,(d.buttons&bits[i])!=0);
    SDL_SetJoystickVirtualAxis(joystick,0,stick(d.lx));
    SDL_SetJoystickVirtualAxis(joystick,1,stick(d.ly));
    SDL_SetJoystickVirtualAxis(joystick,2,stick(d.rx));
    SDL_SetJoystickVirtualAxis(joystick,3,stick(d.ry));
    SDL_SetJoystickVirtualAxis(joystick,4,(Sint16)((unsigned)d.l2*257-32768));
    SDL_SetJoystickVirtualAxis(joystick,5,(Sint16)((unsigned)d.r2*257-32768));
}
static int attach_virtual_pad(void)
{
    SDL_VirtualJoystickDesc desc;
    SDL_INIT_INTERFACE(&desc);
    desc.type=SDL_JOYSTICK_TYPE_GAMEPAD;
    desc.vendor_id=0x054c;desc.product_id=0x0ce6;
    desc.naxes=6;desc.nbuttons=16;desc.axis_mask=0x3f;desc.button_mask=0xffff;
    desc.name="PS5 DualSense";desc.Update=update;desc.Rumble=rumble;
    virtual_id=SDL_AttachVirtualJoystick(&desc);
    if(virtual_id)joystick=SDL_OpenJoystick(virtual_id);
    return joystick!=NULL;
}
int main(int argc,char **argv)
{
    (void)argc;(void)argv;
    scePthreadSetaffinity(pthread_self(),UINT64_C(0x1fff));
    if((mkdir("/data/ico",0777)<0 && access("/data/ico",W_OK)<0) ||
       (mkdir(DATA,0777)<0 && access(DATA,W_OK)<0)) {
        ico_ps5_notify("cannot create the writable folder " DATA);return 1;
    }
    mkdir(DATA "/logs",0777);
    rename(DATA "/logs/boot.log",DATA "/logs/boot.previous");
    rename(DATA "/logs/pad.log",DATA "/logs/pad.previous");
    /* Native titles can refuse dup2; replace libc streams directly. */
    FILE *boot=fopen(DATA "/logs/boot.log","w");
    if(boot){stdout=boot;stderr=boot;}
    setvbuf(stdout,NULL,_IONBF,0);setvbuf(stderr,NULL,_IONBF,0);
    fprintf(stderr,"ICO PS5: native startup, data " DATA "\n");
    chdir("/app0");
    setenv("HOME",DATA,1);
    setenv("SDL_VIDEODRIVER","offscreen",1);
    setenv("SDL_AUDIODRIVER","ps5",1);
    SDL_SetHint(SDL_HINT_VIDEO_DRIVER,"offscreen");
    SDL_SetHint(SDL_HINT_AUDIO_DRIVER,"ps5");
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,"1");
    SDL_SetHint(SDL_HINT_AUDIO_DEVICE_SAMPLE_FRAMES,"256");
    int us_rc=sceUserServiceInitialize(NULL);
    int pad_rc=scePadInit();
    pad_log("init user=0x%08x pad=0x%08x",(unsigned)us_rc,(unsigned)pad_rc);
    if(!SDL_Init(SDL_INIT_GAMEPAD)){fprintf(stderr,"ICO: SDL gamepad: %s\n",SDL_GetError());return 1;}
    if(!attach_virtual_pad()){fprintf(stderr,"ICO: virtual DualSense: %s\n",SDL_GetError());SDL_Quit();return 1;}
    char *args[]={"/app0/eboot.bin",NULL};
    sceSystemServiceHideSplashScreen();
    int rc=ico_host_main(1,args);
    close_pad();
    /* ico_host_shutdown may already have called SDL_Quit. */
    if(SDL_WasInit(SDL_INIT_JOYSTICK)) {
        SDL_CloseJoystick(joystick);SDL_DetachVirtualJoystick(virtual_id);
    }
    joystick=NULL;SDL_Quit();return rc;
}
