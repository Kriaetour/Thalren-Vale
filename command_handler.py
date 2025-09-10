import random
import sys

from item import Item, Weapon, Armor, Consumable, Spellbook, RecipeScroll, Key
from npc import QuestGiver, Shopkeeper, Banker, Guard, ProceduralQuestGiver
from monster import Mimic
from world import cooking_recipes, herblore_recipes, smelting_recipes, word_combinations
from ui import print_bordered


def handle_movement(player, direction, context):
    """Handles player movement."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    if player.jail_time_remaining > 0 and current_location.get("name") == "Rivenshade Jail":
        print("The guard outside rattles the bars. 'Not so fast! You're not done serving your time.'")
        return

    if direction in current_location.get("exits", {}):
        destination = current_location["exits"][direction]

        if isinstance(destination, dict) and destination.get('locked'):
            key_id = destination.get('key_id')
            key_in_inventory = next((item for item in player.inventory if isinstance(item, Key) and item.unlocks_what == key_id), None)
            
            if key_in_inventory:
                print(f"You use the {key_in_inventory.name} to unlock the door.")
                player.inventory.remove(key_in_inventory)
                unlocked_destination = destination['destination']
                current_location["exits"][direction] = unlocked_destination
                destination = unlocked_destination
            else:
                print("The door is locked. It requires a specific key.")
                return

        player.location = destination
        context['advance_time']()
        print(f"You go {direction}.")
        context['print_location'](player)
        return

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

        if 0 <= new_row < len(context['world']["grid"]) and 0 <= new_col < len(context['world']["grid"][new_row]):
            player.location = (new_row, new_col)
            context['advance_time']()
            print(f"You go {direction}.")
            context['print_location'](player)
        else:
            print("You can't go that way.")
    else:
        print("You can only move to specific exits from here.")

def handle_take_item(player, item_name, context):
    """Handles the player taking an item."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    items_in_room = current_location.get("items", [])
    
    item_to_take = next((item for item in items_in_room if item_name.lower() in item.name.lower()), None)
    
    if item_to_take:
        player.inventory.append(item_to_take)
        items_in_room.remove(item_to_take)
        print(f"You take the {item_to_take.name}.")
        
        # Dispatch an event for picking up an item
        context['event_manager'].dispatch('on_item_pickup', player=player, item=item_to_take)
    else:
        print(f"You don't see a {item_name} here.")

def handle_drop_item(player, item_name, context):
    """Handles the player dropping an item from their inventory."""
    item_to_drop = next((item for item in player.inventory if item_name.lower() in item.name.lower()), None)

    if not item_to_drop:
        print(f"You don't have a '{item_name}' in your inventory.")
        return

    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    current_location.setdefault("items", []).append(item_to_drop)
    player.inventory.remove(item_to_drop)
    print(f"You drop the {item_to_drop.name} on the ground.")

def handle_inventory(player):
    """Displays the player's inventory."""
    if not player.inventory:
        content = ["Your inventory is empty."]
    else:
        content = [f"- A {item.name}" for item in player.inventory]
    print_bordered("Inventory", content)

def handle_look_at(player, target_name, context):
    """Handles the player looking at an item or detail."""
    item_in_inventory = next((item for item in player.inventory if target_name.lower() in item.name.lower()), None)
    if item_in_inventory:
        print(item_in_inventory.description)
        for quest in player.active_quests:
            quest.update_progress('discover', item_in_inventory.name)
        return

    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    items_in_room = current_location.get("items", [])
    item_in_room = next((item for item in items_in_room if target_name.lower() in item.name.lower()), None)
    if item_in_room:
        print(item_in_room.description)
        for quest in player.active_quests:
            quest.update_progress('discover', item_in_room.name)
        return

    npcs_in_room = current_location.get("npcs", [])
    npc_in_room = next((npc for npc in npcs_in_room if target_name.lower() in npc.name.lower()), None)
    if npc_in_room:
        print(npc_in_room.description)
        return

    monsters_in_room = current_location.get("monsters", [])
    monster_in_room = next((monster for monster in monsters_in_room if target_name.lower() in monster.name.lower()), None)
    if monster_in_room:
        print(monster_in_room.description)
        return

    print(f"You don't see a {target_name} to look at.")

