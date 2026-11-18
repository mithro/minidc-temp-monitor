/* Linker script of the bootloader.  The boot area is mapped at address 0
 * while it runs.  Preprocessed with BOOT_SIZE and RAM_SIZE defined. */
ENTRY(_start)

MEMORY
{
	FLASH (rx) : ORIGIN = 0x00000000, LENGTH = BOOT_SIZE
	RAM (xrw)  : ORIGIN = 0x20000000, LENGTH = RAM_SIZE
}

SECTIONS
{
	.text :
	{
		KEEP(*(.init))
		*(.text .text.*)
		*(.rodata .rodata.* .srodata .srodata.*)
		. = ALIGN(4);
	} >FLASH

	/* All state lives on the stack, so there is no data to copy or clear. */
	.data : { *(.data .data.* .sdata .sdata.*) } >RAM AT>FLASH
	.bss (NOLOAD) : { *(.bss .bss.* .sbss .sbss.* COMMON) } >RAM
	ASSERT(SIZEOF(.data) == 0, "bootloader must not have initialised data")
	ASSERT(SIZEOF(.bss) == 0, "bootloader must not have static data")

	PROVIDE(_eusrstack = ORIGIN(RAM) + LENGTH(RAM));

	/* The application looks for the signature word at this offset. */
	ASSERT(boot_main >= 16, "boot signature is not at offset 12")

	/DISCARD/ : { *(.eh_frame) *(.comment) *(.note.*) }
}
