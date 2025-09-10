from event_manager import event_manager

def handle_securing_the_road_talk(player, npc, context):
    """Handles the special dialogue for the 'Securing the Road' quest."""
    quest = next((q for q in player.active_quests if q.name == "Securing the Road"), None)
    if not quest or npc.name != "Bandit Lookout" or player.location != quest.objective.get('location'):
        return None # This listener doesn't handle this interaction

    print(f'"{npc.name}: Halt! This road is closed by order of the Red Fangs. You can pay the toll, or you can turn back... or you can die."')
    print("What will you do?")
    for i, choice in enumerate(quest.reward_choice):
        print(f"  {i+1}. {choice['description']}")
    
    while True:
        try:
            choice_input = input("Choose your action (number): > ")
            if not choice_input: continue
            choice_index = int(choice_input) - 1
            if 0 <= choice_index < len(quest.reward_choice):
                chosen_option = quest.reward_choice[choice_index]
                if choice_index == 0:
                    print("\nYou draw your weapon. The lookout shouts a warning, and the bandits prepare for a fight!")
                    quest.complete(player, chosen_reward_option=chosen_option)
                elif choice_index == 1:
                    toll = 100
                    if player.money >= toll:
                        player.money -= toll
                        print(f"\nYou hand over {toll} gold. The lookout nods. 'Wise choice. The road is yours... for now.'")
                        current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
                        current_location.get("monsters", []).clear()
                        current_location.get("npcs", []).remove(npc)
                        quest.complete(player, chosen_reward_option=chosen_option)
                    else:
                        print(f"You don't have the {toll} gold they demand!")
                elif choice_index == 2:
                    print("\nYou lower your voice. 'The Master is displeased with this unsanctioned toll. You are to withdraw.'")
                    print("The lookout's eyes widen in fear. 'Apologies! We will leave at once!'")
                    current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
                    current_location.get("monsters", []).clear()
                    current_location.get("npcs", []).remove(npc)
                    quest.complete(player, chosen_reward_option=chosen_option)
                return True # Event was handled
        except (ValueError, IndexError):
            print("Invalid choice.")
    return True # Should be unreachable, but good practice

def handle_whispers_ledger_talk(player, npc, context):
    """Handles turning in the ledger for the 'Whispers Beneath the Ledger' quest."""
    quest = next((q for q in player.active_quests if q.name == "Whispers Beneath the Ledger"), None)
    if not quest or not any(item.name == "Suspicious Ledger" for item in player.inventory):
        return None

    turn_in_options = []
    if npc.name == "Captain Valerius":
        turn_in_options.append(quest.reward_choice[0])
    elif npc.name == "Shady Figure":
        turn_in_options.append(quest.reward_choice[1])

    if not turn_in_options:
        return None

    print(f"'I have some... sensitive information that might interest you.' You show {npc.name} the ledger.")
    print("Their eyes widen as they scan the pages. 'This is... valuable. What do you want for it?'")
    print("What will you do?")
    
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
                quest.complete(player, chosen_reward_option=chosen_option)
                ledger_item = next((item for item in player.inventory if item.name == "Suspicious Ledger"), None)
                if ledger_item:
                    player.inventory.remove(ledger_item)
                return True # Event handled
            elif choice_index == len(turn_in_options):
                print("'I'll hold onto this for now.' You put the ledger away.")
                return True # Event handled
            else:
                print("Invalid choice.")
        except (ValueError, IndexError):
            print("Please enter a number.")
    return True

def handle_trade_of_shadows_talk(player, npc, context):
    """Handles the choice for the 'A Trade of Shadows' quest."""
    quest = next((q for q in player.active_quests if q.name == "A Trade of Shadows"), None)
    if not quest or player.location != quest.objective.get('location'):
        return None

    if npc.name == "Caravan Guard Captain":
        print(f'"{npc.name}: You\'re here. Good. The Whispered Hand has been sniffing around. Are you with us, or are you going to be a problem?"')
    elif npc.name == "Whispered Hand Agent":
        print(f'"{npc.name}: The Guild grows too bold. This caravan is an opportunity. A smart adventurer knows which side butters their bread. What\'s it going to be?"')
    else:
        return None # Not the right NPC for this interaction

    print("The choice is yours. What will you do?")
    for i, choice in enumerate(quest.reward_choice):
        print(f"  {i+1}. {choice['description']}")

    while True:
        try:
            choice_input = input("Choose your action (number): > ")
            if not choice_input: continue
            choice_index = int(choice_input) - 1
            if 0 <= choice_index < len(quest.reward_choice):
                chosen_option = quest.reward_choice[choice_index]
                print("\nYou've made your choice. The caravan moves on, its fate sealed by your decision.")
                quest.complete(player, chosen_reward_option=chosen_option)
                current_location = context['get_current_location'](player, context['world'], context['current_dungeon'])
                current_location["npcs"] = [n for n in current_location.get("npcs", []) if n.name not in ["Caravan Guard Captain", "Whispered Hand Agent"]]
                return True # Event handled
        except (ValueError, IndexError):
            print("Invalid choice.")
    return True

def handle_merchants_plea_talk(player, npc, context):
    """Handles the choice for 'The Merchant's Plea' quest."""
    quest = next((q for q in player.active_quests if q.name == "The Merchant's Plea"), None)
    if not quest or npc.name != "Village Elder Aelric":
        return None

    print(f'"{npc.name}: The situation has become untenable. The Guild demands our support, the Hunters threaten to abandon us, and this talk of a cult grows louder. The Vale needs a clear path forward. What do you advise?"')
    print("The fate of the Vale rests on your counsel. What will you do?")
    for i, choice in enumerate(quest.reward_choice):
        print(f"  {i+1}. {choice['description']}")

    while True:
        try:
            choice_input = input("Choose your action (number): > ")
            if not choice_input: continue
            choice_index = int(choice_input) - 1
            if 0 <= choice_index < len(quest.reward_choice):
                chosen_option = quest.reward_choice[choice_index]
                print("\nYou have given your counsel. The Elder nods grimly, the path now set. The consequences of this day will be felt for a long time to come.")
                quest.complete(player, chosen_reward_option=chosen_option)
                return True # Event handled
            else:
                print("Invalid choice.")
        except (ValueError, IndexError):
            print("Please enter a number.")
    return True


def register_quest_listeners():
    """Registers all quest-related event listeners."""
    event_manager.register_listener('on_talk', handle_securing_the_road_talk)
    event_manager.register_listener('on_talk', handle_whispers_ledger_talk)
    event_manager.register_listener('on_talk', handle_trade_of_shadows_talk)
    event_manager.register_listener('on_talk', handle_merchants_plea_talk)