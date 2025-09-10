from character import Character
from item import Weapon, Armor
from ability import Ability
from skill import Skill
from faction import Faction
from ui import print_bordered

class Player(Character):
    """Represents the player character in the game."""
    def __init__(self, name, location=(1, 1), health=100, attack_power=10, defense=5):
        super().__init__(name, health, attack_power, defense)
        self.location = location
        self.inventory = []
        self.weapon = None
        self.armor = None
        self.active_quests = []
        self.completed_quests = []
        self.known_recipes = []
        self.last_npc_talked_to = None
        self.bank_items = []
        self.factions = {} # To store player's standing with different factions
        self.bank_gold = 0
        self.money = 25
        self.skills_affected_this_turn = set()
        self.skills = {
            "Attack": Skill("Attack"),
            "Defense": Skill("Defense"),
            "Agility": Skill("Agility"),
            "Magic": Skill("Magic"),
            "Crafting": Skill("Crafting"),
            "Wordbinding": Skill("Wordbinding"),
            "Mining": Skill("Mining"),
            "Smelting": Skill("Smelting"),
            "Smithing": Skill("Smithing"),
            "Thieving": Skill("Thieving"),
            "Woodcutting": Skill("Woodcutting"),
            "Lockpicking": Skill("Lockpicking"),
            "Fishing": Skill("Fishing"),
            "Cooking": Skill("Cooking"),
            "Herblore": Skill("Herblore"),
            "Hunting": Skill("Hunting")
        }
        self.jail_time_remaining = 0
        self.max_words_to_bind = 2

        # Give the player a starting spell
        firebolt = Ability("Firebolt", "Hurls a small bolt of fire at the enemy.", mana_cost=5, effect={'type': 'damage', 'amount': 20})
        self.abilities.append(firebolt)

    def add_skill_xp(self, skill_name, amount):
        """Adds XP to a specific skill and handles leveling up."""
        if skill_name in self.skills:
            self.skills[skill_name].add_xp(amount, self)
            self.skills_affected_this_turn.add(skill_name)
        else:
            print(f"Warning: Attempted to add XP to an unknown skill '{skill_name}'.")

    def learn_recipe(self, recipe):
        """Adds a new recipe to the player's list of known recipes."""
        # Check if the recipe is already known by comparing names
        if not any(r.name == recipe.name for r in self.known_recipes):
            self.known_recipes.append(recipe)
            print(f"You have learned a new recipe: {recipe.name}!")
        else:
            print("You already know this recipe. The scroll crumbles to dust.")

    def learn_ability(self, ability):
        """Adds a new ability to the player's spellbook if they don't already know it."""
        if any(ab.name == ability.name for ab in self.abilities):
            print(f"You already know the spell '{ability.name}'.")
        else:
            self.abilities.append(ability)
            print(f"You have learned a new spell: {ability.name}!")
            print(f'"{ability.description}"')

    def change_faction_rep(self, faction_name, amount):
        """Changes the player's reputation with a specific faction."""
        from event_manager import event_manager # Local import to avoid circular dependency

        if faction_name in self.factions:
            old_standing = self.factions[faction_name].get_standing()
            self.factions[faction_name].change_reputation(amount)
            new_standing = self.factions[faction_name].get_standing()
            print(f"Your reputation with {self.factions[faction_name].name} has changed by {amount}. (New standing: {new_standing})")
            event_manager.dispatch('on_faction_change', player=self, faction_name=faction_name, amount=amount, old_standing=old_standing, new_standing=new_standing)
        else:
            print(f"Warning: Attempted to change reputation with an unknown faction '{faction_name}'.")

    @property
    def attack_power(self):
        """Calculates total attack power including weapon bonus."""
        bonus = self.weapon.attack_bonus if self.weapon else 0
        return self.base_attack + bonus

    @property
    def defense(self):
        """Calculates total defense including armor and status effects."""
        armor_bonus = self.armor.defense_bonus if self.armor else 0
        # Get the base defense + status effect bonus from the parent
        base_and_effect_defense = super().defense
        return base_and_effect_defense + armor_bonus

    def clear_affected_skills(self):
        """Clears the set of skills affected in a turn."""
        self.skills_affected_this_turn.clear()

    def print_combat_status(self, enemy):
        """Prints a summary of player and enemy status during combat."""
        player_effects = self.get_status_effects_string()
        enemy_effects = enemy.get_status_effects_string()

        content = [
            f"Your Status:",
            f"  HP: {self.health}/{self.max_health} | MP: {self.mana}/{self.max_mana}",
            f"  Effects: {player_effects}",
            "",
            f"{enemy.name}'s Status:",
            f"  HP: {enemy.health}/{enemy.max_health}",
            f"  Effects: {enemy_effects}"
        ]
        print_bordered("Combat Status", content)

    def print_status(self, affected_skills=None):
        """Prints the player's current stats and equipment."""
        title = f"{self.name}'s Status"
        content = [
            f"HP: {self.health}/{self.max_health} | MP: {self.mana}/{self.max_mana} | Gold: {self.money}",
            f"Atk: {self.attack_power} ({self.base_attack} base) | Def: {self.defense} ({self.base_defense} base)",
            f"Weapon: {self.weapon.name if self.weapon else 'None'} | Armor: {self.armor.name if self.armor else 'None'}",
        ]

        effects_string = self.get_status_effects_string()
        if effects_string != "None":
            content.append(f"Active Effects: {effects_string}")

        # Determine which skills to show
        skills_to_display = []
        if affected_skills is not None:
            skills_to_display = [self.skills[name] for name in affected_skills if name in self.skills]
        else:
            skills_to_display = self.skills.values()

        if skills_to_display:
            content.append("")
            content.append("Skills:")
        for skill in skills_to_display:
            xp_to_next = skill.xp_to_next_level - skill.xp
            content.append(f"- {skill.name}: Level {skill.level} ({skill.xp}/{skill.xp_to_next_level} XP, {xp_to_next} to next)")
        
        print_bordered(title, content)
