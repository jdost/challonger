import challonge

from app import config

challonge.set_credentials(
    config["challonge_credentials"]["username"],
    config["challonge_credentials"]["token"]
)

__import__(__name__ + ".commands")
__import__(__name__ + ".state")
__import__(__name__ + ".scheduler")
