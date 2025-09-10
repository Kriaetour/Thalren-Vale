import random
from quest import Quest

class QuestTemplate:
    """A blueprint for generating procedural quests."""
    def __init__(self, name_format, description_format, objective_type, target_category, count=1, reward_gold=50, reward_xp=100, xp_skill="Combat", faction_reward=None):
        self.name_format = name_format
        self.description_format = description_format
        self.objective_type = objective_type
        self.target_category = target_category # e.g., "bandit", "wildlife"
        self.count = count
        self.reward_gold = reward_gold
        self.reward_xp = reward_xp
        self.xp_skill = xp_skill
        self.faction_reward = faction_reward or {}

class QuestGenerator:
    """Generates new quests from templates based on the world state."""
    def __init__(self, world, monster_mapping):
        self.world = world
        self.monster_mapping = monster_mapping

    def generate_quest(self, template, player_location):
        """
        Generates a specific Quest instance from a template.
        For now, we'll focus on 'kill' quests.
        """
        if template.objective_type == 'kill': # --- KILL QUEST ---
            # Find a suitable monster and location near the player
            # This is a simple implementation; a real one might check distance
            
            # Find all monsters matching the target category
            possible_targets = []
            for monster_key, monster_class in self.monster_mapping.items():
                # A simple way to categorize monsters
                if template.target_category == "any" or template.target_category in monster_key:
                    possible_targets.append(monster_class)
            
            if not possible_targets:
                return None # Cannot generate a quest for this category

            target_monster_class = random.choice(possible_targets)
            target_monster_instance = target_monster_class()
            target_name = target_monster_instance.name

            # Find a location where this monster spawns
            possible_locations = []
            for r_idx, row in enumerate(self.world["grid"]):
                for c_idx, loc in enumerate(row):
                    if target_monster_instance.name.lower() in [m.lower() for m in loc.get("enemies", [])]:
                        possible_locations.append(loc["name"])
            
            location_name = random.choice(possible_locations) if possible_locations else "the nearby area"

            # Format the quest details
            quest_name = template.name_format.format(monster_name=target_name)
            quest_description = template.description_format.format(monster_name=target_name, location_name=location_name, count=template.count)
            
            objective = {'type': 'kill', 'target': target_name, 'count': template.count}
            reward = {'gold': template.reward_gold, 'xp': {template.xp_skill: template.reward_xp}}

            # Add faction reward if it exists
            if template.faction_reward:
                reward['faction'] = template.faction_reward

            return Quest(quest_name, quest_description, objective, reward)

        elif template.objective_type == 'sabotage': # --- SABOTAGE QUEST ---
            # Find a location that has the target station
            possible_locations = []
            for r_idx, row in enumerate(self.world["grid"]):
                for c_idx, loc in enumerate(row):
                    if template.target_category in loc.get("stations", []):
                        possible_locations.append(loc)
            
            if not possible_locations:
                return None # No suitable location found

            target_location = random.choice(possible_locations)
            quest_name = template.name_format.format(target=template.target_category, location_name=target_location['name'])
            quest_description = template.description_format.format(target=template.target_category, location_name=target_location['name'])
            objective = {'type': 'sabotage', 'target': template.target_category, 'location': target_location['name']}
            reward = {'gold': template.reward_gold, 'xp': {template.xp_skill: template.reward_xp}, 'faction': template.faction_reward}
            return Quest(quest_name, quest_description, objective, reward)

        return None # Return None for unsupported quest types for now