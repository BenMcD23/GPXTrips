# Represent a card deck
suits = ['Hearts', "Diamonds", 'Clubs', 'Spades']
ranks = ['2', '3', '4', '5', '6', '7', '8', '9', '10', 'J', 'Q', 'K', 'A']
deck = [{'rank': rank, 'suit': suit} for suit in suits for rank in ranks]

# Define game rules




def is_valid_move(card, pile):
    if not pile:

      
        return True
      
    last_card_rank = pile[-1]["rank"]
    return ranks.index(card['rank']) > ranks.index(last_card_rank)
