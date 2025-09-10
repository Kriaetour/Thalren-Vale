import random
from dialogue import DIALOGUE_TEMPLATES

class NPC:
    """
    Base class for Non-Player Characters in the game.
    """
    def __init__(self, name, description, dialogue="...", personality=None, faction=None):
        self.name = name
        self.description = description
        self.dialogue = dialogue
        self.is_available = True
        self.level = 1
        self.pickpocket_loot = []
        self.has_been_pickpocketed = False
        self.personality = personality or {'friendliness': 5, 'grumpiness': 3, 'talkativeness': 5}
        self.memory = []
        self.schedule = None # A sorted list of (time, location_key) tuples
        self.faction = faction
        self.dialogue_night = None # Default to no special night dialogue
        self.current_location_key = None

    def record_interaction(self, interaction_type, turn_count, details=None):
        """Records an interaction in the NPC's memory."""
        self.memory.append({'type': interaction_type, 'turn': turn_count, 'details': details})

    def get_relationship_score(self):
        """Calculates a relationship score based on past interactions."""
        score = 0
        for event in self.memory:
            if event['type'] == 'completed_quest':
                score += 10
            elif event['type'] == 'insult':
                score -= 15
            elif event['type'] == 'trade':
                score += 2
        return score

    def generate_greeting(self, player):
        """Generates a greeting based on personality and memory."""
        # Start with personal relationship score
        relationship_score = self.get_relationship_score()

        # Factor in faction reputation
        if self.faction and self.faction in player.factions:
            relationship_score += player.factions[self.faction].reputation

        if relationship_score < -20:
            mood = 'greeting_angry'
        elif relationship_score > 10:
            mood = 'greeting_grateful'
        elif self.personality.get('grumpiness', 0) > 7:
            mood = 'greeting_grumpy'
        elif self.personality.get('friendliness', 0) > 7:
            mood = 'greeting_friendly'
        else:
            mood = 'greeting_neutral'
        
        template = random.choice(DIALOGUE_TEMPLATES[mood])
        return template.format(player_name=player.name)

class Shopkeeper(NPC):
    """
    A shopkeeper NPC who can sell items.
    """
    def __init__(self, name, description, dialogue="Welcome to my shop!", personality=None, faction=None):
        super().__init__(name, description, dialogue, personality, faction)
        self.inventory = [] # Items the shopkeeper has for sale

    def add_item(self, item):
        """Adds an item to the shopkeeper's inventory."""
        self.inventory.append(item)

    def talk(self, player, game_state):
        """Handles dialogue with a shopkeeper."""
        if not self.is_available:
            print(f'"{self.name} has closed up for the night."')
            return
        print(f'"{self.generate_greeting(player)}"')
        self.list_items()

    def list_items(self):
        """Lists items available for sale."""
        if not self.inventory:
            print(f"{self.name}: I have nothing for sale at the moment.")
            return
        print(f"{self.name}: I have these items for sale:")
        for i, item in enumerate(self.inventory):
            print(f"  {i+1}. {item.name} - {item.value} gold")
        print("Type 'buy <item>' or 'sell <item>' to trade.")

    def buy_item(self, player, item_identifier, game_state):
        """Handles the player buying an item from the shopkeeper."""
        if not self.is_available:
            print(f'"{self.name} has closed up for the night."')
            return

        item_to_buy = None
        try:
            # Try to get item by number
            item_index = int(item_identifier) - 1
            if 0 <= item_index < len(self.inventory):
                item_to_buy = self.inventory[item_index]
        except ValueError:
            # If not a number, try to get by name
            for item in self.inventory:
                if item.name.lower() == item_identifier.lower():
                    item_to_buy = item
                    break

        if not item_to_buy:
            print(f"{self.name}: I don't have '{item_identifier}' for sale.")
            return

        if player.money >= item_to_buy.value:
            player.money -= item_to_buy.value
            player.inventory.append(item_to_buy)
            self.inventory.remove(item_to_buy) # Remove from shop's inventory
            self.record_interaction('trade', game_state['turn_count'], {'item': item_to_buy.name})
            print(f"You bought the {item_to_buy.name} for {item_to_buy.value} gold.")
        else:
            print(f"{self.name}: You don't have enough gold for that. You need {item_to_buy.value} gold.")

    def sell_item(self, player, item_identifier, game_state):
        """Handles the player selling an item to the shopkeeper."""
        if not self.is_available:
            print(f'"{self.name} has closed up for the night."')
            return

        item_to_sell = next((item for item in player.inventory if item_identifier.lower() in item.name.lower()), None)

        if not item_to_sell:
            print(f"You don't have a '{item_identifier}' to sell.")
            return

        if item_to_sell.quest_item:
            print(f"You cannot sell the {item_to_sell.name}; it seems important.")
            return

        sell_price = item_to_sell.value // 2  # Shopkeepers buy for half price
        player.money += sell_price
        player.inventory.remove(item_to_sell)
        self.add_item(item_to_sell) # Add to shop's inventory
        print(f"You sell the {item_to_sell.name} for {sell_price} gold.")
