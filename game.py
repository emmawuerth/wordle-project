import argparse
import sys
from collections import defaultdict
from numpy import mean
from random import choice, sample, shuffle
from tqdm import tqdm
import pygame as pg
from agent import initialize_agent
from graphics import CartesianPlane, WordleLetter, WordleSlot, PlayButton, Histogram
from util import read_words, get_feedback
import time

class WordleGame:

    def __init__(self):
        self.clock = WordleGame.initialize_pygame()

    @staticmethod
    def initialize_pygame():
        pg.init()
        if not pg.font:
            print("Warning, fonts disabled")
        if not pg.mixer:
            print("Warning, sound disabled")
        pg.display.set_caption("Wordle")
        pg.mouse.set_visible(True)
        clock = pg.time.Clock()
        clock.tick(60)
        return clock

    def guess_word(self, word):
        colors = get_feedback(guess=word, target=self.target)
        letters = [WordleLetter(word[0], colors[0], 1, self.y_max-self.round),
                   WordleLetter(word[1], colors[1], 2, self.y_max-self.round),
                   WordleLetter(word[2], colors[2], 3, self.y_max-self.round),
                   WordleLetter(word[3], colors[3], 4, self.y_max-self.round),
                   WordleLetter(word[4], colors[4], 5, self.y_max-self.round)]
        for i, letter in enumerate(letters):
            self.plane.add_sprite(letter)
            letter.appear(delay=i*6)
            if word == self.target:
               letter.dance(delay=40+i*6)
        return letters


class WordlePlayer:

    def __init__(self, agent, allowed_guesses, pool):
        self.agent = agent
        self.allowed_guesses = allowed_guesses
        self.pool = pool
        self.results = []
        self.target_queue = [word for word in self.pool]
        shuffle(self.target_queue)
        self.busy = False

    def most_recent_result(self):
        if len(self.results) > 0:
            return self.results[-1]
        else:
            return None

    def play_one(self, target):
        guess = self.agent.first_guess()
        guesses = [guess]
        game_over = False
        while not game_over:
            if guess == target or len(guesses) == 6:
                game_over = True
            else:
                self.agent.report_feedback(guess, get_feedback(guess, target))
                guess = self.agent.next_guess()
                guesses.append(guess)
        return guesses, guess==target

    def notify(self, event):
        pass

    def draw(self, screen):
        self.update()

    def all_done(self):
        return len(self.target_queue) == 0

    def update(self):
        if not self.busy and len(self.target_queue) > 0:
            target, self.target_queue = self.target_queue[0], self.target_queue[1:]
            self.busy = True
            guesses, is_win = self.play_one(target)
            self.results.append((target, guesses))
            self.busy = False
            if is_win:
                return len(guesses)
            else:
                return 7


class WordleFlow(WordleGame):
    """Plays a complete game of Wordle.

    Parameters
    ----------
    agent : agent.WordleAgent
        AI who will play Wordle
    allowed_guesses : list[str]
        List of allowable guesses.
    pool : list[str]
        Pool of possible answers.
    """

    def __init__(self, agent, allowed_guesses, pool):
        super().__init__()
        self.round = 0
        self.y_max = 7
        self.plane = CartesianPlane(x_max=8, y_max=self.y_max,
                                    screen_width=440, screen_height=385)
        for y in range(self.y_max-6, self.y_max):
            for x in range(1, 6):
                self.plane.add_sprite(WordleSlot(x,y))
        self.player = WordlePlayer(agent, allowed_guesses, pool)
        self.histogram = Histogram(x=320, y=305, num_games=len(pool))
        self.plane.add_widget(self.histogram)
        self.target = None
        self.guess_queue = []

    def refresh(self):
        self.round = 0
        self.target, self.guess_queue = self.player.most_recent_result()
        self.plane.clear()
        for y in range(self.y_max-6, self.y_max):
            for x in range(1, 6):
                self.plane.add_sprite(WordleSlot(x,y))
        self.plane.add_widget(self.histogram)

    def play(self):
        end_game = False
        game_over = False
        active_letters = []
        for _ in range(15):
            num_guesses = self.player.update()
            self.histogram.report_win(num_guesses)
        while not end_game and not (game_over and len(active_letters) == 0):
            for event in pg.event.get():
                self.plane.notify(event)
                if event.type == pg.QUIT:
                    game_over = True
                    end_game = True
            if len(active_letters) == 0 and len(self.guess_queue) == 0:
                game_over = True
            elif len(active_letters) == 0:
                self.round += 1
                guess, self.guess_queue = self.guess_queue[0], self.guess_queue[1:]
                active_letters = self.guess_word(guess)
                num_guesses = self.player.update()
                self.histogram.report_win(num_guesses)
                if guess == self.target or self.round > 6:
                    game_over = True
            active_letters = [letter for letter in active_letters if letter.active()]
            self.plane.refresh()
        return end_game


