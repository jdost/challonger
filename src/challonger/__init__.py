import challonge

from app import config

challonge.set_credentials(
    config["challonge_credentials"]["username"],
    config["challonge_credentials"]["token"]
)

__import__("challonger.commands")
__import__("challonger.state")
