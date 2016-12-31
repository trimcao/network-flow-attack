"""
Network Flow FEOL Attack - Split Manufacturing
Author: Tri Minh Cao
Email: tricao@utdallas.edu
Date: December 2016
"""
from def_parser import *
from lef_parser import *

# Main Class
if __name__ == '__main__':
    # Load the Layout
    lef_file = "./c17_example/NangateOpenCellLibrary.lef"
    lef_parser = LefParser(lef_file)
    lef_parser.parse()

    def_file = "./c17_example/c17_split_metal3.def"
    def_parser = DefParser(def_file)
    def_parser.parse()


    # Build lists of source pins and sink pins
    # source pins = primary input pins, output cell pins
    # sink pins = primary output pins, input cell pins
    source_pins = []
    sink_pins = []

    # Get pins from nets
    nets = def_parser.nets
    pin_dict = def_parser.pins.pin_dict
    pin_net_dict = {}
    for each_net in nets.nets:
        print(each_net.comp_pin)



