# Chess over Reticulum

A peer-to-peer chess game that uses the [Reticulum Network Stack](https://reticulum.network/) for encrypted, serverless communication. Play chess with anyone reachable on your Reticulum network — no central server required.

## Requirements

Install dependencies:

```bash
pip install -r requirements.txt
```

Or manually:

```bash
pip install rns chess
```

## Usage

### Host a game (you play White)

```bash
python chess_app.py host
```

The app prints a destination hash. Share it with your opponent.

### Join a game (you play Black)

```bash
python chess_app.py join <destination_hash>
```

Replace `<destination_hash>` with the hash printed by the host.

## Gameplay

Moves are entered in [UCI notation](https://www.chessprogramming.org/UCI):

| Move type        | Example                                          |
|------------------|--------------------------------------------------|
| Regular move     | `e2e4`                                           |
| Capture          | `d5e4`                                           |
| Pawn promotion   | `e7e8q` (q=queen, r=rook, b=bishop, n=knight)   |
| Kingside castle  | `e1g1`                                           |
| Queenside castle | `e1c1`                                           |

Type `resign` at any time to concede the game.

## How it works

- The **host** creates a Reticulum `Destination` and announces it on the network.
- The **client** discovers the host via the destination hash and opens an encrypted `Link`.
- Moves are serialised as JSON and exchanged over the link.
- All traffic is end-to-end encrypted by Reticulum automatically.
