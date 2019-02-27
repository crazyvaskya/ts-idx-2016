#!/usr/bin/env python
import struct
import parse_tree
import cPickle as pickle
import sys
import linecache


def main():
    index_file = open("index.bin", 'rb')
    dict_file = open("dictionary.pkl", 'rb')

    dictionary = pickle.load(dict_file)
    dict_file.close()

    header_len = struct.unpack('i', index_file.read(4))[0]
    coding_type = index_file.read(header_len)
    while True:
        try:
            line = raw_input()
            if line == "":
                break

            print line
            line = line.decode('utf8')
            tree_root = parse_tree.parse_query(line)
            parse_tree.leaf_term_into_index(tree_root, dictionary, index_file, coding_type)

            docid = 0
            result = []

            while docid >= 0:
                tree_root.goto(docid)
                docid = tree_root.evaluate()
                if docid >= 0:
                    result.append(docid)
                else:
                    break
                docid += 1

            result = sorted(result)
            print len(result)
            for i in result:
                sys.stdout.write(linecache.getline("url.txt", i))
        except:
            break


if __name__ == '__main__':
    main()

