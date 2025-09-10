class Ability:
    """
    Represents a special ability or spell that a character can use.
    """
    def __init__(self, name, description, mana_cost, effect=None, status_effect=None):
        """
        Initializes an Ability object.
        :param name: The name of the ability.
        :param description: A description of what the ability does.
        :param mana_cost: The amount of mana required to use the ability.
        :param effect: A dictionary describing the effect, e.g.,
                       {'type': 'damage', 'amount': 25} or
                       {'type': 'heal', 'amount': 30}
        :param status_effect: A dictionary describing a status effect to apply, e.g.,
                       {'type': 'poison', 'damage': 5, 'duration': 3}

        """
        self.name = name
        self.description = description
        self.mana_cost = mana_cost
        self.effect = effect
        self.status_effect = status_effect

# --- Player-learnable Abilities ---
heal_light = Ability("Heal Light", "A minor spell that restores a small amount of health.", mana_cost=8, effect={'type': 'heal', 'amount': 25})
