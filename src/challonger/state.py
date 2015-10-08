import challonge
from app import bot, config
from lazbot.utils import lookup_channel
import lazbot.logger as logger
from datetime import datetime, timedelta

from .models import Participant, Match

players = {}
matches = {}
tournaments = []
default_tournament = None
last_update = None


def get_match(match_id):
    return matches.get(match_id, None)


def get_participants(*particpant_ids):
    return [players.get(id, None) for id in particpant_ids]


def lookup_participant(user):
    for participant in players.values():
        if user in participant:
            return participant

    return None


@bot.setup
def load_info(*_):
    global tournaments
    global default_tournament
    global players
    global last_update

    tournaments = challonge.tournaments.index()
    logger.info("Loaded %d tournaments", len(tournaments))

    default_tournament = [tournament for tournament in tournaments
                          if not tournament["completed-at"]][0]

    for participant in challonge.participants.index(default_tournament["id"]):
        players[participant["id"]] = Participant(
            default_tournament["id"], participant)

    for match in challonge.matches.index(default_tournament["id"]):
        matches[match["id"]] = Match(match)

    logger.info("Loaded %d players", len(players))
    last_update = datetime.now()


@bot.schedule(after=timedelta(minutes=3), recurring=True)
def check_for_updates():
    global last_update
    changes = 0
    matches = []

    try:
        matches = challonge.matches.index(default_tournament["id"])
    except Exception as error:
        logger.error("Error connecting: %s", error)
        return

    for match_data in matches:
        match = get_match(match_data["id"])
        update = match.update(match_data)
        if update:
            changes += 1
            for channel in config["challonger"]["channels"]:
                bot.post(
                    channel=lookup_channel(channel),
                    text=str(match),
                )

    last_update = datetime.now()
    logger.info("Updated %s matches", changes)
