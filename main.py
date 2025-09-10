import sys
import os
import random
import json
from player import Player
from item import Item, Weapon, Armor, Consumable, Spellbook, RecipeScroll, Key, pouch_of_gold
from world import world, default_recipes, smelting_recipes, word_combinations, cooking_recipes, herblore_recipes, dungeon_generator
from monster import Monster
from enemy_ai import enemy_decision
from npc import QuestGiver, Shopkeeper, Banker, Guard, ProceduralQuestGiver
from ui import print_bordered
from json_utils import GameEncoder, decode_game_object
from event_manager import event_manager
import viewport_generator
from quest_hooks import register_quest_listeners
import command_handler as cmd

SAVE_FILENAME = "savegame.json"

game_state = {
    "time_of_day": "Day",
    "turn_count": 0,
    "day_length": 20,
    "night_length": 15
}
faction_events = {
    "bandit_raid": {
        "is_active": False, "location_key": None, "duration": 0, "original_npcs": []
    }
}
current_dungeon = None

def respawn_monsters(world_state, current_game_state):
    """Clears and repopulates monsters in all locations based on the time of day."""
    from world import monster_mapping # Import here to avoid circular dependency issues

    # Respawn for grid locations
    for row in world_state["grid"]:
        for location_data in row:
            # Clear existing monsters
            location_data["monsters"] = []
            
            # Combine regular and rare enemies for spawning
            monster_names_to_spawn = list(location_data.get("enemies", []))
            monster_names_to_spawn.extend(location_data.get("rare_creatures", []))

            # Add nocturnal enemies if it's night
            if current_game_state['time_of_day'] == "Night":
                monster_names_to_spawn.extend(location_data.get("night_enemies", []))

            for name in monster_names_to_spawn:
                if name in monster_mapping:
                    location_data["monsters"].append(monster_mapping[name]())
    # Note: This could be expanded to handle monsters in special locations too

def update_npc_availability(world_state, current_game_state):
    """Updates NPC availability based on the time of day."""
    is_day = current_game_state['time_of_day'] == "Day"
    for row in world_state["grid"]:
        for location_data in row:
            for npc in location_data.get("npcs", []):
                if isinstance(npc, Shopkeeper):
                    npc.is_available = is_day

def advance_time(turns=1):
    """Advances the game time and handles the day/night cycle."""
    global game_state
    game_state["turn_count"] += turns
    
    total_cycle_length = game_state["day_length"] + game_state["night_length"]
    current_cycle_turn = game_state["turn_count"] % total_cycle_length
    
    new_time_of_day = "Day" if 0 <= current_cycle_turn < game_state["day_length"] else "Night"
    
    if new_time_of_day != game_state["time_of_day"]:
        game_state["time_of_day"] = new_time_of_day
        if new_time_of_day == "Night":
            print("\nThe sun sets, and darkness falls upon Thalren Vale.")
        else:
            print("\nThe sun rises, casting long shadows across the land.")
        respawn_monsters(world, game_state)
        update_npc_availability(world, game_state)
        process_npc_schedules(world, game_state)
    
    process_faction_events(world, faction_events)

def _get_location_data_by_key(world_state, location_key):
    """Helper to get location data from either the grid or special locations."""
    if isinstance(location_key, tuple):
        row, col = location_key
        if 0 <= row < len(world_state["grid"]) and 0 <= col < len(world_state["grid"][row]):
            return world_state["grid"][row][col]
    elif isinstance(location_key, str):
        return world_state["special"].get(location_key)
    return None

def process_npc_schedules(world_state, current_game_state):
    """Moves NPCs based on their schedules."""
    current_cycle_turn = current_game_state["turn_count"] % (current_game_state["day_length"] + current_game_state["night_length"])
    
    # Create a list of all NPCs that have schedules to avoid iterating the whole world
    scheduled_npcs = [npc for row in world_state["grid"] for loc in row for npc in loc.get("npcs", []) if npc.schedule]
    for loc in world_state["special"].values():
        scheduled_npcs.extend([npc for npc in loc.get("npcs", []) if npc.schedule])

    for npc in scheduled_npcs:
        # Determine where the NPC should be right now
        target_location_key = None
        for time, location_key in reversed(npc.schedule):
            if current_cycle_turn >= time:
                target_location_key = location_key
                break
        
        # If a target location is found and the NPC is not there, move them.
        if target_location_key and npc.current_location_key != target_location_key:
            old_loc_data = _get_location_data_by_key(world_state, npc.current_location_key)
            new_loc_data = _get_location_data_by_key(world_state, target_location_key)

            if old_loc_data and new_loc_data:
                if npc in old_loc_data.get("npcs", []):
                    old_loc_data["npcs"].remove(npc)
                if "npcs" not in new_loc_data: new_loc_data["npcs"] = []
                new_loc_data["npcs"].append(npc)
                npc.current_location_key = target_location_key
                # print(f"[DEBUG] Moved {npc.name} to {new_loc_data['name']}.") # Optional debug message

