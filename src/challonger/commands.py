from app import bot, config
from . import state

channels = config["challonger"]["channels"]


@bot.listen("@me: current", channel=channels)
def list_matches(channel, **kwargs):
    matches = []
    for match in state.matches.values():
        if match.is_open():
            matches.append(str(match))
    bot.post(
        channel=channel,
        text=', '.join(matches)
    )


@bot.listen("@me: link <[username]:users> <*:participant>", regex=True)
def link_users(user, channel, users, participant, **kwargs):
    participant = None
    for player in state.players.values():
        if player.name == participant:
            participant = player
            break

    if not participant:
        bot.post(
            channel=channel,
            text=u"sorry {!s}, {} does not exist".format(user, participant)
        )
        return

    participant.register(*users)
