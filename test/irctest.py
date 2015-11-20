# vi: set expandtab ai:
#!/usr/bin/env python

import irc
import irc.bot

class BotConnection(irc.client.SimpleIRCClient):
    def __init__(self, channelname):
        irc.client.SimpleIRCClient.__init__(self)
        self.channelname = channelname

    def on_welcome(self, connection, event):
        connection.join(self.channelname)

    def on_join(self, connection, event):
        do_say(self)

    def on_disconnect(self, connection, event):
        sys.exit(0)

    def say(self, msg):
        self.connection.privmsg(self.channelname, msg)


def main():
    server = 'irc.muppetlabs.com'
    port = 6667
    target = "#test"
    nickname = 'testbot'
    c = BotConnection(target)
    try:
        c.connect(server, port, nickname)
    except irc.client.ServerConnectionError as x:
        print(x)
        sys.exit(1)
    c.start()

def do_say(obj):
    obj.say('this is a test')
    
if __name__ == '__main__':
    main()
