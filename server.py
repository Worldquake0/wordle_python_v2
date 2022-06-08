from _thread import *
import socket
import random
import sys
import ssl
import hashlib
from cryptography.fernet import Fernet


# Define Constants and File Destinations
ENCODING = 'utf-8'
TARGET_LIST = 'target.txt'
GUESS_LIST = 'guess.txt'
SERVER_PRIVATE_KEY = 'server.key'
SERVER_CERTIFICATE = 'server.crt'
CLIENT_CERTIFICATE = 'client.crt'


def hint_generator(guess, answer):
    """
    Checks the guessed word against the correct word, and generates a hint to be sent to the client.
    If a letter at a given position in the guess matches the letter at that same position in the answer,
    the character at that position in the hint will be the corresponding letter from the guess in uppercase.
    If a letter at a given position in the guess does not match the letter at that same position in the answer,
    but the letter in the guess does appear somewhere in the target word that has not already been matched,
    the character at that position in the hint will be the corresponding letter from the guess in lowercase.
    Otherwise, the character at a given position in the hint will be an underscore
    :param guess: The guessed word sent from the client
    :param answer: The target word for this instance of Wordle
    :return: The hint to be sent to the client
    """
    hint = ["_", "_", "_", "_", "_"]
    for i in range(len(guess)):
        if guess[i] == answer[i]:
            hint[i] = guess[i].upper()
    for i in range(len(guess)):
        if guess[i] in answer and guess[i] != answer[i]:
            if (hint.count(guess[i]) + hint.count(guess[i].lower())) < answer.count(guess[i]):
                hint[i] = guess[i].lower()
    return "".join(hint)


def read_random_word():
    """
    Opens the list of target words and returns a random word from the list.
    :return: A random word from the target.txt
    """
    with open(TARGET_LIST) as f:
        words = f.read().splitlines()
        return random.choice(words)


def wordle_game_server(client, session_key):
    """
    Contains the logic for the Wordle game and will run the game when called.
    Utilises Fernet symmetrical encryption to securely send messages to each client.
    A hash of the target word is sent to clients when the game starts to assure anti-cheating practices
    :param client: The client for this instance of the game
    :param session_key: The symmetrical key used for the Fernet encryption in this game instance
    """
    # Select the target word for the game instance. It is displayed on the server side for debugging purposes
    selected_word = read_random_word()
    print(selected_word)
    # Hash the selected word, which is sent to the client so that they can verify the server is not cheating
    hashed_word = hashlib.sha3_256(selected_word.encode(ENCODING)).hexdigest()
    # Send the first hint and the hashed target word to the client to start the game
    client.send(session_key.encrypt(b"_____" + hashed_word.encode(ENCODING)))
    # Initiate game variables
    number_of_guesses = 0
    active_game_state = True
    while active_game_state:
        # Converts the incoming guess to upper case
        guess = session_key.decrypt(client.recv(1024)).decode(ENCODING).upper()
        # Validate the incoming guess
        with open(GUESS_LIST) as f:
            if guess in f.read():
                # Increment number_of_guesses if the guess was valid
                number_of_guesses += 1
                # If the guess matches the target word, send the game ending prompt to the client
                if guess == selected_word:
                    client.send(session_key.encrypt((str(number_of_guesses) + "GAME OVER" + "\n").encode(ENCODING)))
                    active_game_state = False
                else:
                    # If the guess does not match the target word, hints are sent to the client
                    new_hint = hint_generator(guess, selected_word)
                    client.send(session_key.encrypt((new_hint + "\n").encode(ENCODING)))
            else:
                # If the guess was invalid, notify the client
                client.send(session_key.encrypt(("INVALID GUESS" + "\n").encode(ENCODING)))


def main(port_arg):
    """
    Creates a secure Wordle server that can handle multiple concurrent clients.
    Incoming clients must perform a TLS handshake, request a new game and offer a session key
    before the Wordle game can begin
    :param port_arg: The port number to host the game server on
    """

    # Attempt to create a server socket and attempt to bind to the port number.
    # If successful, print a confirmation message.
    # If unsuccessful, exit with error message.
    try:
        host = ""
        port = int(port_arg)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            sock.bind((host, port))
            # Configure the TLS wrapper for the server
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_SERVER)
            context.verify_mode = ssl.CERT_REQUIRED
            context.load_cert_chain(certfile=SERVER_CERTIFICATE, keyfile=SERVER_PRIVATE_KEY)
            context.load_verify_locations(cafile=CLIENT_CERTIFICATE)
            # Wrap the server socket
            secure_sock = context.wrap_socket(sock, server_side=True, do_handshake_on_connect=True)
            print(f"Secure server socket has successfully bound to Port {port}")
    except (socket.error, IndexError) as e:
        print(e)
        sys.exit(1)

    # Put the server socket into listening mode, queuing up to 5 connection requests
    secure_sock.listen(5)
    # Connect to incoming clients.
    while True:
        client_socket, address = secure_sock.accept()
        print(f"Received a connection from {address}")
        client_message = client_socket.recv(1024)
        # Start the game once 'START GAME' is received from the client and store the attached session key.
        # The unique symmetrical session key will be used to encrypt and decrypt all messages for that game instance.
        if client_message[:10].decode(ENCODING) == "START GAME":
            print(f"Game starting with {address}")
            key = client_message[10:]
            session_key = Fernet(key)
            start_new_thread(wordle_game_server, (client_socket, session_key))
        else:
            print(f"Game start with {address} unsuccessful")
            client_socket.close()


if __name__ == '__main__':
    main(sys.argv[1])
