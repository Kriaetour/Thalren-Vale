import random

class Character:
    """
    A base class for any character in the game (Player, Monster).
    """
    def __init__(self, name, health, attack_power, defense, description=""):
        self.name = name
        self.description = description
        self.max_health = health
        self.health = health
        self.money = 0
        self.base_attack = attack_power
        self.base_defense = defense
        self.max_mana = 20
        self.mana = self.max_mana
        self.abilities = []
        self.status_effects = []
        self.loot_table = []

    @property
    def attack_power(self):
        """Returns the character's total attack power."""
        bonus = 0
        # Check for attack buff status effect
        for effect in self.status_effects:
            if effect['type'] == 'attack_buff':
                bonus += effect.get('amount', 0)
        return self.base_attack + bonus

    @property
    def defense(self):
        """Returns the character's total defense."""
        bonus = 0
        # Check for defense buff status effect
        for effect in self.status_effects:
            if effect['type'] == 'defense_buff':
                bonus += effect.get('amount', 0)
        return self.base_defense + bonus
        
    def is_alive(self):
        """Check if the character is still alive."""
        return self.health > 0

    def heal(self, amount):
        """Heals the character, not exceeding max health. Returns amount healed."""
        amount_to_heal = min(amount, self.max_health - self.health)
        self.health += amount_to_heal
        return amount_to_heal

    def restore_mana(self, amount):
        """Restores the character's mana, not exceeding max mana. Returns amount restored."""
        amount_to_restore = min(amount, self.max_mana - self.mana)
        self.mana += amount_to_restore
        return amount_to_restore

    def add_status_effect(self, effect_data):
        """Adds a new status effect to the character."""
        # Create a copy to avoid modifying the original ability's data
        active_effect = effect_data.copy()
        active_effect['turns_left'] = active_effect.pop('duration')
        self.status_effects.append(active_effect)
        print(f"{self.name} is now afflicted with {active_effect['type']}!")

    def process_turn_effects(self):
        """
        Processes all active status effects at the start of a turn.
        Returns True if the character is stunned, False otherwise.
        """
        is_stunned = False
        effects_to_remove = []

        for effect in self.status_effects:
            if effect['type'] == 'poison':
                damage = effect.get('damage', 0)
                self.health -= damage
                print(f"{self.name} takes {damage} damage from poison.")
                if not self.is_alive(): break
            
            if effect['type'] == 'stun':
                is_stunned = True
                print(f"{self.name} is stunned and cannot act!")
            
            if effect['type'] == 'defense_buff':
                print(f"{self.name}'s defenses are bolstered by a magical effect.")

            if effect['type'] == 'attack_buff':
                print(f"{self.name} feels a surge of strength!")

            effect['turns_left'] -= 1
            if effect['turns_left'] <= 0:
                effects_to_remove.append(effect)
                if effect['type'] == 'defense_buff':
                    print(f"The magical defense around {self.name} fades.")
                elif effect['type'] == 'attack_buff':
                    print(f"The surge of strength in {self.name} fades.")
                else:
                    print(f"{self.name} is no longer afflicted with {effect['type']}.")

        self.status_effects = [eff for eff in self.status_effects if eff not in effects_to_remove]
        return is_stunned

    def take_damage(self, damage, bypass_defense=False):
        """Applies damage to the character, considering their defense."""
        if bypass_defense:
            damage_taken = damage
        else:
            # Simple damage formula: damage taken is attack - defense
            # Ensure damage is at least 1, so you can always hurt an enemy.
            damage_taken = max(1, damage - self.defense)
        self.health -= damage_taken
        print(f"{self.name} takes {damage_taken} damage!")
        if not self.is_alive():
            print(f"{self.name} has been defeated!")
        return damage_taken

    def attack(self, target):
        """The character attacks a target."""
        print(f"{self.name} attacks {target.name}!")
        target.take_damage(self.attack_power)

    def drop_loot(self):
        """Determines and returns loot dropped by the character upon defeat."""
        # For now, we'll assume a 100% drop rate for all items in the loot table.
        return self.loot_table
