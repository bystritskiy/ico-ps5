/* ICO PS5 host, MIT. What the shared port/platform code asks of main_ps5.c. */
#ifndef ICO_PS5_HOST_H
#define ICO_PS5_HOST_H

#include <stddef.h>

/* /data/ico/<title ID>: settings, saves, logs and the extracted game data.
   CMakeLists.txt sets it from port/ps5/dependencies.json's title_id. */
#ifndef ICO_PS5_DATA_DIR
#error "ICO_PS5_DATA_DIR comes from CMakeLists.txt (port/ps5/dependencies.json)"
#endif

/* The folders searched for the player's disc image after /app0: the data
   folder, /data/ico, then /mnt/usb0 ... /mnt/usb7 (an ico folder first, then
   the drive's top folder). */
#define ICO_PS5_IMAGE_DIR_COUNT 18
void ico_ps5_image_dir(int k, char *out, size_t size);

/* A system notification ("ICO: " and text). */
void ico_ps5_notify(const char *text);

#endif
