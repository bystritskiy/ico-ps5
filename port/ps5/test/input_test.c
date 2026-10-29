/* ICO PS5, MIT. Real SDL virtual driver with mocked console services. */
#define main ico_ps5_entry
#include "../src/main_ps5.c"
#undef main
#include <assert.h>
static PadData mock;
static int read_rc,opens,closes;
static uint8_t last_motors[2];
int scePthreadSetaffinity(pthread_t t,uint64_t m){(void)t;(void)m;return 0;}
int sceUserServiceInitialize(const void *p){(void)p;return 0;}
int sceUserServiceGetInitialUser(int *p){*p=123;return 0;}
int scePadInit(void){return 0;}
int scePadOpen(int u,int t,int i,const void *p){(void)u;(void)t;(void)i;(void)p;opens++;return 17;}
int scePadGetHandle(int u,int t,int i){(void)u;(void)t;(void)i;return -1;}
int scePadReadState(int h,void *p){assert(h==17);memcpy(p,&mock,sizeof(mock));return read_rc;}
int scePadClose(int h){assert(h==17);closes++;return 0;}
int scePadSetVibration(int h,const void *p){assert(h==17);memcpy(last_motors,p,2);return 0;}
int scePadSetVibrationMode(int h,int m){assert(h==17&&m==2);return 0;}
int sceKernelSendNotificationRequest(int i,void *p,size_t n,int j){(void)i;(void)p;(void)n;(void)j;return 0;}
int ico_host_main(int a,char **v){(void)a;(void)v;return 0;}
static void poll_state(void){SDL_UpdateJoysticks();SDL_UpdateGamepads();}
int main(void)
{
 SDL_SetHint(SDL_HINT_JOYSTICK_ALLOW_BACKGROUND_EVENTS,"1");
 assert(SDL_Init(SDL_INIT_GAMEPAD));assert(attach_virtual_pad());
 SDL_Gamepad *g=SDL_OpenGamepad(virtual_id);assert(g);
 mock.connected=1;mock.lx=mock.ly=mock.rx=mock.ry=128;poll_state();
 assert(opens==1);assert(SDL_GetGamepadAxis(g,SDL_GAMEPAD_AXIS_LEFTX)==0);
 assert(SDL_GetGamepadAxis(g,SDL_GAMEPAD_AXIS_LEFT_TRIGGER)==0);
 const uint32_t ps[]={0x4000,0x2000,0x8000,0x1000,0x8,0x100000,0x400,0x800,0x10,0x40,0x80,0x20,0x2,0x4};
 const SDL_GamepadButton buttons[]={SDL_GAMEPAD_BUTTON_SOUTH,SDL_GAMEPAD_BUTTON_EAST,SDL_GAMEPAD_BUTTON_WEST,SDL_GAMEPAD_BUTTON_NORTH,SDL_GAMEPAD_BUTTON_START,SDL_GAMEPAD_BUTTON_BACK,SDL_GAMEPAD_BUTTON_LEFT_SHOULDER,SDL_GAMEPAD_BUTTON_RIGHT_SHOULDER,SDL_GAMEPAD_BUTTON_DPAD_UP,SDL_GAMEPAD_BUTTON_DPAD_DOWN,SDL_GAMEPAD_BUTTON_DPAD_LEFT,SDL_GAMEPAD_BUTTON_DPAD_RIGHT,SDL_GAMEPAD_BUTTON_LEFT_STICK,SDL_GAMEPAD_BUTTON_RIGHT_STICK};
 for(unsigned i=0;i<sizeof(ps)/sizeof(*ps);i++){
  mock.buttons=ps[i];poll_state();
  for(unsigned j=0;j<sizeof(ps)/sizeof(*ps);j++)assert(SDL_GetGamepadButton(g,buttons[j])==(i==j));
 }
 mock.buttons=0;mock.lx=0;mock.ly=255;mock.l2=255;poll_state();
 assert(SDL_GetGamepadAxis(g,SDL_GAMEPAD_AXIS_LEFTX)==-32768);
 assert(SDL_GetGamepadAxis(g,SDL_GAMEPAD_AXIS_LEFTY)==32767);
 assert(SDL_GetGamepadAxis(g,SDL_GAMEPAD_AXIS_LEFT_TRIGGER)==32767);
 assert(SDL_RumbleGamepad(g,0xff00,0x8000,100));assert(last_motors[0]==255&&last_motors[1]==128);
 read_rc=-1;poll_state();assert(closes==1&&pad==-1);
 assert(!SDL_GetGamepadButton(g,SDL_GAMEPAD_BUTTON_START));
 assert(SDL_GetGamepadAxis(g,SDL_GAMEPAD_AXIS_LEFTX)==0);
 read_rc=0;retry=0;mock.lx=128;poll_state();assert(opens==2&&pad==17);
 close_pad();assert(closes==2);assert(!last_motors[0]&&!last_motors[1]);
 SDL_CloseGamepad(g);SDL_CloseJoystick(joystick);joystick=NULL;SDL_DetachVirtualJoystick(virtual_id);SDL_Quit();
 puts("PS5 input: 14 buttons, axes, triggers, rumble, read failure and reconnect passed");return 0;
}
/* The host SDL build includes the native audio adapter; this test opens no audio. */
int sceAudioOutInit(void){return 0;}
int sceAudioOutOpen(int u,int t,int i,unsigned f,unsigned r,unsigned s){(void)u;(void)t;(void)i;(void)f;(void)r;(void)s;return -1;}
int sceAudioOutOutput(int h,const void *p){(void)h;(void)p;return -1;}
int sceAudioOutClose(int h){(void)h;return 0;}
