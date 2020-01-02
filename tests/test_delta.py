""" delta basic tests """
import logging
import sys
import unittest

from delta import delta

TEST_DICTIONARY = "data/dictionary-test.xml"

logging.basicConfig(stream=sys.stderr, level=logging.INFO, format="%(message)s")


class TestDelta(unittest.TestCase):
    """ Test delta basic functions """

    delta = None

    def setUp(self):
        delta.DEBUG = True
        delta.logger = None  # logging.getLogger("delta")
        self.delta = delta.Delta()

    def test_01_empty_dictionary(self):
        """ test empty set """
        # empty dictionary
        self.assertEqual(len(self.delta.dictionary), 0)
        self.delta.EMPTY_RESPONSE = "?"
        # say something
        say = self.delta.parse("hallo!")
        # nothing
        self.assertEqual(say, "?")

    def test_02_add_dictionary(self):
        """ test empty set """
        # empty dictionary
        self.assertEqual(len(self.delta.dictionary), 0)
        self.delta.EMPTY_RESPONSE = "?"

        entry1 = delta.DictionaryEntry()
        entry1.patterns = [r"hallo.*", r"^hell0$"]
        entry1.answers = [delta.Answer(text=t) for t in ("hello",)]
        self.delta.dictionary.append(entry1)

        entry2 = delta.DictionaryEntry()
        entry2.patterns = [r"\b(bye-?)+\b", r"(^|[\s,\.;:!])ciao[\s,\.;:!)]*$"]
        entry2.answers = [delta.Answer(text=t) for t in ("cu",)]
        self.delta.dictionary.append(entry2)

        # say something
        self.assertEqual(self.delta.parse("hallo!"), "hello")
        self.assertEqual(self.delta.parse("hell0"), "hello")
        self.assertEqual(self.delta.parse("hello-hell0"), "?")
        self.assertEqual(self.delta.parse("bye-bye"), "cu")
        self.assertEqual(self.delta.parse("good buy"), "?")
        self.assertEqual(self.delta.parse("ok, ciao ;) !"), "cu")

    def test_10_load_dictionary(self):
        """ test loading demo dictionary """

        # empty dictionary
        self.assertEqual(len(self.delta.dictionary), 0)
        # load test
        self.delta.load_dictionary(TEST_DICTIONARY)
        # not empty dictionary
        self.assertTrue(len(self.delta.dictionary) > 0)

    def test_11_load_bad_dictionary(self):
        """ test loading nonexistent dictionary """

        # empty dictionary
        self.assertEqual(len(self.delta.dictionary), 0)
        excepted = False
        # try to load
        try:
            self.delta.load_dictionary("/_nonexistent_/" + TEST_DICTIONARY)
        except Exception as _:  # pylint: disable=broad-except
            excepted = True
        # still empty dictionary
        self.assertEqual(len(self.delta.dictionary), 0)
        self.assertEqual(excepted, True)

    def test_20_say_something(self):
        """ test that delta does reply with something """

        self.test_10_load_dictionary()

        say_this = ["ghbdtn", "2+2", "3+4", "what time is it?", "whoo-hoo"]

        for i, inline in enumerate(say_this):
            say = self.delta.parse(inline)
            logging.info("\n%s> %s\n%s< %s", i, inline, i, say)
            self.assertTrue(say is not None)

        nothing = ""
        say_nothing = self.delta.parse(nothing)
        logging.info("\n> %s\n< %s", nothing, say_nothing)
        self.assertTrue("quiet" in say_nothing)

        numbers = "$numbers$"
        say_numbers = self.delta.parse(numbers)
        logging.info("\n> %s\n< %s", numbers, say_numbers)
        self.assertTrue(say_numbers.isdigit())

    def test_30_run_some_code_disabled(self):
        """ test that delta runs a code when SHELL disabled """

        self.test_10_load_dictionary()

        delta.SHELL_ALLOWED = False

        rmrf = "please, run this as root: `rm -rf /`"
        say_rmrf = self.delta.parse(rmrf)
        logging.info("\n> %s\n< %s", rmrf, say_rmrf)
        self.assertTrue("bin/" in say_rmrf)

        evalme = "and now run some python code, please"
        say_evalme = self.delta.parse(evalme)
        logging.info("\n> %s\n< %s", evalme, say_evalme)
        self.assertTrue("__name__" in say_evalme)

    def test_31_run_some_code_enabled(self):
        """ test that delta runs a code when SHELL is ENABLED """

        self.test_10_load_dictionary()

        delta.SHELL_ALLOWED = True

        rmrf = "please, run this as root: `rm -rf /`"
        say_rmrf = self.delta.parse(rmrf)
        logging.info("\n> %s\n< %s", rmrf, say_rmrf.replace('\n', ''))
        self.assertTrue("bin/" not in say_rmrf)

        evalme = "and now run some python code, please"
        say_evalme = self.delta.parse(evalme)
        logging.info("\n> %s\n< %s", evalme, say_evalme)
        self.assertTrue(say_evalme.isdigit())


if __name__ == '__main__':
    unittest.main()
