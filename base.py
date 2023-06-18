#!/usr/bin/env python3
import os
import argparse
import sys
import subprocess
from migen import *
from litex.build.generic_platform import IOStandard, Subsignal, Pins
from migen.genlib.resetsync import AsyncResetSynchronizer
from litex.build.io import DDROutput
from litex_boards.platforms import colorlight_i5
from litex.build.lattice.trellis import trellis_args, trellis_argdict
from litex.soc.cores.clock import *
from litex.soc.integration.soc_core import *
from litex.soc.integration.builder import *
from litedram.modules import M12L64322A # Compatible with EM638325-6H.
from litedram.phy import GENSDRPHY, HalfRateGENSDRPHY
from litespi.modules import GD25Q16
from litespi.opcodes import SpiNorFlashOpCodes as Codes
from litex.soc.cores.spi import SPIMaster
from liteeth.phy.rmii import LiteEthPHYRMII
from litex.soc.cores.bitbang import I2CMaster
from ios import Led
# IOs ------------------------------------------------------------------------
_serial = [
    ("serial", 0,
        Subsignal("tx", Pins("J17")),  # J1.1
        Subsignal("rx", Pins("H18")),  # J1.2
        IOStandard("LVCMOS33")
     ),
]
_leds = [
    ("user_led", 0, Pins("U16"), IOStandard("LVCMOS33")),  # LED en la placa
    ("user_led", 1, Pins("F3"), IOStandard("LVCMOS33")),  # LED externo
]

_i2c = [("i2c", 0,
            Subsignal("sda",   Pins("C17")),
            Subsignal("scl",   Pins("B18")),
            IOStandard("LVCMOS33"),
        )
]


_spi = [("spi", 0,
                Subsignal("cs_n", Pins("D1")), 
                Subsignal("clk",  Pins("C1")), 
                Subsignal("mosi", Pins("C2")), 
                Subsignal("miso", Pins("E3")),
                IOStandard("LVCMOS33"),
        ) 
]
        
# BaseSoC -----------------------------------------------------------------------------------------
class _CRG(Module):
    def __init__(self, platform, sys_clk_freq, use_internal_osc=False, with_usb_pll=False, with_rst=True, sdram_rate="1:1"):
        self.rst    = Signal()
        self.clock_domains.cd_sys      = ClockDomain()
        self.clock_domains.cd_sys2x    = ClockDomain()
        self.clock_domains.cd_sys2x_ps = ClockDomain()
        clk = platform.request("clk25")
        clk_freq = 25e6
        rst_n = platform.request("cpu_reset_n", 0)
        # PLL
        self.submodules.pll = pll = ECP5PLL()
        self.comb += pll.reset.eq(~rst_n | self.rst)
        pll.register_clkin(clk, clk_freq)
        pll.create_clkout(self.cd_sys,    sys_clk_freq)
        pll.create_clkout(self.cd_sys2x,    2*sys_clk_freq)
        pll.create_clkout(self.cd_sys2x_ps, 2*sys_clk_freq, phase=180) # Idealy 90° but needs to be increased.
        # SDRAM clock
        sdram_clk = ClockSignal("sys2x_ps")
        self.specials += DDROutput(1, 0, platform.request("sdram_clock"), sdram_clk)
        
# BaseSoC --------------------------------------------------------------------
class BaseSoC(SoCCore):
    def __init__(self):
        SoCCore.mem_map = {
            "rom":          0x00000000,
            "sram":         0x10000000,
            "main_ram":     0x40000000,
            "csr":          0x82000000,
        }
        platform = colorlight_i5.Platform()
        sys_clk_freq = int(100e6)
        platform.add_extension(_serial)
        platform.add_extension(_leds)
        platform.add_extension(_i2c)
        platform.add_extension(_spi)
        # SoC with CPU
        SoCCore.__init__(
            self, platform,
            cpu_type                 = "vexriscv",
            clk_freq                 = sys_clk_freq,
            ident                    = "LiteX CPU cain_test", ident_version=True,
            integrated_rom_size      = 0x9000,
            timer_uptime             = True)
        self.submodules.crg = _CRG(
            platform         = platform, 
            sys_clk_freq     = sys_clk_freq,
            use_internal_osc = False,
            with_usb_pll     = False,
            sdram_rate       = "1:1"
        )
        # SDR SDRAM --------------------------------------------------------------------------------
        self.sdrphy = GENSDRPHY(platform.request("sdram"))
        self.add_sdram("sdram",
            phy           = self.sdrphy,
            module        = M12L64322A(sys_clk_freq,  "1:2"),
            origin        = self.mem_map["main_ram"],
            l2_cache_size = 8192,
        )
        self.ethphy = LiteEthPHYRMII(
          clock_pads = self.platform.request("eth_clocks"),
          pads       = self.platform.request("eth"),
          refclk_cd  = None)
        self.add_ethernet(phy=self.ethphy)
        self.i2c0 = I2CMaster(pads=platform.request("i2c"))
        # SPI --------------------------------------------------------------------------------
        spi_pads = self.platform.request("spi", 0)
        self.submodules.spi1 = SPIMaster(spi_pads, 8, self.sys_clk_freq, 8e6)
        self.spi1.add_clk_divider()
        self.add_csr("spi1")
        
        # Led
        user_leds = Cat(*[platform.request("user_led", i) for i in range(1)])
        self.submodules.leds = Led(user_leds)
#        self.add_spi_flash(mode="1x", module=GD25Q16(Codes.READ_1_1_1), with_master=True)  #What is the diference with master=false?
        self.add_csr("leds")
# Build -----------------------------------------------------------------------
soc = BaseSoC()
builder = Builder(soc, output_dir="build", csr_csv="csr.csv", csr_svd="csr.svd", csr_json="csr.json")
builder.build()

#https://github.com/litex-hub/litespi/issues/52


















