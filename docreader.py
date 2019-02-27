#!/usr/bin/env python
import argparse
import document_pb2
import doc2words
import struct
import gzip
import compress
import cPickle as pickle
import timeit
from collections import defaultdict


class DocumentStreamReader:
    def __init__(self, paths):
        self.paths = paths

    def open_single(self, path):
        return gzip.open(path, 'rb') if path.endswith('.gz') else open(path, 'rb')

    def __iter__(self):
        for path in self.paths:
            with self.open_single(path) as stream:
                while True:
                    sb = stream.read(4)
                    if sb == '':
                        break

                    size = struct.unpack('i', sb)[0]
                    msg = stream.read(size)
                    doc = document_pb2.document()
                    doc.ParseFromString(msg)
                    yield doc


def parse_command_line():
    parser = argparse.ArgumentParser(description='compressed documents reader')
    parser.add_argument('coding', nargs=1, help="Coding algorithm, possible 'varbyte' or 'simple9'")
    parser.add_argument('files', nargs='+', help='Input files (.gz or plain) to process')
    return parser.parse_args()


def main():
    coding = parse_command_line().coding[0]
    if (coding != 'varbyte') & (coding != 'simple9'):
        print "Possible values for coding are 'varbyte' or 'simple9'"
        return
    reader = DocumentStreamReader(list(parse_command_line().files))
    i = int(1)
    index = defaultdict(list)
    urls = []
    for doc in reader:
        urls.append(doc.url)
        for word in set(doc2words.extract_words(doc.text)):
            index[word].append(i)
        i += 1

    index_file = open("index.bin", 'wb')
    dict_file = open("dictionary.pkl", 'wb')
    url_file = open("url.txt", 'w')
    pos = int(len(coding))
    index_file.write(struct.pack('i', pos))
    index_file.write(bytearray(coding))
    pos += 4

    for word in index:
        binary = bytearray(compress.compress(index[word], coding))
        index_file.write(binary)
        index[word] = pos, len(binary)
        pos += len(binary)

    pickle.dump(index, dict_file, 2)
    for i in urls:
        url_file.write("%s\n" % i)

    index_file.close()
    dict_file.close()
    url_file.close()


if __name__ == '__main__':
    main()
