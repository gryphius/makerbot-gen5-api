#!/usr/bin/python
import makerbotapi
import sys

if __name__ == '__main__':
    config = makerbotapi.makerbotapi.Config()
    # Load a config. If you don't have a config, makerbotapi will create one
    # for you.
    config.load()

    # Here's a few sample bots. Bot info is a tuple in the form of (<ip>, <name>, <serial>)
    #   Usually you'll get this from discover()
    bot = ['10.1.10.114', 'MakerBot Replicator 5th Gen',
           '23C100053C7059000551']
    bot2 = ['10.1.10.242', 'MakerBot Replicator Mini', '23C100043C8054003A74']

    # Adding the bots to the config
    config.addBot(bot)
    config.addBot(bot2)

    # Here we changed the ip of bot. Since the serial hasn't changed, this
    # won't add a new bot, but will change the current one.
    bot[0] = '10.1.10.99'
    config.addBot(bot)

    # All bots require an authorization code before allowing access. You can
    # store the code in you config file if you'd like.

    # First we have to explicitly state that we are ok with saving the Auth code.
    # The first argument is the serial number of bot, and the second arg is
    # saying that we have permission to save.
    config.setAuthCodeSavePermission(bot[2], True)

    # Now we can save an authentication code to the bot.
    config.saveAuthCode(bot[2], 'SampleAuthCode')

    # Let's check that the Auth Code actually got inputted.
    print config.getBotInfo(bot[2])

    # Lastly, we'll save the config
    config.save()
