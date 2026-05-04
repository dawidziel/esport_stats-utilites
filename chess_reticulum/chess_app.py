#!/usr/bin/env python3
"""
Chess over Reticulum Network Stack

A peer-to-peer chess game that uses RNS for encrypted, serverless communication.

Usage:
    Host a game (play as White):  python chess_app.py host
    Join a game (play as Black):  python chess_app.py join <destination_hash>
"""

import json
import sys
import time
import threading

import chess
import RNS

APP_NAME = "chess_reticulum"
ANNOUNCE_INTERVAL = 5  # seconds between periodic announces while waiting


class ChessGame:
    """Manages game state and Reticulum link callbacks."""

    def __init__(self):
        self.board = chess.Board()
        self.link = None
        self.is_white = None        # set by host() / join()
        self.my_turn = False        # set by host() / join()
        self.game_over = False
        self.received_move = None
        self.move_event = threading.Event()
        self.connected_event = threading.Event()

    # ------------------------------------------------------------------
    # Display helpers
    # ------------------------------------------------------------------

    def display_board(self):
        # Flip the board so each player always sees their own pieces at the bottom
        if self.is_white:
            ranks = "87654321"
            files = "a b c d e f g h"
            lines = str(self.board).split("\n")
        else:
            ranks = "12345678"
            files = "h g f e d c b a"
            lines = str(self.board.transform(chess.flip_vertical).transform(chess.flip_horizontal)).split("\n")
        print()
        for i, line in enumerate(lines):
            print("  {}  {}".format(ranks[i], line))
        print("     {}".format(files))
        color = "White" if self.is_white else "Black"
        turn = "White" if self.board.turn == chess.WHITE else "Black"
        print("\n  You: {}  |  Turn: {}".format(color, turn))
        if self.board.is_check():
            print("  *** CHECK ***")
        print()

    # ------------------------------------------------------------------
    # Networking helpers
    # ------------------------------------------------------------------

    def send_message(self, data):
        payload = json.dumps(data).encode("utf-8")
        RNS.Packet(self.link, payload).send()

    # ------------------------------------------------------------------
    # RNS callbacks  (called from background threads)
    # ------------------------------------------------------------------

    def on_client_connected(self, link):
        """Server-side: called when a client establishes a link."""
        RNS.log("Opponent connected", RNS.LOG_INFO)
        self.link = link
        link.set_packet_callback(self.on_packet)
        link.set_link_closed_callback(self.on_link_closed)
        self.connected_event.set()

    def on_link_established(self, link):
        """Client-side: called when the outgoing link is ready."""
        RNS.log("Link established", RNS.LOG_INFO)
        self.link = link
        link.set_packet_callback(self.on_packet)
        link.set_link_closed_callback(self.on_link_closed)
        self.connected_event.set()

    def on_packet(self, message, packet):
        try:
            data = json.loads(message.decode("utf-8"))
        except (UnicodeDecodeError, json.JSONDecodeError) as exc:
            RNS.log("Malformed packet ignored: {}".format(exc), RNS.LOG_WARNING)
            return

        msg_type = data.get("type")
        if msg_type == "move":
            self.received_move = data.get("move")
            self.move_event.set()
        elif msg_type == "resign":
            print("\nOpponent resigned.  You win!")
            self.game_over = True
            self.move_event.set()

    def on_link_closed(self, link):
        print("\nOpponent disconnected.")
        self.game_over = True
        self.move_event.set()

    # ------------------------------------------------------------------
    # Main game loop  (runs on main thread)
    # ------------------------------------------------------------------

    def game_loop(self):
        print("\n=== Chess Game Started ===")
        print("Enter moves in UCI notation (e.g. e2e4) or type 'resign'\n")

        while not self.game_over:
            self.display_board()

            if self.board.is_checkmate():
                winner = "Black" if self.board.turn == chess.WHITE else "White"
                print("Checkmate!  {} wins!".format(winner))
                self.game_over = True
                break
            elif self.board.is_stalemate():
                print("Stalemate!  Draw!")
                self.game_over = True
                break
            elif self.board.is_insufficient_material():
                print("Draw by insufficient material!")
                self.game_over = True
                break
            elif self.board.is_fifty_moves():
                print("Draw by fifty-move rule!")
                self.game_over = True
                break
            elif self.board.is_repetition(3):
                print("Draw by threefold repetition!")
                self.game_over = True
                break

            if self.my_turn:
                while True:
                    try:
                        move_str = input("Your move: ").strip()
                    except (EOFError, KeyboardInterrupt):
                        self.send_message({"type": "resign"})
                        print("\nYou resigned.")
                        self.game_over = True
                        return

                    if move_str.lower() == "resign":
                        self.send_message({"type": "resign"})
                        print("You resigned.")
                        self.game_over = True
                        return

                    try:
                        move = chess.Move.from_uci(move_str)
                    except chess.InvalidMoveError:
                        print("Invalid format. Use UCI notation (e.g. e2e4 or e7e8q for promotion).")
                        continue

                    if move in self.board.legal_moves:
                        self.board.push(move)
                        self.send_message({"type": "move", "move": move_str})
                        self.my_turn = False
                        break
                    else:
                        print("Illegal move. Try again.")
            else:
                print("Waiting for opponent's move...")
                self.move_event.clear()
                self.move_event.wait()

                if self.game_over:
                    break

                if self.received_move:
                    try:
                        move = chess.Move.from_uci(self.received_move)
                        self.board.push(move)
                        print("Opponent played: {}".format(self.received_move))
                        self.my_turn = True
                        self.received_move = None
                    except chess.InvalidMoveError as exc:
                        RNS.log("Invalid move received: {}".format(exc), RNS.LOG_ERROR)

        print("\nGame over.  Thanks for playing!")


