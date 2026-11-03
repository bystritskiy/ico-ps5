/* ICO PS5, MIT. Memory protection must enter through libkernel.
 * PayloadSDK's libc.a defines mmap and mprotect as raw syscalls; a native
 * title may not issue one directly, or the kernel terminates it with
 * SYSTEM_ILLEGAL_FUNCTION_CALL (PPRBUG-22859: syscall 477 from Mesa's disk
 * cache at radv_physical_device_try_create, observed on the console).
 * Defined here, they keep libc.a's mman.o out of the link; libkernel errors
 * are 0x8002xxxx with the FreeBSD errno in the low 16 bits. */
#include <errno.h>
#include <stddef.h>
#include <stdint.h>
#include <sys/mman.h>
#include <sys/types.h>

extern int sceKernelMmap(void *, size_t, int, int, int, off_t, void **);
extern int sceKernelMprotect(const void *, size_t, int);

void *mmap(void *at, size_t size, int prot, int flags, int fd, off_t offset)
{
    void *mapped = NULL;
    int error = sceKernelMmap(at, size, prot, flags, fd, offset, &mapped);
    if (error) {
        errno = error & 0xffff;
        return MAP_FAILED;
    }
    return mapped;
}

int mprotect(const void *at, size_t size, int prot)
{
    int error = sceKernelMprotect(at, size, prot);
    if (error) {
        errno = error & 0xffff;
        return -1;
    }
    return 0;
}
