#!/usr/bin/env python3
#
# - support tool for preparation to lecture, alloc_book -
#    written by Hiroki Funashima in Nabari, 2024
#
#

import argparse
import json
import os
import re


class Lecture(object):
    def __init__(self, args):
        self.args = args
        self.prompt = r'\(^o^)/>'
        self.main()

    def main(self):
        if self.args.init:
            # initilize version
            self.initialize_preference()
        else:
            # normal version
            self.exec_main()

    def initialize_preference(self):
        check = False
        while not check:
            configfile = input('filename? > ')
            configfile = configfile.strip().replace(' ', '_')
            if os.path.isfile(configfile):
                print('----- error -----')
                print('file:{configfile} is already exist.')
                exit()
            self.configfile = configfile
            self.total_pages = int(input('total pages in textbook? > '))
            self.nlec = int(input('number of lectures? > '))
            self.prefaces = int(input('number of pages for prefaces? > '))
            self.confirmed_list = [None for _ in range(self.nlec)]
            print()
            print('preferences:')
            print(f'  filename     : {self.configfile}')
            print(f'  total page   : {self.total_pages}')
            print(f'  # of lectures: {self.nlec}')
            print(f'  # pf prefaces: {self.prefaces}')
            print('-----------------------------------------')
            print()
            ans = input('Is this correct? y/n[n]')
            if re.search('^y', ans.strip().lower()):
                check = True
        self.proc_main()

    def exec_main(self):
        configfile = self.args.configfile
        if configfile is None:
            print("===== Error(configfile) =====")
            print(f'file:configfile is not found.')
            exit()
        if not os.path.isfile(configfile):
            print("===== Error(configfile) =====")
            print(f'file:{configfile} is not found.')
            exit()
        self.configfile = configfile
        with open(self.configfile, mode='r') as fin:
            self.configure = json.load(fin)
        #
        # total_pages   : total page in textbook
        # confirmed_list: confirmed page list
        # prefaces      : number of pages for prefaces (uncount)
        # nlec          : number of lectures
        #
        self.total_pages = self.configure['total_pages']
        self.confirmed_list = self.configure['page_list']
        self.prefaces = self.configure['prefaces']
        self.nlec = len(self.confirmed_list)
        self.proc_main()

    def proc_main(self):
        #
        # total_pages   : total page in textbook
        # confirmed_list: confirmed page list
        # prefaces      : number of pages for prefaces (uncount)
        # nlec          : number of lectures
        #
        while True:
            self.parse(input(self.prompt))

    def parse(self, line):
        if not re.search('^:', line.strip()):
            return
        self.evaluate()
        command = line.replace(',', ' ').split()
        if re.search('^:[0-9]', command[0]):
            n = int(command[0].replace(':', '')) - 1
            if len(command) == 1:
                self.display_single_line(n+1)
            else:
                if command[1] == 'r':
                    if len(command) == 3:
                        v = int(command[2])
                    else:
                        v = self.buffer_list[n]
                    self.replace_line(n, v)
                elif command[1] == 'dd':
                    self.delete_line(n)
                elif command[1] == 'e':
                    if len(command) == 3:
                        v = int(command[2])
                    else:
                        _, v = self.get_page_range(n)
                    self.set_end_page(n, v)
        elif command[0] == ':%':
            self.display_total_line()
        elif command[0] == ':wq':
            self.write_file()
            self.quit()
        elif command[0] == ':w':
            self.write_file()
        elif command[0] == ':q':
            self.quit()
        elif command[0] == ':help':
            self.show_help()

    def sum_up_pages(self):
        return self.prefaces + sum(self.buffer_list)

    def evaluate(self):
        # buffer_list   : page list to display
        self.buffer_list = [None for _ in range(self.nlec)]
        undefined_pages = self.total_pages - self.prefaces
        for (i, page) in enumerate(self.confirmed_list):
            if page is None:
                self.buffer_list[i] = 0
            else:
                self.buffer_list[i] = page
                undefined_pages -= page
        while (self.sum_up_pages() < self.total_pages):
            for (i, page) in enumerate(self.confirmed_list):
                if self.sum_up_pages() == self.total_pages:
                    break
                if page is None:
                    self.buffer_list[i] += 1
                    undefined_pages -= 1
                    if undefined_pages == 0:
                        break

    def set_end_page(self, n, v):
        #
        # n: index of line
        # v: page number of end page
        #
        bn = v - self.prefaces - sum(self.buffer_list[:n])
        self.buffer_list[n] = bn
        self.confirmed_list[n] = bn

    def replace_line(self, n, v):
        #
        # n: index of line
        # v: value
        #
        self.buffer_list[n] = v
        self.confirmed_list[n] = v

    def delete_line(self, n):
        #
        # n: index of line
        #
        self.buffer_list[n] = None
        self.confirmed_list[n] = None

    def get_page_range(self, n):
        if self.buffer_list[n] == 0:
            return [0, 0]
        if n == 0:
            start_page = self.prefaces + 1
        else:
            start_page = self.prefaces + sum(self.buffer_list[:n]) + 1

        if n == self.nlec:
            end_page = self.prefaces + sum(self.buffer_list)
        else:
            end_page = self.prefaces + sum(self.buffer_list[:n+1])
        return [start_page, end_page]

    def write_file(self):
        d = {'prefaces': self.prefaces,
             'total_pages': self.total_pages,
             'page_list': self.confirmed_list}
        with open(self.configfile, mode='w') as fout:
            json.dump(d, fout, indent=4)

    def quit(self):
        print('-*- alloc_book has been finished -*-')
        exit()

    def display_total_line(self):
        print('---- page list -----')
        for n in range(self.nlec):
            self.display_single_line(n)

    def display_single_line(self, n):
        self.evaluate()
        if self.confirmed_list[n] is not None:
            mark = '*'
        else:
            mark = ' '
        start_page, end_page = self.get_page_range(n)
        npage = self.buffer_list[n]
        print(f'  ({mark})lect{n+1:02d}', end='')
        print(f'  pp.{start_page:3d} -- {end_page:3d}', end='')
        print(f' ({npage:3d} pages)')

    def show_help(self):
        #
        # simple manual to operate alloc_book
        #
        #
        print('# here "n" is the line you want to modify/remove line')
        print(':help     ... display this manual')
        print(':%        ... show all list')
        print(':n        ... single list')
        print(':n, r, m  ... replace m in lect n')
        print(':n, r     ... replace candidate value in lect n')
        print(':n, dd    ... delete value in lect n')
        print(':w        ... save file')
        print(':q        ... quit alloc_book')
        print(':wq       ... save file and quit alloc_book')
        return self


if __name__ == '__main__':
    parser = argparse.ArgumentParser(description="support planning lecture")
    parser.add_argument('configfile', type=str, nargs="?")
    parser.add_argument('--init', '-i',
                        help='initial proc',
                        action='store_true')
    Lecture(parser.parse_args())
