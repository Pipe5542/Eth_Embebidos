from litex.build.generic_platform import *
from litex.build.lattice import LatticeECP5Platform
from litex.build.lattice.programmer import OpenOCDJTAGProgrammer
_io = [
    # Clk
    ("clk25", 0, Pins("P3"), IOStandard("LVCMOS33")),
    # Led
    ("user_led_n", 0, Pins("T6"), IOStandard("LVCMOS33")),
    # Button
    ("user_btn_n", 0, Pins("K18"), Misc("PULLMODE=UP"), IOStandard("LVCMOS33")),
    # Serial
    ("serial", 0,
        Subsignal("tx", Pins("J17")), # led (J19 DATA_LED-)
        Subsignal("rx", Pins("H18")), # btn (J19 KEY+)
        IOStandard("LVCMOS33")
    ),
    # SDRAM SDRAM (EM638325-6H)
    ("sdram_clock", 0, Pins("B9"), IOStandard("LVCMOS33")),
    ("sdram", 0,
        Subsignal("a", Pins(
            "B13 C14 A16 A17 B16 B15 A14 A13",
            "A12 A11 B12")),
        Subsignal("dq", Pins(
            "D15 E14 E13 D12 E12 D11 C10 B17",
            "B8  A8  C7  A7  A6  B6  A5  B5",
            "D5  C5  D6  C6  E7  D7  E8  D8",
            "E9  D9  E11 C11 C12 D13 D14 C15")),
        Subsignal("we_n",  Pins("A10")),
        Subsignal("ras_n", Pins("B10")),
        Subsignal("cas_n", Pins("A9")),
        #Subsignal("cs_n", Pins("")), # gnd
        #Subsignal("cke",  Pins("")), # 3v3
        Subsignal("ba",    Pins("B11 C8")), # sdram pin BA0 and BA1
        #Subsignal("dm",   Pins("")), # gnd
        IOStandard("LVCMOS33"),
        Misc("SLEWRATE=FAST")
    ),

    # SPIFlash (W25Q32JV)
    ("spiflash", 0,
        Subsignal("cs_n", Pins("N8")),
        #Subsignal("clk",  Pins("")), driven through USRMCLK
        Subsignal("mosi", Pins("T8")),
        Subsignal("miso", Pins("T7")),
        IOStandard("LVCMOS33"),
    ),
    ("eth_clocks", 0,
        Subsignal("ref_clk", Pins("T18")),
        IOStandard("LVCMOS33")
    ),
    ("eth", 0,
        #Subsignal("rst_n",   Pins("P4")),
        Subsignal("rx_data", Pins("R17 R18")),
        Subsignal("crs_dv",  Pins("C18")),
        Subsignal("tx_en",   Pins("M17")),
        Subsignal("tx_data", Pins("P17 U18")),
        #Subsignal("mdc",     Pins("U16")),
        #Subsignal("mdio",    Pins("K18")),
        #Subsignal("rx_er",  Pins("P2")),
        #Subsignal("int_n",  Pins("P2")),
        IOStandard("LVCMOS33")
    ),
]

def sdcard_io():
  return [
    ("spisdcard", 0,
        Subsignal("mosi", Pins("D20")),
        Subsignal("miso",  Pins("B19")),
        Subsignal("clk",  Pins("A19")),
        Subsignal("cs_n",   Pins("A18")),
        IOStandard("LVCMOS33"),
        Misc("SLEWRATE=FAST")
    ),
]
_sdcard_io = sdcard_io()
    
_connectors = []
class Platform(LatticeECP5Platform):
    default_clk_name = "clk25"
    default_clk_period = 1e9/25e6
    def __init__(self, toolchain="trellis", **kwargs):
        LatticeECP5Platform.__init__(self, "LFE5U-25F-6BG381C", _io, connectors=_connectors, toolchain=toolchain)
    def create_programmer(self):
        return OpenOCDJTAGProgrammer("openocd_colorlight_5a_75b.cfg")
    def do_finalize(self, fragment):
        LatticeECP5Platform.do_finalize(self, fragment)
        self.add_period_constraint(self.lookup_request("clk25", loose=True), 1e9/25e6)
