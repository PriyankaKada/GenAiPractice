class TicTacToe:
    def __init__(self):
        # Initialize the game board as a 3x3 grid filled with spaces
        self.board = [[' ' for _ in range(3)] for _ in range(3)]
        self.current_player = 'X'  # Player X starts the game

    def print_board(self):
        # Print the current state of the board
        for row in self.board:
            print('|'.join(row))
            print('-' * 5)  # Print a separator between rows

    def make_move(self, row, col):
        # Place the current player's mark on the board if the cell is empty
        if self.board[row][col] == ' ':
            self.board[row][col] = self.current_player
            return True
        return False

    def check_winner(self):
        # Check rows, columns, and diagonals for a winner
        for i in range(3):
            if self.board[i][0] == self.board[i][1] == self.board[i][2] != ' ':
                return self.board[i][0]
            if self.board[0][i] == self.board[1][i] == self.board[2][i] != ' ':
                return self.board[0][i]
        if self.board[0][0] == self.board[1][1] == self.board[2][2] != ' ':
            return self.board[0][0]
        if self.board[0][2] == self.board[1][1] == self.board[2][0] != ' ':
            return self.board[0][2]
        return None  # No winner yet

    def switch_player(self):
        # Switch the current player between 'X' and 'O'
        self.current_player = 'O' if self.current_player == 'X' else 'X'

    def is_full(self):
        # Check if the board is full
        return all(cell != ' ' for row in self.board for cell in row)

    def play_game(self):
        # Main game loop
        while True:
            self.print_board()  # Print the board
            row = int(input(f'Player {self.current_player}, enter row (0-2): '))
            col = int(input(f'Player {self.current_player}, enter column (0-2): '))
            if self.make_move(row, col):
                winner = self.check_winner()
                if winner:
                    self.print_board()
                    print(f'Player {winner} wins!')
                    break
                if self.is_full():
                    self.print_board()
                    print('The game is a draw!')
                    break
                self.switch_player()  # Switch to the other player
            else:
                print('Invalid move, try again.')