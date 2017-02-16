"""
Data structures for Lib Parser
Author: Tri Minh Cao
Email: tricao@utdallas.edu
Date: December 2016
"""


class Library:
    """
    Class Library represents the library section in the LIB file.
    Usually one lib file only has one library.
    """
    def __init__(self, name):
        self.name = name
        self.stack = []
        self.stack.append(name)
        self.cell_dict = {}

    def parse_next(self, info):
        if len(self.stack) > 0:
            current = self.stack[-1]
        # first case, the stack currently has some parsable object
        if not isinstance(current, str):
            if current.parse_next(info):
                self.stack.pop()
        else:
            # the library will parse by itself
            if info[-1][-1] == '{':
                if info[0] == 'cell':
                    cell_name = info[1][1:-1]
                    new_cell = Cell(cell_name)
                    print(cell_name)
                    self.stack.append(new_cell)
                    self.cell_dict[cell_name] = new_cell
                else:
                    self.stack.append(info[0])
            elif info[-1][-1] == '}':
                last_section = self.stack.pop()
                if last_section == self.name:
                    return 1
                else:
                    return 0


class Comment:
    """
    Class Comment parses comment in the LIB file.
    """
    def __init__(self):
        pass

    def parse_next(self, info):
        if info[-1][len(info[-1]) - 2:len(info[-1])] == '*/':
            # print('done comment')
            return 1
        else:
            return 0


class Cell:
    """
    Class Cell represents a cell section in the LIB file.
    """
    def __init__(self, name):
        self.name = name
        self.stack = []
        self.stack.append(name)
        self.pin_dict = {}
        self.drive_strength = None
        self.area = None

    def parse_next(self, info):
        if len(self.stack) > 0:
            current = self.stack[-1]
        # first case, the stack currently has some parsable object
        if not isinstance(current, str):
            if current.parse_next(info):
                self.stack.pop()
        else:
            if info[-1][-1] == '{':
                # print('start section ' + info[0])
                if info[0] == 'pin':
                    pin_name = info[1][1:-1]
                    new_pin = Pin(pin_name)
                    self.stack.append(new_pin)
                    self.pin_dict[pin_name] = new_pin
                else:
                    self.stack.append(info[0])
            elif info[0] == 'drive_strength':
                self.drive_strength = float(info[2][:-1])
            elif info[0] == 'area':
                self.area = float(info[2][:-1])
            elif info[-1][-1] == '}':
                last_section = self.stack.pop()
                # print ('end section ' + last_section)
                if last_section == self.name:
                    return 1
                else:
                    return 0


class Pin:
    """
    Class Pin represents information of a pin (which belongs to a cell).
    """
    def __init__(self, name):
        self.name = name
        self.stack = []
        self.stack.append(name)
        self.direction = None
        self.capacitance = None
        self.rise_capacitance = None
        self.fall_capacitance = None
        self.max_capacitance = None
        self.timings = []

    def parse_next(self, info):
        if len(self.stack) > 0:
            current = self.stack[-1]
        # first case, the stack currently has some parsable object
        if not isinstance(current, str):
            if current.parse_next(info):
                self.stack.pop()
        else:
            if info[-1][-1] == '{' or (len(info) > 1 and info[1][0] == '{'):
                # print('start section ' + info[0])
                if info[0] == 'timing':
                    new_timing = Timing()
                    self.timings.append(new_timing)
                    self.stack.append(new_timing)
                elif info[0] == 'internal_power':
                    # print('internal power')
                    self.stack.append(info[0])
                    # self.stack.append('internal_power')
                else:
                    self.stack.append(info[0])
            elif info[0] == 'direction':
                self.direction = info[2][:-1]
            elif info[0] == 'capacitance':
                self.capacitance = float(info[2][:-1])
            elif info[0] == 'max_capacitance':
                self.max_capacitance = float(info[2][:-1])
            elif info[-1][-1] == '}':
                last_section = self.stack.pop()
                # print ('end section ' + last_section)
                if last_section == self.name:
                    return 1
                else:
                    return 0


class Timing:
    """
    Class Timing represents timing information of a pin.
    """
    def __init__(self):
        self.name = 'timing'
        self.stack = []
        self.stack.append(self.name)
        # cell fall
        # cell rise
        # fall transition
        # rise transition
        self.related_pin = None
        self.cell_fall = None
        self.cell_rise = None
        self.fall_transition = None
        self.rise_transition = None

    def parse_next(self, info):
        if len(self.stack) > 0:
            current = self.stack[-1]
        # first case, the stack currently has some parsable object
        if not isinstance(current, str):
            if current.parse_next(info):
                self.stack.pop()
        else:
            if info[-1][-1] == '{' or (len(info) > 1 and info[1][0] == '{'):
            # if info[-1][-1] == '{':
                # print('start section ' + info[0])
                section_name = info[0][0:9]
                if section_name == 'cell_fall':
                    new_timing_val = Timing_Vals(section_name)
                    self.stack.append(new_timing_val)
                    self.cell_fall = new_timing_val
                elif section_name == 'cell_rise':
                    new_timing_val = Timing_Vals(section_name)
                    self.stack.append(new_timing_val)
                    self.cell_rise = new_timing_val
                elif section_name == 'fall_tran':
                    new_timing_val = Timing_Vals(section_name)
                    self.stack.append(new_timing_val)
                    self.fall_transition = new_timing_val
                elif section_name == 'rise_tran':
                    new_timing_val = Timing_Vals(section_name)
                    self.stack.append(new_timing_val)
                    self.rise_transition = new_timing_val
                else:
                    self.stack.append(info[0])
            elif info[0] == 'related_pin':
                pin_name = ''
                for i in range(1, len(info[2])):
                    if info[2][i] == '\"':
                        break
                    else:
                        pin_name += info[2][i]
                self.related_pin = pin_name
            elif info[-1][-1] == '}':
                last_section = self.stack.pop()
                # print ('end section ' + last_section)
                if last_section == self.name:
                    return 1
                else:
                    return 0


class Timing_Vals:
    """
    Class Timing_Vals represents timing values from a timing section.
    Values can be: cell_rise, cell_fall, fall_transition, rise_transition.
    """
    def __init__(self, type):
        self.type = type
        # self.stack = []
        # self.stack.append(name)
        self.value = None

    def parse_next(self, info):
        # if len(self.stack) > 0:
        #    current = self.stack[-1]
        # # first case, the stack currently has some parsable object
        # if not isinstance(current, str):
        #    if current.parse_next(info):
        #        self.stack.pop()
        if info[-1][-1] == '}':
            return 1
        elif info[0] == 'values':
            numbers = info[1]
            value = ''
            for i in range(2, len(numbers)):
                if numbers[i] == ',':
                    break
                else:
                    value += numbers[i]
            self.value = float(value)

        else:
            return 0


# class Internal_Power:
#     pass

