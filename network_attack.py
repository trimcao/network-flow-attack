"""
Network Flow FEOL Attack - Split Manufacturing
Author: Tri Minh Cao
Email: tricao@utdallas.edu
Date: December 2016
"""
from def_parser import *
from lef_parser import *
import networkx as nx
from networkx.algorithms.flow import max_flow_min_cost


def get_done_sinks(sink_pins, pin_net_dict):
    """
    Find all the sink pins that are already connected.
    :param sink_pins: a list of sink pins.
    :param pin_net_dict: pin to net dictionary (mapping).
    :return: a set of connected sink pins
    """
    done_sinks = set()
    for each_pin in sink_pins:
        net = pin_net_dict[each_pin]
        if len(net.comp_pin) > 1:
            done_sinks.add(each_pin)
    return done_sinks


def distance_two_nets(net1, net2):
    """
    Get the distance between two nets.
    :param net1:
    :param net2:
    :return: distance value
    """
    min_dist = float('inf')
    # get all the points from the routes of each net
    points1 = []
    points2 = []
    for each_route in net1.routed:
        for each_pt in each_route.points:
            points1.append(each_pt[:2])
    for each_route in net2.routed:
        for each_pt in each_route.points:
            points2.append(each_pt[:2])
    # find the pair of points with minimum distance
    for i in range(len(points1)):
        for j in range(len(points2)):
            current_dist = manhattan_dist(points1[i], points2[j])
            if current_dist < min_dist:
                min_dist = current_dist
    return min_dist


def connected_comps(def_data, lef_data, pin_net_dict):
    """
    Get the dictionary of connected components for each cell in the layout.
    :param def_data: DEF data
    :return: a dictionary.
    """
    connected = {}
    cell_dict = def_data.components.comp_dict
    for each_cell in cell_dict:
        inputs, outputs = get_pins_cell(each_cell, def_data, lef_data)
        connected[each_cell] = set()
        for each_input in inputs:
            # print(each_input)
            if each_input in pin_net_dict:
                connected_net = pin_net_dict[each_input]
                # print(connected_net)
                for each_pin in connected_net.comp_pin:
                    if each_pin[0] != each_cell:
                        connected[each_cell].add(tuple(each_pin))
    return connected


def find_cell_connected(cell, connected_dict):
    """
    Find the chain of cells (that potentially can cause a loop).
    Recursive function.
    :param cell:
    :param connected_dict:
    :return: a set of connected cells
    """
    if cell == 'PIN':
        return set()
    connected_cells = set()
    stack = []
    stack.append(cell)
    while len(stack) > 0:
        current_cell = stack.pop()
        for each_pin in connected_dict[current_cell]:
            next_cell = each_pin[0]
            if next_cell != 'PIN':
                connected_cells.add(each_pin[0])
                stack.append(each_pin[0])
    return connected_cells


def get_pins_cell(cell, def_data, lef_data):
    inputs = []
    outputs = []
    macro_name = def_data.components.comp_dict[cell].macro
    macro_data = lef_data.macro_dict[macro_name]
    for each_pin in macro_data.pin_dict:
        pin_data = macro_data.pin_dict[each_pin]
        if pin_data.direction == 'INPUT':
            inputs.append((cell, pin_data.name))
        elif pin_data.direction == 'OUTPUT':
            outputs.append((cell, pin_data.name))
    return inputs, outputs


