/* ICO PS5 host, MIT. Public PayloadSDK exports, no Sony SDK. */
#include <SDL3/SDL.h>
#include <stdint.h>
#include <stddef.h>
#include <stdio.h>
#include <stdlib.h>
#include <string.h>
#include <sys/stat.h>
#include <unistd.h>
#include <fcntl.h>
#include <pthread.h>
extern int ico_host_main(int, char **);
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
extern int scePadReadState(int,void *);
extern int scePadClose(int);
extern int scePadSetVibration(int,const void *);
extern int scePadSetVibrationMode(int,int);
typedef struct PadData {
    uint32_t buttons;
    uint8_t lx,ly,rx,ry,l2,r2,reserved[66],connected,tail[179];
} PadData;
_Static_assert(offsetof(PadData,connected)==76,"libScePad ABI");
static SDL_Joystick *joystick;
static SDL_JoystickID virtual_id;
static int pad=-1, owned;
static Uint64 retry;
static bool SDLCALL rumble(void *unused, Uint16 low, Uint16 high)
{
    (void)unused;
    uint8_t motors[2]={(uint8_t)(low>>8),(uint8_t)(high>>8)};
    return pad>=0 && scePadSetVibration(pad,motors)>=0;
}
static void close_pad(void)
{
    if (pad>=0) {rumble(NULL,0,0);if(owned)scePadClose(pad);}
    pad=-1;owned=0;
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
        if(sceUserServiceGetInitialUser(&user)>=0) {
            pad=scePadOpen(user,0,0,NULL);owned=pad>=0;
            if(pad<0)pad=scePadGetHandle(user,0,0);
            if(pad>=0)scePadSetVibrationMode(pad,2);
        }
    }
    PadData d={0};
    if(pad>=0 && scePadReadState(pad,&d)<0){close_pad();memset(&d,0,sizeof(d));}
    if(!d.connected){memset(&d,0,sizeof(d));d.lx=d.ly=d.rx=d.ry=128;}
    const uint32_t bits[16]={0x4000,0x2000,0x8000,0x1000,0x100000,0,0x8,0x2,0x4,0x400,0x800,0x10,0x40,0x80,0x20,0x100000};
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
       (mkdir("/data/ico/PPSA99030",0777)<0 && access("/data/ico/PPSA99030",W_OK)<0)) {
        fprintf(stderr,"ICO: cannot create writable /data/ico/PPSA99030\n");return 1;
    }
    mkdir("/data/ico/PPSA99030/logs",0777);
    rename("/data/ico/PPSA99030/logs/boot.log","/data/ico/PPSA99030/logs/boot.previous");
    int boot=open("/data/ico/PPSA99030/logs/boot.log",O_WRONLY|O_CREAT|O_TRUNC,0666);
    if(boot>=0){dup2(boot,STDOUT_FILENO);dup2(boot,STDERR_FILENO);if(boot>2)close(boot);}
    setvbuf(stdout,NULL,_IONBF,0);setvbuf(stderr,NULL,_IONBF,0);
    fprintf(stderr,"ICO PS5: native startup, data /data/ico/PPSA99030\n");
    chdir("/app0");
    setenv("HOME","/data/ico/PPSA99030",1);
    setenv("SDL_VIDEODRIVER","offscreen",1);
    setenv("SDL_AUDIODRIVER","ps5",1);
    SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,"1");
    SDL_SetHint(SDL_HINT_AUDIO_DEVICE_SAMPLE_FRAMES,"256");
    sceUserServiceInitialize(NULL);scePadInit();
    if(!SDL_Init(SDL_INIT_GAMEPAD)){fprintf(stderr,"ICO: SDL gamepad: %s\n",SDL_GetError());return 1;}
    if(!attach_virtual_pad()){fprintf(stderr,"ICO: virtual DualSense: %s\n",SDL_GetError());SDL_Quit();return 1;}
    char *args[]={"/app0/eboot.bin",NULL};
    int rc=ico_host_main(1,args);
    close_pad();
    /* ico_host_shutdown may already have called SDL_Quit. */
    if(SDL_WasInit(SDL_INIT_JOYSTICK)) {
        SDL_CloseJoystick(joystick);SDL_DetachVirtualJoystick(virtual_id);
    }
    joystick=NULL;SDL_Quit();return rc;
}
