# Firmware for the sensor strip boards: relay application and I2C bootloader,
# each for the CH32V003 and the CH32V005.  See README.md.
#
#   make            build everything into build/
#   make test       run the host tests
#   make clean

PREFIX   ?= riscv64-unknown-elf
NEWLIB   ?= /usr/include/newlib
CH32FUN  := ch32fun/ch32fun
PYTHON   ?= python3
B        := build

# Downstream I2C speed in Hz.  Raise to 100000 only if R5/R6 are fitted.
DN_I2C_HZ ?= 10000

CFLAGS_COMMON := -Os -flto -ffunction-sections -fdata-sections -fmessage-length=0 \
	-msmall-data-limit=8 -fno-tree-loop-distribute-patterns -mabi=ilp32e \
	-static-libgcc -nostdlib -Wall -Wextra -Wno-unused-parameter \
	-I$(NEWLIB) -I$(CH32FUN) -Ich32fun/extralibs -Icommon
LDFLAGS_COMMON := -Wl,--gc-sections -Lch32fun/misc -lgcc

# Per MCU: compiler flags, linker script variant of ch32fun.ld, boot area, RAM
FLAGS_ch32v003 := -march=rv32ec -DCH32V003
FLAGS_ch32v005 := -march=rv32ec_zmmul -DCH32V005 -DCH32V00x=1
LD_ch32v003    := 0
LD_ch32v005    := 6
BOOT_ch32v003  := 1920
BOOT_ch32v005  := 3328
RAM_ch32v003   := 2K
RAM_ch32v005   := 6K

MCUS := ch32v003 ch32v005
RELAY_SRC := relay/main.c relay/relay_core.c $(CH32FUN)/ch32fun.c
RELAY_DEP := $(RELAY_SRC) $(wildcard relay/*.h common/*.h)
BOOT_DEP  := bootloader/boot.c $(wildcard bootloader/*.h common/*.h)

all: $(foreach m,$(MCUS),$(B)/relay-$(m).bin $(B)/relay-$(m)-full.bin $(B)/boot-$(m).bin)
	@$(PREFIX)-size $(B)/*.elf

$(B):
	mkdir -p $@

define mcu_rules
$(B)/relay-$(1).ld: $(CH32FUN)/ch32fun.ld | $(B)
	$(PREFIX)-gcc -E -P -x c -DTARGET_MCU_LD=$(LD_$(1)) $$< > $$@

$(B)/relay-$(1).elf: $(RELAY_DEP) $(B)/relay-$(1).ld
	$(PREFIX)-gcc $(CFLAGS_COMMON) $(FLAGS_$(1)) -DDN_I2C_HZ=$(DN_I2C_HZ)u -Irelay \
		$(RELAY_SRC) -o $$@ -T $(B)/relay-$(1).ld $(LDFLAGS_COMMON) -Wl,-Map=$(B)/relay-$(1).map

# Application plus its image marker, for programming a blank board over SWIO.
$(B)/relay-$(1)-full.bin: $(B)/relay-$(1).bin tools/minidc.py
	$(PYTHON) tools/minidc.py mkimage --mcu $(1) $$< $$@

$(B)/boot-$(1).ld: bootloader/boot.ld.S | $(B)
	$(PREFIX)-gcc -E -P -x c -DBOOT_SIZE=$(BOOT_$(1)) -DRAM_SIZE=$(RAM_$(1)) $$< > $$@

$(B)/boot-$(1).elf: $(BOOT_DEP) $(B)/boot-$(1).ld
	$(PREFIX)-gcc $(CFLAGS_COMMON) $(FLAGS_$(1)) -ffreestanding -Ibootloader \
		bootloader/boot.c -o $$@ -T $(B)/boot-$(1).ld $(LDFLAGS_COMMON) -Wl,-Map=$(B)/boot-$(1).map
endef
$(foreach m,$(MCUS),$(eval $(call mcu_rules,$(m))))

%.bin: %.elf
	$(PREFIX)-objcopy -O binary $< $@

# Host tests: the protocol code of both programs in a simulated chain, then
# the Python hub library against the same simulation.
HOST_CC ?= cc
HOST_CFLAGS := -std=gnu11 -O1 -g -Wall -Wextra -Werror -fsanitize=address,undefined \
	-Icommon -Irelay -Ibootloader
SIM_DEP := test/sim.c relay/relay_core.c $(wildcard relay/*.h bootloader/*.h common/*.h)

$(B)/sim-ch32v003: $(SIM_DEP) | $(B)
	$(HOST_CC) $(HOST_CFLAGS) test/sim.c relay/relay_core.c -o $@

$(B)/sim-ch32v005: $(SIM_DEP) | $(B)
	$(HOST_CC) $(HOST_CFLAGS) -DSIM_V005 test/sim.c relay/relay_core.c -o $@

test: $(B)/sim-ch32v003 $(B)/sim-ch32v005
	$(PYTHON) tools/gen_ntc_table.py --check common/ntc_table.h
	$(B)/sim-ch32v003
	$(B)/sim-ch32v005
	$(PYTHON) test/test_hub.py $(B)

clean:
	rm -rf $(B)

.PHONY: all test clean