def handle_talk_to(player, npc_name, context):
    """Handles the player talking to an NPC."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    game_state = context['game_state']
    if game_state['time_of_day'] == "Night":
        npcs_in_room = current_location.get("npcs", []) + current_location.get("night_npcs", [])
    else:
        npcs_in_room = current_location.get("npcs", [])

    target_npc = next((npc for npc in npcs_in_room if npc_name.lower() in npc.name.lower()), None)

    if not target_npc:
        print(f"You don't see a '{npc_name}' here to talk to.")
        return
    
    # Dispatch an 'on_talk' event. If a listener handles it, it will return True.
    event_was_handled = context['event_manager'].dispatch('on_talk', player=player, npc=target_npc, context=context)
    if event_was_handled:
        return # A quest hook handled the interaction, so we stop here.

    if target_npc.faction and target_npc.faction in player.factions:
        faction = player.factions[target_npc.faction]
        if faction.get_standing() == "Hated":
            if not isinstance(target_npc, ProceduralQuestGiver):
                print(f'"{target_npc.name} spits on the ground as you approach. \'I have nothing to say to the likes of you.\'"')
                return

    player.last_npc_talked_to = target_npc

    if hasattr(target_npc, 'talk'):
        target_npc.talk(player, game_state)
    else:
        print(f"{target_npc.name} doesn't seem to have much to say.")

def handle_insult(player, npc_name, context):
    """Handles the player insulting an NPC."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    target_npc = next((npc for npc in current_location.get("npcs", []) if npc_name.lower() in npc.name.lower()), None)

    if not target_npc:
        print(f"You shout insults at the air. No one named '{npc_name}' is here.")
        return

    print(f"You shout a rather creative insult at {target_npc.name}.")
    target_npc.record_interaction('insult', context['game_state']['turn_count'])
    target_npc.talk(player, context['game_state'])

def handle_bank_view(player, context):
    """Displays the contents of the player's bank."""
    location = context['get_current_location'](player, context['world'], context['current_dungeon'])
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

def handle_deposit(player, args, context):
    """Handles depositing items or gold into the bank."""
    location = context['get_current_location'](player, context['world'], context['current_dungeon'])
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

def handle_withdraw(player, args, context):
    """Handles withdrawing items or gold from the bank."""
    location = context['get_current_location'](player, context['world'], context['current_dungeon'])
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

def handle_map(player, context):
    """Displays a local area map centered on the player."""
    if not isinstance(player.location, tuple):
        print("You can't see the regional map from here.")
        return

    player_row, player_col = player.location
    map_size = 11
    radius = map_size // 2

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
            elif 0 <= r < len(context['world']["grid"]) and 0 <= c < len(context['world']["grid"][r]):
                loc_type = context['world']["grid"][r][c].get("type", "plains")
                map_char = type_to_char.get(loc_type, "?")
                map_line += f"[{map_char}]"
            else:
                map_line += "   "
        map_lines.append(map_line)
    
    map_lines.append("")
    map_lines.append("--- Legend ---")
    map_lines.append("X: You | T: Town | V: Village | F/f: Forest | c: Camp")
    map_lines.append("~: River | p: Plains | h: Hills | ^: Mountains | M: Mine | R: Ruins | O: Outpost")
    map_lines.append("a: Ash Plains | s: Swamp | S: Special")
    
    print_bordered("Local Area Map", map_lines)