def process_faction_events(world_state, faction_events_state):
    """Manages the lifecycle of procedural world events."""
    # --- Bandit Raid Event ---
    event = faction_events_state["bandit_raid"]
    if event["is_active"]:
        event["duration"] -= 1
        if event["duration"] <= 0:
            # End the raid
            raided_loc = _get_location_data_by_key(world_state, event["location_key"])
            if raided_loc:
                print(f"The bandits have been driven from {raided_loc['name']} and the villagers are returning.")
                # Remove bandits and restore original NPCs
                raided_loc["monsters"] = [m for m in raided_loc.get("monsters", []) if not isinstance(m, monster_mapping.get("bandit"))]
                raided_loc["npcs"] = event["original_npcs"]
            # Reset the event state
            event["is_active"] = False
            event["location_key"] = None
            event["original_npcs"] = []
    else:
        # Chance to trigger a new raid
        if random.random() < 0.02: # 2% chance per turn
            # Select a valid, non-town location to be raided
            possible_locations = []
            for r, row in enumerate(world_state["grid"]):
                for c, loc in enumerate(row):
                    if loc.get("type") in ["village", "camp", "plains"] and loc.get("npcs"):
                        possible_locations.append(((r, c), loc))
            
            if possible_locations:
                loc_key, target_loc = random.choice(possible_locations)
                print(f"\n[World Event] Word on the road is that bandits are raiding {target_loc['name']}!")
                
                # Activate the event
                event["is_active"] = True
                event["location_key"] = loc_key
                event["duration"] = random.randint(20, 40) # Raid lasts for 20-40 turns
                
                # Store original NPCs and replace them with bandits
                event["original_npcs"] = list(target_loc.get("npcs", []))
                target_loc["npcs"] = []
                from world import monster_mapping
                if "monsters" not in target_loc: target_loc["monsters"] = []
                target_loc["monsters"].extend([monster_mapping["bandit"]() for _ in range(random.randint(2, 4))])


def get_current_location(player, world_state, dungeon_state):
    """Gets the location data for the player's current position."""
    loc = player.location
    if isinstance(loc, tuple): # Player is on the grid
        row, col = loc
        if 0 <= row < len(world_state["grid"]) and 0 <= col < len(world_state["grid"][row]):
            return world_state["grid"][row][col]
    elif isinstance(loc, str): # Player is in a special location
        if dungeon_state and loc in dungeon_state:
            return dungeon_state[loc]
        return world_state["special"].get(loc)
    return None

def set_current_dungeon(dungeon_data):
    """Sets the current dungeon data."""
    global current_dungeon
    current_dungeon = dungeon_data