class Banker(NPC):
    """
    A banker NPC who can store items and gold for the player.
    """
    def __init__(self, name, description, dialogue="...", personality=None, faction=None):
        super().__init__(name, description, dialogue, personality, faction)

    def talk(self, player, game_state):
        """Handles dialogue with a banker."""
        if not self.is_available:
            print(f'"{self.name} has closed up for the night."')
            return
        print(f'"{self.generate_greeting(player)}"')

class Innkeeper(NPC):
    """
    An innkeeper NPC who offers a place to rest.
    """
    def __init__(self, name, description, dialogue, personality=None, faction=None):
        super().__init__(name, description, dialogue, personality, faction)
        self.rest_cost = 10

    def talk(self, player, game_state):
        """Handles dialogue with an innkeeper."""
        print(f'"{self.generate_greeting(player)}"')
        print(f'"{self.dialogue}"')
        print(f"(You can `rest` here for {self.rest_cost} gold to fully recover.)")

class Guard(NPC):
    """
    A guard NPC, typically found in jails or important locations.
    """
    def __init__(self, name, description, dialogue, personality=None, faction=None):
        super().__init__(name, description, dialogue, personality, faction)
        self.is_available = True # Guards are always "available"

    def talk(self, player, game_state):
        """Handles dialogue with a guard."""
        if player.jail_time_remaining > 0:
            print(f'"{self.name} scoffs. \'Serve your time, criminal. Or... you could make it worth my while to look the other way.\'"')
        else:
            print(f'"{self.generate_greeting(player)}"')

class QuestGiver(NPC):
    """
    An NPC who can give quests to the player.
    """
    def __init__(self, name, description, quests, dialogue, personality=None, faction=None, dialogue_night=None):
        super().__init__(name, description, dialogue, personality, faction)
        self.quests = quests if isinstance(quests, list) else [quests]
        self.dialogue_night = dialogue_night

    def talk(self, player, game_state):
        """Handles dialogue with a quest-giving NPC."""
        print(f'"{self.generate_greeting(player)}"')

        # Find the current relevant quest (either active or the next one to be offered)
        current_quest = None
        for quest in self.quests:
            if quest in player.active_quests:
                current_quest = quest
                break
        
        if not current_quest:
            for quest in self.quests:
                if not quest.is_completed and quest not in player.completed_quests:
                    prereqs_met = all(p in [q.name for q in player.completed_quests] for p in quest.prerequisites)
                    if prereqs_met:
                        current_quest = quest
                        break

        if not current_quest:
            print(f'"{self.name}: It is good to see you, but I have no tasks for you right now."')
            return

        if current_quest in player.active_quests:
            if current_quest.check_completion(player):
                # Handle quests with a choice of rewards
                if current_quest.reward_choice:
                    print(f'"{self.name}: You\'ve done it! Amazing work. For your reward, you can have one of the following:"')
                    for i, choice in enumerate(current_quest.reward_choice):
                        print(f"  {i+1}. {choice['description']}")
                    
                    while True:
                        try:
                            choice_input = input("Choose your reward (number): > ")
                            if not choice_input: continue
                            choice_index = int(choice_input) - 1
                            if 0 <= choice_index < len(current_quest.reward_choice):
                                chosen_reward_option = current_quest.reward_choice[choice_index]
                                self.record_interaction('completed_quest', game_state['turn_count'], {'quest_name': current_quest.name})
                                current_quest.complete(player, chosen_reward_option=chosen_reward_option)
                                break
                            else:
                                print("Invalid choice.")
                        except ValueError:
                            print("Please enter a number.")
                else: # Standard quest completion
                    print(f'"{self.name}: You\'ve done it! Amazing work. Here is your reward."')
                    self.record_interaction('completed_quest', game_state['turn_count'], {'quest_name': current_quest.name})
                    current_quest.complete(player)
            else:
                progress = current_quest.get_progress_string()
                print(f'"{self.name}: How goes the task? I see you still have more to do. {progress}"')
        else: # Quest has not been accepted yet
            if current_quest:
                # Use night dialogue if available
                if game_state['time_of_day'] == 'Night' and self.dialogue_night:
                    print(f'"{self.dialogue_night}"')
                else:
                    print(f'"{self.dialogue}"')
                print(f"{self.name} wants you to complete the quest: '{current_quest.name}'.")
                print(f"Description: {current_quest.description}")
                print("Do you 'accept' or 'decline'?")

