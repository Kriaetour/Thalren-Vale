class Faction:
    """Represents a faction in the game and the player's standing with them."""

    def __init__(self, name, description):
        self.name = name
        self.description = description
        self.reputation = 0  # Player's standing with this faction

    def get_standing(self):
        """Returns a string describing the player's current standing."""
        if self.reputation >= 50:
            return "Honored"
        elif self.reputation >= 20:
            return "Friendly"
        elif self.reputation > -20:
            return "Neutral"
        elif self.reputation > -50:
            return "Unfriendly"
        else:
            return "Hated"

    def change_reputation(self, amount):
        """Changes the player's reputation with this faction."""
        self.reputation += amount