def print_location(player, world_state, dungeon_state, game_state_dict):
    """Prints a clear and concise summary of the player's location and available interactions."""
    location_data = get_current_location(player, world_state, dungeon_state)
    if not location_data:
        print("You are lost in an unfamiliar place.")
        # Attempt to move player back to a safe spot if they are out of bounds
        player.location = (12, 11) # Rivenshade
        return

    # --- Generate and Display ASCII Viewport ---
    sprites_to_render = []
    # Map game objects to sprite filenames
    if location_data.get("npcs"):
        sprites_to_render.extend(["npc.txt"] * len(location_data["npcs"]))
    if location_data.get("night_npcs") and game_state_dict['time_of_day'] == 'Night':
        sprites_to_render.extend(["npc.txt"] * len(location_data["night_npcs"]))
    
    living_monsters = [m for m in location_data.get("monsters", []) if m.is_alive()]
    if living_monsters:
        sprites_to_render.extend(["monster.txt"] * len(living_monsters))

    for node in location_data.get("nodes", []):
        if "tree" in node.name.lower():
            sprites_to_render.append("tree.txt")
        elif "vein" in node.name.lower() or "rock" in node.name.lower():
            sprites_to_render.append("rock.txt")
    
    # Get available exits to display on the viewport border
    available_exits = list(location_data.get("exits", {}).keys())
    # Also check for implicit grid-based exits
    if isinstance(player.location, tuple):
        row, col = player.location
        grid = world_state["grid"]
        # Check North
        if row > 0 and grid[row - 1][col]: available_exits.append("north")
        # Check South
        if row < len(grid) - 1 and grid[row + 1][col]: available_exits.append("south")
        # Check West
        if col > 0 and grid[row][col - 1]: available_exits.append("west")
        # Check East
        if col < len(grid[row]) - 1 and grid[row][col + 1]: available_exits.append("east")

    viewport_generator.display_viewport(viewport_generator.generate_viewport(sprites_to_render), exits=available_exits)

    # --- Handle Quest Ambushes ---
    for quest in player.active_quests:
        if quest.objective.get('type') == 'ambush':
            if player.location == quest.objective.get('location') and game_state_dict['time_of_day'] == 'Night':
                # Check if the ambush has already been triggered
                if not quest.progress: # progress = 0 means not triggered
                    print("\nAs you step into the clearing, the shadows themselves seem to writhe and coalesce!")
                    ambush_monsters = quest.objective.get('monsters', [])
                    from world import monster_mapping
                    for monster_name in ambush_monsters:
                        if monster_name in monster_mapping:
                            location_data.setdefault('monsters', []).append(monster_mapping[monster_name]())
                    quest.update_progress('ambush', 'trigger') # Mark ambush as triggered
                    # Immediately start combat with the first monster
                    if location_data['monsters']:
                        handle_combat(player, location_data['monsters'][0].name)

    title = f"{location_data['name']} ({game_state_dict['time_of_day']})"
    content = []

    description = location_data.get(f"description_{game_state_dict['time_of_day'].lower()}", location_data.get("description_day"))
    content.append(description)

    # List exits
    exits = location_data.get("exits", {})
    if exits:
        content.append("")
        content.append(f"Exits: {', '.join(exits.keys())} (`go <exit>`)")

    # List NPCs
    if game_state_dict['time_of_day'] == "Night":
        npcs_in_room = location_data.get("npcs", []) + location_data.get("night_npcs", [])
    else:
        npcs_in_room = location_data.get("npcs", [])

    if npcs_in_room:
        content.append("")
        content.append("People:")
        for npc in npcs_in_room:
            if npc.is_available:
                content.append(f"- {npc.name} (`talk to {npc.name.lower()}`)")
            else:
                content.append(f"- {npc.name} (Unavailable)")

    # List items on the ground
    items_in_room = location_data.get("items", [])
    if items_in_room:
        content.append("")
        content.append("Items:")
        for item in items_in_room:
            content.append(f"- A {item.name} (`take {item.name.lower()}`)")

    # List monsters
    living_monsters = [m for m in location_data.get("monsters", []) if m.is_alive()]
    if living_monsters:
        content.append("")
        content.append("Danger!")
        for monster in living_monsters:
            content.append(f"- {monster.name} ({monster.health}/{monster.max_health} HP) (`attack {monster.name.lower()}`)")

    # List resource nodes
    nodes_in_room = location_data.get("nodes", [])
    if nodes_in_room:
        content.append("")
        content.append("Resources:")
        for node in nodes_in_room:
            target_keyword = node.name.split()[0].lower()
            content.append(f"- {node.name} (`{node.verb} {target_keyword}`)")
    
    features_in_room = location_data.get("features", [])
    if features_in_room:
        content.append("")
        for feature in features_in_room:
            content.append(f"You see a {feature}. (`enter {feature}`)")
    
    if location_data.get('chest'):
        content.append("")
        content.append("You see a treasure chest. (`open chest`, `disarm chest`)")
    
    print_bordered(title, content)

def get_target(parts):
    """Helper function to get the target of a command (e.g., 'look at sword')."""
    if len(parts) > 1:
        # Handle multi-word targets like "look at short sword"
        if parts[1] == "at" and len(parts) > 2:
            return " ".join(parts[2:])
        return " ".join(parts[1:])
    return None