class WordleTournament(WordleGame):

    def __init__(self, agent, allowed_guesses, pool, use_graphics=True):
        super().__init__()
        self.round = 0
        self.y_max = 7
        self.player = WordlePlayer(agent, allowed_guesses, pool)
        self.use_graphics = use_graphics
        if self.use_graphics:
            self.plane = CartesianPlane(x_max=8, y_max=self.y_max,
                                        screen_width=200, screen_height=700)
            self.histogram = Histogram(x=50, y=620, num_games=len(pool), display_rate=True)
            self.plane.add_widget(self.histogram)

    def refresh(self):
        self.round = 0
        if self.use_graphics:
            self.plane.clear()
            self.plane.add_widget(self.histogram)

    def play(self):
        game_over = False
        while not game_over:
            if self.use_graphics:
                for event in pg.event.get():
                    self.plane.notify(event)
                    if event.type == pg.QUIT:
                        game_over = True
            self.round += 1
            num_guesses = self.player.update()
            if self.use_graphics and num_guesses is not None:
                self.histogram.report_win(num_guesses)
                self.plane.refresh()
        return game_over


class WordleEvaluation:

    def __init__(self, agent, allowed_guesses, pool):
        self.round = 0
        self.y_max = 7
        self.player = WordlePlayer(agent, allowed_guesses, pool)

    def refresh(self):
        self.round = 0

    def play(self):
        guess_total = 0
        play_time = 0
        while not self.player.all_done():
            self.round += 1
            start_time = time.time()
            num_guesses = self.player.update()
            stop_time = time.time()
            play_time += (stop_time - start_time)
            guess_total += num_guesses
        avg_num_guesses = guess_total / self.round
        play_rate = self.round / play_time
        return avg_num_guesses, play_rate


class WordleInteractive(WordleGame):
    """Plays a complete game of Wordle.

    Parameters
    ----------
    agent : agent.WordleAgent
        AI who will play Wordle
    allowed_guesses : list[str]
        List of allowable guesses.
    pool : list[str]
        Pool of possible answers.
    target : str
        The hidden target word for this game
    logger : function
        Function for logging game progress.
    """

    def __init__(self, agent, allowed_guesses, pool):
        super().__init__()
        self.agent = agent
        self.allowed_guesses = allowed_guesses
        self.pool = pool
        self.round = 0
        self.target = None
        self.y_max = 8
        self.plane = CartesianPlane(x_max=6, y_max=8, screen_width=330, screen_height=440)
        self.refresh()

    def refresh(self):
        self.plane.clear()
        self.plane.add_sprite(PlayButton(3,0.75))
        for y in range(2, 8):
            for x in range(1, 6):
                self.plane.add_sprite(WordleSlot(x,y))
        self.round = 0
        self.target = choice(self.pool)

    def play(self):
        end_game = False
        game_over = False
        game_will_be_over = False
        guess = self.agent.first_guess()
        while not game_over:
            for event in pg.event.get():
                self.plane.notify(event)
                if event.type == pg.QUIT:
                    game_over = True
                    end_game = True
                elif event.type == pg.MOUSEBUTTONDOWN and game_will_be_over:
                    game_over = True
                elif event.type == pg.MOUSEBUTTONDOWN:
                    self.round += 1
                    self.agent.report_feedback(guess, get_feedback(guess, self.target))
                    self.guess_word(guess)
                    if guess == self.target:
                        game_will_be_over = True
                    else:
                        if self.round > 6:
                            game_will_be_over = True
                        else:
                            guess = self.agent.next_guess()
            self.plane.refresh()
        return end_game


def main():
    parser = argparse.ArgumentParser(description='Play Wordle with your search-based agent.')
    parser.add_argument('-a', '--allowed', required=False, default="data/answers.txt",
                        help='text file containing allowed guesses, one per line')
    parser.add_argument('-p', '--possible', required=False, default="data/answers.txt",
                        help='text file containing possible answers, one per line')
    parser.add_argument('-m', '--mode', dest='mode', required=False, default="interactive",
                        help='game mode: interactive, continuous, histogram')
    args = parser.parse_args()
    allowed = read_words(args.allowed)
    possible = read_words(args.possible)
    agent = initialize_agent(allowed, possible)
    if args.mode == 'continuous':
        game = WordleFlow(agent, allowed, possible)
    elif args.mode == 'histogram':
        game = WordleTournament(agent, allowed, possible)
    elif args.mode == 'interactive':
        game = WordleInteractive(agent, allowed, possible)
    else:
        raise ValueException(f"Unsupported game mode: {args.mode}")
    going = True
    while going:
        if game.play():
            pg.quit()
            going = False
        else:
            game.refresh()


if __name__ == '__main__':
    main()
