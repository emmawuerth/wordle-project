import sys
from abc import ABC, abstractmethod
from collections import defaultdict
from numpy import mean
from random import choice, sample, shuffle
from tqdm import tqdm
from util import read_words, filter_possible_words, get_feedback


def initialize_agent(allowed, possible):
    """Initializes the WordleAgent that game.py uses to play Wordle.

    """
    return WordleAgent(allowed, possible)


class WordleAgent(ABC):

    def __init__(self, allowed, possible):
        self.allowed = allowed
        self.possible = possible
        self.saved_string = possible

        #Finds best word guess from the list of allowed guesses
        best_word = ("", 0)
        for word in self.allowed:
            score = self.find_exp_value(word)
            if score > best_word[1]:
                best_word = (word, score)
        self.first_word_guess = best_word[0]

        
    def find_exp_value(self, a_word):
        '''
        Calculates the "expected value" for the input word (based on 
        the number of greys, greens and yellows.)

        Parameters
        ----------
        a_word : str
            The word being considered as a guess from the list of allowed guesses.

        Returns
        -------
            The average score across all possible final words.
        '''
        word_sum = 0.0
        for poss in self.possible:
            for i in range(0,5):
                #gets value for each letter in (each) possible word
                word_sum += self.get_letter_score(a_word, poss, i)
        return word_sum / len(self.possible)


    
    def get_letter_score(self, a_word, poss, i):
        ''' Calculates score for a letter.
        
        Parameters
            ----------
            a_word : str
                The word being considered as a guess from the list of allowed guesses.
            poss : str
                The word whose score is being calculated from the list of possible final words. 
            i : int
                Value to index a letter from the word

            Returns
            -------
            int
                The value for the given letter in the possible final word.
        '''
        #grey
        if poss[i] not in a_word:
            return 0.0
        #green
        if poss[i] == a_word[i]:
            return 2.0
        #yellow
        else: 
            return 1.0

      

    #@abstractmethod
    def first_guess(self):
        """Makes the first guess of a Wordle game.

        A WordleGame will call this method to get the agent's first guess of the game.
        This is an implicit signal to the agent that a new game has begun. Subsequent
        guess requests during the same game will use the .next_guess method.

        Returns
        -------

            The first guess of a game of Wordle
        """

        self.possible = self.saved_string
        return self.first_word_guess

    #@abstractmethod
    def next_guess(self):
        """Makes the next guess of an in-progress Wordle game.

        A WordleGame will call this method to get the agent's next guess of an
        in-progress game.

        Returns
        -------
        str
            The next guess of the agent, during an in-progress game of Wordle
        """

        # Returns final word
        if len(self.possible) == 1:
            return self.possible[0]
        
        # Finds best guess using same strategy as above
        else:
            best_word = ("", 0)

            for word in self.allowed:
                score = self.find_exp_value(word)
                if score > best_word[1]:
                    best_word = (word, score)
            return best_word[0]

    #@abstractmethod
    def report_feedback(self, guess, feedback):
        """Provides feedback to the agent after a guess.

        After the agent makes a guess, a WordleGame calls this method to deliver
        feedback to the agent about the guess. No return value is expected from the
        method call.

        Feedback takes the form of a list of colors, corresponding to the letters
        of the guess:
        - "green" means the guessed letter is in the target word, and in the specified position
        - "yellow" means the guessed letter is in the target word, but not in the specified position
        - "gray" means the guessed letter is not in the target word

        For instance, if the WordleGame calls:
            agent.report_feedback("HOUSE", ["gray", "green", "gray", "gray", "yellow"])
        Then the agent can infer that:
            - the target word has the letter "O" in position 2 (counting from 1)
            - the target word contains the letter "E", but not in position 5
            - the target word does not contain letters "H", "U", or "S"
        An example target word that fits this feedback is "FOYER".

        There are some important special cases when the guess contains the same letter in
        multiple positions. Suppose the letter X appears M times in the guess and N times
        in the target:
            - the K appearances of X in a correct position will be "GREEN"
            - if M <= N, then all other appearances of X will be "YELLOW"
            - if M > N, then N-K of the other appearances of X (selected arbitrarily) will
            be "YELLOW". The remaining appearances of X will be "GRAY"

        Parameters
        ----------
        guess : str
            The guess made by the agent
        feedback : list[str]
            A list of colors (expressed as strings "green", "yellow", "gray") corresponding
            to the letters in the guess
        """
        self.possible = filter_possible_words(guess, feedback, self.possible)


class RandomAgent(WordleAgent):
    """A WordleAgent that guesses (randomly) from among words that satisfy the accumulated feedback."""

    def __init__(self, allowed, possible):
        super().__init__(allowed, possible)
        self.pool = self.allowed

    def first_guess(self):
        self.pool = self.allowed
        shuffle(self.pool)
        return self.next_guess()

    def next_guess(self):
        shuffle(self.pool)
        return self.pool[0]

    def report_feedback(self, guess, feedback):
        self.pool = filter_possible_words(guess, feedback, self.pool)