class ProceduralQuestGiver(QuestGiver):
    """
    An NPC who can generate quests for the player from a set of templates.
    """
    def __init__(self, name, description, dialogue, quest_generator, templates, quests=None, personality=None, faction=None, reputation_quests=None, dialogue_night=None):
        super().__init__(name, description, quests or [], dialogue, personality, faction, dialogue_night)
        self.quest_generator = quest_generator
        self.templates = templates
        self.offered_quest = None
        self.reputation_quests = reputation_quests or {}

    def talk(self, player, game_state):
        """Handles dialogue and quest generation."""
        # First, try to handle any static, story-based quests.
        # We can check if a static quest was handled by seeing if the method returns something.
        # A more robust way would be to have the talk method return a status. For now, we check the output.
        
        # Temporarily redirect stdout to capture the output of the parent's talk method
        import io
        from contextlib import redirect_stdout
        f = io.StringIO()
        with redirect_stdout(f):
            super().talk(player, game_state)
        output = f.getvalue()

        # If the parent's talk method did something other than say "no tasks", print its output and stop.
        if "I have no tasks for you right now" not in output:
            print(output.strip())
            return

        # If there were no static quests, proceed with procedural quest logic.
        # The greeting is already printed by the parent call, so we skip it here.
        
        # Check if the player is already on an offered procedural quest
        if self.offered_quest and self.offered_quest in player.active_quests:
            if self.offered_quest.check_completion(player):
                print(f'\n"{self.name}: You\'ve done it! Amazing work. Here is your reward."')
                self.record_interaction('completed_quest', game_state['turn_count'], {'quest_name': self.offered_quest.name})
                self.offered_quest.complete(player)
                self.offered_quest = None # Clear the offered quest
            else:
                print(f'\n"{self.name}: You\'re still working on that task, I see. Good luck!"')
            return

        # Generate a new procedural quest if one isn't currently offered
        is_hated = self.faction and self.faction in player.factions and player.factions[self.faction].get_standing() == "Hated"
        template = self.reputation_quests.get(self.faction) if is_hated else random.choice(self.templates)
        
        if template:
            self.offered_quest = self.quest_generator.generate_quest(template, player.location)
            if self.offered_quest:
                dialogue = f'"{self.name} eyes you with distrust. \'Your reputation precedes you. If you wish to be welcome in these parts again, you must prove your worth.\'"' if is_hated else f'"{self.dialogue}"'
                print(f"\n{dialogue}")
                print(f"{self.name} has a task for you: '{self.offered_quest.name}'.")
                print(f"Description: {self.offered_quest.description}")
                print("Do you 'accept' or 'decline'?")