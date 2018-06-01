"""
Inline tokenizer for mistletoe.
"""
import operator


def tokenize(string, token_types):
    *token_types, fallback_token = token_types
    tokens = find_tokens(string, token_types, fallback_token)
    token_buffer = []
    if tokens:
        prev = tokens[0]
        for curr in tokens[1:]:
            prev = eval_tokens(prev, curr, token_buffer)
        token_buffer.append(prev)
    return make_tokens(token_buffer, 0, len(string), string, fallback_token)


def find_tokens(string, token_types, fallback_token):
    tokens = []
    for token_type in token_types:
        for m in token_type.pattern.finditer(string):
            tokens.append(ParseToken(m.start(), m.end(), m, string, token_type, fallback_token))
    return sorted(tokens, key=operator.attrgetter('start'))


def eval_tokens(x, y, token_buffer):
    r = relation(x, y)
    if r == 0:
        token_buffer.append(x)
        return y
    if r == 1:
        return x if x.cls.precedence >= y.cls.precedence else y
    x.append_child(y)
    return x


def relation(x, y):
    if x.end <= y.start:
        return 0  # x preceeds y
    if (x.end >= y.end
            and x.parse_start <= y.start
            and x.parse_end >= y.end):
        return 2  # x contains y
    return 1      # x intersects y


def make_tokens(tokens, start, end, string, fallback_token):
    result = []
    prev_end = start
    for token in tokens:
        if token.start > prev_end:
            result.append(fallback_token(string[prev_end:token.start]))
        result.append(token.make())
        prev_end = token.end
    if prev_end != end:
        result.append(fallback_token(string[prev_end:end]))
    return result


class ParseToken:
    def __init__(self, start, end, match, string, cls, fallback_token):
        self.start = start
        self.end = end
        self.parse_start = match.start(cls.in_group)
        self.parse_end = match.end(cls.in_group)
        self.match = match
        self.string = string
        self.cls = cls
        self.fallback_token = fallback_token
        self.children = []

    def append_child(self, child):
        if self.cls.parse_inner:
            if not self.children:
                self.children.append(child)
            else:
                prev = self.children.pop()
                prev = eval_tokens(prev, child, self.children)
                self.children.append(prev)

    def make(self):
        if not self.cls.parse_inner:
            return self.cls(self.match.group(self.cls.in_group), self.match)
        children = make_tokens(self.children, self.parse_start, self.parse_end, self.string, self.fallback_token)
        return self.cls(children, self.match)


    def __repr__(self):
        pattern = '<ParseToken span=({},{}) parse_span=({},{}) cls={} children={}>'
        return pattern.format(self.start, self.end,
                              self.parse_start, self.parse_end,
                              repr(self.cls.__name__), self.children)
