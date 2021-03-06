#!/usr/bin/env python3
# -*- coding: utf-8 -*-

# kppvh - performs some checking on text files to submit to Project Gutenberg
# Copyright 2012-2014 bibimbop at pgdp, all rights reserved

# This program is free software; you can redistribute it and/or
# modify it under the terms of the GNU General Public License
# as published by the Free Software Foundation; either version 2
# of the License, or (at your option) any later version.
#
# This program is distributed in the hope that it will be useful,
# but WITHOUT ANY WARRANTY; without even the implied warranty of
# MERCHANTABILITY or FITNESS FOR A PARTICULAR PURPOSE.  See the
# GNU General Public License for more details.
#
# You should have received a copy of the GNU General Public License
# along with this program; if not, write to the Free Software
# Foundation, Inc., 51 Franklin Street, Fifth Floor, Boston, MA  02110-1301, USA.

"""
 kppvh - performs some checking on PGDP or Project Gutenberg files.
"""

import re
from itertools import count, groupby
from helpers.exfootnotes import get_block

class FootNotes(object):

    def check_footnotes(self, myfile):
        """Performs some checking on footnotes. Only arabic numeral are considered.
        """

        self.anchor_not_found = []

        # Find all footnotes and their anchors
        anchors = []

        # Does the line start with "[xx]", "[Note xx:" or "[Footnote
        # xx:" ? Also, expect a space or a newline right after the
        # closing bracket; having something else is probably an error,
        # or it's an anchor. Don't expect an anchor inside a footnote,
        # at least on the first line.
        regexes = [r"^\[(\w+)\]( |$)",
                   r"^ \[(\w+)\]( |$)",
                   r"^  \[(\w+)\]( |$)",
                   r"^   \[(\w+)\]( |$)",
                   r"^    \[(\w+)\]( |$)",
                   r"^     \[(\w+)\]( |$)",
                   r"^      \[(\w+)\]( |$)",
                   r"^\[Note ([\w\-]+):( |$)",
                   r"^  \[Note ([\w\-]+):( |$)",
                   r"^     \[Note ([\w\-]+):( |$)",
                   r"^          \[Note ([\w\-]+):( |$)",
                   r"^\[Footnote ([\w\-]+):( |$)",
                   r"^  \[Footnote ([\w\-]+)\]:( |$)",
                   r"^     \[Footnote ([\w\-]+):( |$)",
                   r"^          \[Footnote ([\w\-]+):( |$)",
                   r"^\     Note ([\w\-]+):( |$)",
                   r"^\      Note ([\w\-]+):( |$)"]

        # note_regexes[1] will contain matching numerical matches,
        # while note_regexes[2] will contain the other (non numerical)
        note_regexes = [(re.compile(x), [], []) for x in regexes]

        for block, _ in get_block(myfile.text):
            if not len(block):
                continue

            # Look for the Footnote
            line = block[0]
            for regex in note_regexes:
                m = regex[0].match(line)
                if m is not None:
                    # Add it to the 1st list if it's a number
                    # otherwise put it on the 2nd list.
                    if m.group(1).isdigit():
                        regex[1].append(int(m.group(1)))
                    else:
                        # Remove known words, that are certainly not a
                        # footnote
                        if m.group(1) in ["Illustration", "Decoration",
                                          "D??coration", "Bandeau", "Logo",
                                          "Ornement"]:
                            m = None
                            continue

                        regex[2].append(m.group(1))

                    # Remove the footnote marker, but keep the rest of
                    # the line because it might contain an anchor
                    block[0] = m.group(2)

            # Look for the anchors anywhere in the block.
            for line in block:
                for m in re.finditer(r"\[(\d+)\]", line):
                    anchors.append(int(m.group(1)))

        # Remove consecutive duplicates, but keep the order.
        # Go from  [1, 2, 2, 2, 5, 6, 7] to [1, 2, 5, 6, 7]
        anchors = [x[0] for x in groupby(anchors)]

        # Create individual ranges
        # Python magic to go from [1, 2, 5, 6, 7, 2] to [[1, 2], [5, 7], [2, 2]]
        G = (list(x) for _, x in groupby(anchors, lambda x, c=count(): next(c)-x))
        self.anchor_ranges = [[g[0], g[-1]] for g in G]

        # Create global range.
        # Python magic to go from [1, 2, 5, 6, 7, 2] to [[1,2], [5, 7]]
        anchors.sort()
        anchors = [x[0] for x in groupby(anchors)]
        G = (list(x) for _, x in groupby(anchors, lambda x, c=count(): next(c)-x))
        self.anchor_global_ranges = [[g[0], g[-1]] for g in G]

        # If both anchor_ranges and anchor_global_ranges, ignore the
        # latter. We just don't want to repeat information
        if self.anchor_ranges == self.anchor_global_ranges:
            self.anchor_global_ranges = None

        # For each non numerical footnote, try to find an anchor.
        for regex in note_regexes:
            for note in regex[2]:
                anchor = '['+note+']'

                for line in myfile.text:
                    if anchor in line:

                        # Ensure it's not the declaration
                        if regex[0].match(line):
                            continue
                        break
                else:
                    # For loop completed, so the anchor hasn't been found
                    self.anchor_not_found.append(anchor)

        # Build ranges of footnotes found
        index = -1
        self.fn_found = {}
        for regex in note_regexes:
            index += 1
            if len(regex[1]) == 0 and len(regex[2]) == 0:
                continue

            # Footnotes: create range. More than one range might indicate an
            # error in the document.
            G = (list(x) for _, x in groupby(regex[1], lambda x, c=count(): next(c)-x))
            notes_ranges = [[g[0], g[-1]] for g in G]

            # Put the ranges in a dictionary, indexed by the regular
            # expression that found them. First in the tuple is the
            # numerical range, second is the non-numerical instances,
            # with duplicates removed, then sorted.
            self.fn_found[regexes[index]] = (notes_ranges, sorted(list(set(regex[2]))))





def main():

    import argparse
    import sys

    sys.path.append("../../helpers")
    import sourcefile

    parser = argparse.ArgumentParser(description='Footnotes checker PGDP PP.')
    parser.add_argument('filename', metavar='FILENAME', type=str,
                        help='input text file')
    args = parser.parse_args()

    myfile = sourcefile.SourceFile()

    myfile.load_text(args.filename)

    if myfile.text is None:
        print("Cannot read file", f)
        return

    x = FootNotes()
    x.check_footnotes(myfile)

    print(x.anchor_ranges)
    print(x.fn_found)
    print(x.anchor_not_found)

if __name__ == '__main__':
    main()
