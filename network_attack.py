"""
Network Flow FEOL Attack - Split Manufacturing
Author: Tri Minh Cao
Email: tricao@utdallas.edu
Date: December 2016
"""
from def_parser import *
from lef_parser import *
import networkx as nx
# from networkx.algorithms.flow import max_flow_min_cost
import argparse


def get_done_sinks(sink_pins, pin_net_dict):
    """
    Find all the sink pins that are already connected.a
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


def distance_two_nets(net1, net2, net_ends_dict):
    """
    Get the distance between two nets.
    :param net1:
    :param net2:
    :return: distance value
    """
    min_dist = float('inf')
    points1 = net_ends_dict[net1.name][0]
    points2 = net_ends_dict[net2.name][0]

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
    (that means for each cell, we store the cells that connect to the input
    pins of that cell).
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
    :param cell:
    :param connected_dict:
    :return: a set of connected cells
    """
    if cell == 'PIN':
        return set()
    connected_cells = set()
    parent = {} # stores the parent of a node
    stack = []
    stack.append(cell)
    while len(stack) > 0:
        current_cell = stack.pop()
        for each_pin in connected_dict[current_cell]:
            next_cell = each_pin[0]
            if next_cell != 'PIN':
                parent[each_pin[0]] = current_cell
                connected_cells.add(each_pin[0])
                stack.append(each_pin[0])
    return connected_cells, parent


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
                    pin_net_dict, connected_dict, net_ends_dict, def_data):
    """
    Build the distance table for every pair of pins.
    A distance of -1 means there is no possible connection between those pins.
    :param source_pins: the source pins.
    :param sink_pins: the sink pins.
    :param primary_inputs: the primary input pins.
    :param primary_outputs: the primary output pins.
    :param pin_net_dict:
    :param connected_dict:
    :param net_ends_dict: dictionary that store the end points of each net.
    :return: a 2D table of distance values.
    """
    # default value = 1
    distances = [[1 for i in range(len(sink_pins))] for j in range(len(source_pins))]
    # print(len(source_pins))
    # print(len(sink_pins))
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
            # find the direction of sink_net
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
            elif not dangling_net(source_net, sink_net, net_ends_dict, def_data):
                # case 4: dangling wire
                distances[i][j] = -1
            else:
                # find the actual distance between pins
                # indeed, it's the distance between the nets that connected to
                # those pins.
                # re-write distance_two_nets
                distances[i][j] = distance_two_nets(source_net, sink_net, net_ends_dict)
            print(source_pins[i], sink_pins[j], distances[i][j])
        print()

    # print(distances)
    # print(distances[-2])
    return distances


def output_verilog(connections, def_data, lef_data, verilog_file):
    """
    Output a verilog netlist from the connections inferred.
    :param connections: connections dictionary
    :param verilog_file: verilog file name
    :return: void
    """
    inputs = []
    outputs = []
    wires = []
    # create the netlist, a dictionary of net that connects each pin
    netlist = {}
    net_idx = 1
    for each_pin in connections:
        # get the net name
        net_name = None
        if each_pin[0] == 'PIN':
            net_name = each_pin[1]
            inputs.append(net_name)
        else:
            # check for primary output pin
            for each_connect in connections[each_pin]:
                if each_connect[0] == 'PIN':
                    net_name = each_connect[1]
                    outputs.append(net_name)
            if not net_name:
                net_name = 'n' + str(net_idx)
                wires.append(net_name)
                net_idx += 1
        # assign the net to pins
        netlist[each_pin] = net_name
        for each_connect in connections[each_pin]:
            netlist[each_connect] = net_name
    # print(netlist)
    # write cells in verilog format
    cell_dict = def_data.components.comp_dict
    cells = []
    for each_cell in cell_dict:
        new_cell = ''
        # get the pin dictionary of the cell
        macro_name = cell_dict[each_cell].macro
        macro_data = lef_data.macro_dict[macro_name]
        new_cell += macro_name + ' ' + each_cell + ' ( '
        pin_dict = macro_data.pin_dict
        pin_list = []
        for each_pin in pin_dict:
            direction = pin_dict[each_pin].direction
            if direction == 'INPUT' or direction == 'OUTPUT':
                new_pin = ''
                pin_tuple = (each_cell, each_pin)
                new_pin += '.' + each_pin + '('
                net_name = netlist[pin_tuple]
                new_pin += net_name + ')'
                pin_list.append(new_pin)
        new_cell += ', '.join(pin_list)
        new_cell += ' );'
        cells.append(new_cell)
    # building the output string
    design_name = def_data.design_name
    inouts = inputs + outputs
    # start writing
    f = open(verilog_file, 'w')
    s = '\n'
    s += 'module ' + design_name + ' ( '
    s += ', '.join(inouts)
    s += ' );\n'
    # write input
    s += '  input ' + ', '.join(inputs) + ';\n'
    # write output
    s += '  output ' + ', '.join(outputs) + ';\n'
    # write wire
    s += '  wire ' + ', '.join(wires) + ';\n'
    s += '\n'
    # write cells
    for each_cell in cells:
        s += '  ' + each_cell + '\n'
    s += '\n'
    s += 'endmodule'
    # write to file
    f.write(s)
    f.close()


