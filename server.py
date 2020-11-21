from Werewolf.server.logic import Game

if __name__ == "__main__":
    playerCount: int = 6
    print('the number of players is: %d' % playerCount)

    # initialize a new game
    game = Game(playerCount)
    identityList = {
        "Villager": 2,
        "Witch": 1,
        "Wolf": 2,
        "Predictor": 1
    }
    game.setIdentityList(**identityList)
    game.startListening()
    game.activate()
    # start the game
    game.launch()
