import random
from player import Player
from world import world, default_recipes, dungeon_generator
from enemy_ai import enemy_decision
from item import Key
import pickle
import os

class Game:
    """
    Encapsulates the entire game state and logic, designed to be controlled
    by a UI instead of a command-line loop.
    """
    def __init__(self):
        self.save_filename = "savegame.pkl"
        self.player = Player(name="Adventurer") # Placeholder name
        self.world = world
        self.game_state = {
            "time_of_day": "Day",
            "turn_count": 0,
            "day_length": 20,
            "night_length": 15
        }
        self.current_dungeon = None
        self.in_combat = False
        self.combat_target = None
        self._initialize_game()

    def _initialize_game(self):
        """Sets up the initial state of the game world."""
        self.player.known_recipes.extend(default_recipes)
        self._respawn_monsters()
        self._update_npc_availability()

    def set_player_name(self, name):
        self.player.name = name

    def get_current_location(self):
        """Gets the location data for the player's current position."""
        loc = self.player.location
        if isinstance(loc, tuple):
            row, col = loc
            if 0 <= row < len(self.world["grid"]) and 0 <= col < len(self.world["grid"][row]):
                return self.world["grid"][row][col]
        elif isinstance(loc, str):
            if self.current_dungeon and loc in self.current_dungeon:
                return self.current_dungeon[loc]
            return self.world["special"].get(loc)
        return None

    def _respawn_monsters(self):
        """Respawns monsters in the world."""
        from world import monster_mapping
        for row in self.world["grid"]:
            for loc_data in row:
                loc_data["monsters"] = []
                for name in loc_data.get("enemies", []):
                    if name in monster_mapping:
                        loc_data["monsters"].append(monster_mapping[name]())

    def _update_npc_availability(self):
        """Updates NPC availability based on time."""
        from npc import Shopkeeper
        is_day = self.game_state['time_of_day'] == "Day"
        for row in self.world["grid"]:
            for loc_data in row:
                for npc in loc_data.get("npcs", []):
                    if isinstance(npc, Shopkeeper):
                        npc.is_available = is_day

    def _get_location_data_by_key(self, location_key):
        """Helper to get location data from a key."""
        if isinstance(location_key, tuple):
            row, col = location_key
            if 0 <= row < len(self.world["grid"]) and 0 <= col < len(self.world["grid"][row]):
                return self.world["grid"][row][col]
        elif isinstance(location_key, str):
            return self.world["special"].get(location_key)
        return None

    def _process_npc_schedules(self):
        """Moves NPCs based on their schedules."""
        current_cycle_turn = self.game_state["turn_count"] % (self.game_state["day_length"] + self.game_state["night_length"])
        
        scheduled_npcs = [npc for row in self.world["grid"] for loc in row for npc in loc.get("npcs", []) if npc.schedule]
        for loc in self.world["special"].values():
            scheduled_npcs.extend([npc for npc in loc.get("npcs", []) if npc.schedule])

        for npc in scheduled_npcs:
            target_location_key = None
            for time, location_key in reversed(npc.schedule):
                if current_cycle_turn >= time:
                    target_location_key = location_key
                    break
            
            if target_location_key and npc.current_location_key != target_location_key:
                old_loc_data = self._get_location_data_by_key(npc.current_location_key)
                new_loc_data = self._get_location_data_by_key(target_location_key)

                if old_loc_data and new_loc_data:
                    if npc in old_loc_data.get("npcs", []):
                        old_loc_data["npcs"].remove(npc)
                    if "npcs" not in new_loc_data: new_loc_data["npcs"] = []
                    new_loc_data["npcs"].append(npc)
                    npc.current_location_key = target_location_key

    def advance_time(self, turns=1):
        """Advances game time and updates the world accordingly."""
        self.game_state["turn_count"] += turns
        total_cycle_length = self.game_state["day_length"] + self.game_state["night_length"]
        current_cycle_turn = self.game_state["turn_count"] % total_cycle_length
        new_time_of_day = "Day" if 0 <= current_cycle_turn < self.game_state["day_length"] else "Night"
        
        if new_time_of_day != self.game_state["time_of_day"]:
            self.game_state["time_of_day"] = new_time_of_day
            self._respawn_monsters()
            self._update_npc_availability()
            self._process_npc_schedules()
            return f"The sun has { 'set' if new_time_of_day == 'Night' else 'risen'}."
        return None

    def handle_movement(self, direction):
        """Processes player movement and returns feedback."""
        current_location = self.get_current_location()
        if self.player.jail_time_remaining > 0 and current_location.get("name") == "Rivenshade Jail":
            return "The guard outside rattles the bars. 'Not so fast! You're not done serving your time.'"

        if direction in current_location.get("exits", {}):
            destination = current_location["exits"][direction]

            if isinstance(destination, dict) and destination.get('locked'):
                key_id = destination.get('key_id')
                key_in_inventory = next((item for item in self.player.inventory if isinstance(item, Key) and item.unlocks_what == key_id), None)
                if key_in_inventory:
                    self.player.inventory.remove(key_in_inventory)
                    unlocked_destination = destination['destination']
                    current_location["exits"][direction] = unlocked_destination
                    destination = unlocked_destination
                    feedback = f"You use the {key_in_inventory.name} to unlock the door."
                else:
                    return "The door is locked. It requires a specific key."
            
            self.player.location = destination
            time_feedback = self.advance_time()
            return f"You go {direction}. {time_feedback or ''}"

        if isinstance(self.player.location, tuple):
            row, col = self.player.location
            if direction == "north": row -= 1
            elif direction == "south": row += 1
            elif direction == "east": col += 1
            elif direction == "west": col -= 1
            
            if 0 <= row < len(self.world["grid"]) and 0 <= col < len(self.world["grid"][row]):
                self.player.location = (row, col)
                time_feedback = self.advance_time()
                return f"You go {direction}. {time_feedback or ''}"
            else:
                return "You can't go that way."
        return "You can't go that way from here."

    def handle_enter(self, target):
        """Handles entering a feature and returns feedback."""
        current_location = self.get_current_location()
        if target in current_location.get("features", []):
            if target == "cave":
                self.current_dungeon = dungeon_generator.generate()
                self.player.location = "f0_room_0_0"
                return "You gather your courage and step into the deep, dark cave..."
            elif target == "inn":
                self.player.location = "drunken_griffin_inn"
                return "You push open the heavy wooden door and enter The Drunken Griffin."
        return f"You don't see a '{target}' to enter here."
    

    def handle_take_item(self, item_name):
        """Handles the player taking an item."""
        current_location = self.get_current_location()
        items_in_room = current_location.get("items", [])
        item_to_take = next((item for item in items_in_room if item.name == item_name), None)
        
        if item_to_take:
            self.player.inventory.append(item_to_take)
            items_in_room.remove(item_to_take)
            return f"You take the {item_to_take.name}."
        return f"You don't see a {item_name} here."

    def handle_drop_item(self, item_name):
        """Handles the player dropping an item."""
        item_to_drop = next((item for item in self.player.inventory if item.name == item_name), None)
        if not item_to_drop:
            return f"You don't have a '{item_name}' in your inventory."

        current_location = self.get_current_location()
        if "items" not in current_location:
            current_location["items"] = []
        current_location["items"].append(item_to_drop)
        self.player.inventory.remove(item_to_drop)
        return f"You drop the {item_to_drop.name}."

    def handle_use_item(self, item_name):
        """Handles the player using a consumable item."""
        from item import Consumable
        item_to_use = next((item for item in self.player.inventory if item.name == item_name), None)

        if not item_to_use:
            return f"You don't have a '{item_name}'."
        if not isinstance(item_to_use, Consumable):
            return f"You can't use the {item_to_use.name}."

        if item_to_use.effect == "heal":
            amount_healed = self.player.heal(item_to_use.amount)
            if amount_healed > 0:
                self.player.inventory.remove(item_to_use)
                return f"You use the {item_to_use.name} and recover {amount_healed} HP."
            return "Your health is already full."
        # Add other effects like mana restoration here
        return f"The {item_to_use.name} has no effect."

    def handle_equip_item(self, item_name):
        """Equips an item from the player's inventory."""
        from item import Weapon, Armor
        item_to_equip = next((item for item in self.player.inventory if item.name == item_name), None)
        if not item_to_equip:
            return f"You don't have a {item_name}."

        if isinstance(item_to_equip, Weapon):
            if self.player.weapon:
                self.player.inventory.append(self.player.weapon)
            self.player.weapon = item_to_equip
            self.player.inventory.remove(item_to_equip)
            return f"You equip the {item_to_equip.name}."
        elif isinstance(item_to_equip, Armor):
            if self.player.armor:
                self.player.inventory.append(self.player.armor)
            self.player.armor = item_to_equip
            self.player.inventory.remove(item_to_equip)
            return f"You equip the {item_to_equip.name}."
        else:
            return f"You can't equip a {item_to_equip.name}."

    def handle_open_chest(self):
        """Handles opening a treasure chest."""
        current_location = self.get_current_location()
        chest = current_location.get('chest')
        if not chest:
            return "There is no chest here."

        if chest.get('is_mimic'):
            from monster import Mimic
            mimic = Mimic()
            current_location['monsters'].append(mimic)
            del current_location['chest']
            return self.start_combat(mimic)

        if chest.get('trapped') and not chest.get('disarmed'):
            self.player.take_damage(25, bypass_defense=True)
            log = ["As you open the chest, a dart shoots out and hits you for 25 damage!"]
        else:
            log = ["You open the chest and find:"]

        loot = chest.get('loot', [])
        if not loot:
            log.append("- Nothing but dust.")
        else:
            for item in loot:
                if item.name == "Pouch of Gold":
                    self.player.money += item.value
                    log.append(f"- {item.value} gold")
                else:
                    self.player.inventory.append(item)
                    log.append(f"- A {item.name}")
        
        del current_location['chest']
        return "\n".join(log)

    def start_combat(self, monster):
        """Initiates combat with a target monster."""
        if not monster.is_alive():
            return f"The {monster.name} is already defeated."
        self.in_combat = True
        self.combat_target = monster
        return f"You engage the {monster.name}!"

    def handle_combat_turn(self, player_action):
        """Processes a single turn of combat."""
        if not self.in_combat or not self.combat_target:
            return "You are not in combat."

        log = []

        # --- Player Action ---
        player_damage_dealt = 0
        if player_action == 'a':
            # Player attacks do 10% more damage
            player_damage_dealt = int(self.player.attack_power * 1.1)
            log.append(f"You attack the {self.combat_target.name}!")
        elif player_action == 'd':
            log.append("You brace yourself for an attack.")
        elif player_action == 'p':
            log.append("You take a ready stance, preparing to parry.")
            self.player.add_skill_xp("Attack", 2)

        # --- Enemy AI Decision ---
        monster_action, _ = enemy_decision(self.combat_target.health, self.combat_target.max_health, player_action)

        # --- Resolve Player Damage ---
        if player_damage_dealt > 0:
            if monster_action == 'defend':
                blocked = min(player_damage_dealt, self.combat_target.defense)
                dealt = player_damage_dealt - blocked
                log.append(f"{self.combat_target.name} defends, blocking {blocked} damage!")
            elif monster_action == 'parry':
                blocked = int(player_damage_dealt * 0.5)
                dealt = player_damage_dealt - blocked
                log.append(f"{self.combat_target.name} parries, blocking {blocked} damage!")
            else: # Attack
                dealt = max(1, player_damage_dealt - self.combat_target.defense)
            
            if dealt > 0:
                self.combat_target.take_damage(dealt)
                self.player.add_skill_xp("Attack", dealt)
                log.append(f"Your attack deals {dealt} damage.")

        if not self.combat_target.is_alive():
            self.in_combat = False
            log.append(f"\nYou have defeated the {self.combat_target.name}!")
            # Rebalanced XP distribution
            xp_reward = self.combat_target.xp_yield
            self.player.add_skill_xp("Attack", xp_reward // 2)
            self.player.add_skill_xp("Defense", xp_reward // 2)
            # Handle loot, victory, etc. here
            return "\n".join(log)

        # --- Resolve Enemy Action ---
        if monster_action == 'attack':
            # Enemies do 10% less damage
            enemy_damage = int(self.combat_target.attack_power * 0.9)
            log.append(f"The {self.combat_target.name} attacks for {enemy_damage} potential damage!")
            if player_action == 'd':
                blocked = min(enemy_damage, self.player.defense)
                taken = enemy_damage - blocked
                self.player.health -= taken
                self.player.add_skill_xp("Defense", blocked)
                log.append(f"You defend, blocking {blocked} and taking {taken} damage.")
            elif player_action == 'p':
                block_perc = 0.4 + (self.player.skills["Agility"].level * 0.01)
                blocked = int(enemy_damage * block_perc)
                taken = enemy_damage - blocked
                self.player.health -= taken
                self.player.add_skill_xp("Defense", blocked)
                log.append(f"You parry, blocking {blocked} and taking {taken} damage.")
                if random.random() < 0.25:
                    counter_dmg = int(self.player.attack_power * 0.5)
                    self.combat_target.take_damage(counter_dmg)
                    self.player.add_skill_xp("Attack", counter_dmg)
                    log.append(f"You counter-attack for {counter_dmg} damage!")
            else:
                mitigated = min(enemy_damage, self.player.defense)
                taken = enemy_damage - mitigated
                self.player.health -= taken
                self.player.add_skill_xp("Defense", mitigated)
                log.append(f"Your armor mitigates {mitigated}. You take {taken} damage.")
        elif monster_action == 'defend':
            log.append(f"{self.combat_target.name} takes a defensive stance.")
        elif monster_action == 'parry':
            log.append(f"{self.combat_target.name} readies itself to parry.")

        if not self.player.is_alive():
            self.in_combat = False
            log.append("You have been defeated. Game Over.")

        return "\n".join(log)

    def save_game(self):
        """Saves the current game state to a file."""
        save_data = {
            "player": self.player,
            "world": self.world,
            "game_state": self.game_state,
            "current_dungeon": self.current_dungeon
        }
        try:
            with open(self.save_filename, "wb") as save_file:
                pickle.dump(save_data, save_file)
            return "Game saved successfully!"
        except Exception as e:
            return f"Error saving game: {e}"
