#!/usr/bin/env python
import re
import compress

SPLIT_RGX = re.compile(r'\w+|[\(\)&\|!]', re.U)


class QtreeTypeInfo:
    def __init__(self, value, op=False, bracket=False, term=False):
        self.value = value
        self.is_operator = op
        self.is_bracket = bracket
        self.is_term = term

    def __repr__(self):
        return repr(self.value)

    def __eq__(self, other):
        if isinstance(other, QtreeTypeInfo):
            return self.value == other.value
        return self.value == other


class QTreeTerm(QtreeTypeInfo):
    def __init__(self, term):
        QtreeTypeInfo.__init__(self, term, term=True)
        self.ind = 0

    def evaluate(self):
        if self.ind < 0:
            return self.ind
        return self.value[self.ind]

    def goto(self, docid):
        if self.ind == -1:
            return
        if len(self.value) <= self.ind:
            self.ind = -1
            return

        while self.ind < len(self.value):
            if self.value[self.ind] >= docid:
                return
            self.ind += 1
        self.ind = -1


class QTreeOperator(QtreeTypeInfo):
    def __init__(self, op):
        QtreeTypeInfo.__init__(self, op, op=True)
        self.priority = get_operator_prio(op)
        self.left = None
        self.right = None
        self.docid = -1

    def evaluate(self):
        if self.value == '|':
            left  = self.left.evaluate()
            right = self.right.evaluate()

            if left < 0:
                return right
            if right < 0:
                return left
            return min(left, right)

        elif self.value == '&':
            left = self.left.evaluate()
            right = self.right.evaluate()
            while left != right:

                if left < 0 or right < 0:
                    return -1

                if left > right:
                    self.right.goto(left)
                    right = self.right.evaluate()
                if right > left:
                    self.left.goto(right)
                    left = self.left.evaluate()
            return right

        elif self.value == '!':
            if self.docid < 0:
                return self.docid

            curr = self.right.evaluate()
            if curr > self.docid:
                return self.docid

            while self.docid == self.right.evaluate():
                self.docid += 1
                self.right.goto(self.docid)

            if self.right.evaluate() < 0:
                self.docid = -2

            return self.docid

    def goto(self, docid):
        if self.value == '|':
            self.left.goto(docid)
            self.right.goto(docid)
            return

        if self.value == '&':
            self.left.goto(docid)
            self.right.goto(docid)
            return

        if self.value == '!':
            self.docid = docid
            self.right.goto(docid)
            return



class QTreeBracket(QtreeTypeInfo):
    def __init__(self, bracket):
        QtreeTypeInfo.__init__(self, bracket, bracket=True)


def get_operator_prio(s):
    if s == '|':
        return 0
    if s == '&':
        return 1
    if s == '!':
        return 2

    return None


def is_operator(s):
    return get_operator_prio(s) is not None


def tokenize_query(q):
    tokens = []
    for t in map(lambda w: w.lower(), re.findall(SPLIT_RGX, q)):
        if t == '(' or t == ')':
            tokens.append(QTreeBracket(t))
        elif is_operator(t):
            tokens.append(QTreeOperator(t))
        else:
            tokens.append(QTreeTerm(t))

    return tokens


def build_query_tree(tokens):
    """ write your code here """
    if all(not t.is_operator for t in tokens):
        for t in tokens:
            if t.is_term:
                return t
        return None
    min_depth = -1
    depth = 0
    max_op_ind = 0
    curr_ind = 0
    for t in tokens:
        if t == '(':
            depth += 1
        elif t == ')':
            depth -= 1
        elif is_operator(t):
            if (min_depth < 0) or (min_depth > depth) or \
                    (depth == min_depth and get_operator_prio(tokens[max_op_ind]) >= get_operator_prio(t)):
                max_op_ind = curr_ind
                min_depth = depth
        curr_ind += 1

    tokens[max_op_ind].right = build_query_tree(tokens[max_op_ind + 1:])
    tokens[max_op_ind].left  = build_query_tree(tokens[: max_op_ind])
    return tokens[max_op_ind]


def parse_query(q):
    tokens = tokenize_query(q)
    return build_query_tree(tokens)


def leaf_term_into_index(leaf, dictionary, index_file, coding_type):
    if leaf.is_term:
        if dictionary.get(leaf.value) is None:
            leaf.value = []
        else:
            index_file.seek(dictionary[leaf.value][0], 0)
            leaf.value = compress.decompress(index_file.read(dictionary[leaf.value][1]), coding_type)
    else:
        if leaf.left is not None:
            leaf_term_into_index(leaf.left , dictionary, index_file, coding_type)
        if leaf.right is not None:
            leaf_term_into_index(leaf.right, dictionary, index_file, coding_type)
