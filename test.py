import unittest
from game import WordleEvaluation
from agent import initialize_agent
from util import read_words


def evaluate(allowed, possible):
    try:
        agent = initialize_agent(allowed, possible)
        game = WordleEvaluation(agent, allowed, possible)
        avg_num_guesses, play_rate = game.play()
        msg = "\n-------------------------------------------------------"
        msg += f"\nYour agent achieved"
        msg += f"\n  a guess average of:  {avg_num_guesses:.2f}"
        msg += f"\n  at a play rate of:   {play_rate:.2f} games/sec"
        msg += "\n-------------------------------------------------------"
        return True, msg
    except Exception as e:
        msg = f"\nEncoder/decoder crashed! It triggered the following exception:\n{e}"
        return False, msg


class TestPolish(unittest.TestCase):

    def test_pl(self):
        allowed = read_words("data/pl.allowed.txt")
        possible = read_words("data/pl.possible.txt")
        successful, msg = evaluate(allowed, possible)
        print(msg)
        assert successful, msg


class TestSecretLanguageOne(unittest.TestCase):

    def test_de(self):
        allowed = read_words("data/de.allowed.txt")
        possible = read_words("data/de.possible.txt")
        successful, msg = evaluate(allowed, possible)
        print(msg)
        assert successful, msg


class TestSecretLanguageTwo(unittest.TestCase):

    def test_el(self):
        allowed = read_words("data/el.allowed.txt")
        possible = read_words("data/el.possible.txt")
        successful, msg = evaluate(allowed, possible)
        print(msg)
        assert successful, msg

