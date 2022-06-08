import socket
import sys
import ssl
import hashlib
from cryptography.fernet import Fernet


# Define Constants and File Destinations
ENCODING = 'utf-8'
SERVER_CERTIFICATE = 'server.crt'
CLIENT_CERTIFICATE = 'client.crt'
CLIENT_PRIVATE_KEY = 'client.key'
SERVER_HOSTNAME = 'Wordle Server'


def main(host_arg, port_arg):
    """
    Creates a client to connect to an existing Wordle server.
    Utilises Fernet symmetrical encryption to securely send messages to the server.
    A symmetrical session key is generated through the Fernet cryptography module,
    which is sent to the server and used to encrypt all subsequent communication over this connection.
    Client side validation ensures guesses are screened before being sent to the server.
    A hash of the target word is received from the server when the game starts to assure anti-cheating practices
    :param host_arg: The host address the game server is being hosted on
    :param port_arg: The port number the game server is being hosted on
    """

    # Create the client socket
    # Attempt to connect to the server. If unsuccessful, exit with error message.
    host = None
    port = None
    try:
        host = host_arg
        port = int(port_arg)
        with socket.socket(socket.AF_INET, socket.SOCK_STREAM) as sock:
            # Configure TLS for the client
            context = ssl.SSLContext(ssl.PROTOCOL_TLS_CLIENT)
            context.load_cert_chain(certfile=CLIENT_CERTIFICATE, keyfile=CLIENT_PRIVATE_KEY)
            context.load_verify_locations(cafile=SERVER_CERTIFICATE)
            # Wrap the client socket
            secure_sock = context.wrap_socket(sock,
                                              server_side=False,
                                              server_hostname=SERVER_HOSTNAME,
                                              do_handshake_on_connect=True)
            secure_sock.connect((host, port))
    except (socket.error, IndexError) as e:
        print(f"Error. Unable to connect to the server at ({host}, {port})")
        print(e)
        sys.exit(1)

    # Generate a session key for this connection using the Fernet module
    key = Fernet.generate_key()
    session_key = Fernet(key)
    # Send the 'START GAME' prompt and session key to the server
    secure_sock.send("START GAME".encode(ENCODING) + key)
    # Receive the first hint and the hash of the target word from the server to confirm game start
    server_message = session_key.decrypt(secure_sock.recv(1024)).decode(ENCODING)
    initial_hint = server_message[:5]
    hashed_target = server_message[5:]
    if initial_hint == "_____":
        active_game_state = True
        print(initial_hint + "\n")
        # Enter the game loop where the client will begin guessing the target word
        while active_game_state:
            guessing = True
            guess = None
            match_target_word = False
            while guessing:
                # Prompt the user for a guess.
                guess = input("Enter a 5 letter word: ")
                # Perform client side validation. Invalid guesses cause the game to prompt for a new guess.
                if guess.isalpha() is False:
                    print("Error. User input is invalid." + "\n")
                elif len(guess) < 5:
                    print("Error. User input is too short." + "\n")
                elif len(guess) > 5:
                    print("Error. User input is too long." + "\n")
                else:
                    guessing = False
            # Compare and verify the hash of the guess word to the hash of the target word
            hashed_guess = hashlib.sha3_256(guess.upper().encode(ENCODING)).hexdigest()
            if hashed_guess == hashed_target:
                print("Your guess has been verified to match the target word." + "\n")
                match_target_word = True
            # Valid guesses are sent to the server
            secure_sock.send(session_key.encrypt(guess.encode(ENCODING)))
            # If the response from the server contains a numerical score and the hashes match,
            # the score and a game over message sent from the server is displayed. The game then ends.
            # If the hashes match, but the server does not end the game, it is deemed to be cheating,
            # and the game is terminated.
            # Otherwise, a hint is displayed and the game continues with another guess prompt.
            server_response = session_key.decrypt(secure_sock.recv(1024)).decode(ENCODING)
            score = "".join(filter(str.isdigit, server_response))
            if len(score) == 0 and match_target_word:
                print("SERVER INTEGRITY CHECK: Cheating Detected." + "\n")
                secure_sock.close()
            elif len(score) > 0 and match_target_word:
                server_message = server_response[len(score):]
                print("SERVER INTEGRITY CHECK: No Cheating Was Detected." + "\n")
                print(f"Number of valid guesses: {score}" + "\n")
                print(server_message)
                active_game_state = False
            else:
                print(server_response)
        # Close the connection to the server if the game loop ends
        secure_sock.close()
    else:
        # Close the connection to the server if the game start is unsuccessful
        secure_sock.close()


if __name__ == '__main__':
    main(sys.argv[1], sys.argv[2])
