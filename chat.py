""" this module sets up a generic chat interface, to the extent
possible.  it will specifically allow for either irc or mattermost to be
used agnostically.  other chat systems aren't currently in spec, but by
attempting to be generic and allowing dialect modules to be used, it
should be relatively easy to adapt for other chat systems. """

import logging
import json
import cmdparser as p
from player import Player

logger = logging.getLogger(__name__)

class CAHmsg:
    """ message object """
    def __init__(self, player, message, source):
        if not isinstance(player, Player):
            raise TypeError('First arg must be a Player object')
        self.player = player
        self.message = message
        self.source = source

    def __repr__(self):
        return f'CAHmsg("{self.player.nick}", "{self.message}", "{self.source}")'

    def json(self):
        return json.dumps({'nick': self.player.nick, 
                           'message': self.message,
                           'source': self.source})

class Chat:
    """
    class to allow generic access to chat systems.  this depends
    upon imported dialect modules implementing the same interface.
    allowed dialects:
    
    * irc
    * mattermost
    """

    def __init__(self, game):
        """ set up which type of interface we're using """
        dialect = game.config['chat']['dialect']
        if dialect == 'irc':
            import cahirc
            self.system = cahirc.Cahirc(game)
        elif dialect == 'mattermost':
            import cahmm
            self.system = cahmm.Cahmm(game)
        self.game = game
        self.channel = self.system.channel

    def start(self):
        """ start the selected chat system. """
        # we expect start() to do everything with the chat system
        # necessary to be ready to start sending and receiving messages
        # with the system.  the system should furthermore handle
        # reconnecting autonomously.
        logger.info("Starting Chat subsystem")
        self.system.start()

    def say(self, destination, text: str) -> None:
        """ say something to the requested destination.  destination
        should be either a player object (for a direct message
        to a person) or a channel name. """
        self.system.say(destination, text)

    def receive_msg(self, msg: CAHmsg):
        """ function to process an incoming message. the msg variable
        should contain a CAHmsg object.  """
        parser = p.CmdParser(self.game)
        parser.parse(msg)
        self.game.command(parser)

    def stop(self, text: str="Shutting down") -> None:
        """ shut down the chat system, with an optional message """
        self.system.stop(text)
