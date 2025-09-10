import sys
import os
import random
import pickle
from player import Player
from item import Item, Weapon, Armor, Consumable, Spellbook, RecipeScroll, Key, pouch_of_gold
from world import world, default_recipes, smelting_recipes, word_combinations, cooking_recipes, herblore_recipes, dungeon_generator
from monster import Monster
from enemy_ai import enemy_decision
from npc import QuestGiver, Shopkeeper, Banker, Guard, ProceduralQuestGiver
from ui import print_bordered


SAVE_FILENAME = "savegame.pkl"

game_state = {
    "time_of_day": "Day",
    "turn_count": 0,
    "day_length": 20,
    "night_length": 15
}
current_dungeon = None

def respawn_monsters():
    """Clears and repopulates monsters in all locations based on the time of day."""
    from world import monster_mapping # Import here to avoid circular dependency issues

    # Respawn for grid locations
    for row in world["grid"]:
        for location_data in row:
            # Clear existing monsters
            location_data["monsters"] = []
            
            # Combine regular and rare enemies for spawning
            monster_names_to_spawn = list(location_data.get("enemies", []))
            monster_names_to_spawn.extend(location_data.get("rare_creatures", []))

            # Add nocturnal enemies if it's night
            if game_state['time_of_day'] == "Night":
                monster_names_to_spawn.extend(location_data.get("night_enemies", []))

            for name in monster_names_to_spawn:
                if name in monster_mapping:
                    location_data["monsters"].append(monster_mapping[name]())
    # Note: This could be expanded to handle monsters in special locations too

def update_npc_availability():
    """Updates NPC availability based on the time of day."""
    is_day = game_state['time_of_day'] == "Day"
    for row in world["grid"]:
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
        respawn_monsters()
        update_npc_availability()
        process_npc_schedules()

def _get_location_data_by_key(location_key):
    """Helper to get location data from either the grid or special locations."""
    if isinstance(location_key, tuple):
        row, col = location_key
        if 0 <= row < len(world["grid"]) and 0 <= col < len(world["grid"][row]):
            return world["grid"][row][col]
    elif isinstance(location_key, str):
        return world["special"].get(location_key)
    return None

def process_npc_schedules():
    """Moves NPCs based on their schedules."""
    current_cycle_turn = game_state["turn_count"] % (game_state["day_length"] + game_state["night_length"])
    
    # Create a list of all NPCs that have schedules to avoid iterating the whole world
    scheduled_npcs = [npc for row in world["grid"] for loc in row for npc in loc.get("npcs", []) if npc.schedule]
    for loc in world["special"].values():
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
            old_loc_data = _get_location_data_by_key(npc.current_location_key)
            new_loc_data = _get_location_data_by_key(target_location_key)

            if old_loc_data and new_loc_data:
                if npc in old_loc_data.get("npcs", []):
                    old_loc_data["npcs"].remove(npc)
                if "npcs" not in new_loc_data: new_loc_data["npcs"] = []
                new_loc_data["npcs"].append(npc)
                npc.current_location_key = target_location_key
                # print(f"[DEBUG] Moved {npc.name} to {new_loc_data['name']}.") # Optional debug message

def get_current_location(player):
    """Gets the location data for the player's current position."""
    loc = player.location
    if isinstance(loc, tuple): # Player is on the grid
        row, col = loc
        if 0 <= row < len(world["grid"]) and 0 <= col < len(world["grid"][row]):
            return world["grid"][row][col]
    elif isinstance(loc, str): # Player is in a special location
        if current_dungeon and loc in current_dungeon:
            return current_dungeon[loc]
        return world["special"].get(loc)
    return None

def print_location(player):
    """Prints a clear and concise summary of the player's location and available interactions."""
    location_data = get_current_location(player)
    if not location_data:
        print("You are lost in an unfamiliar place.")
        # Attempt to move player back to a safe spot if they are out of bounds
        player.location = (1, 1) # Rivenshade
        return

    # --- Handle Quest Ambushes ---
    for quest in player.active_quests:
        if quest.objective.get('type') == 'ambush':
            if player.location == quest.objective.get('location') and game_state['time_of_day'] == 'Night':
                # Check if the ambush has already been triggered
                if not quest.progress: # progress = 0 means not triggered
                    print("\nAs you step into the clearing, the shadows themselves seem to writhe and coalesce!")
                    ambush_monsters = quest.objective.get('monsters', [])
                    from world import monster_mapping
                    for monster_name in ambush_monsters:
                        if monster_name in monster_mapping:
                            location_data['monsters'].append(monster_mapping[monster_name]())
                    quest.update_progress('ambush', 'trigger') # Mark ambush as triggered
                    # Immediately start combat with the first monster
                    if location_data['monsters']:
                        handle_combat(player, location_data['monsters'][0].name)

    title = f"{location_data['name']} ({game_state['time_of_day']})"
    content = []

    description = location_data.get(f"description_{game_state['time_of_day'].lower()}", location_data.get("description_day"))
    content.append(description)

    # List exits
    exits = location_data.get("exits", {})
    if exits:
        content.append("")
        content.append(f"Exits: {', '.join(exits.keys())} (`go <exit>`)")

    # List NPCs
    if game_state['time_of_day'] == "Night":
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

def handle_movement(player, direction):
    """Handles player movement."""
    current_location = get_current_location(player)
    if player.jail_time_remaining > 0 and current_location.get("name") == "Rivenshade Jail":
        print("The guard outside rattles the bars. 'Not so fast! You're not done serving your time.'")
        return

    # Handle special exits (like 'out' of the inn or jail) and dungeon exits
    if direction in current_location.get("exits", {}):
        destination = current_location["exits"][direction]

        # Check for locked doors
        if isinstance(destination, dict) and destination.get('locked'):
            key_id = destination.get('key_id')
            key_in_inventory = next((item for item in player.inventory if isinstance(item, Key) and item.unlocks_what == key_id), None)
            
            if key_in_inventory:
                print(f"You use the {key_in_inventory.name} to unlock the door.")
                player.inventory.remove(key_in_inventory)
                # Permanently unlock the door for this dungeon instance
                unlocked_destination = destination['destination']
                current_location["exits"][direction] = unlocked_destination
                destination = unlocked_destination # Continue movement with the unlocked destination
            else:
                print("The door is locked. It requires a specific key.")
                return # Stop further movement processing

        player.location = destination
        advance_time()
        print(f"You go {direction}.")
        print_location(player)
        return

    # Handle grid-based movement
    if isinstance(player.location, tuple):
        row, col = player.location
        new_row, new_col = row, col

        if direction == "north": new_row -= 1
        elif direction == "south": new_row += 1
        elif direction == "east": new_col += 1
        elif direction == "west": new_col -= 1
        else:
            print(f"You can't go {direction}.")
            return

        # Bounds checking
        if 0 <= new_row < len(world["grid"]) and 0 <= new_col < len(world["grid"][new_row]):
            player.location = (new_row, new_col)
            advance_time()
            print(f"You go {direction}.")
            print_location(player)
        else:
            print("You can't go that way.")
    else:
        # Player is in a special location without a matching cardinal direction exit
        print("You can only move to specific exits from here.")

