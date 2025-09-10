class Quest:
    """
    Represents a quest in the game.
    """
    def __init__(self, name, description, objective, reward=None, reward_choice=None, prerequisites=None):
        """
        Initializes a Quest object.
        :param name: The name of the quest.
        :param description: A detailed description of the quest.
        :param objective: A dictionary defining the quest goal. e.g., {'type': 'kill', 'target': 'Goblin', 'count': 3}
        :param reward: A dictionary defining the quest reward. e.g., {'gold': 100, 'xp': 50}
        :param reward_choice: A list of dictionaries, each representing a reward option.
        :param prerequisites: A list of quest names that must be completed first.
        """
        self.name = name
        self.description = description
        self.objective = objective
        self.reward = reward
        self.reward_choice = reward_choice
        self.prerequisites = prerequisites or []
        self.is_completed = False
        if self.objective.get('type') == 'activity':
            self.progress = {activity: 0 for activity in self.objective.get('activities', {})}
        else:
            self.progress = 0

    def check_completion(self, player):
        """
        Checks if the quest has been completed based on its criteria and current progress.
        :param player: The player object, needed for checking inventory.
        """
        if self.is_completed:
            return True

        obj_type = self.objective.get('type')
        if obj_type == 'kill':
            if self.progress >= self.objective.get('count', 1):
                return True
        elif obj_type == 'fetch':
            item_name = self.objective.get('target')
            required_count = self.objective.get('count', 1)
            current_count = sum(1 for item in player.inventory if item.name.lower() == item_name.lower())
            if current_count >= required_count:
                return True
        elif obj_type == 'activity':
            required_activities = self.objective.get('activities', {})
            return all(self.progress.get(act, 0) >= count for act, count in required_activities.items())
        elif obj_type == 'discover':
            if self.progress >= 1:
                return True
        elif obj_type == 'decision':
            # This type of quest is completed simply by making a choice with the NPC.
            return True
        elif obj_type == 'ambush':
            # This quest is completed once the ambush is defeated.
            return self.progress >= self.objective.get('count', 1)
        elif obj_type == 'explore':
            if player.location == self.objective.get('target'):
                return True
        
        return False

    def get_progress_string(self):
        """Returns a formatted string of the quest progress."""
        if self.objective.get('type') == 'kill':
            return f"({self.progress}/{self.objective.get('count', 1)})"
        elif self.objective.get('type') == 'activity':
            parts = []
            for act, count in self.objective.get('activities', {}).items():
                parts.append(f"{act.capitalize()}: {self.progress.get(act, 0)}/{count}")
            return f"({', '.join(parts)})"
        elif self.objective.get('type') == 'ambush':
            parts = []
            for act, count in self.objective.get('activities', {}).items():
                parts.append(f"{act.capitalize()}: {self.progress.get(act, 0)}/{count}")
            return f"({', '.join(parts)})"
        return ""

    def update_progress(self, objective_type, target_name):
        """
        Updates the progress of the quest.
        :param objective_type: The type of objective (e.g., "kill", "activity").
        :param target_name: The name of the target (e.g., "goblin") or activity (e.g., "craft").
        """
        if self.is_completed:
            return

        current_obj_type = self.objective.get('type')
        if current_obj_type != objective_type:
            return

        if current_obj_type == 'kill':
            if self.objective.get('target').lower() == target_name.lower():
                self.progress += 1
                print(f"[Quest Update: {self.name} {self.get_progress_string()}]")
        elif current_obj_type == 'activity':
            activity_name = target_name
            if activity_name in self.progress:
                required_count = self.objective['activities'][activity_name]
                if self.progress[activity_name] < required_count:
                    self.progress[activity_name] += 1
                    print(f"[Quest Update: {self.name} {self.get_progress_string()}]")
        elif current_obj_type == 'discover':
            if self.objective.get('target').lower() in target_name.lower():
                self.progress = 1
                print(f"[Quest Update: {self.name} {self.get_progress_string()}]")

    def complete(self, player, chosen_reward_option=None):
        """Gives the player the quest reward and updates their quest log."""
        print(f"Quest Completed: {self.name}!")
        
        reward = None
        if chosen_reward_option:
            reward = chosen_reward_option.get('reward')
        else:
            reward = self.reward

        if not reward:
            print("There was no immediate reward for this quest.")
        else:
            gold_reward = reward.get('gold', 0)
            if gold_reward > 0:
                player.money += gold_reward
                print(f"You receive {gold_reward} gold.")
            
            xp_rewards = reward.get('xp', {})
            for skill_name, amount in xp_rewards.items():
                player.add_skill_xp(skill_name, amount)

            faction_rewards = reward.get('faction', {})
            for faction_name, amount in faction_rewards.items():
                player.change_faction_rep(faction_name, amount)
            
            item_reward = reward.get('item')
            if item_reward:
                player.inventory.append(item_reward)
                print(f"You receive a {item_reward.name}.")

        # Handle removing fetch quest items
        if self.objective.get('type') == 'fetch':
            # Default to removing the item unless specified otherwise in the chosen reward
            should_remove = chosen_reward_option.get('remove_item', True) if chosen_reward_option else True
            if should_remove:
                item_name = self.objective.get('target')
                required_count = self.objective.get('count', 1)
                for _ in range(required_count):
                    item_to_remove = next((item for item in player.inventory if item.name.lower() == item_name.lower()), None)
                    if item_to_remove:
                        player.inventory.remove(item_to_remove)

        self.is_completed = True
        if self in player.active_quests:
            player.active_quests.remove(self)
        player.completed_quests.append(self)