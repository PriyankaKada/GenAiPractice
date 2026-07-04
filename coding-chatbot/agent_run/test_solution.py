import pytest
from solution import TicTacToe


def test_initial_board():
    game = TicTacToe()
    assert game.board == [[' ', ' ', ' '], [' ', ' ', ' '], [' ', ' ', ' ']]


def test_make_move_valid():
    game = TicTacToe()
    assert game.make_move(0, 0) is True
    assert game.board[0][0] == 'X'


def test_make_move_invalid():
    game = TicTacToe()
    game.make_move(0, 0)
    assert game.make_move(0, 0) is False  # Trying to overwrite


def test_check_winner_horizontal():
    game = TicTacToe()
    game.make_move(0, 0)
    game.make_move(1, 0)
    game.make_move(0, 1)
    game.make_move(1, 1)
    game.make_move(0, 2)
    assert game.check_winner() == 'X'  # X wins horizontally


def test_check_winner_vertical():
    game = TicTacToe()
    game.make_move(0, 0)
    game.make_move(0, 1)
    game.make_move(1, 0)
    game.make_move(1, 1)
    game.make_move(2, 0)
    assert game.check_winner() == 'X'  # X wins vertically


def test_check_winner_diagonal():
    game = TicTacToe()
    game.make_move(0, 0)
    game.make_move(1, 1)
    game.make_move(1, 0)
    game.make_move(2, 1)
    game.make_move(2, 2)
    assert game.check_winner() == 'X'  # X wins diagonally


def test_is_full():
    game = TicTacToe()
    for i in range(3):
        for j in range(3):
            game.make_move(i, j)
    assert game.is_full() is True


def test_is_not_full():
    game = TicTacToe()
    game.make_move(0, 0)
    assert game.is_full() is False


def test_switch_player():
    game = TicTacToe()
    assert game.current_player == 'X'
    game.switch_player()
    assert game.current_player == 'O'
    game.switch_player()
    assert game.current_player == 'X'