# ------------------------------------------------------------------
# Host / join entry points
# ------------------------------------------------------------------

def host(configpath=None):
    """Start a new game as White and wait for an opponent."""
    reticulum = RNS.Reticulum(configpath)

    game = ChessGame()
    game.is_white = True
    game.my_turn = True  # White moves first

    identity = RNS.Identity()
    destination = RNS.Destination(
        identity,
        RNS.Destination.IN,
        RNS.Destination.SINGLE,
        APP_NAME,
        "game",
    )
    destination.set_link_established_callback(game.on_client_connected)
    destination.announce()

    print("Chess game ready!")
    print("\nShare this address with your opponent:")
    print("  {}\n".format(RNS.prettyhexrep(destination.hash)))
    print("Waiting for opponent to connect...")

    last_announce = time.time()
    while not game.connected_event.is_set():
        if time.time() - last_announce >= ANNOUNCE_INTERVAL:
            destination.announce()
            last_announce = time.time()
        time.sleep(0.1)

    print("Opponent connected!  Starting game...\n")
    game.game_loop()


def join(destination_hash_str, configpath=None):
    """Join an existing game as Black."""
    reticulum = RNS.Reticulum(configpath)

    game = ChessGame()
    game.is_white = False
    game.my_turn = False  # White moves first

    # Normalise the hash string (strip colons / spaces that prettyhexrep adds)
    clean_hash = destination_hash_str.replace(":", "").replace(" ", "")
    try:
        dest_hash = bytes.fromhex(clean_hash)
    except ValueError:
        print("Invalid destination hash: {!r}".format(destination_hash_str))
        sys.exit(1)

    print("Connecting to {}...".format(destination_hash_str))

    if not RNS.Transport.has_path(dest_hash):
        print("Requesting path to destination...")
        RNS.Transport.request_path(dest_hash)
        timeout = 30
        start = time.time()
        while not RNS.Transport.has_path(dest_hash):
            time.sleep(0.1)
            if time.time() - start > timeout:
                print("Could not find a path to the destination.")
                print("Make sure the host is running and reachable on the Reticulum network.")
                sys.exit(1)

    server_identity = RNS.Identity.recall(dest_hash)
    if server_identity is None:
        print("Could not recall server identity.")
        print("Make sure the host has announced and try again.")
        sys.exit(1)

    server_destination = RNS.Destination(
        server_identity,
        RNS.Destination.OUT,
        RNS.Destination.SINGLE,
        APP_NAME,
        "game",
    )

    link = RNS.Link(server_destination)
    link.set_link_established_callback(game.on_link_established)
    link.set_packet_callback(game.on_packet)
    link.set_link_closed_callback(game.on_link_closed)

    print("Link request sent.  Waiting for host to accept...")
    if not game.connected_event.wait(timeout=30):
        print("Connection timed out.  Is the host still running?")
        sys.exit(1)

    print("Connected!  Starting game...\n")
    game.game_loop()


# ------------------------------------------------------------------
# CLI entry point
# ------------------------------------------------------------------

def main():
    if len(sys.argv) < 2:
        print(__doc__)
        sys.exit(0)

    command = sys.argv[1].lower()

    if command == "host":
        host()
    elif command == "join":
        if len(sys.argv) < 3:
            print("Usage:  python chess_app.py join <destination_hash>")
            sys.exit(1)
        join(sys.argv[2])
    else:
        print("Unknown command: {!r}".format(sys.argv[1]))
        print("Use 'host' or 'join <destination_hash>'")
        sys.exit(1)


if __name__ == "__main__":
    main()
