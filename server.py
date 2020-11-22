from Werewolf.misc.preset12 import Villager4Wolf4PredictorWitchHunterIdiot
from Werewolf.server.logic import Game

if __name__ == "__main__":
    playerCount: int = 12
    print('the number of players is: %d' % playerCount)

    # initialize a new game
    game = Game(playerCount)
    identityList = Villager4Wolf4PredictorWitchHunterIdiot
    game.setIdentityList(**identityList)
    game.startListening()
    game.activate()
    # start the game
    game.launch()