def handle_take_item(player, item_name):
    """Handles the player taking an item."""
    current_location = get_current_location(player)
    items_in_room = current_location.get("items", [])
    
    item_to_take = next((item for item in items_in_room if item_name.lower() in item.name.lower()), None)
    
    if item_to_take:
        player.inventory.append(item_to_take)
        items_in_room.remove(item_to_take)
        print(f"You take the {item_to_take.name}.")

        # --- Special Quest Trigger for "Whispers Beneath the Ledger" ---
        if item_to_take.name == "Suspicious Ledger":
            from world import whispers_beneath_the_ledger_quest
            # Check if prerequisites are met and quest isn't already active/completed
            completed_quest_names = [q.name for q in player.completed_quests]
            if all(p in completed_quest_names for p in whispers_beneath_the_ledger_quest.prerequisites) and \
               whispers_beneath_the_ledger_quest not in player.active_quests and \
               not any(q.name == whispers_beneath_the_ledger_quest.name for q in player.completed_quests):
                
                player.active_quests.append(whispers_beneath_the_ledger_quest)
                print("\nAs you pick up the ledger, you notice some strange entries. This seems important.")
                print(f"Quest Started: {whispers_beneath_the_ledger_quest.name}")
    else:
        print(f"You don't see a {item_name} here.")

def handle_drop_item(player, item_name):
    """Handles the player dropping an item from their inventory."""
    item_to_drop = next((item for item in player.inventory if item_name.lower() in item.name.lower()), None)

    if not item_to_drop:
        print(f"You don't have a '{item_name}' in your inventory.")
        return

    # Add the item to the current room
    current_location = get_current_location(player)
    current_location.get("items", []).append(item_to_drop)

    # Remove the item from player's inventory
    player.inventory.remove(item_to_drop)

    print(f"You drop the {item_to_drop.name} on the ground.")

def handle_inventory(player):
    """Displays the player's inventory."""
    if not player.inventory:
        content = ["Your inventory is empty."]
    else:
        content = [f"- A {item.name}" for item in player.inventory]
    print_bordered("Inventory", content)

def handle_look_at(player, target_name):
    """Handles the player looking at an item or detail."""
    # Check player's inventory first
    item_in_inventory = next((item for item in player.inventory if target_name.lower() in item.name.lower()), None)
    if item_in_inventory:
        print(item_in_inventory.description)
        for quest in player.active_quests:
            quest.update_progress('discover', item_in_inventory.name)
        return

    # Check items in the current room
    current_location = get_current_location(player)
    items_in_room = current_location.get("items", [])
    item_in_room = next((item for item in items_in_room if target_name.lower() in item.name.lower()), None)
    if item_in_room:
        print(item_in_room.description)
        for quest in player.active_quests:
            quest.update_progress('discover', item_in_room.name)
        return

    # Check NPCs in the room
    npcs_in_room = current_location.get("npcs", [])
    npc_in_room = next((npc for npc in npcs_in_room if target_name.lower() in npc.name.lower()), None)
    if npc_in_room:
        print(npc_in_room.description)
        return

    # Check monsters in the room
    monsters_in_room = current_location.get("monsters", [])
    monster_in_room = next((monster for monster in monsters_in_room if target_name.lower() in monster.name.lower()), None)
    if monster_in_room:
        print(monster_in_room.description)
        return

    print(f"You don't see a {target_name} to look at.")

def get_target(parts):
    """Helper function to get the target of a command (e.g., 'look at sword')."""
    if len(parts) > 1:
        # Handle multi-word targets like "look at short sword"
        if parts[1] == "at" and len(parts) > 2:
            return " ".join(parts[2:])
        return " ".join(parts[1:])
    return None

def handle_talk_to(player, npc_name):
    """Handles the player talking to an NPC."""
    current_location = get_current_location(player)
    if game_state['time_of_day'] == "Night":
        npcs_in_room = current_location.get("npcs", []) + current_location.get("night_npcs", [])
    else:
        npcs_in_room = current_location.get("npcs", [])

    target_npc = next((npc for npc in npcs_in_room if npc_name.lower() in npc.name.lower()), None)

    if not target_npc:
        print(f"You don't see a '{npc_name}' here to talk to.")
        return
    
    # --- Special Quest Interaction for "Securing the Road" ---
    securing_road_quest = next((q for q in player.active_quests if q.name == "Securing the Road"), None)
    if securing_road_quest and target_npc.name == "Bandit Lookout" and player.location == securing_road_quest.objective.get('location'):
        print(f'"{target_npc.name}: Halt! This road is closed by order of the Red Fangs. You can pay the toll, or you can turn back... or you can die."')
        print("What will you do?")
        for i, choice in enumerate(securing_road_quest.reward_choice):
            print(f"  {i+1}. {choice['description']}")
        
        while True:
            try:
                choice_input = input("Choose your action (number): > ")
                if not choice_input: continue
                choice_index = int(choice_input) - 1
                if 0 <= choice_index < len(securing_road_quest.reward_choice):
                    chosen_option = securing_road_quest.reward_choice[choice_index]
                    if choice_index == 0: # Fight
                        print("\nYou draw your weapon. The lookout shouts a warning, and the bandits prepare for a fight!")
                        securing_road_quest.complete(player, chosen_reward_option=chosen_option)
                        return # End the talk action, player must now initiate combat
                    elif choice_index == 1: # Negotiate
                        toll = 100
                        if player.money >= toll:
                            player.money -= toll
                            print(f"\nYou hand over {toll} gold. The lookout nods. 'Wise choice. The road is yours... for now.'")
                            current_location.get("monsters", []).clear() # Bandits leave
                            current_location.get("npcs", []).remove(target_npc)
                            securing_road_quest.complete(player, chosen_reward_option=chosen_option)
                        else:
                            print(f"You don't have the {toll} gold they demand!")
                    elif choice_index == 2: # Deceive
                        print("\nYou lower your voice. 'The Master is displeased with this unsanctioned toll. You are to withdraw.'")
                        print("The lookout's eyes widen in fear. 'Apologies! We will leave at once!'")
                        current_location.get("monsters", []).clear() # Bandits leave
                        current_location.get("npcs", []).remove(target_npc)
                        securing_road_quest.complete(player, chosen_reward_option=chosen_option)
                    return # End the talk action
            except (ValueError, IndexError):
                print("Invalid choice.")
        return # End the function after the special interaction

    # --- Special Quest Interaction for "Whispers Beneath the Ledger" ---
    whispers_quest = next((q for q in player.active_quests if q.name == "Whispers Beneath the Ledger"), None)
    if whispers_quest and any(item.name == "Suspicious Ledger" for item in player.inventory):
        turn_in_options = []
        if target_npc.name == "Captain Valerius":
            turn_in_options.append(whispers_quest.reward_choice[0])
        elif target_npc.name == "Shady Figure":
            turn_in_options.append(whispers_quest.reward_choice[1])
        # The third option for the cult would be added here with another 'elif'

        if turn_in_options:
            print(f"'I have some... sensitive information that might interest you.' You show {target_npc.name} the ledger.")
            print("Their eyes widen as they scan the pages. 'This is... valuable. What do you want for it?'")
            print("What will you do?")
            
            # Present the valid choice(s) for this NPC
            for i, choice in enumerate(turn_in_options):
                print(f"  {i+1}. {choice['description']}")
            print(f"  {len(turn_in_options) + 1}. 'On second thought, never mind.'")

            while True:
                try:
                    choice_input = input("Choose your action (number): > ")
                    if not choice_input: continue
                    choice_index = int(choice_input) - 1

                    if 0 <= choice_index < len(turn_in_options):
                        chosen_option = turn_in_options[choice_index]
                        print("\nYou've made your choice. The ledger is no longer in your hands, but the consequences of your decision are just beginning.")
                        whispers_quest.complete(player, chosen_reward_option=chosen_option)
                        # The ledger is a quest item, so it should be removed upon completion
                        ledger_item = next((item for item in player.inventory if item.name == "Suspicious Ledger"), None)
                        if ledger_item:
                            player.inventory.remove(ledger_item)
                        break
                    elif choice_index == len(turn_in_options):
                        print("'I'll hold onto this for now.' You put the ledger away.")
                        break
                    else:
                        print("Invalid choice.")
                except (ValueError, IndexError):
                    print("Please enter a number.")
            return # End the talk action

    # --- Special Quest Interaction for "A Trade of Shadows" ---
    trade_quest = next((q for q in player.active_quests if q.name == "A Trade of Shadows"), None)
    if trade_quest and player.location == trade_quest.objective.get('location'):
        if target_npc.name == "Caravan Guard Captain":
            print(f'"{target_npc.name}: You\'re here. Good. The Whispered Hand has been sniffing around. Are you with us, or are you going to be a problem?"')
        elif target_npc.name == "Whispered Hand Agent":
            print(f'"{target_npc.name}: The Guild grows too bold. This caravan is an opportunity. A smart adventurer knows which side butters their bread. What\'s it going to be?"')
        else: # Not one of the quest NPCs, proceed normally
            pass
        
        print("The choice is yours. What will you do?")
        for i, choice in enumerate(trade_quest.reward_choice):
            print(f"  {i+1}. {choice['description']}")

        while True:
            try:
                choice_input = input("Choose your action (number): > ")
                if not choice_input: continue
                choice_index = int(choice_input) - 1
                if 0 <= choice_index < len(trade_quest.reward_choice):
                    chosen_option = trade_quest.reward_choice[choice_index]
                    print("\nYou've made your choice. The caravan moves on, its fate sealed by your decision.")
                    trade_quest.complete(player, chosen_reward_option=chosen_option)
                    # Remove the quest NPCs from the location
                    current_location["npcs"] = [npc for npc in current_location.get("npcs", []) if npc.name not in ["Caravan Guard Captain", "Whispered Hand Agent"]]
                    break
            except (ValueError, IndexError):
                print("Invalid choice.")
        return # End the talk action
    
    # --- Special Quest Interaction for "The Merchant's Plea" ---
    plea_quest = next((q for q in player.active_quests if q.name == "The Merchant's Plea"), None)
    if plea_quest and target_npc.name == "Village Elder Aelric":
        print(f'"{target_npc.name}: The situation has become untenable. The Guild demands our support, the Hunters threaten to abandon us, and this talk of a cult grows louder. The Vale needs a clear path forward. What do you advise?"')
        print("The fate of the Vale rests on your counsel. What will you do?")
        for i, choice in enumerate(plea_quest.reward_choice):
            print(f"  {i+1}. {choice['description']}")

        while True:
            try:
                choice_input = input("Choose your action (number): > ")
                if not choice_input: continue
                choice_index = int(choice_input) - 1
                if 0 <= choice_index < len(plea_quest.reward_choice):
                    chosen_option = plea_quest.reward_choice[choice_index]
                    print("\nYou have given your counsel. The Elder nods grimly, the path now set. The consequences of this day will be felt for a long time to come.")
                    plea_quest.complete(player, chosen_reward_option=chosen_option)
                    break
                else:
                    print("Invalid choice.")
            except (ValueError, IndexError):
                print("Please enter a number.")
        return # End the talk action


    # Check faction standing before allowing conversation
    if target_npc.faction and target_npc.faction in player.factions:
        faction = player.factions[target_npc.faction]
        if faction.get_standing() == "Hated":
            # Allow talking to procedural quest givers to get reputation quests
            if not isinstance(target_npc, ProceduralQuestGiver):
                print(f'"{target_npc.name} spits on the ground as you approach. \'I have nothing to say to the likes of you.\'"')
                return

    player.last_npc_talked_to = target_npc # Remember who we talked to

    if hasattr(target_npc, 'talk'):
        # The QuestGiver's talk method requires the player object
        target_npc.talk(player, game_state)
    else:
        print(f"{target_npc.name} doesn't seem to have much to say.")

