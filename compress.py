#!/usr/bin/env python
from sys import stdout
printf = stdout.write


class BitstreamWriter:
    def __init__(self):
        self.nbits  = 0
        self.curbyte = 0
        self.vbytes = []

    """ add single bit """
    def add(self, x):
        self.curbyte |= x << (8-1 - (self.nbits % 8))
        self.nbits += 1

        if self.nbits % 8 == 0:
            self.vbytes.append(chr(self.curbyte))
            self.curbyte = 0

    """ get byte-aligned bits """
    def getbytes(self):
        if self.nbits & 7 == 0:
            return "".join(self.vbytes)

        return "".join(self.vbytes) + chr(self.curbyte)


class BitstreamReader:
    def __init__(self, blob):
        self.blob = blob
        self.pos  = 0

    """ extract next bit """
    def get(self):
        ibyte = self.pos / 8
        ibit  = self.pos & 7

        self.pos += 1
        return (ord(self.blob[ibyte]) & (1 << (7 - ibit))) >> (7 - ibit)

    def finished(self):
        return self.pos >= len(self.blob) * 8


def compress_varbyte(dl):
    bs = BitstreamWriter()
    num = dl[0]
    while num >= 128:
        bits = num & 127
        num >>= 7
        for j in xrange(7):
            bs.add(bits & 1)
            bits >>= 1
        bs.add(0)
    bits = num & 127
    for j in xrange(7):
        bs.add(bits & 1)
        bits >>= 1
    bs.add(1)

    for i in xrange(1, len(dl)):
        num = dl[i] - dl[i - 1]
        while num >= 128:
            bits = num & 127
            num >>= 7
            for j in xrange(7):
                bs.add(bits & 1)
                bits >>= 1
            bs.add(0)
        bits = num & 127
        for j in xrange(7):
            bs.add(bits & 1)
            bits >>= 1
        bs.add(1)
    return bs.getbytes()


def decompress_varbyte(s):
    bs = BitstreamReader(s)
    array = []
    i = 0

    array.append(0)
    byte_num = 0
    extract = True
    while extract:
        for j in xrange(7):
            array[i] |= bs.get() << (j + byte_num * 7)
        byte_num += 1
        extract = not bool(bs.get())
    i += 1

    while not bs.finished():
        array.append(0)
        byte_num = 0
        extract = True
        while extract:
            for j in xrange(7):
                array[i] |= bs.get() << (j + byte_num * 7)
            byte_num += 1
            extract = not bool(bs.get())
        array[i] += array[i - 1]
        i += 1
    return array


def compress_simple9(dl):
    bs = BitstreamWriter()
    length = len(dl)
    i = 0

    max_bits = dl[i].bit_length()
    amount = 1
    prev = dl[i]
    substract = True
    while max_bits * amount < 28:
        j = i + amount
        if j >= length:
            break
        tmp = dl[j]
        dl[j] -= prev
        prev = tmp
        next_size = dl[j].bit_length()
        tmp_max_bit_size = max(max_bits, next_size)
        if tmp_max_bit_size * (amount + 1) > 28:
            substract = False
            break
        max_bits = tmp_max_bit_size
        amount += 1

    for j in xrange(4):
        bs.add((amount >> j) & 1)

    one_item_size = 28 / amount
    for j in xrange(amount):
        for k in xrange(one_item_size):
            bs.add((dl[i + j] >> k) & 1)
    for j in xrange(one_item_size * amount, 28):
        bs.add(0)
    i += amount

    while i < length:
        if substract:
            tmp = dl[i]
            dl[i] -= prev
            prev = tmp
        substract = True
        max_bits = dl[i].bit_length()
        amount = 1

        while max_bits * amount < 28:
            j = i + amount
            if j >= length:
                break
            tmp = dl[j]
            dl[j] -= prev
            prev = tmp
            next_size = dl[j].bit_length()
            tmp_max_bit_size = max(max_bits, next_size)
            if tmp_max_bit_size * (amount + 1) > 28:
                substract = False
                break
            max_bits = tmp_max_bit_size
            amount += 1

        for j in xrange(4):
            bs.add((amount >> j) & 1)

        one_item_size = 28 / amount
        for j in xrange(amount):
            for k in xrange(one_item_size):
                bs.add((dl[i + j] >> k) & 1)
        for j in xrange(one_item_size * amount, 28):
            bs.add(0)
        i += amount

    return bs.getbytes()


def decompress_simple9(s):
    array = []
    bs = BitstreamReader(s)

    num = 0

    amount = 0

    for i in xrange(4):
        amount |= bs.get() << i

    for i in xrange(amount):
        array.append(0)

        for j in xrange(28 / amount):
            array[num] |= bs.get() << j
        if num > 0:
            array[num] += array[num - 1]
        num += 1
    rest = 28 % amount
    for i in xrange(rest):
        bs.get()

    while not bs.finished():
        amount = 0

        for i in xrange(4):
            amount |= bs.get() << i

        for i in xrange(amount):
            array.append(0)

            for j in xrange(28 / amount):
                array[num] |= bs.get() << j
            array[num] += array[num - 1]
            num += 1
        rest = 28 % amount
        for i in xrange(rest):
            bs.get()
    return array


def compress(dl, compress_type):
    if compress_type == 'varbyte':
        return compress_varbyte(dl)
    elif compress_type == 'simple9':
        return compress_simple9(dl)
    else:
        print "Possible arguments are 'simple9' or 'varbyte'"


def decompress(s, decompress_type):
    if decompress_type == 'varbyte':
        return decompress_varbyte(s)
    elif decompress_type == 'simple9':
        return decompress_simple9(s)
    else:
        print "Possible arguments are 'simple9' or 'varbyte'"


if __name__ == '__main__':
    print [1, 21, 27, 31, 41, 44, 46, 51, 63, 65, 76, 94, 95, 128, 444, 19999999, 20000000]
    s = compress_simple9([1, 21, 27, 31, 41, 44, 46, 51, 63, 65, 76, 94, 95, 128, 444, 19999999, 20000000])
    print decompress_simple9(s)