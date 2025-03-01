"""
delta -- yet another answering machine
a.k.a. Сверхъестественный интеллект или ёщё одна программа автоответчик

It implements super simple context-free regexps patterns matching algorithm.

Usage example:

    import delta
    d = delta.Delta()
    d.load_dictionary('dictionary.xml')
    output = d.parse('hello, world!')
    print(output)

"""

import random
import re
import subprocess
import xml.sax

__all__ = ["DEBUG", "SHELL_ALLOWED", "Delta", "logger"]

SHELL_ALLOWED = False
DEBUG = False
logger = None  # pylint: disable=invalid-name

SPACES_RE = re.compile(r"[ \t\n\r]+")
MACROS_RE = re.compile(r"\$([a-zA-Z0-9_]+)\$")


class DictionaryEntry:
    """
    Dictionary entry:
    Every entry contains a list of patterns and list of answers.
    All patterns must be compiled before usage to make searching faster.
    """

    re_flags = re.UNICODE | re.IGNORECASE  # regexp compiler flags

    def __init__(self, patterns=None, answers=None, exclusions=None, priority=0):
        """
        Args:
            patterns (list, optional): regexps for matching.
            answers (list, optional): Answer objects.
            exclusions (list, optional): regexps for exclusion in matching.
            priority (int, optional): entry priority (used in dict sorting).
        """

        # set of patterns and precompiled regexps
        self.patterns = patterns or []
        self.patterns_cmp = []

        # set of answers (strings with marcos)
        self.answers = answers or []

        # set of exclusion patterns and precompiled regexps
        self.exclusions = exclusions or []
        self.exclusions_cmp = []

        # entry priority
        self.priority = priority

    def compile_patterns(self):
        """call compiler for all regexps (patterns and exclusions)"""
        self.patterns_cmp = [self.re_compiler(x) for x in self.patterns]
        if self.exclusions:
            self.exclusions_cmp = [self.re_compiler(x) for x in self.exclusions]

    def re_compiler(self, pattern):
        """compile pattern and log errors"""
        try:
            return re.compile(pattern, self.re_flags)
        except Exception as exc:  # pylint: disable=broad-except
            _log("error", "failed to compile pattern `%s`: %s", pattern, exc)

    def __str__(self):
        return (
            f"`{self.patterns and self.patterns[0]}`=>`{self.answers and self.answers[0]}`"
            f" ({len(self.patterns)}:{len(self.answers)})"
        )

    def match(self, inline):
        """
        Test input and return `entry match object` if:
        - input string matches at least one pattern
        - does not match any exclusion pattern.
        Args:
            inline (str): input string
        Returns:
            match object (re.Match object) or None
        """

        emo = None  # entry matching object

        # searching for good patterns
        for i, patt in enumerate(self.patterns_cmp):

            if not patt:
                continue

            emo = patt.search(inline)

            if emo is not None:
                _log("debug", "matched: `%s` => `%s`", inline, self.patterns[i])
                break

        # nothing matched
        if emo is None:
            return None

        # checking for exclusions
        if self.exclusions:
            for i, patt in enumerate(self.exclusions_cmp):
                xmo = patt.search(inline)
                if xmo is not None:
                    _log("debug", "excluded: `%s` => `%s`", inline, self.exclusions[i])
                    return None

        return emo

    def get_answer(self, safe=True, index=None):
        """gets random answer, returns text"""
        if index is not None and index < len(self.answers):
            answer = self.answers[index]
        else:
            answer = random.choice(self.answers)
        return answer.as_text(safe=safe)