def handle_insult(player, npc_name):
    """Handles the player insulting an NPC."""
    current_location = get_current_location(player)
    target_npc = next((npc for npc in current_location.get("npcs", []) if npc_name.lower() in npc.name.lower()), None)

    if not target_npc:
        print(f"You shout insults at the air. No one named '{npc_name}' is here.")
        return

    print(f"You shout a rather creative insult at {target_npc.name}.")
    target_npc.record_interaction('insult', game_state['turn_count'])
    target_npc.talk(player, game_state) # Let the talk method handle the immediate reaction

def handle_bank_view(player):
    """Displays the contents of the player's bank."""
    location = get_current_location(player)
    if not any(isinstance(npc, Banker) and npc.is_available for npc in location.get("npcs", [])):
        print("You must be at an available bank to do that.")
        return

    content = [f"Gold: {player.bank_gold}", "", "Items:"]
    if not player.bank_items:
        content.append("- Empty")
    else:
        for item in player.bank_items:
            content.append(f"- {item.name}")
    
    print_bordered("Your Bank", content)

def handle_deposit(player, args):
    """Handles depositing items or gold into the bank."""
    location = get_current_location(player)
    if not any(isinstance(npc, Banker) and npc.is_available for npc in location.get("npcs", [])):
        print("You must be at an available bank to do that.")
        return

    if not args:
        print("Deposit what? (e.g., 'deposit gold 100' or 'deposit rusty sword')")
        return

    if args[0].lower() == 'gold':
        try:
            amount = int(args[1])
            if amount <= 0:
                print("You must deposit a positive amount of gold.")
            elif player.money >= amount:
                player.money -= amount
                player.bank_gold += amount
                print(f"You deposit {amount} gold. Your bank balance is now {player.bank_gold} gold.")
            else:
                print("You don't have that much gold to deposit.")
        except (ValueError, IndexError):
            print("Invalid amount. Usage: 'deposit gold <amount>'")
    else:
        item_name = " ".join(args)
        item_to_deposit = next((item for item in player.inventory if item_name.lower() in item.name.lower()), None)
        if item_to_deposit:
            player.inventory.remove(item_to_deposit)
            player.bank_items.append(item_to_deposit)
            print(f"You deposit the {item_to_deposit.name} into your bank.")
        else:
            print(f"You don't have a '{item_name}' in your inventory.")

def handle_withdraw(player, args):
    """Handles withdrawing items or gold from the bank."""
    location = get_current_location(player)
    if not any(isinstance(npc, Banker) and npc.is_available for npc in location.get("npcs", [])):
        print("You must be at an available bank to do that.")
        return

    if not args:
        print("Withdraw what? (e.g., 'withdraw gold 100' or 'withdraw rusty sword')")
        return

    if args[0].lower() == 'gold':
        try:
            amount = int(args[1])
            if amount <= 0:
                print("You must withdraw a positive amount of gold.")
            elif player.bank_gold >= amount:
                player.bank_gold -= amount
                player.money += amount
                print(f"You withdraw {amount} gold. You now have {player.money} gold.")
            else:
                print("You don't have that much gold in your bank.")
        except (ValueError, IndexError):
            print("Invalid amount. Usage: 'withdraw gold <amount>'")
    else:
        item_name = " ".join(args)
        item_to_withdraw = next((item for item in player.bank_items if item_name.lower() in item.name.lower()), None)
        if item_to_withdraw:
            player.bank_items.remove(item_to_withdraw)
            player.inventory.append(item_to_withdraw)
            print(f"You withdraw the {item_to_withdraw.name} from your bank.")
        else:
            print(f"You don't have a '{item_name}' in your bank.")

