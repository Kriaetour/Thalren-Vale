import math

def _calculate_total_xp_for_level(level):
    """
    Calculates the total XP needed to reach a specific level,
    based on a formula inspired by OSRS.
    """
    total_xp = 0
    for l in range(1, level):
        total_xp += math.floor(l + 300 * (2 ** (l / 7.0)))
    return math.floor(total_xp / 4)

class Skill:
    """Manages the state of a single skill for a character."""
    def __init__(self, name, level=1, xp=0):
        self.name = name
        self.level = level
        self.xp = xp
        self.xp_to_next_level = _calculate_total_xp_for_level(self.level + 1)

    def add_xp(self, amount, player):
        """Adds XP to the skill and checks for level up."""
        if amount <= 0:
            return
        
        self.xp += amount
        print(f"You gain {amount} {self.name} XP.")
        
        while self.xp >= self.xp_to_next_level:
            self._level_up(player)

    def _level_up(self, player):
        """Handles leveling up the skill and applying bonuses to the player."""
        self.level += 1
        self.xp_to_next_level = _calculate_total_xp_for_level(self.level + 1)
        print("\n" + "*" * 35)
        print(f"** Your {self.name} level has increased to {self.level}! **")

        # Apply stat bonuses based on the skill
        if self.name == "Combat":
            player.max_health += 10
            player.base_attack += 2
            player.base_defense += 1
            player.health = player.max_health  # Full heal on level up
            print(f"Max HP, Base Attack, and Base Defense increased.")
        elif self.name == "Attack":
            player.base_attack += 1
            print(f"Your Base Attack has increased to {player.base_attack}.")
        elif self.name == "Defense":
            player.base_defense += 1
            player.max_health += 10
            player.health = player.max_health # Heal on level up
            print(f"Your Base Defense has increased to {player.base_defense} and your Max HP is now {player.max_health}!")
        elif self.name == "Agility":
            print("You feel more nimble and quick on your feet.")
        elif self.name == "Magic":
            player.max_mana += 10
            player.mana = player.max_mana
            print(f"Max Mana increased.")
        elif self.name == "Wordbinding":
            # Increase word slots every 5 levels
            if self.level % 5 == 0:
                player.max_words_to_bind += 1
                print(f"You can now bind {player.max_words_to_bind} words at once!")
        elif self.name == "Mining":
            print("You feel more confident with a pickaxe in your hands.")
        elif self.name == "Smelting":
            print("You feel more adept at working the forge.")
        elif self.name == "Smithing":
            print("Your hands feel more steady at the anvil.")
        elif self.name == "Thieving":
            print("Your fingers feel more nimble.")
        elif self.name == "Woodcutting":
            print("Your grip on the axe feels stronger.")
        elif self.name == "Fishing":
            print("You feel a deeper connection to the waters.")
        elif self.name == "Cooking":
            print("You feel more comfortable around a cooking fire.")
        elif self.name == "Herblore":
            print("You feel more attuned to the properties of plants.")
        elif self.name == "Hunting":
            print("You feel more adept at tracking and dispatching your prey.")
        print("*" * 35 + "\n")