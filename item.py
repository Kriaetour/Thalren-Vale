class Item:
    """
    Represents an item in the game.
    """
    def __init__(self, name, description, value=0, quest_item=False):
        """
        Initializes an Item object.
        :param name: The name of the item.
        :param description: A brief description of the item.
        :param value: The monetary value of the item.
        :param quest_item: A boolean indicating if this is a quest item.
        """
        self.name = name
        self.description = description
        self.value = value
        self.quest_item = quest_item

class Weapon(Item):
    """
    Represents a weapon item in the game.
    """
    def __init__(self, name, description, value, attack_bonus):
        super().__init__(name, description, value)
        self.attack_bonus = attack_bonus

class Armor(Item):
    """
    Represents an armor item in the game.
    """
    def __init__(self, name, description, value, defense_bonus):
        super().__init__(name, description, value)
        self.defense_bonus = defense_bonus

class Consumable(Item):
    """
    Represents a consumable item that can be used.
    """
    def __init__(self, name, description, value, effect, amount):
        super().__init__(name, description, value)
        self.effect = effect  # e.g., "heal", "restore_mana"
        self.amount = amount  # e.g., 25 (for healing), 50 (for mana)

class Spellbook(Item):
    """
    A special item that teaches the player a new ability when used.
    """
    def __init__(self, name, description, value, ability):
        super().__init__(name, description, value)
        self.ability = ability
        
class Key(Item):
    """
    A simple key item that might unlock something.
    """
    def __init__(self, name, description, value, unlocks_what=None):
        super().__init__(name, description, value)
        self.unlocks_what = unlocks_what # e.g., "door_to_dungeon_level_2"

class Word(Item):
    """A special item representing a word of power for the Wordbinding skill."""
    pass

class RecipeScroll(Item):
    """
    A special item that teaches the player a new recipe when used.
    """
    def __init__(self, name, description, value, recipe):
        super().__init__(name, description, value)
        self.recipe = recipe

# --- Special Items ---
pouch_of_gold = Item("Pouch of Gold", "A small leather pouch heavy with coins.", value=50)
healing_potion = Consumable("Healing Potion", "A small vial of red liquid. Restores health.", value=20, effect="heal", amount=30)
mana_potion = Consumable("Mana Potion", "A small vial of blue liquid. Restores mana.", value=20, effect="restore_mana", amount=25)