def handle_help():
    """Displays a list of available commands and their usage."""
    content = [
        "Movement:",
        "  go <direction>   - Move to a new location (e.g., 'go north').",
        "  north, south, etc. - Shortcut for movement.",
        "",
        "Interaction:",
        "  look             - Examine your current location.",
        "  look at <target> - Examine an item, NPC, or monster.",
        "  take <item>      - Pick up an item from the ground.",
        "  talk to <npc>    - Speak with a person (e.g., 'talk to elara').",
        "  insult <npc>     - Insult a person (be careful!).",
        "  wait             - Pass a short amount of time.",
        "  rest             - Rest at a tavern to heal (costs gold).",
        "  enter <feature>  - Enter a specific feature, like a cave or inn.",
        "",
        "Gathering & Crafting:",
        "  mine <vein>      - Mine an ore vein (e.g., 'mine copper').",
        "  chop <tree>      - Chop a tree (e.g., 'chop tree').",
        "  fish <spot>      - Fish at a fishing spot (e.g., 'fish spot').",
        "  cook <item>      - Cook raw food at a campfire or range.",
        "  brew <potion>    - Brew a potion from herbs.",
        "  smelt <bar>      - Smelt ore into a bar at a forge.",
        "  craft <item>     - Craft a new item from materials.",
        "  recipes          - Show a list of known crafting recipes.",
        "  bind <word1> ... - Attempt to bind words of power into a new spell.",
        "",
        "Combat & Thievery:",
        "  attack <monster> - Engage a monster in combat.",
        "  cast <spell_num> - Cast a known spell during combat.",
        "  defend / parry   - Take a defensive stance in combat.",
        "  flee             - Attempt to escape from combat.",
        "  open chest       - Open a treasure chest.",
        "  disarm chest     - Attempt to disarm a trapped chest.",
        "  pickpocket <npc> - Attempt to steal from an NPC.",
        "  lockpick / bribe - Used to escape from jail.",
        "",
        "Character & Game:",
        "  inventory (i)    - View the items you are carrying.",
        "  status (stats)   - View your character's stats and level.",
        "  quests (journal) - View your active quests.",
        "  factions         - View your reputation with various factions.",
        "  equip <item>     - Equip a weapon or armor.",
        "  unequip <slot>   - Unequip an item ('weapon' or 'armor').",
        "  bank             - View your bank balance.",
        "  deposit/withdraw - Manage your bank account.",
        "  save / quit      - Save your progress or exit the game.",
    ]
    print_bordered("Help: Available Commands", content)

def handle_factions(player):
    """Displays the player's reputation with all known factions."""
    if not player.factions:
        content = ["You have not encountered any factions yet."]
    else:
        content = []
        for faction in player.factions.values():
            standing = faction.get_standing()
            content.append(f"- {faction.name}: {standing} ({faction.reputation})")
    print_bordered("Faction Reputations", content)

def handle_map(player):
    """Displays a local area map centered on the player."""
    if not isinstance(player.location, tuple):
        print("You can't see the regional map from here.")
        return

    player_row, player_col = player.location
    map_size = 11  # How many tiles to show across (width and height)
    radius = map_size // 2

    # Define a mapping from location type to map character
    type_to_char = {
        'town': 'T', 'village': 'V', 'forest': 'F', 'forest_edge': 'f',
        'camp': 'c', 'river': '~', 'plains': 'p', 'hills': 'h',
        'mountains': '^', 'mine': 'M', 'ruins': 'R', 'fort': 'O',
        'ash_plains': 'a', 'special': 'S', 'swamp': 's'
    }


    map_lines = []
    for r in range(player_row - radius, player_row + radius + 1):
        map_line = ""
        for c in range(player_col - radius, player_col + radius + 1):
            if r == player_row and c == player_col:
                map_line += "[X]"
            elif 0 <= r < len(world["grid"]) and 0 <= c < len(world["grid"][r]):
                loc_type = world["grid"][r][c].get("type", "plains")
                map_char = type_to_char.get(loc_type, "?")
                map_line += f"[{map_char}]"
            else:
                # Represent off-map area with empty space
                map_line += "   "
        map_lines.append(map_line)
    
    map_lines.append("")
    map_lines.append("--- Legend ---")
    map_lines.append("X: You | T: Town | V: Village | F/f: Forest | c: Camp")
    map_lines.append("~: River | p: Plains | h: Hills | ^: Mountains | M: Mine | R: Ruins | O: Outpost")
    map_lines.append("a: Ash Plains | s: Swamp | S: Special")
    
    print_bordered("Local Area Map", map_lines)

def handle_cleanse_shrine(player):
    """Handles the player interacting with the defiled altar."""
    current_location = get_current_location(player)
    quest = next((q for q in player.active_quests if q.name == "The Ruined Shrine"), None)

    if not quest or player.location != quest.objective.get('location'):
        print("There is nothing here to cleanse.")
        return

    # Check if there are still monsters
    if any(m.is_alive() for m in current_location.get("monsters", [])):
        print("You must defeat the guardians of the shrine first!")
        return

    print("With the guardians defeated, you approach the defiled altar. The air crackles with dark energy.")
    print("What will you do?")
    
    for i, choice in enumerate(quest.reward_choice):
        print(f"  {i+1}. {choice['description']}")

    while True:
        try:
            choice_input = input("Choose your action (number): > ")
            if not choice_input: continue
            choice_index = int(choice_input) - 1
            if 0 <= choice_index < len(quest.reward_choice):
                chosen_reward_option = quest.reward_choice[choice_index]
                quest.complete(player, chosen_reward_option=chosen_reward_option)
                break
            else:
                print("Invalid choice.")
        except ValueError:
            print("Please enter a number.")

def handle_rest(player):
    """Allows the player to rest at a tavern to restore health and mana for a price."""
    if player.location != "drunken_griffin_inn":
        print("You can only rest at a tavern.")
        return

    cost = 10
    if player.health == player.max_health and player.mana == player.max_mana:
        print("You are already fully rested.")
        return

    if player.money < cost:
        print(f"You need {cost} gold to rent a room, but you only have {player.money}.")
        return

    player.money -= cost
    player.health = player.max_health
    player.mana = player.max_mana
    
    # Resting passes a significant amount of time (e.g., 8 hours)
    advance_time(8)

    print(f"\nYou pay {cost} gold and rest soundly in a warm bed, feeling fully refreshed.")
    print_location(player)

def handle_wait(player):
    """Allows the player to wait and pass one turn."""
    print("You wait for a while...")
    advance_time()
    print_location(player)
    if player.jail_time_remaining > 0:
        player.jail_time_remaining -= 1
        if player.jail_time_remaining > 0:
            print(f"You have {player.jail_time_remaining} more turns to wait.")
        else:
            print("\nA guard unlocks the door. 'Your sentence is served. Now get out of here!'")