def get_macro_pins(cell_name, def_data, lef_data):
    """
    Get a dictionary of pins for a cell
    :param macro:
    :param lef_data:
    :return:
    """
    pass


def net_end_points(net_name, def_data):
    """
    Find the end-points and the point leading to each end-point (so we can
      infer the direction of the wire)
    :param net_name: name of the net
    :param def_data: data from DEF file
    :return: a dictionary of end-points
    """
    top_layer = def_data.nets.get_top_layer()
    via_split = 'via' + top_layer[-1]
    die_area = def_data.diearea
    net_data = def_data.nets.net_dict[net_name]
    ends_dict = {} # end-points dictionary
    end_points = set() # set of end_points
    # initialize the ends_dict
    for each_route in net_data.routed:
        if each_route.end_via and each_route.end_via[:4] == via_split:
            tuple_pt = tuple(each_route.end_via_loc[:2])
            end_points.add(tuple_pt)
        for each_pt in each_route.points:
            # check for border (pin location)
            # if on_border(each_pt, die_area):
            #     end_points.add(tuple(each_pt[:2]))
            tuple_pt = tuple(each_pt[:2])
            # create the list in ends_dict if it does not exist
            if tuple_pt not in ends_dict:
                ends_dict[tuple_pt] = []
            # add end points from the route
            for each_end in each_route.points:
                if each_end != each_pt:
                    ends_dict[tuple_pt].append(tuple(each_end[:2]))
    end_points = list(end_points)
    return end_points, ends_dict


def net_end_points2(net_name, def_data):
    """
    Find the end-points and the point leading to each end-point (so we can
      infer the direction of the wire)
    :param net_name: name of the net
    :param def_data: data from DEF file
    :return: a dictionary of end-points
    """
    # NOTE: This function might need serious re-work.
    die_area = def_data.diearea
    net_data = def_data.nets.net_dict[net_name]
    ends_dict = {} # end-points dictionary
    end_points = set() # set of end_points
    # initialize the ends_dict
    for each_route in net_data.routed:
        if each_route.end_via and each_route.end_via[:4] == 'via1':
            end_points.add(tuple(each_route.end_via_loc[:2]))
        for each_pt in each_route.points:
            # check for border (pin location)
            if on_border(each_pt, die_area):
                end_points.add(tuple(each_pt[:2]))
            tuple_pt = tuple(each_pt[:2])
            # create the list in ends_dict if it does not exist
            if tuple_pt not in ends_dict:
                ends_dict[tuple_pt] = []
            # add end points from the route
            for each_end in each_route.points:
                if each_end != each_pt:
                    ends_dict[tuple_pt].append(tuple(each_end[:2]))
    # consider end_points as a stack
    end_points = list(end_points)
    # visited points
    visited = set()
    # follow the end points
    num_points = len(ends_dict)
    while len(visited) < num_points and len(end_points) > 0:
        # cont = False
        current_end = end_points.pop()
        if current_end not in visited:
            visited.add(current_end)
            next_pts = ends_dict[current_end]
            if len(next_pts) == 0:
                end_points.append(current_end)
            else:
                new_end = False
                for each_next in next_pts:
                    if each_next not in visited:
                        # if we see another end point, then remove it as an end-point
                        if each_next in end_points:
                            visited.add(each_next)
                            end_points.remove(each_next)
                        else:
                            end_points.append(each_next)
                            new_end = True
                if not new_end:
                    end_points.append(current_end)
    return end_points, ends_dict


def get_net_direction(net_name, def_data):
    end_points, ends_dict = net_end_points(net_name, def_data)
    return net_direction(end_points, ends_dict, def_data)


def net_direction(end_points, ends_dict, def_data):
    """
    Find the directions that accept connection for a net (which may consist
    of multiple wires)
    :param end_points:
    :param ends_dict:
    :param def_data:
    :return: a list of pairs of corner points. If a connection is within
    one of those pairs, then it's possible.
    """
    # find the maximum x and y coordinate
    die_area = def_data.diearea
    # check for special case
    if len(end_points) == 0:
        return [die_area]
    else:
        areas = []
        for each_end in end_points:
            areas.append(wire_direction(each_end, ends_dict, die_area))
        return areas


