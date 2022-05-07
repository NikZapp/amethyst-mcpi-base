from mcpi import minecraft


class Plugin:
    name = 'mcpi'
    author = 'NikZapp'
    players = {}

    def __init__(self):
        # We do not need plugin info, so we don't have a function attached to amethyst.setup
        self.api = minecraft.Minecraft.create()
        # Well this is it. Use amethyst['plugins']['mcpi'].api.setBlock() or whatever
        # A stop event may be useful, but needs library modification

    events = {}