def handle_combat(player, monster_name_input):
    """Manages the turn-based combat loop."""
    current_location = get_current_location(player, world, current_dungeon)
    monsters_in_room = current_location.get("monsters", [])
    target_monster = next((m for m in monsters_in_room if monster_name_input.lower() in m.name.lower()), None)

    if not target_monster:
        print(f"There is no {monster_name_input} here to attack.")
        return

    if not target_monster.is_alive():
        print(f"The {target_monster.name} is already defeated.")
        return
    print(f"\n--- You engage the {target_monster.name}! ---")

    while player.is_alive() and target_monster.is_alive():
        player.clear_affected_skills()
        # Player's Turn
        print("\n" + "="*15 + " Your Turn " + "="*15)
        player_is_stunned = player.process_turn_effects()
        if not player.is_alive():
            break

        player_action = None

        if player_is_stunned:
            pass # Skip the player's action
        else:
            print("Choose your action: (A)ttack, (D)efend, (P)arry, (C)ast, (F)lee, (S)tatus")
            action = input("> ").lower()
            player_action = action

            if action == 'a':
                # The monster's action for the turn will be decided after this,
                # so we calculate potential damage now and apply it later.
                print(f"You attack the {target_monster.name}!")
            elif action == 'd':
                print("You brace yourself for an attack, focusing on defense.")
            elif action == 'p':
                print("You take a ready stance, preparing to parry the next blow.")
                player.add_skill_xp("Attack", 2) # Minor XP for attempting a parry
            elif action == 'c':
                # Show available spells
                if not player.abilities:
                    print("You don't know any spells!")
                    continue
                print("Spells:")
                for i, ability in enumerate(player.abilities):
                    print(f"  {i+1}. {ability.name} (Cost: {ability.mana_cost} MP) - {ability.description}")
                spell_choice = input("Cast which spell? (number) > ")
                try:
                    spell_index = int(spell_choice) - 1
                    chosen_ability = player.abilities[spell_index]
                    if player.mana >= chosen_ability.mana_cost:
                        player.mana -= chosen_ability.mana_cost
                        print(f"You cast {chosen_ability.name}!")
                        if chosen_ability.effect:
                            player.add_skill_xp("Magic", 5) # Grant magic XP for casting
                            if chosen_ability.effect['type'] == 'damage':
                                target_monster.take_damage(chosen_ability.effect['amount'])
                            elif chosen_ability.effect['type'] == 'heal':
                                player.heal(chosen_ability.effect['amount'])
                        if chosen_ability.status_effect:
                            target_monster.add_status_effect(chosen_ability.status_effect)
                    else:
                        print("Not enough mana!")
                except (ValueError, IndexError):
                    print("Invalid spell choice.")
            elif action == 's':
                player.print_combat_status(target_monster)
                continue # This action does not use up a turn
            elif action == 'f':
                # Flee chance is based on player level vs monster attack power
                level_difference = player.skills["Agility"].level - (target_monster.attack_power / 4) # A higher level or lower monster attack helps
                flee_chance = 0.5 + (level_difference * 0.05) # Base 50%, with 5% change per point of difference
                # Clamp the chance between 10% and 90% to keep it from being impossible or a sure thing
                flee_chance = max(0.1, min(flee_chance, 0.9))
                print(f"(Your chance to flee is {int(flee_chance * 100)}%)")
                if random.random() < flee_chance:
                    print("You successfully escape from the battle!")
                    break # Exit the combat loop
                else:
                    print("You failed to escape!")
            else:
                print("Invalid action. You hesitate and do nothing.")

        if not target_monster.is_alive():
            event_manager.dispatch('on_kill', player=player, monster=target_monster)
            print(f"\nYou have defeated the {target_monster.name}!")            
            # --- Special Post-Combat Quest Logic for "Ashes on the Road" ---
            quest = next((q for q in player.active_quests if q.name == "Ashes on the Road"), None)
            if quest and quest.check_completion(player):
                print(f"\nThe {target_monster.name} slumps to the ground, defeated but still breathing. You have a moment to act.")
                for i, choice in enumerate(quest.reward_choice):
                    print(f"  {i+1}. {choice['description']}")
                
                while True:
                    try:
                        choice_input = input("Choose your action (number): > ")
                        if not choice_input: continue
                        choice_index = int(choice_input) - 1
                        if 0 <= choice_index < len(quest.reward_choice):
                            chosen_option = quest.reward_choice[choice_index]
                            quest.complete(player, chosen_reward_option=chosen_option)
                            # Remove the defeated monster from the room
                            current_location.get("monsters", []).remove(target_monster)
                            return # Exit combat function entirely
                        else:
                            print("Invalid choice.")
                    except (ValueError, IndexError):
                        print("Please enter a number.")
                return # Should be unreachable, but good practice

            xp_reward = target_monster.xp_yield
            player.add_skill_xp("Attack", xp_reward // 2)
            player.add_skill_xp("Defense", xp_reward // 2)
            
            # --- Handle Loot Drop ---
            dropped_loot = target_monster.drop_loot()
            if dropped_loot:
                current_location.get("items", []).extend(dropped_loot)
                print(f"The {target_monster.name} dropped:")
                for item in dropped_loot:
                    print(f"- A {item.name}")
            # ----------------------

            # --- Victory Condition ---
            if target_monster.name == "Thalraxos":
                print("\n" + "="*20)
                print("With a final, earth-shattering groan, Thalraxos crumbles to dust.")
                print("The shadow over the mountain has been lifted. You are victorious!")
                print(f"Congratulations, {player.name}! You have saved Thalren Vale.")
                sys.exit()
            # -------------------------
            break

        # Monster's Turn
        print("\n" + "="*14 + " Enemy Turn " + "="*14)
        monster_is_stunned = target_monster.process_turn_effects()
        if not target_monster.is_alive():
            break

        # --- Enemy AI Decision ---
        monster_action, final_weights = enemy_decision(target_monster.health, target_monster.max_health, player_action)
        print(f"({target_monster.name} considers its options: {final_weights})")

        # --- Player Damage Phase (if player attacked) ---
        if player_action == 'a':
            # Player attacks do 10% more damage
            player_damage = int(player.attack_power * 1.1)
            if monster_action == 'defend':
                damage_blocked = min(player_damage, target_monster.defense)
                damage_dealt = player_damage - damage_blocked
                print(f"{target_monster.name} defends, blocking {damage_blocked} damage!")
            elif monster_action == 'parry':
                # For simplicity, enemy parry blocks 50%
                damage_blocked = int(player_damage * 0.5)
                damage_dealt = player_damage - damage_blocked
                print(f"{target_monster.name} parries, blocking {damage_blocked} damage!")
            else: # Monster chose 'attack'
                damage_dealt = max(1, player_damage - target_monster.defense)
                print(f"Your attack hits!")
            
            if damage_dealt > 0:
                target_monster.take_damage(damage_dealt)
                player.add_skill_xp("Attack", damage_dealt)

        if not target_monster.is_alive():
            continue # Skip monster's turn if it was defeated by player's attack

        if not monster_is_stunned:
            # --- Monster AI ---
            can_use_ability = any(target_monster.mana >= ab.mana_cost for ab in target_monster.abilities)
            # 50% chance to use an ability if possible
            if can_use_ability and random.random() < 0.5:
                affordable_abilities = [ab for ab in target_monster.abilities if target_monster.mana >= ab.mana_cost]
                chosen_ability = random.choice(affordable_abilities)
                target_monster.mana -= chosen_ability.mana_cost
                print(f"The {target_monster.name} uses {chosen_ability.name}!")
                if chosen_ability.effect:
                    if chosen_ability.effect['type'] == 'damage':
                        # Special attacks are more direct, less mitigated by standard defense
                        player.take_damage(chosen_ability.effect['amount'])
                    elif chosen_ability.effect['type'] == 'heal':
                        target_monster.heal(chosen_ability.effect['amount'])
                if chosen_ability.status_effect:
                    player.add_status_effect(chosen_ability.status_effect)
            elif monster_action == 'attack': # Basic Attack
                # Enemies do 10% less damage
                enemy_damage = int(target_monster.attack_power * 0.9)
                print(f"The {target_monster.name} attacks you for {enemy_damage} potential damage!")

                if player_action == 'd': # Defend
                    damage_blocked = min(enemy_damage, player.defense)
                    damage_taken = enemy_damage - damage_blocked
                    player.health -= damage_taken
                    player.add_skill_xp("Defense", damage_blocked)
                    print(f"You defend, blocking {damage_blocked} damage and taking {damage_taken} damage.")
                elif player_action == 'p': # Parry
                    block_percentage = 0.4 + (player.skills["Agility"].level * 0.01)
                    block_percentage = min(block_percentage, 0.8) # Cap parry at 80%
                    damage_blocked = int(enemy_damage * block_percentage)
                    damage_taken = enemy_damage - damage_blocked
                    player.health -= damage_taken
                    player.add_skill_xp("Defense", damage_blocked)
                    print(f"You parry, blocking {damage_blocked} damage and taking {damage_taken} damage.")
                    # Counter-attack chance
                    if random.random() < 0.25: # 25% chance to counter
                        counter_damage = int(player.attack_power * 0.5)
                        print(f"You seize an opening and counter-attack for {counter_damage} damage!")
                        target_monster.take_damage(counter_damage)
                        player.add_skill_xp("Attack", counter_damage)
                else: # Default (Attack, Cast, Flee fail, etc.)
                    damage_mitigated = min(enemy_damage, player.defense)
                    damage_taken = enemy_damage - damage_mitigated
                    player.health -= damage_taken
                    player.add_skill_xp("Defense", damage_mitigated)
                    print(f"Your armor mitigates {damage_mitigated} damage. You take {damage_taken} damage.")
            elif monster_action == 'defend':
                print(f"{target_monster.name} takes a defensive stance, preparing for your next move.")
            elif monster_action == 'parry':
                print(f"{target_monster.name} readies itself to parry an attack.")

        if not player.is_alive():
            print("\nYou have been defeated. Game Over.")
            sys.exit()
        # Print status at the end of the round
        player.print_status(affected_skills=player.skills_affected_this_turn)
        print(f"Enemy HP: {target_monster.health}/{target_monster.max_health}")
        print("-" * 25)

def save_game(player, world_state):
    """Saves the current game state to a JSON file."""
    save_data = {
        "player": player,
        "world": world_state,
        "game_state": game_state,
        "current_dungeon": current_dungeon,
        "faction_events": faction_events
    }
    try:
        with open(SAVE_FILENAME, "w") as save_file:
            json.dump(save_data, save_file, cls=GameEncoder, indent=4)
        print("\nGame saved successfully!")
    except Exception as e:
        print(f"\nError saving game: {e}")

def load_game():
    """Loads the game state from a file."""
    if not os.path.exists(SAVE_FILENAME):
        return None, None, None, None, None

    try:
        with open(SAVE_FILENAME, "r") as save_file:
            save_data = json.load(save_file, object_hook=decode_game_object)
        
        player = save_data["player"]
        loaded_world = save_data["world"]
        loaded_game_state = save_data["game_state"]
        loaded_dungeon = save_data.get("current_dungeon", None)
        loaded_faction_events = save_data.get("faction_events", {
            "bandit_raid": {
                "is_active": False, "location_key": None, "duration": 0, "original_npcs": []
            }
        })

        # --- Post-load reconstruction ---
        # The JSON load gives us names/placeholders. We need to replace them
        # with the actual, full objects from the master world data.
        
        # Create a master lookup for all items and quests
        from world import factions, word_combinations, default_recipes, smelting_recipes, cooking_recipes, herblore_recipes
        import world as world_module
        import item as item_module
        from quest import Quest
        # Create a more robust item lookup to avoid including non-item objects
        world_items = {i.name: i for i in world_module.__dict__.values() if isinstance(i, Item) and not isinstance(i, type)}
        item_items = {i.name: i for i in item_module.__dict__.values() if isinstance(i, Item) and not isinstance(i, type)}
        all_items = {**world_items, **item_items}
        all_quests = {q.name: q for q in world_module.__dict__.values() if isinstance(q, Quest) and not isinstance(q, type)}

        # Re-link player's inventory and quests
        player.inventory = [all_items.get(item_name, Item(item_name, "Lost Item")) for item_name in player.inventory]
        player.active_quests = [all_quests.get(quest_name) for quest_name in player.active_quests if quest_name in all_quests]
        player.completed_quests = [all_quests.get(quest_name) for quest_name in player.completed_quests if quest_name in all_quests]
        
        if player.weapon:
            player.weapon = all_items.get(player.weapon)
        if player.armor:
            player.armor = all_items.get(player.armor)

        # Re-link world state (NPCs, items on ground, etc.)
        for row in loaded_world["grid"]:
            for loc_data in row:
                if "items" in loc_data:
                    loc_data["items"] = [all_items.get(item_name) for item_name in loc_data["items"] if item_name in all_items]
                if "npcs" in loc_data:
                    for npc in loc_data["npcs"]:
                        if hasattr(npc, 'quests'):
                            # This assumes quests are single objects, not lists for now.
                            # A more complex system would handle lists of quests.
                            if isinstance(npc.quests, list) and npc.quests:
                                npc.quests = [all_quests.get(q_name) for q_name in npc.quests if q_name in all_quests]
        
        respawn_monsters(loaded_world, loaded_game_state)
        update_npc_availability(loaded_world, loaded_game_state)

        print("\nGame loaded successfully!")
        return player, loaded_world, loaded_game_state, loaded_dungeon, loaded_faction_events
    except Exception as e:
        print(f"\nError loading game: {e}")
        return None, None, None, None, None

game_context = {
    'world': world,
    'game_state': game_state,
    'current_dungeon': current_dungeon,
    'get_current_location': get_current_location,
    'set_dungeon': set_current_dungeon,
    'dungeon_generator': dungeon_generator,
    'advance_time': advance_time,
    'print_location': lambda p: print_location(p, world, current_dungeon, game_state),
    'handle_combat': handle_combat,
    'event_manager': event_manager,
}

# Add a reference to the context dictionary into itself to solve inter-dependencies
# within the command_handler module (e.g. handle_open_chest calling handle_combat)
game_context['context'] = game_context


def parse_command(command, player):
    """Parses the player's command."""
    parts = command.lower().split()
    if not parts:
        print("Say something!")
        return

    # Check if player is in jail
    current_location = get_current_location(player, world, current_dungeon)
    if player.jail_time_remaining > 0 and current_location and current_location.get("name") == "Rivenshade Jail":
        allowed_verbs = ["wait", "look", "status", "stats", "inventory", "i", "help", "quit", "bribe", "lockpick", "talk"]
        verb = parts[0].lower()
        if verb not in allowed_verbs:
            print("You can't do that in jail. You must serve your time. (Type 'wait', 'bribe', or 'lockpick').")
            return

    verb = parts[0]

    if verb == "quit":
        print(f"Goodbye, {player.name}!")
        sys.exit()
    elif verb == "help":
        cmd.handle_help()
    elif verb == "look":
        target = get_target(parts)
        if target and target != "at":
            cmd.handle_look_at(player, target, game_context)
        else:
            print_location(player, world, current_dungeon, game_state)
    elif verb in ["get", "take"]:
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Take what?")
        else:
            cmd.handle_take_item(player, item_name, game_context)
    elif verb == "drop":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Drop what?")
        else:
            cmd.handle_drop_item(player, item_name, game_context)
    elif verb in ["go", "move"]:
        if len(parts) > 1:
            direction = parts[1]
            cmd.handle_movement(player, direction, game_context)
        else:
            print("Go where?")
    elif verb in ["north", "south", "east", "west"]:
        cmd.handle_movement(player, verb, game_context)
    elif verb in ["inventory", "i"]:
        cmd.handle_inventory(player)
    elif verb in ["status", "stats"]:
        player.print_status()
    elif verb == "attack":
        target_name = " ".join(parts[1:])
        if not target_name:
            print("Attack what?")
        else:
            handle_combat(player, target_name)
    elif verb == "equip":
        item_name = " ".join(parts[1:])
        if not item_name: print("Equip what?")
        else: cmd.handle_equip_item(player, item_name)
    elif verb == "unequip":
        slot = parts[1] if len(parts) > 1 else ""
        if not slot: print("Unequip what? ('weapon' or 'armor')")
        else: cmd.handle_unequip_item(player, slot)
    elif verb == "save":
        save_game(player, world)
    elif verb == "load":
        print("Loading the game will overwrite your current progress.")
        print("This feature is best used from the main menu.")
    elif verb == "talk":
        if len(parts) > 1 and parts[1] == "to":
            npc_name = " ".join(parts[2:])
            cmd.handle_talk_to(player, npc_name, game_context)
        else:
            print("Talk to whom?")
    elif verb == "insult":
        npc_name = " ".join(parts[1:])
        if not npc_name:
            print("Insult whom?")
        else:
            cmd.handle_insult(player, npc_name, game_context)
    elif verb == "accept":
        cmd.handle_accept_quest(player)
    elif verb == "decline":
        print("You decide not to take on the task for now.")
    elif verb in ["quests", "journal"]:
        cmd.handle_quests_log(player)
    elif verb == "sell":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Sell what?")
        else:
            current_location = get_current_location(player, world, current_dungeon)
            shopkeeper = next((npc for npc in current_location.get("npcs", []) if isinstance(npc, Shopkeeper)), None)
            if shopkeeper:
                shopkeeper.sell_item(player, item_name, game_state)
            else:
                print("There is no one here to sell to.")
    elif verb == "factions":
        cmd.handle_factions(player)
    elif verb == "use":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Use what?")
        else:
            cmd.handle_use_item(player, item_name)
    elif verb == "bank":
        cmd.handle_bank_view(player, game_context)
    elif verb == "deposit":
        args = parts[1:]
        cmd.handle_deposit(player, args, game_context)
    elif verb == "withdraw":
        args = parts[1:]
        cmd.handle_withdraw(player, args, game_context)
    elif verb == "wait":
        cmd.handle_wait(player, game_context)
    elif verb == "craft":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Craft what? (e.g., 'craft goblin leather gloves')")
        else:
            cmd.handle_craft_item(player, item_name, game_context)
    elif verb == "pickpocket":
        npc_name = " ".join(parts[1:])
        if not npc_name:
            print("Pickpocket whom?")
        else:
            cmd.handle_pickpocket(player, npc_name, game_context)
    elif verb == "lockpick":
        cmd.handle_lockpick(player, game_context)
    elif verb == "bribe":
        cmd.handle_bribe(player, game_context)
    elif verb == "smelt":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Smelt what? (e.g., 'smelt copper bar')")
        else:
            cmd.handle_smelt_item(player, item_name, game_context)
    elif verb == "mine":
        node_name = " ".join(parts[1:])
        if not node_name:
            print("Mine what?")
        else:
            cmd.handle_gather_node(player, "mine", node_name, game_context)
    elif verb == "cook":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Cook what? (e.g., 'cook trout')")
        else:
            cmd.handle_cook_item(player, item_name, game_context)
    elif verb == "open":
        if " ".join(parts[1:]) == "chest":
            cmd.handle_open_chest(player, game_context)
        else:
            print("Open what?")
    elif verb == "disarm":
        if " ".join(parts[1:]) == "chest":
            cmd.handle_disarm_chest(player, game_context)
    elif verb == "brew":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Brew what? (e.g., 'brew greater healing potion')")
        else:
            cmd.handle_brew_potion(player, item_name, game_context)
    elif verb == "chop":
        node_name = " ".join(parts[1:])
        if not node_name:
            print("Chop what?")
        else:
            cmd.handle_gather_node(player, "chop", node_name, game_context)
    elif verb == "fish":
        node_name = " ".join(parts[1:])
        if not node_name:
            print("Fish what? (e.g., 'fish spot')")
        else:
            cmd.handle_gather_node(player, "fish", node_name, game_context)
    elif verb == "bind":
        if " ".join(parts[1:]) == "altar": # Special command for the quest
            cmd.handle_cleanse_shrine(player, game_context)
            return
        # Split by comma to handle multi-word item names
        words_to_bind_str = " ".join(parts[1:])
        words = [word.strip().title() for word in words_to_bind_str.split(',')]
        cmd.handle_bind_words(player, words, game_context)
    elif verb == "recipes":
        cmd.handle_recipes(player)
    elif verb == "rest":
        cmd.handle_rest(player, game_context)
    elif verb in ["map", "m"]:
        cmd.handle_map(player, game_context)
    elif verb == "enter":
        target = " ".join(parts[1:])
        if not target:
            print("Enter what?")
        else:
            cmd.handle_enter(player, target, game_context)
    elif verb == "cleanse":
        cmd.handle_cleanse_shrine(player, game_context)
    else:
        print("I don't understand that command.")

def game_loop(player):
    """The main game loop."""
    print_location(player, world, current_dungeon, game_state)
    while True:
        try:
            command = input("> ")
            parse_command(command, player)
        except (EOFError, KeyboardInterrupt):
            print(f"\nGoodbye, {player.name}!")
            sys.exit()

def start_game():
    """Initializes and starts the game."""
    global world, game_state, current_dungeon, faction_events # Declare that we might modify global variables

    print("Welcome to Ashania!")
    if os.path.exists(SAVE_FILENAME):
        print("A saved game was found. (L)oad or (N)ew Game?")
        choice = ""
        while choice not in ['l', 'n']:
            choice = input("> ").lower()
        
        if choice == 'l':
            player, loaded_world, loaded_game_state, loaded_dungeon, loaded_faction_events = load_game()
            if player and loaded_world and loaded_game_state and loaded_faction_events:
                world = loaded_world # Overwrite the template world with the loaded one
                game_context['world'] = world # IMPORTANT: Update the context as well
                game_context['current_dungeon'] = loaded_dungeon
                game_state = loaded_game_state
                current_dungeon = loaded_dungeon
                faction_events = loaded_faction_events
                game_loop(player)
                return # Exit after the game loop finishes

    # If no save file or user chose New Game
    print("\nStarting a new adventure...")
    print("What is your name, adventurer?")
    
    player_name = ""
    while not player_name:
        try:
            player_name = input("> ")
            if not player_name:
                print("You must enter a name.")
        except (EOFError, KeyboardInterrupt):
            print("\nQuitting game.")
            sys.exit()
    
    from world import factions # Import here to use for new player
    from faction import Faction # Import here to create new faction instances

    # Initialize monsters for the first time
    respawn_monsters(world, game_state)
    update_npc_availability(world, game_state)

    player = Player(name=player_name, location=(12, 11)) # Start in Rivenshade
    # Initialize player's factions from the world template
    for key, faction_template in factions.items():
        player.factions[key] = Faction(faction_template.name, faction_template.description)
    # Give the player their default known recipes
    player.known_recipes.extend(default_recipes)
    print(f"\nWelcome, {player.name}! Your journey begins now.")
    print("Commands: look, go, take, drop, craft, recipes, bind, brew, mine, chop, fish, cook, smelt, pickpocket, bribe, lockpick, map, enter, open, disarm, use, attack, inventory, status, quests, talk to, insult, bank, deposit, withdraw, wait, rest, equip, unequip, save, quit, help.")
    game_loop(player)

def register_core_event_listeners():
    """Registers all game event listeners."""
    # Register quest-specific listeners first
    register_quest_listeners()

    def on_kill_listener(player, monster):
        """Updates quests and skills when a monster is killed."""
        for quest in player.active_quests:
            quest.update_progress('kill', monster.name)
            quest.update_progress('activity', 'hunt')
            # Check if this was a hunting task and grant on-kill XP
            if quest.reward and 'xp' in quest.reward and 'Hunting' in quest.reward['xp']:
                hunting_xp_per_kill = int(monster.xp_yield * 0.5)
                player.add_skill_xp("Hunting", hunting_xp_per_kill)
            elif quest.reward_choice:
                if any('Hunting' in choice['reward'].get('xp', {}) for choice in quest.reward_choice):
                    hunting_xp_per_kill = int(monster.xp_yield * 0.5)
                    player.add_skill_xp("Hunting", hunting_xp_per_kill)

    def on_item_pickup_listener(player, item):
        """Handles special quest triggers when an item is picked up."""
        if item.name == "Suspicious Ledger":
            from world import whispers_beneath_the_ledger_quest
            completed_quest_names = [q.name for q in player.completed_quests]
            if all(p in completed_quest_names for p in whispers_beneath_the_ledger_quest.prerequisites) and \
               whispers_beneath_the_ledger_quest not in player.active_quests and \
               not any(q.name == whispers_beneath_the_ledger_quest.name for q in player.completed_quests):
                player.active_quests.append(whispers_beneath_the_ledger_quest)
                print("\nAs you pick up the ledger, you notice some strange entries. This seems important.")
                print(f"Quest Started: {whispers_beneath_the_ledger_quest.name}")

    event_manager.register_listener('on_kill', on_kill_listener)
    event_manager.register_listener('on_item_pickup', on_item_pickup_listener)

if __name__ == "__main__":
    register_core_event_listeners()
    start_game()