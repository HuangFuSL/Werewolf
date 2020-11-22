from Werewolf.misc.preset6 import Villager2Wolf2WitchPredictor
from Werewolf.server.logic import Game

if __name__ == "__main__":
    playerCount: int = 6
    print('the number of players is: %d' % playerCount)

    # initialize a new game
    game = Game(playerCount)
    identityList = Villager2Wolf2WitchPredictor
    game.setIdentityList(**identityList)
    game.startListening()
    game.activate()
    # start the game
    game.launch()
