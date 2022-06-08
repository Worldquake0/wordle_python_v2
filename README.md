# Wordle

Wordle is a word guessing game created by Josh Wardle and released in October 2021.
This iteration of the game was developed using Python 3.8, and runs on a server that
supports multiple concurrent clients/players. Additionally, various security measures 
have been implemented into this version of the game to help prevent threats such as 
man-in-the-middle (MITM) attacks. These measures include:
- Secure TLS connections utilising self-signed X.509 certificates
- AES encryption and HMAC authentication through the Fernet cryptography module
- Client-side hash verification to prevent server-side cheating. 


## Installation

Unzip the contents to a target destination. 
The package should contain the following files which are needed to run the game:
- startServer.sh
- startClient.sh
- server.py
- server.key
- server.crt
- client.py
- client.key
- client.crt
- target.txt
- guess.txt

Additionally, the cryptography package containing the Fernet module needs to be 
installed to run the game. 

Additional information regarding the installation of this module can be accessed using the following link:
https://cryptography.io/en/latest/installation/


## Usage

Once all files are contained within the same folder, the game can be run through the command line interface (CLI). 
The server and each separate concurrent client will require a separate CLI.

**startServer.sh** takes a port number as its only command-line parameter.
- E.g. startServer.sh 12345

**startClient.sh** takes a host name as its first command-line parameter 
and a port number as its second command-line parameter.
- E.g. startClient.sh 0.0.0.0 12345


## Game Rules

When a new client connects to the server, the server will randomly select a word from its target word list 
to be the target word for that client. The server will give the client an initial hint, 
consisting of five underscores: "_____"

The client will then need to send along guesses of five-letter words until it discovers the target word. 
After each valid guess, the server will respond with a five-character hint. Each hint depends on the previous 
guess from the user, and is determined as follows (in order of priority):

1. If a letter at a given position in the guess matches the letter at that same position in the target word, 
the character at that position in the hint will be the corresponding letter from the guess in uppercase.
2. If a letter at a given position in the guess does not match the letter at that same position in the target word, 
but the letter in the guess does appear somewhere in the target word that has not already been matched by this or 
the previous rule, the character at that position in the hint will be the corresponding letter from the guess in lowercase.
3. If neither of the conditions above are met, the character at a given position in the hint will be an underscore: "_"

Once the client has correctly guessed the target word, the server sends a score to the player consisting of the 
number of valid guesses it took to discover the target word, followed by a "GAME OVER" message. 
Players are prompted with "INVALID GUESS" when a guess does not exist in the guess.txt file. 
Invalid guesses do not increment the score counter.
Note: Player guesses are not case-sensitive.


## Author
Jesse Chow
220234555

Last Updated: 20 May 2022