def handle_cleanse_shrine(player, context):
    """Handles the player interacting with the defiled altar."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    quest = next((q for q in player.active_quests if q.name == "The Ruined Shrine"), None)

    if not quest or player.location != quest.objective.get('location'):
        print("There is nothing here to cleanse.")
        return

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

def handle_rest(player, context):
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
    
    context['advance_time'](8)

    print(f"\nYou pay {cost} gold and rest soundly in a warm bed, feeling fully refreshed.")
    context['print_location'](player)

def handle_wait(player, context):
    """Allows the player to wait and pass one turn."""
    print("You wait for a while...")
    context['advance_time']()
    context['print_location'](player)
    if player.jail_time_remaining > 0:
        player.jail_time_remaining -= 1
        if player.jail_time_remaining > 0:
            print(f"You have {player.jail_time_remaining} more turns to wait.")
        else:
            print("\nA guard unlocks the door. 'Your sentence is served. Now get out of here!'")

def handle_bribe(player, context):
    """Handles the player attempting to bribe the guard to get out of jail."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    if not current_location or current_location.get("name") != "Rivenshade Jail" or player.jail_time_remaining <= 0:
        print("There's no one to bribe here.")
        return

    guard = next((npc for npc in current_location.get("npcs", []) if isinstance(npc, Guard)), None)

    if not guard:
        print("There are no guards to bribe here.")
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
            context['print_location'](player)
        else:
            print("You decide to keep your money.")
    else:
        print(f"You don't have enough gold to pay the bribe.")

def handle_lockpick(player, context):
    """Handles the player attempting to pick the lock of their jail cell."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    if not current_location or current_location.get("name") != "Rivenshade Jail" or player.jail_time_remaining <= 0:
        print("There's nothing to lockpick here.")
        return

    lockpick = next((item for item in player.inventory if item.name == "Lockpick"), None)
    if not lockpick:
        print("You need a lockpick to attempt this.")
        return

    success_chance = 0.1 + (player.skills["Lockpicking"].level * 0.05)
    success_chance = min(success_chance, 0.75)

    print("You carefully work the lockpick in the keyhole...")
    context['advance_time']()

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
            content.append("")
    print_bordered("Known Recipes", content)

def handle_cook_item(player, item_name, context):
    """Handles the player attempting to cook an item."""
    recipe_to_cook = next((r for r in cooking_recipes for ingredient in r.ingredients if item_name.lower() in ingredient.lower()), None)
    
    if not recipe_to_cook:
        print(f"You don't know how to cook '{item_name}'.")
        return

    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])

    if recipe_to_cook.station:
        available_stations = current_location.get("stations", [])
        if recipe_to_cook.station not in available_stations:
            print(f"You need to be at a {recipe_to_cook.station} to do that.")
            return

    if recipe_to_cook.skill_req:
        skill_name, required_level = recipe_to_cook.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    inventory_counts = {item.name: player.inventory.count(item) for item in set(player.inventory)}
    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_cook.ingredients.items()):
        print("You don't have the required ingredients.")
        return

    for ingredient, required_count in recipe_to_cook.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    cooked_item = recipe_to_cook.result
    player.inventory.append(cooked_item)
    player.add_skill_xp("Cooking", 20)
    print(f"You successfully cook a {cooked_item.name}!")

def handle_open_chest(player, context):
    """Handles the player opening a treasure chest."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    chest = current_location.get('chest')

    if not chest:
        print("There is no chest here to open.")
        return

    if chest.get('is_mimic'):
        print("The chest opens, revealing rows of sharp teeth! It's a Mimic!")
        mimic = Mimic()
        current_location['monsters'].append(mimic)
        del current_location['chest']
        context['handle_combat'](player, 'mimic')
        return

    if chest.get('trapped') and not chest.get('disarmed'):
        trap_damage = 25
        print(f"As you open the chest, a dart shoots out and hits you for {trap_damage} damage!")
        player.take_damage(trap_damage, bypass_defense=True)
        if not player.is_alive():
            return

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
    
    del current_location['chest']