def handle_bribe(player):
    """Handles the player attempting to bribe the guard to get out of jail."""
    current_location = get_current_location(player)
    if not current_location or current_location.get("name") != "Rivenshade Jail" or player.jail_time_remaining <= 0:
        print("There's no one to bribe here.")
        return

    guard = next((npc for npc in current_location.get("npcs", []) if isinstance(npc, Guard)), None)

    if not guard:
        print("There are no guards to bribe here.") # Should not happen if logic is correct
        return

    bribe_cost = player.skills["Attack"].level * 20
    print(f"The guard sizes you up. 'It'll cost you {bribe_cost} gold to make me forget I saw you.'")
    
    if player.money >= bribe_cost:
        print(f"You have {player.money} gold. Pay the bribe? (Y/N)")
        choice = input("> ").lower()
        if choice == 'y':
            player.money -= bribe_cost
            player.jail_time_remaining = 0
            player.location = current_location["exits"]["out"]
            print("\nYou discreetly slip the gold to the guard. The cell door creaks open.")
            print("'Now get out of here before I change my mind,' the guard mutters.")
            print_location(player)
        else:
            print("You decide to keep your money.")
    else:
        print(f"You don't have enough gold to pay the bribe.")

def handle_lockpick(player):
    """Handles the player attempting to pick the lock of their jail cell."""
    current_location = get_current_location(player)
    if not current_location or current_location.get("name") != "Rivenshade Jail" or player.jail_time_remaining <= 0:
        print("There's nothing to lockpick here.")
        return

    lockpick = next((item for item in player.inventory if item.name == "Lockpick"), None)
    if not lockpick:
        print("You need a lockpick to attempt this.")
        return

    # Calculate success chance based on Lockpicking skill
    success_chance = 0.1 + (player.skills["Lockpicking"].level * 0.05) # Base 10% + 5% per level
    success_chance = min(success_chance, 0.75) # Cap at 75%

    print("You carefully work the lockpick in the keyhole...")
    advance_time() # Lockpicking takes time

    if random.random() < success_chance:
        player.jail_time_remaining = 0
        player.location = current_location["exits"]["out"]
        print("Click! The lock springs open. You slip out of the cell and back into the town square.")
        player.add_skill_xp("Lockpicking", 100)
    else:
        print("Snap! The lockpick breaks, leaving a piece inside the lock.")
        player.inventory.remove(lockpick)
        player.add_skill_xp("Lockpicking", 10)
        guard = next((npc for npc in current_location.get("npcs", []) if isinstance(npc, Guard)), None)
        if guard:
            print(f"The {guard.name} outside the cell hears the noise. 'Stop that racket in there!'")

def handle_recipes(player):
    """Displays a list of known crafting recipes and required ingredients."""
    if not player.known_recipes:
        content = ["You don't know any recipes yet."]
    else:
        content = []
        inventory_counts = {}
        for item in player.inventory:
            inventory_counts[item.name] = inventory_counts.get(item.name, 0) + 1

        for recipe in player.known_recipes:
            can_craft = all(inventory_counts.get(ing, 0) >= count for ing, count in recipe.ingredients.items())
            craftable_tag = "(Craftable)" if can_craft else ""
            content.append(f"- {recipe.name} {craftable_tag}")
            ingredients_str = ", ".join([f"{count}x {name}" for name, count in recipe.ingredients.items()])
            content.append(f"  Requires: {ingredients_str}")
            if recipe.station:
                content.append(f"  Station: {recipe.station}")
            content.append("") # Spacer
    print_bordered("Known Recipes", content)

def handle_cook_item(player, item_name):
    """Handles the player attempting to cook an item."""
    # Find a recipe where the item_name matches an ingredient
    recipe_to_cook = next((r for r in cooking_recipes for ingredient in r.ingredients if item_name.lower() in ingredient.lower()), None)
    
    if not recipe_to_cook:
        print(f"You don't know how to cook '{item_name}'.")
        return

    current_location = get_current_location(player)

    # Check for cooking station
    if recipe_to_cook.station:
        current_location = get_current_location(player)
        available_stations = current_location.get("stations", [])
        if recipe_to_cook.station not in available_stations:
            print(f"You need to be at a {recipe_to_cook.station} to do that.")
            return

    # Check for skill requirement
    if recipe_to_cook.skill_req:
        skill_name, required_level = recipe_to_cook.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    # Check if player has enough ingredients
    inventory_counts = {}
    for item in player.inventory:
        inventory_counts[item.name] = inventory_counts.get(item.name, 0) + 1

    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_cook.ingredients.items()):
        print("You don't have the required ingredients.")
        return

    # Consume ingredients
    for ingredient, required_count in recipe_to_cook.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    # Add crafted item to inventory
    cooked_item = recipe_to_cook.result
    player.inventory.append(cooked_item)
    player.add_skill_xp("Cooking", 20) # Grant cooking XP
    print(f"You successfully cook a {cooked_item.name}!")

def handle_open_chest(player):
    """Handles the player opening a treasure chest."""
    current_location = get_current_location(player)
    chest = current_location.get('chest')

    if not chest:
        print("There is no chest here to open.")
        return

    if chest.get('is_mimic'):
        from monster import Mimic # Local import to avoid circular dependency
        print("The chest opens, revealing rows of sharp teeth! It's a Mimic!")
        mimic = Mimic()
        current_location['monsters'].append(mimic)
        del current_location['chest']
        handle_combat(player, 'mimic')
        return

    # It's a real chest
    if chest.get('trapped') and not chest.get('disarmed'):
        trap_damage = 25
        print(f"As you open the chest, a dart shoots out and hits you for {trap_damage} damage!")
        player.take_damage(trap_damage, bypass_defense=True)
        if not player.is_alive():
            return # Player was defeated by the trap

    print("You open the chest and find:")
    loot = chest.get('loot', [])
    if not loot:
        print("- Nothing but dust.")
    else:
        for item in loot:
            if item.name == "Pouch of Gold":
                player.money += item.value
                print(f"- {item.value} gold")
            else:
                player.inventory.append(item)
                print(f"- A {item.name}")
    
    del current_location['chest'] # The chest is now empty and gone

def handle_disarm_chest(player):
    """Handles the player attempting to disarm a trapped chest."""
    current_location = get_current_location(player)
    chest = current_location.get('chest')

    if not chest:
        print("There is no chest here to disarm.")
        return

    if chest.get('is_mimic'):
        from monster import Mimic # Local import
        print("You search for traps, but the chest suddenly lunges at you!")
        mimic = Mimic()
        current_location['monsters'].append(mimic)
        del current_location['chest']
        handle_combat(player, 'mimic')
        return

    if not chest.get('trapped'):
        print("You search for traps but find none.")
        return

    success_chance = 0.2 + (player.skills["Thieving"].level * 0.05)
    if random.random() < success_chance:
        chest['disarmed'] = True
        print("You carefully disable the trap mechanism. The chest is now safe to open.")
        player.add_skill_xp("Thieving", 30)
    else:
        print("You fumble and trigger the trap!")
        player.take_damage(25, bypass_defense=True)
        del current_location['chest'] # The chest and its contents are destroyed
        player.add_skill_xp("Thieving", 5)

def handle_brew_potion(player, item_name):
    """Handles the player attempting to brew a potion."""
    recipe_to_brew = next((r for r in herblore_recipes if item_name.lower() in r.name.lower()), None)
    
    if not recipe_to_brew:
        print(f"You don't know how to brew '{item_name}'.")
        return

    # Check for skill requirement
    if recipe_to_brew.skill_req:
        skill_name, required_level = recipe_to_brew.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    # Check if player has enough ingredients
    inventory_counts = {}
    for item in player.inventory:
        inventory_counts[item.name] = inventory_counts.get(item.name, 0) + 1

    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_brew.ingredients.items()):
        print("You don't have the required ingredients.")
        for ing, count in recipe_to_brew.ingredients.items():
            if inventory_counts.get(ing, 0) < count:
                print(f"  (Missing {count - inventory_counts.get(ing, 0)}x {ing})")
        return

    # Consume ingredients
    for ingredient, required_count in recipe_to_brew.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    # Add crafted item to inventory
    brewed_item = recipe_to_brew.result
    player.inventory.append(brewed_item)
    player.add_skill_xp("Herblore", 40) # Grant herblore XP
    print(f"You carefully combine the ingredients and brew a {brewed_item.name}!")
    advance_time()