class Answer:
    """
    Answer from dictionary enntry.
    Can be simple text or output of the shell command
    or result of python eval (if SHELL_ALLOWED)
    """

    TEXT, EVAL, SHELL = 1, 2, 3
    ACTION_TYPES = {"text": TEXT, "eval": EVAL, "shell": SHELL}
    ACTION_TYPE_DEFAULT = TEXT

    text = ""
    action_type = ACTION_TYPE_DEFAULT

    def __init__(self, text=None, action_type=None):
        if text:
            self.text = text
        if action_type:
            self.action_type = self.ACTION_TYPES.get(action_type, self.ACTION_TYPE_DEFAULT)

    def run_shell(self):
        """runs a program (this feature is disabled by default)"""
        # pylint: disable=broad-except
        output = ""
        try:
            # only command, no arguments, no return code check, stderr>>stdout
            proc = subprocess.run(
                [self.text],
                shell=False,
                check=False,
                stdout=subprocess.PIPE,
                stderr=subprocess.STDOUT,
            )
            output = proc.stdout.decode("utf-8", errors="ignore")
        except Exception as exc:
            _log("error", "shell failed `%s`: %s", self.text, exc)
        return output

    def run_eval(self):
        """execute answer text as python code (this feature is disabled by default)"""
        # pylint: disable=eval-used,broad-except
        output = ""
        try:
            output = str(eval(self.text))
        except Exception as exc:
            _log("error", "eval failed `%s`: %s", self.text, exc)
        return output

    def __str__(self):
        return self.text

    def as_text(self, safe=True):
        """do all the magic and return text value of the answer"""
        if self.action_type == self.SHELL and SHELL_ALLOWED and not safe:
            return self.run_shell()
        if self.action_type == self.EVAL and SHELL_ALLOWED and not safe:
            return self.run_eval()
        return self.text


class Dictionary:
    """
    Dictionary is a collection of dictionary entries
    """

    def __init__(self):
        self.entries = []  # dictionary entries

    def append(self, entry, and_compile=True):
        """add new dictionary entry"""
        if and_compile:
            entry.compile_patterns()
        self.entries.append(entry)
        _log("debug", "added entry %s", entry)

    def sort(self):
        """sort entries list by priority"""
        self.entries.sort(key=lambda x: -x.priority)

    def print(self):
        """print dictionary contents"""
        print(len(self.entries), " items in the dictionary")
        print("\n".join(map(str, self.entries)))

    def __len__(self):
        """return length of the dictionary"""
        return len(self.entries) if self.entries else 0

    def lookup(self, inline):
        """
        For the given input line look up for matching entry in the dictionary.
        Args:
            inline (str): input line
        Returns:
            A tuple of entry and entry match object,
            or (None, None) -- if nothing found.
        """

        for entry in self.entries:
            emo = entry.match(inline)
            if emo is not None:
                return (entry, emo)

        return (None, None)


