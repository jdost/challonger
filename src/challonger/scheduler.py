from app import bot, config
from . import state

channels = config["challonger"]["channels"]
LUNCH = "lunch"
AFTER_WORK = "after_work"

aliases = {
    "at lunch": LUNCH,
    "over lunch": LUNCH,
    "during lunch": LUNCH,
}

available = {
    LUNCH: {
        "can't": set(),
        "can": set(),
    },
    AFTER_WORK: {
        "can't": set(),
        "can": set(),
    },
}


@bot.listen("@me: I <can('t){0,1}:ability> play <*:time>", channel=channels,
            regex=True)
def schedule(time, ability, user, channel, **kwargs):
    time = aliases.get(time, time)
    if time not in [LUNCH, AFTER_WORK]:
        bot.post(
            channel=channel,
            text='Sorry {!s}, I don\'t know that time.'.format(user),
        )

    available_users = available[time]
    if user in available_users[ability]:
        return

    available_users[ability].add(user)
    for match in check(user):
        unavailable_users = match & available_users["can't"]
        if len(unavailable_users) > 0:
            if len(unavailable_users) > 1:
                bot.post(
                    channel=channel,
                    text="Sorry, {} cannot play at that time".format(
                        ', '.join(map(str, unavailable_users)))
                )
            return

        required_users = match - available_users["can"]
        if len(required_users):
            bot.post(
                channel=channel,
                text='Still waiting to hear from: {}'.format(
                    ', '.join(map(str, required_users))),
            )
        else:
            bot.post(
                channel=channel,
                text='{!s} is happening!'.format(match),
            )


def check(*users):
    for match in state.matches.values():
        if match.is_open() and len(users & match):
            yield match