def handle_craft_item(player, item_name):
    """Handles the player attempting to craft an item."""
    recipe_to_craft = next((r for r in player.known_recipes if item_name.lower() in r.name.lower()), None)

    if not recipe_to_craft:
        print(f"You don't know how to craft '{item_name}'.")
        return

    # Check for crafting station
    if recipe_to_craft.station:
        current_location = get_current_location(player)
        available_stations = current_location.get("stations", [])
        if recipe_to_craft.station not in available_stations:
            print(f"You need to be at a {recipe_to_craft.station} to craft this item.")
            return

    # Check for skill requirement
    if recipe_to_craft.skill_req:
        skill_name, required_level = recipe_to_craft.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    # Check if player has enough ingredients
    inventory_counts = {}
    for item in player.inventory:
        inventory_counts[item.name] = inventory_counts.get(item.name, 0) + 1

    can_craft = True
    for ingredient, required_count in recipe_to_craft.ingredients.items():
        if inventory_counts.get(ingredient, 0) < required_count:
            print(f"You don't have enough ingredients. You need {required_count} {ingredient}(s).")
            can_craft = False
            break
    
    if not can_craft:
        return

    # Consume ingredients
    print("You use your materials to craft the item...")
    for ingredient, required_count in recipe_to_craft.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    # Add crafted item to inventory
    crafted_item = recipe_to_craft.result
    player.inventory.append(crafted_item)
    
    # Grant XP to the relevant skill
    xp_skill = recipe_to_craft.skill_req[0] if recipe_to_craft.skill_req else "Crafting"
    player.add_skill_xp(xp_skill, 25)
    print(f"You successfully crafted a {crafted_item.name}!")
    for quest in player.active_quests:
        quest.update_progress('activity', 'craft')

def handle_bind_words(player, words_to_bind):
    """Handles the player attempting to bind words into a spell."""
    if not words_to_bind:
        print("Bind what words? (e.g., 'bind word of fire, word of bolt')")
        return

    if len(words_to_bind) > player.max_words_to_bind:
        print(f"You can only bind up to {player.max_words_to_bind} words at your current skill level.")
        return

    # Check if player has the required word items
    inventory_words = [item for item in player.inventory if isinstance(item, Item) and item.name in words_to_bind]
    if len(inventory_words) < len(words_to_bind):
        print("You don't have all the required words in your inventory.")
        return

    # Create a key from the sorted names of the words to check against combinations
    word_names = sorted([word.name for word in inventory_words])
    combination_key = tuple(word_names)

    # Check if the combination is a valid recipe
    if combination_key in word_combinations:
        new_ability = word_combinations[combination_key]
        print("The words resonate and surge with power!")
        player.learn_ability(new_ability)
        
        # Consume the words used
        for word_item in inventory_words:
            player.inventory.remove(word_item)
        
        player.add_skill_xp("Wordbinding", 100) # More XP for success
    else:
        print("You chant the words, but they fizzle into nothingness.")
        # Grant a small amount of XP for the attempt
        player.add_skill_xp("Wordbinding", 10)

    # Advance time for the effort
    advance_time()

def handle_pickpocket(player, npc_name):
    """Handles the player attempting to pickpocket an NPC."""
    current_location = get_current_location(player)
    target_npc = next((npc for npc in current_location.get("npcs", []) if npc_name.lower() in npc.name.lower()), None)

    if not target_npc:
        print(f"You don't see a '{npc_name}' here to pickpocket.")
        return

    if not target_npc.is_available:
        print(f"You can't get close enough to {target_npc.name}.")
        return

    if target_npc.has_been_pickpocketed:
        print(f"{target_npc.name} is watching you suspiciously. You can't try again.")
        return

    # Calculate success chance
    level_diff = player.skills["Thieving"].level - target_npc.level
    success_chance = 0.5 + (level_diff * 0.05) # Base 50%, +/- 5% per level diff
    success_chance = max(0.1, min(success_chance, 0.9)) # Clamp between 10% and 90%

    if random.random() < success_chance:
        if not target_npc.pickpocket_loot:
            print(f"You successfully pick {target_npc.name}'s pockets but find nothing.")
        else:
            looted_item = random.choice(target_npc.pickpocket_loot)
            player.inventory.append(looted_item)
            print(f"Success! You deftly lift a {looted_item.name} from {target_npc.name}.")
            player.add_skill_xp("Thieving", 50)
    else:
        print(f"You clumsy oaf! {target_npc.name} catches your hand!")
        print(f'"{target_npc.name}: Guards! We have a thief!"')
        print("\nYou are swiftly apprehended and thrown in jail to contemplate your actions.")
        player.location = "rivenshade_jail"
        player.jail_time_remaining = 5 # Set sentence to 5 turns
        print_location(player)
        player.add_skill_xp("Thieving", 5) # Small XP for the attempt

    target_npc.has_been_pickpocketed = True # Can only attempt once for now

def handle_smelt_item(player, item_name):
    """Handles the player attempting to smelt ore into a bar."""
    recipe_to_smelt = next((r for r in smelting_recipes if item_name.lower() in r.name.lower()), None)

    if not recipe_to_smelt:
        print(f"You don't know how to smelt '{item_name}'.")
        return

    # Check for crafting station
    if recipe_to_smelt.station:
        current_location = get_current_location(player)
        available_stations = current_location.get("stations", [])
        if recipe_to_smelt.station not in available_stations:
            print(f"You need to be at a {recipe_to_smelt.station} to do that.")
            return

    # Check for skill requirement
    if recipe_to_smelt.skill_req:
        skill_name, required_level = recipe_to_smelt.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    # Check if player has enough ingredients
    inventory_counts = {}
    for item in player.inventory:
        inventory_counts[item.name] = inventory_counts.get(item.name, 0) + 1

    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_smelt.ingredients.items()):
        print("You don't have the required ore.")
        return

    # Consume ingredients
    for ingredient, required_count in recipe_to_smelt.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    # Add crafted item to inventory
    smelted_item = recipe_to_smelt.result
    player.inventory.append(smelted_item)
    player.add_skill_xp("Smelting", 15) # Grant smelting XP
    print(f"You smelt the ore and successfully create a {smelted_item.name}!")

def handle_gather_node(player, verb, node_name):
    """Handles the player attempting to gather from a resource node (e.g., mine, chop)."""
    current_location = get_current_location(player)
    # Flexible matching: find a node where the input is part of the node's name
    node_to_gather = next((node for node in current_location.get("nodes", []) if node_name.lower() in node.name.lower() and node.verb == verb), None)

    if not node_to_gather:
        print(f"You can't {verb} that here.")
        return

    # Check for required tool
    if not any(item.name == node_to_gather.required_tool for item in player.inventory):
        print(f"You need a {node_to_gather.required_tool} to do that.")
        return

    # Check for required skill level
    skill_name = node_to_gather.skill
    if player.skills[skill_name].level < node_to_gather.required_level:
        print(f"Your {skill_name} level is too low. You need level {node_to_gather.required_level}.")
        return

    # Grant resources and XP
    yielded_item = node_to_gather.item_yield
    player.inventory.append(yielded_item)
    player.add_skill_xp(skill_name, node_to_gather.xp_yield)
    print(f"You successfully get some {yielded_item.name}.")
    if verb == 'fish':
        for quest in player.active_quests:
            quest.update_progress('activity', 'fish')
    
    advance_time()