def wire_direction(end_point, ends_dict, die_area):
    """
    Interpret the direction of a wire using end points and end points dictionary.
    Output a pair of points (x1, y1) and (x2, y2). The possible connection must
    belong to the rectangle composed of these two points.
    :param end_point:
    :param ends_dict:
    :return: a pair of corner points
    """
    # boundary from die area
    min_x = die_area[0][0]
    min_y = die_area[0][1]
    max_x = die_area[1][0]
    max_y = die_area[1][1]
    # iterate through each next point
    next_pts = ends_dict[end_point]
    corner1 = [min_x, min_y] # initialize the corner points
    corner2 = [max_x, max_y]
    for each_pt in next_pts:
        diff_x = each_pt[0] - end_point[0]
        diff_y = each_pt[1] - end_point[1]
        if diff_x < 0:
            x1 = end_point[0]
            x2 = max_x
        elif diff_x == 0:
            # make no difference to the possible direction
            x1 = min_x
            x2 = max_x
        else:
            x1 = min_x
            x2 = end_point[0]
        # update corner of x-coordinate
        if x1 > corner1[0]:
            corner1[0] = x1
        if x2 < corner2[0]:
            corner2[0] = x2
        # check y-coordinate
        if diff_y < 0:
            y1 = end_point[1]
            y2 = max_y
        elif diff_y == 0:
            y1 = min_y
            y2 = max_y
        else:
            y1 = min_y
            y2 = end_point[1]
        # update corner of y-coordinate
        if y1 > corner1[1]:
            corner1[1] = y1
        if y2 < corner2[1]:
            corner2[1] = y2
    corners = [corner1, corner2]
    return corners


def dangling_net(net1, net2, net_ends_dict, def_data):
    """
    Find out if net1 and net2 have possible connection due to their dangling
    wires.
    :param net1:
    :param net2:
    :return: True or False
    """
    # find the direction of net1
    net1_ends = net_ends_dict[net1.name]
    net1_direction = net_direction(net1_ends[0], net1_ends[1], def_data)
    # find the direction of net2
    net2_ends = net_ends_dict[net2.name]
    net2_direction = net_direction(net2_ends[0], net2_ends[1], def_data)
    # check if some end point of net1 is in net2's direction
    # that means some end point must be within of some net2 corner pair.
    result1 = False
    for each_end in net1_ends[0]:
        for each_rect in net2_direction:
            # print(each_end)
            # print(each_rect)
            if inside_area(each_end, each_rect):
                result1 = True
    result2 = False
    for each_end in net2_ends[0]:
        for each_rect in net1_direction:
            if inside_area(each_end, each_rect):
                result2 = True
    return result1 and result2





# Main Class
if __name__ == '__main__':
    # inputs: LEF, DEF
    # output: Verilog
    parser = argparse.ArgumentParser(description='FEOL attack tool.')
    parser.add_argument('-lef', '--lef', help='LEF file path', required=True)
    parser.add_argument('-i', '--input', help='Input DEF layout file name', required=True)
    parser.add_argument('-o', '--output', help='Output Verilog file name',
                        required=True)
    args = parser.parse_args()

    # Load the Layout
    # lef_file = "./c17_example/NangateOpenCellLibrary.lef"
    lef_file = args.lef
    lef_parser = LefParser(lef_file)
    lef_parser.parse()

    # def_file = "./c17_example/c17_split_metal3.def"
    def_file = args.input
    def_parser = DefParser(def_file)
    def_parser.parse()

    # find top metal layer
    # print(def_parser.nets.get_top_layer())
    # exit()

    # Build lists of source pins and sink pins
    # source pins = primary input pins, output cell pins
    # sink pins = primary output pins, input cell pins
    source_pins = []
    sink_pins = []
    input_cell_pins = set()
    output_cell_pins = set()
    primary_inputs = set()
    primary_outputs = set()

    # Get the end_points and ends_dict for each net
    nets = def_parser.nets
    net_ends_dict = {} # store the end points for each net
    for each_net in nets.nets:
        # print(each_net.name)
        end_points, ends_dict = net_end_points(each_net.name, def_parser)
        # print(end_points)
        # print(ends_dict)
        net_ends_dict[each_net.name] = (end_points, ends_dict)
        # print()

    # Get pins from nets
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

    # test dangling net
    # print(pin_net_dict)
    # pin_n2 = ('PIN', 'N2')
    # pin_u11_a = ('U11', 'A')
    # print(dangling_net(pin_net_dict[pin_n2], pin_net_dict[pin_u11_a], net_ends_dict,
    #                    def_parser))
    # exit()

    # find the connected dict (chain of cells):
    connected_dict = connected_comps(def_parser, lef_parser, pin_net_dict)
    # print(connected_dict)
    # cells, parent = find_cell_connected('U7', connected_dict)
    # print(parent)
    # exit()

    # Get the distance table between source and sink pins
    # NOTE: maybe a nested dictionary is better than a 2D list to represent
    # the distance table.
    distances = build_distances(source_pins, sink_pins, primary_inputs, primary_outputs,
                    pin_net_dict, connected_dict, net_ends_dict, def_parser)

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
    # print(mincostFlow)
    # print(mincost)
    # print()

    # get the final connections
    connections = {}
    for each in source_pins:
        connections[each] = []
        for each_sink in mincostFlow[each]:
            if mincostFlow[each][each_sink] > 0:
                connections[each].append(each_sink)

    # print(connections)
    for each in connections:
        print(each)
        print(connections[each])
        print()

    verilog_out = args.output
    # output_verilog(connections, def_parser, lef_parser, verilog_out)
