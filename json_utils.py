import json
from player import Player
from npc import NPC, Shopkeeper, QuestGiver, Banker, Guard, ProceduralQuestGiver, Innkeeper
from item import Item, Weapon, Armor, Consumable, Spellbook, RecipeScroll, Key, Word
from monster import Monster, Goblin, Orc, Slime, Skeleton, Zombie, DireWolf, Troll, Specter, GiantSpider, Bandit, RiverSerpent, WildBoar, AshboundCultist, FireSpirit, GiantEagle, SpectralWolf, Thalraxos, Mimic, ShadowWolf, ShadowCultist, CultFanatic, CultistBandit, BanditLeader
from quest import Quest
from skill import Skill
from faction import Faction
from ability import Ability
from recipe import Recipe
from resource_node import ResourceNode


class GameEncoder(json.JSONEncoder):
    """
    A custom JSON encoder for game objects. It converts Python objects
    into dictionaries for JSON serialization.
    """
    def default(self, obj):
        if isinstance(obj, set):
            return list(obj) # Convert sets to lists
        # ResourceNodes are static definitions and should not be saved.
        if isinstance(obj, ResourceNode):
            return None # This will result in 'null' in the JSON, which is fine.
        if isinstance(obj, (Player, NPC, Monster, Item, Quest, Skill, Faction, Ability, Recipe)):
            # Add a __class__ key to identify the object type during decoding
            d = {'__class__': obj.__class__.__name__}
            # For Quests and Items, which are defined centrally, we only need to save
            # their unique name. The stateful part (progress) is handled separately.
            if isinstance(obj, (Quest, Item, Recipe, Ability)):
                 d['name'] = obj.name
                 return d
            # For other objects, we serialize their full state
            obj_dict = obj.__dict__.copy()
            # Exclude non-serializable utility objects
            if isinstance(obj, ProceduralQuestGiver): # Exclude all blueprint/generator attributes
                obj_dict.pop('quest_generator', None)
                obj_dict.pop('templates', None)
                obj_dict.pop('reputation_quests', None)
            # For all NPCs, we don't need to save the schedule, as it's part of their definition
            if isinstance(obj, NPC):
                obj_dict.pop('schedule', None)
            d.update(obj_dict)
            return d
        return super().default(obj)

def decode_game_object(dct):
    """
    A custom JSON decoder hook. It checks for the '__class__' key to
    reconstruct the original Python objects from dictionaries.
    """
    if '__class__' in dct:
        class_name = dct.pop('__class__')
        
        # These classes are templates; we just need their name to look them up later.
        # The actual object will be retrieved from the master world data.
        if class_name in ['Quest', 'Item', 'Weapon', 'Armor', 'Consumable', 'Spellbook', 'RecipeScroll', 'Key', 'Recipe', 'Ability', 'Word']:
            return dct['name'] # Return the name as a placeholder

        # For stateful objects, we reconstruct them.
        cls = globals().get(class_name)
        if cls:
            # This is a simplified reconstruction. It assumes the constructor
            # can be called with the dictionary keys as arguments.
            # A more robust implementation might have `from_dict` classmethods.
            obj = cls.__new__(cls) # Create a new instance without calling __init__
            
            # Re-link definitional attributes on load
            if class_name == 'ProceduralQuestGiver':
                # Find the original NPC object in the world definition to get its blueprints
                from world import world as world_definition
                original_npc = None
                for row in world_definition['grid']:
                    for loc in row:
                        for npc_template in loc.get('npcs', []):
                            if npc_template.name == dct.get('name'):
                                original_npc = npc_template
                                break
                if original_npc:
                    obj.quest_generator = original_npc.quest_generator
                    obj.templates = original_npc.templates
                    obj.reputation_quests = original_npc.reputation_quests
                    obj.schedule = original_npc.schedule

            # Re-convert list back to set for specific attributes
            if 'skills_affected_this_turn' in dct:
                dct['skills_affected_this_turn'] = set(dct['skills_affected_this_turn'])
            obj.__dict__.update(dct)
            return obj
    return dct
