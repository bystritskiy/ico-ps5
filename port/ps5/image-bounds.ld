/* Section addresses from the pinned native PS5 PIE layout. */
/* Keep mutable save-state sections in the writable segment. */
SECTIONS { ico_gdata : { *(ico_gdata) } :data } INSERT AFTER .data;
SECTIONS { ico_gbss (NOLOAD) : { *(ico_gbss) } :data } INSERT AFTER .bss;

HIDDEN(ico_image_text_start = ADDR(.text));
HIDDEN(ico_image_text_end = ADDR(.text) + SIZEOF(.text));
HIDDEN(ico_image_ro_start = ADDR(.eh_frame_hdr));
HIDDEN(ico_image_ro_end = ADDR(.rodata) + SIZEOF(.rodata));
HIDDEN(ico_image_end = ADDR(ico_gbss) + SIZEOF(ico_gbss));
