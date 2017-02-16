"""
LIB (Liberty file) parser
Author: Tri Minh Cao
Email: tricao@utdallas.edu
Date: December 2016
"""

from lib_util import *
import util


class LibParser:
    """
    LibParser will gather information from a LIB file.
    """

    def __init__(self, lib_file):
        self.file_path = lib_file
        # stack to store the ongoing sections (such as cell, timing, etc.)
        self.stack = []
        self.library = None

    def parse(self):
        print ("Start parsing DEF file...")
        # open the file and start reading
        f = open(self.file_path, "r+")
        # the program will run until the end of file f
        for line in f:
            # print(line)
            info = line.split()
            # print(info)
            if len(info) > 0:
                if info[0][:2] == '/*':
                    # print('comment')
                    # check for done comment
                    if info[-1][len(info[-1]) - 2:len(info[-1])] == '*/':
                        # print('done comment')
                        pass
                    else:
                        new_comment = Comment()
                        self.stack.append(new_comment)
                elif info[0] == 'library':
                    print('library')
                    lib_name = info[1][1:-1]
                    new_lib = Library(lib_name)
                    self.stack.append(new_lib)
                    self.library = new_lib
                else:
                    # parse current section
                    if len(self.stack) > 0:
                        current = self.stack[-1]
                        if current.parse_next(info):
                            self.stack.pop()

        f.close()

if __name__ == '__main__':
    print('testing...')
    lib_file = './lib/NangateOpenCellLibrary_typical.lib'
    lib_parser = LibParser(lib_file)
    lib_parser.parse()

    print('Done parsing LIB file.')