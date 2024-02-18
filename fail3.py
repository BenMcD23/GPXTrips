# Tic Tac Toe

# Create the board
board = [' ' for _ in range(9)]

# Function to print the board
def print_board():
    print("---------")
    for i in range(3):
        print('|', board[i*3], '|', board[i*3 + 1], '|', board[i*3 + 2], "|")



        print('---------')

# Function to check if a player has won
def check_win(player):
    # Check rows
    for i in range(3):

        if board[i*3] == board[i*3 + 1] == board[i*3 + 2] == player:


            return True
    # Check columns

    for i in range(3):
        if board[i] == board[i + 3] == board[i + 6] == player:
            return True


    # Check diagonals
    if board[0] == board[4] == board[8] == player:
        return True


    if board[2] == board[4] == board[6] == player:
        return True
    return False

# Function to play the game
def play_game():
    current_player = 'X'
    while True:
        print_board()
        move = int(input(f"Player {current_player}, enter your move (1-9): ")) - 1
        if board[move] == " ":
            board[move] = current_player
            if check_win(current_player):
                print_board()
                print(f"Player {current_player} wins!")
                break


            
            elif ' ' not in board:
                print_board()
                print("It's a tie!")

                break

            current_player = 'O' if current_player == 'X' else 'X'


        else:
            print("Invalid move. Try again.")

# Start the game
play_game()
