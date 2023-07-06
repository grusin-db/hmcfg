"""
simplematch
# code copied from: https://github.com/tfeldmann/simplematch/blob/main/simplematch.py
# minor adjustuments:
# - removed custom types handling code, as they are not needed for my use case
# - changed all ".*" patterns into "[^/]*", so that greedy folder matching is not happening 
"""
import re

# taken from the standard re module - minus "*{}", because that's our own syntax
SPECIAL_CHARS = {i: "\\" + chr(i) for i in b"()[]?+-|^$\\.&~# \t\n\r\v\f"}

class Matcher:
    @property
    def regex(self):
        return self._regex

    @regex.setter
    def regex(self, value):
        self._regex = value
        flags = 0 if self.case_sensitive else re.IGNORECASE
        # cache the compiled regex
        self._regex_compiled = re.compile(value, flags=flags)

    def __init__(self, pattern="*", case_sensitive=True):
        self.converters = {}
        self.pattern = pattern
        self.case_sensitive = case_sensitive
        self.regex = self._create_regex(pattern)

    def test(self, string):
        match = self._regex_compiled.match(string)
        return match is not None

    def match(self, string):
        match = self._regex_compiled.match(string)
        if match:
            # assemble result dict
            result = match.groupdict()
            for i, x in enumerate(self._grouplist(match)):
                result[i] = x

            # run converters
            for key, converter in self.converters.items():
                result[key] = converter(result[key])
            return result
        return None

    def _field_repl(self, matchobj):
        match = re.search(r"\{(\w+)\}", matchobj.group(0))
        if match:
            name = match.group(1)
            #match dont match slashes, as these are forbidden
            return r"(?P<%s>[^/]*)" % name

    def _create_regex(self, pattern):
        self.converters.clear()  # empty converters
        result = pattern.translate(SPECIAL_CHARS)  # escape special chars
        result = result.replace("*", r"[^/]*")  # handle wildcard
        result = re.sub(r"\{\}", r"(.*)", result)  # handle unnamed group
        result = re.sub(r"\{([^\}]*)\}", self._field_repl, result)  # handle named group
        return r"^%s$" % result

    @staticmethod
    def _grouplist(match):
        """ extract unnamed match groups """
        # https://stackoverflow.com/a/53385788/300783
        named = match.groupdict()
        ignored_groups = set()
        for name, index in match.re.groupindex.items():
            if name in named:  # check twice if it is really the named attribute
                ignored_groups.add(index)
        return [
            group
            for i, group in enumerate(match.groups())
            if i + 1 not in ignored_groups
        ]

    def __repr__(self):
        return '<Matcher("%s")>' % self.pattern


def test(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).test(string)


def match(pattern, string, case_sensitive=True):
    return Matcher(pattern, case_sensitive=case_sensitive).match(string)


def to_regex(pattern):
    return Matcher(pattern).regex