import sys
from abc import ABC, abstractmethod
from numpy import mean
from random import sample
from collections import defaultdict

class Constraint(ABC):

    @abstractmethod
    def permits(self, word):
        ...


class LetterPositionConstraint(Constraint):

    def __init__(self, letter, position):
        self.letter = letter
        self.position = position

    def __eq__(self, other):
        return self.letter == other.letter and self.position == other.position

    def __hash__(self):
        return hash(self.letter) + hash(self.position)

    def __str__(self):
        return "letter position constraint"

    __repr__ = __str__


class EqualityConstraint(LetterPositionConstraint):

    def __init__(self, letter, position):
        super().__init__(letter, position)

    def permits(self, word):
        return word[self.position] == self.letter

    def __str__(self):
        return f"{self.letter} at {self.position}"


class InequalityConstraint(LetterPositionConstraint):

    def __init__(self, letter, position):
        super().__init__(letter, position)

    def permits(self, word):
        return word[self.position] != self.letter

    def __str__(self):
        return f"{self.letter} not at {self.position}"


class CountConstraint(Constraint):

    def __init__(self, letter, count):
        self.letter = letter
        self.count = count

    def __eq__(self, other):
        # TODO: do we need to check class name?
        return self.letter == other.letter and self.count == other.count

    def __hash__(self):
        return hash(self.letter) + hash(self.count)

    def __str__(self):
        return "count constraint"

    __repr__ = __str__


class MinCountConstraint(CountConstraint):

    def __init__(self, letter, count):
        super().__init__(letter, count)

    def permits(self, word):
        return word.count(self.letter) >= self.count

    def __str__(self):
        return f"count({self.letter}) >= {self.count}"


class MaxCountConstraint(CountConstraint):

    def __init__(self, letter, count):
        super().__init__(letter, count)

    def permits(self, word):
        return word.count(self.letter) <= self.count

    def __str__(self):
        return f"count({self.letter}) <= {self.count}"


def get_feedback(guess, target):
    result = ["gray"] * 5
    for pos, letter in enumerate(guess):
        if target[pos] == letter:
            result[pos] = "green"
            target = target[:pos] + "*" + target[pos+1:]
    for pos, letter in enumerate(guess):
        if letter in target and result[pos] != "green":
            result[pos] = "yellow"
            target = target[:target.find(letter)] + "*" + target[target.find(letter)+1:]
    return result


def filter_possible_words(guess, feedback, possible_answers):
    """Filters the pool of possible answers based on feedback from a guess.

    Parameters
    ----------
    guess : str
        The player's guess
    feedback : list[str]
        The feedback from a guess, expressed as a list of five colors
    possible_answers : list[str]
        Original pool of possible answers.

    Returns
    -------
    list[str]
        The subset of the original pool that remain possible after making the guess.
    """

    def get_letter_constraints(letter, position_colors):
        retval = []
        green_positions = set([pos for (pos, color) in position_colors if color == "green"])
        yellow_positions = set([pos for (pos, color) in position_colors if color == "yellow"])
        gray_positions = set([pos for (pos, color) in position_colors if color == "gray"])
        retval += [EqualityConstraint(letter, pos) for pos in green_positions]
        retval += [InequalityConstraint(letter, pos) for pos in yellow_positions | gray_positions]
        if len(yellow_positions) > 0:
            retval += [MinCountConstraint(letter, len(green_positions) + len(yellow_positions))]
        elif len(gray_positions) > 0:
            retval += [MaxCountConstraint(letter, len(green_positions) + len(yellow_positions))]
        return retval

    def convert_colors_to_constraints(guess, colors):
        retval = []
        results_by_letter = defaultdict(list)
        for pos, letter in enumerate(guess):
            results_by_letter[letter].append((pos, colors[pos]))
        for letter in results_by_letter:
            retval += get_letter_constraints(letter, results_by_letter[letter])
        return retval

    def is_permitted(word):
        for constraint in constraints:
            if not constraint.permits(word):
                return False
        return True

    constraints = convert_colors_to_constraints(guess, feedback)
    return [word for word in possible_answers if is_permitted(word)]


def read_words(filename):
    """Reads a list of words from a file."""

    with open(filename) as reader:
        words = [line.strip() for line in reader]
    return words

