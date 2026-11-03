/* Section addresses from the pinned native PS5 PIE layout. */
HIDDEN(ico_image_text_start = ADDR(.text));
HIDDEN(ico_image_text_end = ADDR(.text) + SIZEOF(.text));
HIDDEN(ico_image_ro_start = ADDR(.eh_frame_hdr));
HIDDEN(ico_image_ro_end = ADDR(.rodata) + SIZEOF(.rodata));
HIDDEN(ico_image_end = ADDR(.bss) + SIZEOF(.bss));
