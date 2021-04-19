# BBReplay

BBReplay is an attempt to parse Blood Bowl 1 replay files and turn them
into a sequence of actions and other details about the game. The replay files are
SQLite database files, and the commands are included in the `Replay_NetCommands` table.

This may or may not be possible!

## Documentation

The [Docs](docs) directory contains some details about the file format.

## Known problems

* Setup actions are sometimes missing for some players
  * AI in exhibition matches
  * Human coach's players in exhibition match (may be default positioning)
* Some kick-off events don't give all details
  * e.g. "Brilliant Coaching" happens but doesn't say who gets rerolls