def handle_accept_quest(player):
    """Handles the player accepting a quest."""
    if not player.last_npc_talked_to:
        print("You need to talk to someone to accept their quest first.")
        return

    quest_giver = player.last_npc_talked_to
    
    if quest_giver:
        # Determine which quest to accept
        quest_to_accept = None
        if isinstance(quest_giver, QuestGiver) and quest_giver.quest and quest_giver.quest not in player.active_quests and not quest_giver.quest.is_completed:
            quest_to_accept = quest_giver.quest
        elif hasattr(quest_giver, 'offered_quest') and quest_giver.offered_quest and quest_giver.offered_quest not in player.active_quests:
            quest_to_accept = quest_giver.offered_quest

        if quest_to_accept:
            print(f"You have accepted the quest: '{quest_to_accept.name}'.")
            player.active_quests.append(quest_to_accept)
        else:
            print(f"{quest_giver.name} has no quest for you to accept right now.")
    else:
        # This case should ideally not be reached if last_npc_talked_to is set.
        print("You need to talk to someone to accept their quest first.")

def handle_quests_log(player):
    """Displays the player's active quests."""
    if not player.active_quests:
        content = ["You have no active quests."]
    else:
        content = []
        for quest in player.active_quests:
            progress = quest.get_progress_string()
            content.append(f"- {quest.name}: {quest.description} {progress}")
    print_bordered("Your Quests", content)

def handle_equip_item(player, item_name):
    """Equips an item from the player's inventory."""
    item_to_equip = next((item for item in player.inventory if item.name.lower() == item_name.lower()), None)

    if not item_to_equip:
        print(f"You don't have a {item_name} in your inventory.")
        return

    if isinstance(item_to_equip, Weapon):
        if player.weapon:
            player.inventory.append(player.weapon) # Move old weapon back to inventory
        player.weapon = item_to_equip
        player.inventory.remove(item_to_equip)
        print(f"You equip the {item_to_equip.name}.")
    elif isinstance(item_to_equip, Armor):
        if player.armor:
            player.inventory.append(player.armor) # Move old armor back to inventory
        player.armor = item_to_equip
        player.inventory.remove(item_to_equip)
        print(f"You equip the {item_to_equip.name}.")
    else:
        print(f"You can't equip a {item_to_equip.name}.")

def handle_unequip_item(player, slot):
    """Unequips an item and returns it to the inventory."""
    if slot == "weapon":
        if not player.weapon:
            print("You have no weapon equipped.")
            return
        item = player.weapon
        player.inventory.append(item)
        player.weapon = None
        print(f"You unequip the {item.name}.")
    elif slot == "armor":
        if not player.armor:
            print("You have no armor equipped.")
            return
        item = player.armor
        player.inventory.append(item)
        player.armor = None
        print(f"You unequip the {item.name}.")
    else:
        print("You can unequip 'weapon' or 'armor'.")

def handle_use_item(player, item_name):
    """Handles the player using a consumable item."""
    item_to_use = next((item for item in player.inventory if item_name.lower() in item.name.lower()), None)

    if isinstance(item_to_use, Spellbook):
        player.learn_ability(item_to_use.ability)
        player.inventory.remove(item_to_use)
        return
    elif isinstance(item_to_use, RecipeScroll):
        player.learn_recipe(item_to_use.recipe)
        player.inventory.remove(item_to_use)
        return
    
    if not item_to_use:
        print(f"You don't have a '{item_name}' in your inventory.")
        return
    elif not isinstance(item_to_use, Consumable):
        print(f"You can't use the {item_to_use.name}.")
        return

    # Use the item
    if item_to_use.effect == "heal":
        amount_healed = player.heal(item_to_use.amount)
        if amount_healed > 0:
            print(f"You use the {item_to_use.name} and recover {amount_healed} HP.")
            player.inventory.remove(item_to_use)
        else:
            print("Your health is already full.")
    elif item_to_use.effect == "restore_mana":
        amount_restored = player.restore_mana(item_to_use.amount)
        if amount_restored > 0:
            print(f"You use the {item_to_use.name} and recover {amount_restored} MP.")
            player.inventory.remove(item_to_use)
        else:
            print("Your mana is already full.")
    else:
        print(f"The {item_to_use.name} has no effect.")

def handle_combat(player, monster_name_input):
    """Manages the turn-based combat loop."""
    current_location = get_current_location(player)
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
        is_stunned = player.process_turn_effects()
        if not player.is_alive():
            break

        player_action = None

        if not is_stunned:
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
                player.print_status()
                continue # This doesn't use up a turn
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
            # Update any relevant kill quests
            xp_reward = target_monster.xp_yield
            for quest in player.active_quests:
                quest.update_progress('kill', target_monster.name)
                quest.update_progress('activity', 'hunt')
                # Check if this was a hunting task and grant on-kill XP
                if quest.reward and 'xp' in quest.reward and 'Hunting' in quest.reward['xp']:
                    hunting_xp_per_kill = int(target_monster.xp_yield * 0.5) # Grant 50% of base XP as Hunting XP
                    player.add_skill_xp("Hunting", hunting_xp_per_kill)
                elif quest.reward_choice: # Also check reward choices
                    if any('Hunting' in choice['reward'].get('xp', {}) for choice in quest.reward_choice):
                        hunting_xp_per_kill = int(target_monster.xp_yield * 0.5)
                        player.add_skill_xp("Hunting", hunting_xp_per_kill)
            
            # --- Special Post-Combat Quest Logic for "Ashes on the Road" ---
            if quest.name == "Ashes on the Road" and quest.check_completion(player):
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
        is_stunned = target_monster.process_turn_effects()
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

        if not is_stunned:
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
    """Saves the current game state to a file."""
    save_data = {
        "player": player,
        "world": world_state,
        "game_state": game_state
    }
    try:
        with open(SAVE_FILENAME, "wb") as save_file:
            pickle.dump(save_data, save_file)
        print("\nGame saved successfully!")
    except Exception as e:
        print(f"\nError saving game: {e}")

def load_game():
    """Loads the game state from a file."""
    from world import world as template_world # Import here to avoid circular dependency

    if not os.path.exists(SAVE_FILENAME):
        return None, None, None

    try:
        with open(SAVE_FILENAME, "rb") as save_file:
            save_data = pickle.load(save_file)
        
        player = save_data["player"]
        loaded_world = save_data["world"] # Correctly load the saved world state

        # --- Faction Migration for saved games ---
        from world import factions as world_factions
        from faction import Faction
        for key, faction_template in world_factions.items():
            if key not in player.factions:
                player.factions[key] = Faction(faction_template.name, faction_template.description)

        respawn_monsters()
        update_npc_availability()

        # Handle migration for saves without game_state
        loaded_game_state = save_data.get("game_state", {
            "time_of_day": "Day", "turn_count": 0, 
            "day_length": 20, "night_length": 15
        })

        print("\nGame loaded successfully!")
        return player, loaded_world, loaded_game_state
    except Exception as e:
        print(f"\nError loading game: {e}")
        return None, None, None