class Delta:
    """
    Answering machine engine
    """

    dictionary = None

    MAX_PARSER_DEPTH = 25
    EMPTY_RESPONSE = ""

    def __init__(self):
        """Initializer has no arguments"""
        self.dictionary = Dictionary()

    def load_dictionary(self, filename):
        """
        Load dictionary from XML file (new records appended to existing dictionary).
        Args:
            filename (str): XML file
        Returns:
            Total number of dictionary entries.
        Raises:
            Exception if the file cannot be opened or parsed.
        """

        with open(filename, "rb") as infile:

            # Set input file as a input stream for the parser
            isource = xml.sax.xmlreader.InputSource()
            isource.setByteStream(infile)

            # Parser creation
            xparser = xml.sax.make_parser()

            xhandler = DeltaDictionaryXMLHandler(self.dictionary)
            xparser.setContentHandler(xhandler)

            xparser.parse(isource)

        # Reorder dictionary entries by priority flag.
        self.dictionary.sort()

        _log("info", "loaded dictionary %s (%s)", filename, len(self.dictionary))
        return len(self.dictionary)

    def save_dictionary(self, filename):
        """
        Save dictionary into XML-file. FIXME: NIY!
        """
        self.dictionary.print()
        raise NotImplementedError(__file__ + __name__)

    def parse(self, inline, depth=0):
        """
        Parse input line and generate the answer.
        Args:
            inline (str): input string.
        Returns:
            A string with answer.
        Raises:
            An Exception in case of error (any type)
        """

        if depth > self.MAX_PARSER_DEPTH:  # avoid infinite looping
            _log("warning", "I went too deep (%s)", depth)
            return self.EMPTY_RESPONSE

        # clean input
        inline = SPACES_RE.sub(" ", inline.lower().strip())

        # search for matching dictionary entry
        (entry, emo) = self.dictionary.lookup(inline)
        _log("debug", "looked up for `%s` => %s", inline, entry)

        # postprocess answer
        answer = self.process_answer(emo, entry, depth)
        _log("debug", "parsed answer: `%s`", answer)

        return answer

    def process_answer(self, emo, entry, depth):
        """
        Entry answer processing.
        At the first step answer is selected randomly from the list
        of possible answers for the matched pattern.
        Then, all macros inside the answer are expanded (recursively).
        """

        if entry is None or emo is None:
            return self.EMPTY_RESPONSE

        # Get a random answer from the list.
        answer = entry.get_answer(safe=(not SHELL_ALLOWED))

        # Looking for marcos in the text. Every macro starts and ends
        # with the '$' sign. (e.g. '$macro$'). Expansion rules are stored
        # in the main dictionary. All macros are expansed in a reccurent
        # manner, so they may have other macros inside.
        #
        # Special macros $1$, $2$ ... -- will be replaced with substrings
        # groupped in the regular expression pattern.
        #
        # If dollar-sign '$' is needed in text it should be written
        # as three symbols -- '$$$'.

        def _marco_parser(macromo, emo=emo):
            macro_name = macromo.group(1)
            if macro_name.isdigit():  # $1$
                i = int(macro_name)
                if i <= len(emo.groups()):
                    return emo.group(i)
                return self.EMPTY_RESPONSE
            if macro_name == "$":  # $$$
                return "$"
            _log("debug", "expading macro `%s`", macro_name)
            macro_expanded = self.parse(f"${macro_name}$", depth + 1)
            return macro_expanded

        # magically replace all macros with
        answer_expanded = MACROS_RE.sub(_marco_parser, answer)

        return answer_expanded


class DeltaDictionaryXMLHandler(xml.sax.handler.ContentHandler):
    """Content handlers for XML loader"""

    text = ""  # current element text content
    element_type = None  # current element type attribite

    def __init__(self, dictionary):
        self.dictionary = dictionary
        self.entry = None
        super().__init__()

    # <element>
    def startElement(self, name, attrs):

        if name == "entry":  # new entry
            self.entry = DictionaryEntry()
            priority = attrs.get("pri", attrs.get("priority", 0))
            self.entry.priority = _int(priority)

        elif name in ["pattern", "answer"]:
            self.element_type = attrs.get("type")

    # </element>
    def endElement(self, name):

        if name == "entry":  # end of the entry — save it to dictionary
            self.dictionary.append(self.entry)

        elif name == "pattern":  # pattern

            text = self.text.strip()

            if self.element_type == "macro":
                self.entry.patterns.append(f"\\${text}\\$")

            elif self.element_type in ["exculsion", "exception", "exc"]:
                self.entry.exclusions.append(text)

            else:
                self.entry.patterns.append(text)

        elif name == "answer":  # possible answer for the pattern

            text = self.text.strip()
            answer = Answer(text=text, action_type=self.element_type)
            self.entry.answers.append(answer)

        # clean up for the next element
        self.text = ""

    def characters(self, content):
        self.text += content  # save element text content


def _log(level, msg, *args, **kwargs):
    """logging helper"""
    if logger is not None:
        if level in ["error", "warning"]:
            logger.error(msg, *args, **kwargs)
        elif level == "info" and DEBUG:
            logger.info(msg, *args, **kwargs)
        elif DEBUG:
            logger.debug(msg, *args, **kwargs)


def _int(i, fallback=0):
    """int helper"""
    # pylint: disable=broad-except
    try:
        return int(i)
    except BaseException:
        return fallback
