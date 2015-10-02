import json
import challonge
from dateutil import parser

from app import bot
from lazbot import logger
from lazbot.models import User


def parse_time(time_str):
    return parser.parse(time_str)


class Participant(object):
    def __init__(self, tournament, raw):
        self.raw = raw
        self.id = raw["id"]
        self.tournament = tournament
        self.name = raw["name"]
        self.slack_users = []
        self.matches = []

        if "misc" in raw and raw["misc"]:
            self.parse(raw["misc"])

    def parse(self, misc_str):
        data = json.loads(misc_str)
        self.slack_users = data["users"]

    def users(self):
        for user in self.slack_users:
            if type(user) is str or type(user) is unicode:
                self.slack_users.remove(user)
                self.slack_users.insert(0, bot.get_user(user))

        return self.slack_users

    def register(self, *user_ids):
        data = json.dumps({"users": user_ids})
        self.slack_users = [bot.get_user(user) for user in user_ids]

        logger.debug("Registering %s as %s", ", ".join(user_ids), self.name)

        challonge.participants.update(self.tournament, self.id, misc=data)

    def add_match(self, match):
        if match not in self.matches:
            self.matches.append(match)

    def current_match(self):
        for match in self.matches:
            if match.is_open():
                return match

        return None

    def completed_matches(self):
        return [match for match in self.matches if match.is_complete()]

    def __str__(self):
        if len(self.slack_users):
            return ' / '.join([str(user) for user in self.users()])

        return self.name

    def __contains__(self, user):
        if isinstance(user, User):
            return user in self.slack_users
        else:
            return user in map(lambda x: x.id, self.slack_users)


class Match(object):
    OPEN = "open"
    PENDING = "pending"
    COMPLETE = "complete"

    def __init__(self, raw):

        self.raw = raw
        self.updated_at = parse_time(raw["updated-at"])
        self.tournament = raw["tournament-id"]
        self.id = raw["id"]
        self.state = Match.PENDING

        if raw["state"] == Match.OPEN:
            self.set_open()
        elif raw["state"] == Match.COMPLETE:
            self.set_complete()
        else:
            self.participants = []

        for participant in self.participants:
            if isinstance(participant, Participant):
                participant.add_match(self)

        logger.debug("Loaded Match %s - %s", self.state, self)

    def is_open(self):
        return self.state == Match.OPEN

    def set_open(self):
        player1, player2 = self.raw["player1-id"], self.raw["player2-id"]
        from challonger.state import get_participants
        self.participants = get_participants(player1, player2)
        self.state = Match.OPEN

    def is_complete(self):
        return self.state == Match.COMPLETE

    def set_complete(self):
        winner, loser = self.raw["winner-id"], self.raw["loser-id"]
        scores = self.raw["scores-csv"]
        from challonger.state import get_participants
        self.winner, self.loser = get_participants(winner, loser)
        self.participants = [self.winner, self.loser]
        self.scores = self.parse_scores(scores)
        self.state = Match.COMPLETE

    def update(self, raw=None):
        changed = False
        if not raw:
            raw = challonge.matches.show(self.tournament, self.id)

        if raw["state"] != self.state:
            changed = True
            self.raw = raw
            if raw["state"] == Match.COMPLETE:
                self.set_complete()
            elif raw["state"] == Match.OPEN:
                self.set_open()

        return changed

    @classmethod
    def parse_scores(cls, scores_csv):
        outcome = [0, 0]
        for score in scores_csv.split(","):
            a, b = score.split('-')
            if int(a) > int(b):
                outcome[0] += 1
            else:
                outcome[1] += 1

        return '{}-{}'.format(*sorted(outcome, reverse=True))

    def matchup(self):
        return self.participants

    def results(self):
        if not self.is_complete():
            return None

        return {
            "winner": self.winner,
            "loser": self.loser,
            "score": self.scores,
        }

    def __gt__(self, timestamp):
        return self.updated_at > parse_time(timestamp)

    def __ge__(self, timestamp):
        return self.updated_at >= parse_time(timestamp)

    def __lt__(self, timestamp):
        return self.updated_at < parse_time(timestamp)

    def __le__(self, timestamp):
        return self.updated_at <= parse_time(timestamp)

    def __str__(self):
        if self.is_open():
            return "{!s} vs {!s}".format(*self.matchup())
        elif self.is_complete():
            results = self.results()
            return "{winner!s} defeated {loser!s}: {scores!s}".format(
                winner=results["winner"], loser=results["loser"],
                scores=results["score"])
        else:
            return ""