def parse_command(command, player):
    """Parses the player's command."""
    parts = command.lower().split()
    if not parts:
        print("Say something!")
        return

    # Check if player is in jail
    current_location = get_current_location(player)
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
        handle_help()
    elif verb == "look":
        target = get_target(parts)
        if target and target != "at":
            handle_look_at(player, target)
        else:
            print_location(player)
    elif verb in ["get", "take"]:
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Take what?")
        else:
            handle_take_item(player, item_name)
    elif verb == "drop":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Drop what?")
        else:
            handle_drop_item(player, item_name)
    elif verb in ["go", "move"]:
        if len(parts) > 1:
            direction = parts[1]
            handle_movement(player, direction)
        else:
            print("Go where?")
    elif verb in ["north", "south", "east", "west"]:
        handle_movement(player, verb)
    elif verb in ["inventory", "i"]:
        handle_inventory(player)
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
        else: handle_equip_item(player, item_name)
    elif verb == "unequip":
        slot = parts[1] if len(parts) > 1 else ""
        if not slot: print("Unequip what? ('weapon' or 'armor')")
        else: handle_unequip_item(player, slot)
    elif verb == "save":
        save_game(player, world)
    elif verb == "load":
        print("Loading the game will overwrite your current progress.")
        print("This feature is best used from the main menu.")
    elif verb == "talk":
        if len(parts) > 1 and parts[1] == "to":
            npc_name = " ".join(parts[2:])
            handle_talk_to(player, npc_name)
        else:
            print("Talk to whom?")
    elif verb == "insult":
        npc_name = " ".join(parts[1:])
        if not npc_name:
            print("Insult whom?")
        else:
            handle_insult(player, npc_name)
    elif verb == "accept":
        handle_accept_quest(player)
    elif verb == "decline":
        print("You decide not to take on the task for now.")
    elif verb in ["quests", "journal"]:
        handle_quests_log(player)
    elif verb == "sell":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Sell what?")
        else:
            # Find a shopkeeper in the current location
            current_location = get_current_location(player)
            shopkeeper = next((npc for npc in current_location.get("npcs", []) if isinstance(npc, Shopkeeper)), None)
            if shopkeeper:
                shopkeeper.sell_item(player, item_name, game_state)
            else:
                print("There is no one here to sell to.")
    elif verb == "factions":
        handle_factions(player)
    elif verb == "use":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Use what?")
        else:
            handle_use_item(player, item_name)
    elif verb == "bank":
        handle_bank_view(player)
    elif verb == "deposit":
        args = parts[1:]
        handle_deposit(player, args)
    elif verb == "withdraw":
        args = parts[1:]
        handle_withdraw(player, args)
    elif verb == "wait":
        handle_wait(player)
    elif verb == "craft":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Craft what? (e.g., 'craft goblin leather gloves')")
        else:
            handle_craft_item(player, item_name)
    elif verb == "pickpocket":
        npc_name = " ".join(parts[1:])
        if not npc_name:
            print("Pickpocket whom?")
        else:
            handle_pickpocket(player, npc_name)
    elif verb == "lockpick":
        handle_lockpick(player)
    elif verb == "bribe":
        handle_bribe(player)
    elif verb == "smelt":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Smelt what? (e.g., 'smelt copper bar')")
        else:
            handle_smelt_item(player, item_name)
    elif verb == "mine":
        node_name = " ".join(parts[1:])
        if not node_name:
            print("Mine what?")
        else:
            handle_gather_node(player, "mine", node_name)
    elif verb == "cook":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Cook what? (e.g., 'cook trout')")
        else:
            handle_cook_item(player, item_name)
    elif verb == "open":
        if " ".join(parts[1:]) == "chest":
            handle_open_chest(player)
        else:
            print("Open what?")
    elif verb == "disarm":
        if " ".join(parts[1:]) == "chest":
            handle_disarm_chest(player)
    elif verb == "brew":
        item_name = " ".join(parts[1:])
        if not item_name:
            print("Brew what? (e.g., 'brew greater healing potion')")
        else:
            handle_brew_potion(player, item_name)
    elif verb == "chop":
        node_name = " ".join(parts[1:])
        if not node_name:
            print("Chop what?")
        else:
            handle_gather_node(player, "chop", node_name)
    elif verb == "fish":
        node_name = " ".join(parts[1:])
        if not node_name:
            print("Fish what? (e.g., 'fish spot')")
        else:
            handle_gather_node(player, "fish", node_name)
    elif verb == "bind":
        if " ".join(parts[1:]) == "altar": # Special command for the quest
            handle_cleanse_shrine(player)
            return
        # Split by comma to handle multi-word item names
        words_to_bind_str = " ".join(parts[1:])
        words = [word.strip().title() for word in words_to_bind_str.split(',')]
        handle_bind_words(player, words)
    elif verb == "recipes":
        handle_recipes(player)
    elif verb == "rest":
        handle_rest(player)
    elif verb in ["map", "m"]:
        handle_map(player)
    elif verb == "enter":
        target = " ".join(parts[1:])
        if not target:
            print("Enter what?")
        else:
            handle_enter(player, target)
    elif verb == "cleanse":
        handle_cleanse_shrine(player)
    else:
        print("I don't understand that command.")

def handle_enter(player, target):
    """Handles the player entering a special feature like a dungeon."""
    global current_dungeon
    current_location = get_current_location(player)
    
    if target in current_location.get("features", []):
        if target == "cave":
            print("You gather your courage and step into the deep, dark cave...")
            current_dungeon = dungeon_generator.generate()
            player.location = "room_0_0" # Start at the dungeon entrance
            print_location(player)
        elif target == "inn":
            print("You push open the heavy wooden door and enter The Drunken Griffin.")
            player.location = "drunken_griffin_inn"
            print_location(player)
    else:
        print(f"You don't see a '{target}' to enter here.")

def game_loop(player):
    """The main game loop."""
    print_location(player)
    while True:
        try:
            command = input("> ")
            parse_command(command, player)
        except (EOFError, KeyboardInterrupt):
            print(f"\nGoodbye, {player.name}!")
            sys.exit()

def start_game():
    """Initializes and starts the game."""
    global world, game_state # Declare that we might modify global variables

    print("Welcome to Ashania!")
    if os.path.exists(SAVE_FILENAME):
        print("A saved game was found. (L)oad or (N)ew Game?")
        choice = ""
        while choice not in ['l', 'n']:
            choice = input("> ").lower()
        
        if choice == 'l':
            player, loaded_world, loaded_game_state = load_game()
            if player and loaded_world and loaded_game_state:
                world = loaded_world # Overwrite the template world with the loaded one
                game_state = loaded_game_state
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
    respawn_monsters()
    update_npc_availability()

    player = Player(name=player_name, location=(12, 11)) # Start in Rivenshade
    # Initialize player's factions from the world template
    for key, faction_template in factions.items():
        player.factions[key] = Faction(faction_template.name, faction_template.description)
    # Give the player their default known recipes
    player.known_recipes.extend(default_recipes)
    print(f"\nWelcome, {player.name}! Your journey begins now.")
    print("Commands: look, go, take, drop, craft, recipes, bind, brew, mine, chop, fish, cook, smelt, pickpocket, bribe, lockpick, map, enter, open, disarm, use, attack, inventory, status, quests, talk to, insult, bank, deposit, withdraw, wait, rest, equip, unequip, save, quit, help.")
    game_loop(player)

if __name__ == "__main__":
    start_game()