def handle_disarm_chest(player, context):
    """Handles the player attempting to disarm a trapped chest."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    chest = current_location.get('chest')

    if not chest:
        print("There is no chest here to disarm.")
        return

    if chest.get('is_mimic'):
        print("You search for traps, but the chest suddenly lunges at you!")
        mimic = Mimic()
        current_location['monsters'].append(mimic)
        del current_location['chest']
        context['handle_combat'](player, 'mimic')
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
        del current_location['chest']
        player.add_skill_xp("Thieving", 5)

def handle_brew_potion(player, item_name, context):
    """Handles the player attempting to brew a potion."""
    recipe_to_brew = next((r for r in herblore_recipes if item_name.lower() in r.name.lower()), None)
    
    if not recipe_to_brew:
        print(f"You don't know how to brew '{item_name}'.")
        return

    if recipe_to_brew.skill_req:
        skill_name, required_level = recipe_to_brew.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    inventory_counts = {item.name: player.inventory.count(item) for item in set(player.inventory)}
    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_brew.ingredients.items()):
        print("You don't have the required ingredients.")
        for ing, count in recipe_to_brew.ingredients.items():
            if inventory_counts.get(ing, 0) < count:
                print(f"  (Missing {count - inventory_counts.get(ing, 0)}x {ing})")
        return

    for ingredient, required_count in recipe_to_brew.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    brewed_item = recipe_to_brew.result
    player.inventory.append(brewed_item)
    player.add_skill_xp("Herblore", 40)
    print(f"You carefully combine the ingredients and brew a {brewed_item.name}!")
    context['advance_time']()

def handle_craft_item(player, item_name, context):
    """Handles the player attempting to craft an item."""
    recipe_to_craft = next((r for r in player.known_recipes if item_name.lower() in r.name.lower()), None)

    if not recipe_to_craft:
        print(f"You don't know how to craft '{item_name}'.")
        return

    if recipe_to_craft.station:
        current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
        available_stations = current_location.get("stations", [])
        if recipe_to_craft.station not in available_stations:
            print(f"You need to be at a {recipe_to_craft.station} to craft this item.")
            return

    if recipe_to_craft.skill_req:
        skill_name, required_level = recipe_to_craft.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    inventory_counts = {item.name: player.inventory.count(item) for item in set(player.inventory)}
    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_craft.ingredients.items()):
        print(f"You don't have enough ingredients.")
        return

    print("You use your materials to craft the item...")
    for ingredient, required_count in recipe_to_craft.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    crafted_item = recipe_to_craft.result
    player.inventory.append(crafted_item)
    
    xp_skill = recipe_to_craft.skill_req[0] if recipe_to_craft.skill_req else "Crafting"
    player.add_skill_xp(xp_skill, 25)
    print(f"You successfully crafted a {crafted_item.name}!")
    for quest in player.active_quests:
        quest.update_progress('activity', 'craft')

def handle_bind_words(player, words_to_bind, context):
    """Handles the player attempting to bind words into a spell."""
    if not words_to_bind:
        print("Bind what words? (e.g., 'bind word of fire, word of bolt')")
        return

    if len(words_to_bind) > player.max_words_to_bind:
        print(f"You can only bind up to {player.max_words_to_bind} words at your current skill level.")
        return

    inventory_words = [item for item in player.inventory if isinstance(item, Item) and item.name in words_to_bind]
    if len(inventory_words) < len(words_to_bind):
        print("You don't have all the required words in your inventory.")
        return

    word_names = sorted([word.name for word in inventory_words])
    combination_key = tuple(word_names)

    if combination_key in word_combinations:
        new_ability = word_combinations[combination_key]
        print("The words resonate and surge with power!")
        player.learn_ability(new_ability)
        
        for word_item in inventory_words:
            player.inventory.remove(word_item)
        
        player.add_skill_xp("Wordbinding", 100)
    else:
        print("You chant the words, but they fizzle into nothingness.")
        player.add_skill_xp("Wordbinding", 10)

    context['advance_time']()

def handle_pickpocket(player, npc_name, context):
    """Handles the player attempting to pickpocket an NPC."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
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

    level_diff = player.skills["Thieving"].level - target_npc.level
    success_chance = 0.5 + (level_diff * 0.05)
    success_chance = max(0.1, min(success_chance, 0.9))

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
        player.jail_time_remaining = 5
        context['print_location'](player)
        player.add_skill_xp("Thieving", 5)

    target_npc.has_been_pickpocketed = True

