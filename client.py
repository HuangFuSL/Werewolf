from Werewolf.client import launchClient
import sys


if __name__ == "__main__":
    serverAddr = input(
        "Please enter the IP address of the server:\n")
    if not serverAddr:
        serverAddr = "localhost"
    try:
        serverPort = int(
            input("Please enter the port of the server:\n"))
    except:
        serverPort = 21567
    launchClient(serverAddr, serverPort)
