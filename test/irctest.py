class GameIRCTest(unittest.TestCase):
    def setUp(self):
        gameclass.cahirc.Cahirc.say.reset_mock()

    def test_game_start_says_game_start(self):
        config = Config()
        chan = config.data['default_channel']
        text = config.data['text']['en']['round_start']
        game = gameclass.Game()
        bob = Player('Bob')
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertTrue(re.search(text,
            str(gameclass.cahirc.Cahirc.say.mock_calls[0])))

    def test_game_start_joining_works(self):
        game = gameclass.Game()
        # a person who says something on the channel is registered as a
        # Player for this exact situation
        bob = Player('Bob')
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        self.assertEqual(str([bob]), str(game.players))

    def test_game_join_joining_works(self):
        game = gameclass.Game()
        bob = Player('Bob')
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        cmdstring = 'join'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        jim = Player('Jim')
        p.parse(msg)
        game.command(p)
        self.assertEqual(str([bob, jim]), str(game.players))

    def test_game_three_join_starts(self):
        game = gameclass.Game()
        bob = Player('Bob')
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        jim = Player('Jim')
        p.parse('join')
        p.player = jim
        game.command(p)
        joe = Player('Joe')
        p.parse('join')
        p.player = joe
        game.command(p)
        self.assertEqual('wait_answers', game.status)

    def test_game_three_join_starts(self):
        game = gameclass.Game()
        cmdstring = 'start'
        msg = CAHmsg('Bob', cmdstring, 'pubmsg')
        p = CmdParser(game)
        p.parse(msg)
        game.command(p)
        cmdstring = 'join'
        msg = CAHmsg('Jim', cmdstring, 'pubmsg')
        p.parse(msg)
        game.command(p)
        msg = CAHmsg('Joe', cmdstring, 'pubmsg')
        p.parse(msg)
        game.command(p)
        self.assertEqual(10, len(game.players[2].show_hand()))

    def test_first_question_displays(self):
        config = Config().data
        chan = config['default_channel']
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertTrue(re.search('Card: ', 
            str(gameclass.cahirc.Cahirc.say.mock_calls[5])))

    def test_joe_gets_cards(self):
        config = Config().data
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        self.assertTrue(re.search('Your cards are: ', 
            str(gameclass.cahirc.Cahirc.say.mock_calls[6])))

    def test_candidates_are_announced(self):
        config = Config().data
        game = gameclass.Game()
        bob = Player('Bob')
        joe = Player('Joe')
        jim = Player('Jim')
        game.start()
        game.add_player(bob)
        game.add_player(joe)
        game.add_player(jim)
        game.play(joe, joe.deal(1))
        game.play(jim, jim.deal(1))
        played_annc = config['text']['en']['all_cards_played']
        self.assertTrue(re.search(played_annc,
            str(gameclass.cahirc.Cahirc.say.mock_calls[10])))