def handle_smelt_item(player, item_name, context):
    """Handles the player attempting to smelt ore into a bar."""
    recipe_to_smelt = next((r for r in smelting_recipes if item_name.lower() in r.name.lower()), None)

    if not recipe_to_smelt:
        print(f"You don't know how to smelt '{item_name}'.")
        return

    if recipe_to_smelt.station:
        current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
        available_stations = current_location.get("stations", [])
        if recipe_to_smelt.station not in available_stations:
            print(f"You need to be at a {recipe_to_smelt.station} to do that.")
            return

    if recipe_to_smelt.skill_req:
        skill_name, required_level = recipe_to_smelt.skill_req
        if player.skills[skill_name].level < required_level:
            print(f"Your {skill_name} level is too low. You need level {required_level}.")
            return

    inventory_counts = {item.name: player.inventory.count(item) for item in set(player.inventory)}
    if not all(inventory_counts.get(ing, 0) >= count for ing, count in recipe_to_smelt.ingredients.items()):
        print("You don't have the required ore.")
        return

    for ingredient, required_count in recipe_to_smelt.ingredients.items():
        for _ in range(required_count):
            item_to_remove = next(item for item in player.inventory if item.name == ingredient)
            player.inventory.remove(item_to_remove)

    smelted_item = recipe_to_smelt.result
    player.inventory.append(smelted_item)
    player.add_skill_xp("Smelting", 15)
    print(f"You smelt the ore and successfully create a {smelted_item.name}!")

def handle_gather_node(player, verb, node_name, context):
    """Handles the player attempting to gather from a resource node (e.g., mine, chop)."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    node_to_gather = next((node for node in current_location.get("nodes", []) if node_name.lower() in node.name.lower() and node.verb == verb), None)

    if not node_to_gather:
        print(f"You can't {verb} that here.")
        return

    if not any(item.name == node_to_gather.required_tool for item in player.inventory):
        print(f"You need a {node_to_gather.required_tool} to do that.")
        return

    skill_name = node_to_gather.skill
    if player.skills[skill_name].level < node_to_gather.required_level:
        print(f"Your {skill_name} level is too low. You need level {node_to_gather.required_level}.")
        return

    yielded_item = node_to_gather.item_yield
    player.inventory.append(yielded_item)
    player.add_skill_xp(skill_name, node_to_gather.xp_yield)
    print(f"You successfully get some {yielded_item.name}.")
    if verb == 'fish':
        for quest in player.active_quests:
            quest.update_progress('activity', 'fish')
    
    context['advance_time']()

def handle_accept_quest(player):
    """Handles the player accepting a quest."""
    if not player.last_npc_talked_to:
        print("You need to talk to someone to accept their quest first.")
        return

    quest_giver = player.last_npc_talked_to
    
    if quest_giver:
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
            player.inventory.append(player.weapon)
        player.weapon = item_to_equip
        player.inventory.remove(item_to_equip)
        print(f"You equip the {item_to_equip.name}.")
    elif isinstance(item_to_equip, Armor):
        if player.armor:
            player.inventory.append(player.armor)
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

def handle_enter(player, target, context):
    """Handles the player entering a special feature like a dungeon."""
    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    
    if target in current_location.get("features", []):
        if target == "cave":
            print("You gather your courage and step into the deep, dark cave...")
            context['set_dungeon'](context['dungeon_generator'].generate())
            player.location = "f0_room_0_0"
            context['print_location'](player)
        elif target == "inn":
            print("You push open the heavy wooden door and enter The Drunken Griffin.")
            player.location = "drunken_griffin_inn"
            context['print_location'](player)
    else:
        print(f"You don't see a '{target}' to enter here.")

def handle_sabotage(player, target_name, context):
    """Handles the player attempting to sabotage an object for a quest."""
    sabotage_quest = next((q for q in player.active_quests if q.objective.get('type') == 'sabotage'), None)

    if not sabotage_quest:
        print("You have no reason to sabotage anything right now.")
        return

    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
    quest_objective = sabotage_quest.objective

    if current_location.get('name') != quest_objective.get('location'):
        print("This isn't the right place to cause trouble.")
        return

    if target_name.lower() not in quest_objective.get('target').lower():
        print(f"You see no reason to sabotage the {target_name}.")
        return

    print(f"With a bit of clever work, you successfully sabotage the {target_name}!")
    sabotage_quest.update_progress('sabotage', target_name)
    
    # Optionally, remove the station from the location to reflect the sabotage
    if target_name in current_location.get('stations', []):
        current_location['stations'].remove(target_name)