def build_distances(source_pins, sink_pins, primary_inputs, primary_outputs,
                    pin_net_dict, connected_dict):
    """
    Build the distance table for every pair of pins.
    A distance of -1 means there is no possible connection between those pins.
    :param source_pins: the source pins.
    :param sink_pins: the sink pins.
    :param primary_inputs: the primary input pins.
    :param primary_outputs: the primary output pins.
    :return: a 2D table of distance values.
    """
    # default value = 1
    distances = [[1 for i in range(len(sink_pins))] for j in range(len(source_pins))]
    print(len(source_pins))
    print(len(sink_pins))
    done_sinks = get_done_sinks(sink_pins, pin_net_dict)
    for i in range(len(source_pins)):
        # build the set of connected pins
        connected_comps = set()
        source_cell = source_pins[i][0]
        source_net = pin_net_dict[source_pins[i]]
        for each_pin in source_net.comp_pin:
            connected_comps.add(each_pin[0])
        # find the connected cells in the chain (so no loop)
        connected_comps = connected_comps ^ find_cell_connected(source_cell, connected_dict)
        # find the distance through different cases.
        for j in range(len(sink_pins)):
            sink_net = pin_net_dict[sink_pins[j]]
            if sink_pins[j] in done_sinks:
                # case 1: if the current sink pin is already connected.
                distances[i][j] = -1
                for each_pin in sink_net.comp_pin:
                    if tuple(each_pin) == source_pins[i]:
                        distances[i][j] = 0
            elif source_pins[i] in primary_inputs and sink_pins[j] in primary_outputs:
                # case 2: primary input cannot connect to primary output
                distances[i][j] = -1
            elif sink_pins[j][0] in connected_comps:
                # case 3: no loop, and one output pin can only connect to one
                # input pin per gate.
                distances[i][j] = -1
            else:
                # find the actual distance between pins
                # indeed, it's the distance between the nets that connected to
                # those pins.
                distances[i][j] = distance_two_nets(source_net, sink_net)


    print(distances)
    print(distances[-2])
    return distances



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
    input_cell_pins = set()
    output_cell_pins = set()
    primary_inputs = set()
    primary_outputs = set()

    # Get pins from nets
    nets = def_parser.nets
    pin_dict = def_parser.pins.pin_dict
    pin_net_dict = {}
    for each_net in nets.nets:
        for each_pin in each_net.comp_pin:
            current_pin = tuple(each_pin)
            pin_net_dict[current_pin] = each_net
            if current_pin[0] == 'PIN':
                primary_pin = pin_dict[current_pin[1]]
                if primary_pin.direction == 'INPUT':
                    source_pins.append(current_pin)
                    primary_inputs.add(current_pin)
                elif primary_pin.direction == 'OUTPUT':
                    sink_pins.append(current_pin)
                    primary_outputs.add(current_pin)
            else:
                macro_name = def_parser.components.comp_dict[current_pin[0]].macro
                macro_data = lef_parser.macro_dict[macro_name]
                pin_data = macro_data.pin_dict[current_pin[1]]
                if pin_data.direction == 'INPUT':
                    sink_pins.append(current_pin)
                    input_cell_pins.add(current_pin)
                elif pin_data.direction == 'OUTPUT':
                    source_pins.append(current_pin)
                    output_cell_pins.add(current_pin)

    # find the connected dict (chain of cells):
    connected_dict = connected_comps(def_parser, lef_parser, pin_net_dict)

    # find the closest distance between those pins
    # we need a 2D list
    print(source_pins)
    print(sink_pins)

    # Get the distance table between source and sink pins
    # NOTE: maybe a nested dictionary is better than a 2D list to represent
    # the distance table.
    distances = build_distances(source_pins, sink_pins, primary_inputs, primary_outputs,
                    pin_net_dict, connected_dict)

    # start creating a graph
    G = nx.DiGraph()
    # NOTE: the capacity we use right now may not be optimal
    # add the edges between source pins and sink pins
    for i in range(len(source_pins)):
        for j in range(len(sink_pins)):
            current_weight = distances[i][j]
            if current_weight != -1:
                G.add_edge(source_pins[i], sink_pins[j], weight=distances[i][j],
                           capacity=1)
    # add edges from the super source pin to other source pins.
    source_name = 'source'
    # NOTE: need to find the actual load capacitance later
    SOURCE_CAP = 10
    for i in range(len(source_pins)):
        G.add_edge(source_name, source_pins[i], weight=0, capacity=SOURCE_CAP)
    # add edges from the sink pins to super sink
    sink_name = 'sink'
    SINK_CAP = 1 # we want the input pin can receive only 1 connection
    # we can get load capacitance information later, but only for checking for
    # possible load, the capacity should be still 1.
    for i in range(len(sink_pins)):
        G.add_edge(sink_pins[i], sink_name, weight=0, capacity=SINK_CAP)

    # print(G.nodes())
    # print(G.edges())
    # print()
    # for each in G.nodes():
    #     print(each)
    #     print(G[each])
    #     print()

    mincostFlow = nx.max_flow_min_cost(G, source_name, sink_name)
    mincost = nx.cost_of_flow(G, mincostFlow)
    print(mincostFlow)
    print(mincost)
    print()
    for each in source_pins:
        print(each)
        print(mincostFlow[each])
        print()









