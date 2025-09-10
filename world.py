from item import Item, Weapon, Armor, Consumable, Spellbook, Word, RecipeScroll, healing_potion, mana_potion
from monster import *
from npc import NPC, Shopkeeper, QuestGiver, Banker, Guard, ProceduralQuestGiver, Innkeeper
from quest import Quest
from ability import heal_light, Ability
from recipe import Recipe
from faction import Faction
from resource_node import ResourceNode
from world_data import thalren_vale_map_25x25
from quest_generator import QuestTemplate, QuestGenerator

# --- Items ---
iron_sword = Weapon("Iron Sword", "A well-crafted sword made of solid iron.", value=100, attack_bonus=10)
iron_armor = Armor("Iron Armor", "Sturdy armor made from interlocking iron plates.", value=120, defense_bonus=10)
mystical_herb = Item("Mystical Herb", "A rare herb that glows with a faint, silvery light.", value=50)
greater_healing_potion = Consumable("Greater Healing Potion", "A potent brew that restores a large amount of health.", value=100, effect="heal", amount=75)
pickaxe = Item("Pickaxe", "A sturdy pickaxe for mining.", value=25)
axe = Item("Axe", "A simple axe for chopping wood.", value=20)
fishing_rod = Item("Fishing Rod", "A simple rod for catching fish.", value=15)
raw_trout = Item("Raw Trout", "A fresh, uncooked trout.", value=4)
logs = Item("Logs", "A bundle of sturdy logs.", value=2)
iron_ore = Item("Iron Ore", "A chunk of grey, unrefined iron.", value=5)
iron_bar = Item("Iron Bar", "A bar of refined iron.", value=15)
cooked_trout = Consumable("Cooked Trout", "A perfectly cooked trout. Restores a good amount of health.", value=10, effect="heal", amount=40)
stolen_goods = Item("Stolen Goods", "A crate of goods marked with the emblem of a local trader.", value=0, quest_item=True)
silver_locket = Item("Silver Locket", "A beautiful silver locket, clearly cherished by its owner.", value=50, quest_item=True)
cracked_runic_tablet = Word("Cracked Runic Tablet", "A stone tablet fragment covered in strange, unsettling symbols. It hums with a faint, corrupted energy.", value=0, quest_item=True)
torn_cultist_robe = Item("Torn Cultist Robe", "A scrap of dark cloth, torn from a robe. It bears a strange, unsettling symbol.", value=0, quest_item=True)
protective_charm = Item("Protective Charm", "A small, intricately carved wooden charm that radiates a faint, warm energy.", value=0, quest_item=True)
leather = Item("Leather", "A piece of cured animal hide.", value=10)
thread = Item("Thread", "A spool of sturdy thread.", value=2)
sturdy_leather_gloves = Armor("Sturdy Leather Gloves", "Well-made gloves that offer decent protection.", value=50, defense_bonus=2)
fine_leather_boots = Armor("Fine Leather Boots", "Boots made of high-quality leather, offering good protection and comfort.", value=100, defense_bonus=3)
ancient_relic = Item("Ancient Relic", "A small, dark stone that feels cold to the touch. It seems to absorb light.", value=200)
poisoned_stream_water = Item("Vial of Poisoned Water", "A vial of murky water that swirls with an unnatural, sickly green color.", value=0, quest_item=True)
guild_ledger = Item("Suspicious Ledger", "A Guild ledger with strange, coded entries and payments to unknown parties.", value=0, quest_item=True)
forbidden_wordbinding_rune = Word("Forbidden Rune", "A rune of immense power that feels dangerous to even hold.", value=500)
word_of_deception = Word("Word of Deception", "A rune that seems to shift and blur when you try to focus on it.", value=200)
shadowsilk = Item("Shadowsilk", "A bolt of shimmering, dark silk that seems to absorb light.", value=250)
valuable_caravan_goods = Item("Valuable Caravan Goods", "A crate of valuable, unmarked goods.", value=0, quest_item=True)
orb_of_obfuscation = Item("Orb of Obfuscation", "A smoky quartz orb that clouds the minds of those who gaze into it.", value=0, quest_item=True)
hunters_medallion = Item("Hunter's Medallion", "A medallion that grants the wearer an uncanny ability to track beasts.", value=0, quest_item=True)
guild_trade_manifest = Item("Guild Trade Manifest", "A manifest that grants access to rare and exotic goods from distant lands.", value=0, quest_item=True)
word_of_fury = Word("Word of Fury", "A rune that pulses with raw, aggressive energy.", value=300)

# --- Resource Nodes ---
tree = ResourceNode("Tree", "A tall, sturdy oak tree, perfect for chopping.", "chop", "Woodcutting", "Axe", logs, 1, 10)
iron_vein = ResourceNode("Iron Vein", "A rock face with dark streaks of iron.", "mine", "Mining", "Pickaxe", iron_ore, 1, 25)
river_fishing_spot = ResourceNode("Fishing Spot", "The river here is deep and teeming with fish.", "fish", "Fishing", "Fishing Rod", raw_trout, 1, 10)

# --- Recipes ---
recipe_iron_sword = Recipe("Iron Sword", {"Iron Bar": 5}, iron_sword, station="Anvil", skill_req=("Smithing", 5))
recipe_iron_armor = Recipe("Iron Armor", {"Iron Bar": 8}, iron_armor, station="Anvil", skill_req=("Smithing", 8))
recipe_sturdy_gloves = Recipe("Sturdy Leather Gloves", {"Leather": 4, "Thread": 2}, sturdy_leather_gloves, skill_req=("Crafting", 3))
recipe_fine_boots = Recipe("Fine Leather Boots", {"Leather": 6, "Thread": 3}, fine_leather_boots, skill_req=("Crafting", 5))
scroll_sturdy_gloves = RecipeScroll("Recipe: Sturdy Gloves", "A scroll detailing how to craft sturdy leather gloves.", value=100, recipe=recipe_sturdy_gloves)
scroll_fine_boots = RecipeScroll("Recipe: Fine Boots", "A scroll detailing how to craft fine leather boots.", value=150, recipe=recipe_fine_boots)
default_recipes = [recipe_iron_sword, recipe_iron_armor]
smelting_recipes = [Recipe("Iron Bar", {"Iron Ore": 1}, iron_bar, station="Forge", skill_req=("Smelting", 1))]

# --- Cooking Recipes ---
cooking_recipes = [
    Recipe("Cooked Trout", {"Raw Trout": 1}, cooked_trout, station="Campfire", skill_req=("Cooking", 1))
]

# --- Herblore Recipes ---
herblore_recipes = [
    Recipe("Greater Healing Potion", {"Mystical Herb": 1}, greater_healing_potion, skill_req=("Herblore", 1))
]

# --- Wordbinding Abilities & Combinations ---
# Define the abilities that can be created
fire_bolt_spell = Ability("Fire Bolt", "A focused bolt of pure fire.", mana_cost=5, effect={'type': 'damage', 'amount': 20})
ice_shard_spell = Ability("Ice Shard", "A shard of magical ice that can stun enemies.", mana_cost=10, effect={'type': 'damage', 'amount': 15}, status_effect={'type': 'stun', 'duration': 1})
shadow_cloak_spell = Ability("Shadow Cloak", "Wrap yourself in shadows, increasing your defense.", mana_cost=12, status_effect={'type': 'defense_buff', 'amount': 5, 'duration': 3})
venomous_cloud_spell = Ability("Venomous Cloud", "Conjure a cloud of poison that damages an enemy over time.", mana_cost=15, status_effect={'type': 'poison', 'damage': 8, 'duration': 4})
fireball_spell = Ability("Fireball", "A large, explosive ball of fire.", mana_cost=25, effect={'type': 'damage', 'amount': 60})

# Word combinations - A dictionary of valid word bindings
# The key is a tuple of sorted word names.
word_combinations = {
    tuple(sorted(("Word of Fire", "Word of Bolt"))): fire_bolt_spell,
    tuple(sorted(("Word of Water", "Word of Air"))): ice_shard_spell,
    tuple(sorted(("Word of Shadow", "Word of Air"))): shadow_cloak_spell,
    tuple(sorted(("Word of Venom", "Word of Air"))): venomous_cloud_spell,
    # A 3-word combination for higher-level players
    tuple(sorted(("Word of Fire", "Word of Air", "Word of Power"))): fireball_spell,
}

# --- Factions ---
factions = {
    "villagers": Faction("Rivenshade Villagers", "The common folk of the vale."),
    "merchant_guild": Faction("Merchant Guild", "A powerful guild controlling most trade."),
    "town_guard": Faction("Town Guard", "The protectors of Rivenshade."),
    "bandits": Faction("Bandits", "Outlaws who prey on travelers."),
    "stonebound": Faction("The Stonebound", "A stoic group of blacksmiths, miners, and artisans."),
    "whispered_hand": Faction("The Whispered Hand", "A clandestine network of spies and thieves operating in the shadows."),
    "order_of_dawn": Faction("The Order of Dawn", "A devout order of knights and priests dedicated to purging corruption."),
    "cult_of_the_pact": Faction("Cult of the Forgotten Pact", "A secretive cult with mysterious ties to the mountain's ancient power."),
    "hunters": Faction("The Hunters", "A rugged group of trackers and monster slayers who protect the vale's wilds.")
}

# --- Quests ---
the_lost_caravan_quest = Quest(
    name="The Lost Caravan",
    description="Captain Valerius is concerned about a missing caravan on the mountain road. He's asked you to investigate the wreckage.",
    objective={'type': 'discover', 'target': 'Torn Cultist Robe'},
    prerequisites=["Leaving the Vale"],
    reward_choice=[
        {'description': "Report the cultist activity to the Captain.", 'reward': {'xp': {'Agility': 100}, 'faction': {'town_guard': 15, 'cult_of_the_pact': -10}}},
        {'description': "Lie and say it was just bandits.", 'reward': {'xp': {'Thieving': 75}, 'faction': {'town_guard': 5, 'whispered_hand': 10}}}
    ]
)

mine_collapse_quest = Quest(
    name="Mine Collapse",
    description="A dwarven mine in the Cragspire Mountains has collapsed. Look for survivors.",
    objective={'type': 'explore', 'target': (20, 20)}, # Target is now the coordinates of the mine entrance
    reward={'xp': {"Mining": 100}, 'gold': 150}
)

morning_in_the_vale_quest = Quest(
    name="Morning in the Vale",
    description="The local blacksmith, Bjorn, needs some wood for his forge. Chop some logs from a nearby tree and bring them to him.",
    objective={'type': 'fetch', 'target': 'Logs', 'count': 5},
    reward={'xp': {'Woodcutting': 20}, 'faction': {'stonebound': 10}}
)

fishing_for_knowledge_quest = Quest(
    name="Fishing for Knowledge",
    description="Gwen at the inn needs some fresh fish for the evening's stew. She says the river is a good spot.",
    objective={'type': 'fetch', 'target': 'Raw Trout', 'count': 3},
    prerequisites=["Morning in the Vale"],
    reward_choice=[
        {'description': "Some coin for your trouble (20 gold).", 'reward': {'gold': 20}},
        {'description': "A share of the meal and the gratitude of the village.", 'reward': {'xp': {'Fishing': 15}, 'faction': {'villagers': 10}}}
    ]
)

a_thief_in_training_quest = Quest(
    name="A Thief in Training",
    description="A shady figure in the alley wants you to prove your worth by stealing a silver locket from a wealthy merchant in the market.",
    objective={'type': 'fetch', 'target': 'Silver Locket', 'count': 1},
    prerequisites=["Fishing for Knowledge"],
    reward={'xp': {'Thieving': 75}, 'faction': {'whispered_hand': 15}}
)

shadows_at_dusk_quest = Quest(
    name="Shadows at Dusk",
    description="A guard at the West Gate is concerned about creatures that grow bold at night. He's asked you to prove your mettle by slaying a Wild Boar in the nearby fields after sunset.",
    objective={'type': 'kill', 'target': 'Wild Boar', 'count': 1},
    prerequisites=["A Thief in Training"],
    reward={'xp': {'Attack': 25, 'Defense': 25}, 'gold': 15}
)

bandits_on_the_road_quest = Quest(
    name="Bandits on the Road",
    description="A local farmer is being harassed by bandits on the West Road. He's asked you to deal with their leader at the nearby hideout.",
    objective={'type': 'kill', 'target': 'Bandit Leader', 'count': 1},
    prerequisites=["Shadows at Dusk"],
    reward={'xp': {'Attack': 50, 'Defense': 50}, 'gold': 50, 'faction': {'villagers': 15, 'bandits': -25}}
)

evening_in_the_vale_quest = Quest(
    name="Evening in the Vale",
    description="An old man at the town gate suggests you hone your survival skills. He says a true resident of the vale knows how to craft, fish, and hunt to survive.",
    objective={'type': 'activity', 'activities': {'craft': 1, 'fish': 1, 'hunt': 1}},
    prerequisites=["Bandits on the Road"],
    reward={'xp': {'Agility': 50}, 'faction': {'villagers': 5}}
)

a_hunters_call_quest = Quest(
    name="A Hunter's Call",
    description="A hunter on the road to the northern hills has noticed the wildlife is becoming unusually aggressive. She suggests you speak to Hunt Master Kaelen at the nearby lodge if you want to learn how to handle them.",
    objective={'type': 'explore', 'target': (10, 8)}, # Target is the Hunter's Lodge
    prerequisites=["Evening in the Vale"],
    reward={'xp': {'Hunting': 50}, 'faction': {'hunters': 10}}
)

campfire_allegiances_quest = Quest(
    name="Campfire Allegiances",
    description="A merchant and a hunter are in a heated dispute at a campfire. They both want your support.",
    objective={'type': 'decision'},
    prerequisites=["Shadows in the Trees"],
    reward_choice=[
        {
            'description': "Side with the Merchant Guild. (Unlock a new recipe)",
            'reward': {'item': scroll_sturdy_gloves, 'faction': {'merchant_guild': 15, 'hunters': -10}}
        },
        {
            'description': "Side with the Hunters. (+10 Hunter Faction, +100 Hunting XP)",
            'reward': {'xp': {'Hunting': 100}, 'faction': {'hunters': 10, 'merchant_guild': -10}}
        }
    ]
)

a_guild_envoy_arrives_quest = Quest(
    name="A Guild Envoy Arrives",
    description="A well-dressed envoy from the Merchant's Guild has arrived in Rivenshade, requesting a meeting with the town's leadership. As a neutral and respected party, you've been asked to mediate.",
    objective={'type': 'decision'},
    prerequisites=["The Gathering Storm"],
    reward_choice=[
        {
            'description': "Publicly support the Merchant's Guild's proposal for expanded trade routes.",
            'reward': {'item': scroll_fine_boots, 'faction': {'merchant_guild': 20, 'hunters': -5}}
        },
        {
            'description': "Publicly express doubt about the Guild's intentions, siding with the Hunters.",
            'reward': {'xp': {'Hunting': 100}, 'faction': {'hunters': 15, 'merchant_guild': -10}}
        },
        {
            'description': "Privately accept a bribe from the Envoy to ensure a favorable outcome.",
            'reward': {'gold': 250, 'faction': {'whispered_hand': 15, 'merchant_guild': 5}}
        }
    ]
)

the_merchants_plea_quest = Quest(
    name="The Merchant's Plea",
    description="The conflict between the Guild and the Hunters has reached a breaking point, and the Cult's influence grows in the chaos. The Elder has summoned you to help decide the Vale's future.",
    objective={'type': 'decision'},
    prerequisites=["Ashes on the Road"],
    reward_choice=[
        {
            'description': "Back the Merchant's Guild to strengthen the economy.",
            'reward': {'gold': 500, 'faction': {'merchant_guild': 25, 'hunters': -20}}
        },
        {
            'description': "Back the Hunters to protect the wilds.",
            'reward': {'item': hunters_medallion, 'faction': {'hunters': 25, 'merchant_guild': -20}}
        },
        {
            'description': "Refuse to endorse either side, promoting instability.",
            'reward': {'xp': {'Agility': 300}, 'faction': {'whispered_hand': 20}}
        }
    ]
)

ashes_on_the_road_quest = Quest(
    name="Ashes on the Road",
    description="The conflict between the Guild and the Hunters has drawn unwanted attention. A powerful Cult Fanatic has appeared on the Ashen Road, seeking to capitalize on the chaos. You must stop them.",
    objective={'type': 'kill', 'target': 'Cult Fanatic', 'count': 1},
    prerequisites=["The Wild Hunt"],
    reward_choice=[
        {
            'description': "Interrogate the fanatic after the fight.",
            'reward': {'xp': {'Attack': 200}, 'faction': {'town_guard': 20, 'cult_of_the_pact': -15}}
        },
        {
            'description': "Kill them silently and take their belongings.",
            'reward': {'gold': 400, 'faction': {'whispered_hand': 15}}
        },
        {
            'description': "Attempt a wordbinding duel to assert dominance.",
            'reward': {'item': word_of_fury, 'faction': {'cult_of_the_pact': 20, 'order_of_dawn': -15}}
        }
    ]
)

the_wild_hunt_quest = Quest(
    name="The Wild Hunt",
    description="The conflict has boiled over. The Hunters have declared a Wild Hunt against Guild caravans. You must choose a side.",
    objective={'type': 'decision'},
    prerequisites=["Whispers Beneath the Ledger"],
    reward_choice=[
        {
            'description': "Help the Hunters ambush the caravans.",
            'reward': {'item': hunters_medallion, 'faction': {'hunters': 25, 'merchant_guild': -30}}
        },
        {
            'description': "Defend the Guild's caravans from the Hunters.",
            'reward': {'item': guild_trade_manifest, 'faction': {'merchant_guild': 25, 'hunters': -30}}
        },
        {
            'description': "Warn both sides, playing the middle ground.",
            'reward': {'xp': {'Agility': 200}, 'faction': {'whispered_hand': 15}}
        }
    ]
)

a_trade_of_shadows_quest = Quest(
    name="A Trade of Shadows",
    description="The Guild has asked you to escort a valuable caravan. Meet them at the crossroads south of the contested campfire.",
    objective={'type': 'decision', 'location': (10, 15)},
    prerequisites=["Whispers Beneath the Ledger"],
    reward_choice=[
        {
            'description': "Guard the caravan against the Whispered Hand.",
            'reward': {'item': shadowsilk, 'faction': {'merchant_guild': 15, 'whispered_hand': -20}}
        },
        {
            'description': "Help the Whispered Hand sabotage the caravan.",
            'reward': {'item': valuable_caravan_goods, 'faction': {'whispered_hand': 20, 'merchant_guild': -25}}
        },
        {
            'description': "Secretly reroute the goods for the Cult.",
            'reward': {'item': orb_of_obfuscation, 'faction': {'cult_of_the_pact': 20, 'merchant_guild': -10, 'whispered_hand': -10}}
        }
    ]
)

whispers_beneath_the_ledger_quest = Quest(
    name="Whispers Beneath the Ledger",
    description="You've found a suspicious Guild ledger. The coded entries hint at a dark conspiracy. You must decide what to do with this dangerous information.",
    objective={'type': 'decision'},
    prerequisites=["Campfire Allegiances"],
    reward_choice=[
        {
            'description': "Expose the corruption to Captain Valerius.",
            'reward': {'xp': {'Agility': 200}, 'faction': {'town_guard': 15, 'merchant_guild': -25}}
        },
        {
            'description': "Sell the ledger to the Whispered Hand for a hefty sum.",
            'reward': {'gold': 500, 'faction': {'whispered_hand': 20, 'merchant_guild': -5}}
        },
        {
            'description': "Use the ledger to make contact with the Cult.",
            'reward': {'item': forbidden_wordbinding_rune, 'faction': {'cult_of_the_pact': 25, 'town_guard': -10}}
        }
    ]
)

the_hunters_ultimatum_quest = Quest(
    name="The Hunter's Ultimatum",
    description="Hunt Master Kaelen has summoned you. He presents a vial of poisoned water, claiming the Guild's expansion is ruining the wilds and demands you help him stop them.",
    objective={'type': 'decision'},
    prerequisites=["A Trade of Shadows"],
    reward_choice=[
        {
            'description': "Pledge to help the Hunters protect the wild lands.",
            'reward': {'xp': {'Hunting': 250}, 'faction': {'hunters': 20, 'merchant_guild': -15}}
        },
        {
            'description': "Defend the Merchant Guild's need for expansion.",
            'reward': {'gold': 300, 'faction': {'merchant_guild': 15, 'hunters': -15}}
        }
    ]
)

securing_the_road_quest = Quest(
    name="Securing the Road",
    description="The Guild Envoy has tasked you with clearing the bandits from the Mountain Chokepoint. How you do it is up to you.",
    objective={'type': 'decision', 'location': (11, 16)},
    prerequisites=["A Guild Envoy Arrives"],
    reward_choice=[
        {
            'description': "Attack the bandits and clear the road by force.",
            'reward': {'xp': {'Attack': 150}, 'faction': {'town_guard': 10, 'merchant_guild': 5}}
        },
        {
            'description': "Negotiate with the bandits, paying their 'toll'. (Cost: 100 Gold)",
            'reward': {'xp': {'Thieving': 50}, 'faction': {'whispered_hand': 10, 'merchant_guild': -5}}
        },
        {
            'description': "Pretend the Cult sent you and deceive them into leaving.",
            'reward': {'item': word_of_deception, 'faction': {'cult_of_the_pact': 15, 'whispered_hand': 5}}
        }
    ]
)

leaving_the_vale_quest = Quest(
    name="Leaving the Vale",
    description="The Village Elder has asked you to investigate the growing threats in the wilderness outside the vale. It's time to prepare and head out.",
    objective={'type': 'explore', 'target': (12, 9)}, # Target is the Crossroads west of town
    prerequisites=["A Hunter's Call", "A Word of Warning"],
    reward={'xp': {'Agility': 100}, 'faction': {'villagers': 5}}
)

the_hermits_warning_quest = Quest(
    name="The Hermit's Warning",
    description="You've found a reclusive hermit in the woods. He offers a warning about the dangers of the power you're meddling with.",
    objective={'type': 'decision'}, # This quest is completed by talking and making a choice.
    prerequisites=["The Lost Caravan"],
    reward_choice=[
        {'description': "Accept the hermit's guidance and his protective charm.",
         'reward': {'item': protective_charm, 'xp': {'Magic': 50}}},
        {'description': "Reject his 'wild magic' and trust in your own strength.",
         'reward': {'xp': {'Defense': 50}, 'faction': {'order_of_dawn': 5}}}
    ]
)

shadows_in_the_trees_quest = Quest(
    name="Shadows in the Trees",
    description="The Elder is worried about reports of unnaturally aggressive wolves in the Silverwood. He's asked you to investigate a specific clearing at night.",
    objective={'type': 'ambush', 'location': (5, 5), 'monsters': ['Shadow-Marked Wolf', 'Shadow-Marked Wolf'], 'count': 2},
    prerequisites=["The Hermit's Warning"],
    reward_choice=[
        {'description': "Report your victory to the Guard.", 'reward': {'xp': {'Attack': 150, 'Defense': 100}, 'faction': {'town_guard': 10}}},
        {'description': "Keep quiet about the incident, trusting your own abilities.", 'reward': {'xp': {'Agility': 150}, 'faction': {'whispered_hand': 5}}}
    ]
)

the_gathering_storm_quest = Quest(
    name="The Gathering Storm",
    description="You have found proof of the cult's influence. It's time to report back to the leaders of Rivenshade and decide what to do next.",
    objective={'type': 'decision'},
    prerequisites=["The Ruined Shrine"],
    reward_choice=[
        {
            'description': "Support Captain Valerius' call for military action.",
            'reward': {'xp': {'Attack': 200}, 'faction': {'town_guard': 15, 'bandits': -15}}
        },
        {
            'description': "Support Elder Aelric's plea for caution and investigation.",
            'reward': {'xp': {'Magic': 150}, 'faction': {'villagers': 15, 'town_guard': -5}}
        }
    ]
)

the_ruined_shrine_quest = Quest(
    name="The Ruined Shrine",
    description="The Hermit has asked you to cleanse a nearby shrine that has been defiled by the cult. You must defeat the guardians and decide the fate of the altar.",
    objective={'type': 'clear_shrine', 'location': (2, 3), 'target': 'Defiled Altar'},
    prerequisites=["Campfire Allegiances"],
    reward_choice=[
        {
            'description': "Destroy the altar's carvings.",
            'reward': {'xp': {'Attack': 150}, 'faction': {'order_of_dawn': 15, 'cult_of_the_pact': -25}}
        },
        {
            'description': "Study the carvings to learn their power.",
            'reward': {'xp': {'Wordbinding': 200}, 'faction': {'cult_of_the_pact': 15, 'order_of_dawn': -10}}
        },
        {
            'description': "Steal the relic from the altar.",
            'reward': {'item': ancient_relic, 'faction': {'whispered_hand': 15}}
        }
    ]
)

a_word_of_warning_quest = Quest(
    name="A Word of Warning",
    description="Elara has sensed a dark energy emanating from the old ruins in the Silverwood. She asks you to investigate and bring back whatever you find.",
    objective={'type': 'fetch', 'target': 'Cracked Runic Tablet', 'count': 1},
    prerequisites=["Bandits on the Road"],
    reward_choice=[
        {
            'description': "Hand the tablet to Elara for safekeeping.",
            'reward': {'xp': {'Magic': 75}, 'faction': {'villagers': 5}},
            'remove_item': True
        },
        {
            'description': "Keep the tablet to investigate on your own.",
            'reward': {'xp': {'Wordbinding': 50}, 'faction': {'whispered_hand': 5}},
            'remove_item': False
        }
    ]
)

# --- Hunting Task Quest Templates ---
hunting_quest_templates = [
    QuestTemplate("Hunt: Bandits", "The roads are getting dangerous. Go to {location_name} and take out {count} {monster_name}s.", "kill", "bandit", 5, 100, 150, "Hunting"),
    QuestTemplate("Hunt: Giant Spiders", "The Silverwood is crawling with spiders again. Head to {location_name} and cull {count} {monster_name}s.", "kill", "giant_spider", 8, 120, 180, "Hunting"),
    QuestTemplate("Hunt: Wild Boars", "The boars are getting aggressive near {location_name}. Put down {count} {monster_name}s to keep the area safe.", "kill", "wild_boar", 10, 80, 120, "Hunting"),
    QuestTemplate("Hunt: River Serpents", "A nest of {monster_name}s has been spotted in the Glimmering River near {location_name}. Deal with {count} of them.", "kill", "river_serpent", 3, 150, 200, "Hunting")
]

# --- Mappings & Generators (Must be defined before NPCs that use them) ---
monster_mapping = {
    "giant_spider": GiantSpider, "bandit": Bandit, "river_serpent": RiverSerpent, "mimic": Mimic, "shadow-marked wolf": ShadowWolf, "shadow-marked cultist": ShadowCultist, "cultist-aligned bandit": CultistBandit, "cult fanatic": CultFanatic,
    "wild_boar": WildBoar, "ashbound_cultist": AshboundCultist, "fire_spirit": FireSpirit, "bandit_leader": BanditLeader,
    "troll": Troll, "giant_eagle": GiantEagle, "spectral_wolf": SpectralWolf, "thalraxos": Thalraxos
}

# Initialize the Quest Generator
quest_generator = QuestGenerator({"grid": thalren_vale_map_25x25}, monster_mapping)

# --- Reputation Restoration Quests ---
# A dictionary mapping a faction key to a specific, repeatable quest template.
reputation_quest_templates = {
    "town_guard": QuestTemplate(
        name_format="Prove Your Worth: Culling Pests",
        description_format="The Town Guard won't trust you until you've proven you're not a complete menace. They need someone to deal with the overgrown {monster_name} population near {location_name}. Kill {count} of them.",
        objective_type="kill",
        target_category="wild_boar",
        count=5,
        reward_gold=20,
        reward_xp=50,
        xp_skill="Defense",
        faction_reward={"town_guard": 5}
    ),
    "bandits": QuestTemplate(
        name_format="Test of Loyalty",
        description_format="You've made some powerful enemies, and now you want back in? Fine. Prove you're still useful. Go thin out the {monster_name}s near {location_name}. We'll see if you're worth the trouble. Kill {count} of them.",
        objective_type="kill",
        target_category="wild_boar", # Using a neutral target for now
        count=3,
        reward_gold=50,
        reward_xp=50,
        xp_skill="Thieving",
        faction_reward={"bandits": 5}
    )
}

# --- Procedural Quest Templates ---
kill_quest_templates = [
    QuestTemplate("Bandit Bounty", "Bandits have been harassing travelers near {location_name}. Thin their numbers. Kill {count} {monster_name}.", "kill", "bandit", 3, 75, 120, "Attack"),
    QuestTemplate("Wildlife Cull", "The {monster_name} population near {location_name} is out of control. We need someone to cull {count} of them.", "kill", "wild_boar", 5, 40, 80, "Attack"),
    QuestTemplate("Spider Infestation", "The Silverwood is crawling with {monster_name}s. Clear out {count} of them from around {location_name} before they spread.", "kill", "giant_spider", 4, 60, 100, "Agility"),
    QuestTemplate("Serpent Menace", "The Glimmering River is becoming too dangerous. A large {monster_name} has been spotted near {location_name}. Take care of it.", "kill", "river_serpent", 1, 100, 150, "Defense"),
    QuestTemplate("Dark Omens", "The Ashbound Cult is growing bolder. We've seen {monster_name}s performing dark rituals near {location_name}. Disrupt their activities by eliminating {count} of them.", "kill", "ashbound_cultist", 2, 150, 200, "Magic"),
    QuestTemplate("Restless Spirits", "The old ruins are more haunted than usual. The {monster_name}s are becoming aggressive. Put {count} of them to rest near {location_name}.", "kill", "spectral_wolf", 3, 120, 180, "Magic")
]

sabotage_quest_templates = [
    QuestTemplate("Disrupt the Supply", "The bandits at {location_name} are using a {target} to repair their gear. A rival group wants you to sabotage it to weaken them.", "sabotage", "Anvil", count=1, reward_gold=150, reward_xp=100, xp_skill="Thieving", faction_reward={"bandits": -10, "whispered_hand": 5})
]

# --- NPCs ---
innkeeper_gwen = QuestGiver(
    name="Gwen",
    description="Gwen, the cheerful innkeeper of The Drunken Griffin, cleans a mug behind the bar.",
    quests=fishing_for_knowledge_quest,
    dialogue="Welcome to the Griffin! Rest your weary feet. A room is just 10 gold.",
    personality={'friendliness': 8, 'grumpiness': 1, 'talkativeness': 7},
    faction="villagers"
)

merchant_boris = Shopkeeper(
    name="Boris",
    description="Boris, a gruff man with a sharp eye, runs the town's general store.",
    dialogue="Need supplies? Don't waste my time.",
    personality={'friendliness': 2, 'grumpiness': 8, 'talkativeness': 2},
    faction="merchant_guild"
)
merchant_boris.schedule = [(0, (13, 11)), (18, "drunken_griffin_inn")] # Starts at market, goes to inn at turn 18
merchant_boris.current_location_key = (13, 11)
merchant_boris.add_item(healing_potion)
merchant_boris.add_item(pickaxe)
merchant_boris.add_item(axe)
merchant_boris.add_item(fishing_rod)
merchant_boris.add_item(thread)

priestess_lyra = NPC(
    name="Priestess Lyra",
    description="A serene priestess in white robes tends to a small altar.",
    dialogue="May the light of Lyrathis guide and protect you.",
    personality={'friendliness': 9, 'grumpiness': 0, 'talkativeness': 4}
)

guard_captain_valerius = QuestGiver(
    name="Captain Valerius",
    description="Captain Valerius of the Rivenshade Guard looks over a map, a frown on his face.",
    quests=the_lost_caravan_quest,
    dialogue="Another trade caravan hit by bandits in the Silverwood. This is getting out of hand.",
    personality={'friendliness': 4, 'grumpiness': 6, 'talkativeness': 3},
    faction="town_guard"
)

druid_elara = QuestGiver(
    name="Elara",
    description="A woman with leaves woven into her hair watches you from the edge of the woods. She seems to be one with the forest.",
    quests=a_word_of_warning_quest,
    dialogue="The Silverwood breathes, and we are its lungs. Tread with respect.",
    personality={'friendliness': 5, 'grumpiness': 2, 'talkativeness': 6}
)
druid_elara.schedule = [(0, (12, 8)), (10, (5, 5)), (25, (12, 8))] # Forest Outpost -> Moonpetal Clearing -> Forest Outpost
druid_elara.current_location_key = (12, 8) # Starts at the Forest Outpost

dwarf_miner_thrain = QuestGiver(
    name="Thrain",
    description="A stout dwarf with a magnificent beard eyes you suspiciously from near the mine entrance.",
    quests=mine_collapse_quest,
    dialogue="Blast it all! The main shaft collapsed! We need someone brave enough to check for survivors.",
    personality={'friendliness': 3, 'grumpiness': 7, 'talkativeness': 4}
)
dwarf_miner_thrain.schedule = [(0, (20, 20)), (19, "drunken_griffin_inn")] # Starts at mines, goes to inn at turn 19
dwarf_miner_thrain.current_location_key = (20, 20)

jail_guard = Guard(
    name="Guard",
    description="A burly guard with a stern expression, jingling a set of keys.",
    dialogue="'Move along. Nothing to see here.'",
    personality={'friendliness': 2, 'grumpiness': 7, 'talkativeness': 1},
    faction="town_guard"
)

banker_barnaby = Banker(
    name="Barnaby",
    description="A prim and proper banker sits behind a sturdy counter, meticulously counting coins.",
    dialogue="Welcome to the Bank of Thalren Vale. Your assets are safe with us.",
    personality={'friendliness': 6, 'grumpiness': 4, 'talkativeness': 5}
)

bjorn_the_blacksmith = QuestGiver(
    name="Bjorn",
    description="A burly man with soot-stained hands and a friendly but tired expression. He's leaning against his anvil.",
    quests=morning_in_the_vale_quest,
    dialogue="Hmph. Always need more wood for the forge. Can't smith without fire, can you?",
    personality={'friendliness': 5, 'grumpiness': 6, 'talkativeness': 4},
    faction="stonebound"
)

shady_figure = QuestGiver(
    name="Shady Figure",
    description="A person wrapped in dark cloaks lingers in the shadows of the alley, their face obscured.",
    quests=a_thief_in_training_quest,
    dialogue="Psst. You look like you've got quick fingers. Interested in making a name for yourself?",
    personality={'friendliness': 2, 'grumpiness': 5, 'talkativeness': 3},
    faction="whispered_hand"
)

wealthy_merchant = NPC(
    name="Wealthy Merchant",
    description="A portly merchant dressed in fine silks, looking distracted as he inspects his goods.",
    dialogue="The quality of goods in this town is simply dreadful!",
    personality={'friendliness': 3, 'grumpiness': 8, 'talkativeness': 6},
    faction="merchant_guild"
)
wealthy_merchant.pickpocket_loot = [silver_locket]

guard_alaric = QuestGiver(
    name="Guard Alaric",
    description="A weary-looking guard stands watch at the gate, his hand resting on the pommel of his sword.",
    quests=shadows_at_dusk_quest,
    dialogue_night="The night is long. Keep your wits about you.",
    dialogue="Be careful if you're heading out. The beasts get bolder when the sun goes down. It's a good time for a new adventurer to practice their sword arm, though.",
    personality={'friendliness': 4, 'grumpiness': 5, 'talkativeness': 4},
    faction="town_guard"
)

farmer_miller = QuestGiver(
    name="Farmer Miller",
    description="A farmer with kind eyes and a worried expression. He looks like he hasn't slept well.",
    quests=bandits_on_the_road_quest,
    dialogue="Thank the stars, an adventurer! These bandits on the West Road are ruining me. Please, can you help?",
    personality={'friendliness': 7, 'grumpiness': 2, 'talkativeness': 5},
    faction="villagers"
)

old_man_hemlock = QuestGiver(
    name="Old Man Hemlock",
    description="A weathered old man sits on a stool, carving a piece of wood. He looks up at you with sharp, knowing eyes.",
    quests=evening_in_the_vale_quest,
    dialogue="The sun is setting. A good time to practice your skills if you want to see another dawn. A true survivalist can provide for themselves. Try your hand at crafting, fishing, and hunting. It'll serve you well.",
    personality={'friendliness': 6, 'grumpiness': 3, 'talkativeness': 8},
    faction="villagers"
)

hunt_master_kaelen = ProceduralQuestGiver(
    name="Hunt Master Kaelen",
    description="A tall, scarred man with a calm demeanor, cleaning a massive hunting knife. Trophies of monstrous beasts adorn the walls around him.",
    quests=[the_hunters_ultimatum_quest, the_wild_hunt_quest, ashes_on_the_road_quest],
    dialogue="The wilds are a dangerous place. If you've got the stomach for it, I've got work that needs doing.",
    quest_generator=quest_generator,
    templates=hunting_quest_templates,
    personality={'friendliness': 5, 'grumpiness': 4, 'talkativeness': 4},
    faction="hunters"
)

trader_linara = QuestGiver(
    name="Trader Linara",
    description="A sharply dressed woman with a ledger in hand. She looks annoyed.",
    quests=campfire_allegiances_quest,
    dialogue="This stubborn fool wants to halt progress! These trade routes are vital for the vale's survival.",
    personality={'friendliness': 4, 'grumpiness': 7, 'talkativeness': 6},
    faction="merchant_guild"
)

hunter_torvin = NPC(
    name="Hunter Torvin",
    description="A rugged man in furs, leaning on a large hunting spear. He glares at the merchant.",
    dialogue="Progress? You call scarring the wilds 'progress'? The beasts are already on edge because of the cultists!",
    personality={'friendliness': 5, 'grumpiness': 6, 'talkativeness': 4},
    faction="hunters"
)

scout_elara = QuestGiver(
    name="Scout Elara",
    description="A sharp-eyed woman in leather armor watches the road, a bow slung over her shoulder.",
    quests=a_hunters_call_quest,
    dialogue="The boars are getting feisty. If you're looking to make a name for yourself, or just learn to survive out here, you should head up to the lodge and speak with Kaelen. He's always looking for new blood.",
    personality={'friendliness': 6, 'grumpiness': 2, 'talkativeness': 5},
    faction="hunters"
)

village_elder_aelric = QuestGiver(
    name="Village Elder Aelric",
    description="A kind-faced man with a long white beard and thoughtful eyes. He carries the weight of his community on his shoulders.",
    quests=[leaving_the_vale_quest, the_gathering_storm_quest, the_merchants_plea_quest],
    dialogue="The shadows lengthen beyond our borders. The bandits grow bold, and whispers of a darker cult reach my ears. We need someone to be our eyes and ears in the wilds. Will you take up this burden?",
    personality={'friendliness': 8, 'grumpiness': 1, 'talkativeness': 7},
    faction="villagers"
)

guild_envoy_caius = QuestGiver(
    name="Guild Envoy Caius",
    description="A man in expensive, well-tailored clothes. He carries a ledger and a look of supreme confidence.",
    quests=[a_guild_envoy_arrives_quest, securing_the_road_quest, a_trade_of_shadows_quest, ashes_on_the_road_quest],
    dialogue="Ah, the local 'hero'. The Merchant's Guild has a proposal for this town, one that will bring great prosperity. I trust you'll help the leadership see the... wisdom in our offer.",
    personality={'friendliness': 5, 'grumpiness': 5, 'talkativeness': 8},
    faction="merchant_guild"
)

caravan_guard_captain = NPC(
    name="Caravan Guard Captain",
    description="A grim-faced woman in Guild colors, her hand resting on her sword. She looks nervous.",
    dialogue="You're the escort? Good. We move at your signal. Let's get this over with.",
    personality={'friendliness': 4, 'grumpiness': 6, 'talkativeness': 3},
    faction="merchant_guild"
)

whispered_hand_agent = NPC(
    name="Whispered Hand Agent",
    description="A figure leans against a tree, almost invisible in the shadows. They beckon you closer.",
    dialogue="The Guild thinks they own these roads. We have a counter-offer for a person of your talents.",
    personality={'friendliness': 3, 'grumpiness': 4, 'talkativeness': 5},
    faction="whispered_hand"
)

bandit_lookout = NPC(
    name="Bandit Lookout",
    description="A nervous-looking bandit stands guard, ready to shout a warning.",
    dialogue="This is our road now. State your business, or pay the toll.",
    personality={'friendliness': 1, 'grumpiness': 8, 'talkativeness': 3},
    faction="bandits"
)

hermit_npc = QuestGiver(
    name="Hermit",
    description="A man with wild hair and eyes that seem to see more than they should. He is surrounded by strange carvings and artifacts.",
    quests=the_ruined_shrine_quest,
    dialogue="Another wanderer drawn to the whispers in the woods. Be warned, the power you seek is a double-edged sword. It corrupts as easily as it creates.",
    personality={'friendliness': 4, 'grumpiness': 4, 'talkativeness': 9}
)

# Initialize the Dungeon Generator
from dungeon_generator import DungeonGenerator
dungeon_generator = DungeonGenerator(monster_mapping)

# Inject NPCs into the grid
thalren_vale_map_25x25[12][11]["npcs"] = [
    guard_captain_valerius, 
    ProceduralQuestGiver(
        "Guild Master", 
        "The Guild Master looks over a large board of bounties and requests.", 
        "Looking for work, adventurer?", 
        quest_generator, 
        kill_quest_templates + sabotage_quest_templates, 
        personality={'friendliness': 6, 'grumpiness': 4, 'talkativeness': 5},
        faction="town_guard",
        reputation_quests=reputation_quest_templates
    ),
    village_elder_aelric,
    guild_envoy_caius,
] # Rivenshade (12, 11)
thalren_vale_map_25x25[10][15]["npcs"] = [caravan_guard_captain, whispered_hand_agent] # Caravan Crossroads
thalren_vale_map_25x25[11][16]["npcs"] = [bandit_lookout] # Mountain Chokepoint
thalren_vale_map_25x25[13][11]["items"] = [guild_ledger] # Rivenshade Market
thalren_vale_map_25x25[9][15]["npcs"] = [trader_linara, hunter_torvin] # Contested Campfire
thalren_vale_map_25x25[10][8]["npcs"] = [hunt_master_kaelen] # Hunter's Lodge
thalren_vale_map_25x25[11][13]["npcs"] = [old_man_hemlock] # Rivenshade East Gate
thalren_vale_map_25x25[11][10]["npcs"] = [farmer_miller] # Rivenshade Farms
thalren_vale_map_25x25[11][11]["npcs"] = [guard_alaric] # Rivenshade West Gate (11, 11)
thalren_vale_map_25x25[12][10]["npcs"] = [shady_figure] # Rivenshade Alley (12, 10)
thalren_vale_map_25x25[13][11]["npcs"] = [merchant_boris, banker_barnaby, bjorn_the_blacksmith, wealthy_merchant] # Rivenshade Market (13, 11)
thalren_vale_map_25x25[13][11]["features"] = ["inn"] # Add inn entrance to the market
thalren_vale_map_25x25[12][8]["npcs"] = [druid_elara] # Forest Outpost (12, 8)
thalren_vale_map_25x25[6][2]["npcs"] = [hermit_npc] # Secluded Grove
thalren_vale_map_25x25[11][8]["npcs"].append(scout_elara) # Road to Hunter's Lodge
thalren_vale_map_25x25[12][10]["night_npcs"] = [shady_figure] # Rivenshade Alley (12, 10)
thalren_vale_map_25x25[20][20]["npcs"] = [dwarf_miner_thrain] # Mines Entrance (20, 20)

# Inject Items into the grid
thalren_vale_map_25x25[8][14]["items"] = [torn_cultist_robe] # Wrecked Caravan
thalren_vale_map_25x25[0][6]["items"] = [mystical_herb] # Moonpetal Clearing (0, 6)
thalren_vale_map_25x25[2][3]["items"] = [cracked_runic_tablet] # Haunted Ruins of Silverwood

# Inject Resource Nodes
thalren_vale_map_25x25[12][8]["nodes"] = [tree] # Forest Outpost (12, 8)
thalren_vale_map_25x25[12][12]["nodes"] = [river_fishing_spot] # Glimmering River - Town Ford (12, 12)
thalren_vale_map_25x25[20][20]["nodes"] = [iron_vein] # Mines Entrance (20, 20)

# Inject Stations
thalren_vale_map_25x25[13][11]["stations"] = ["Anvil", "Forge"] # Rivenshade Market (13, 11)
thalren_vale_map_25x25[12][8]["stations"] = ["Campfire"] # Forest Outpost (12, 8)

# Create the final world object
world = {
    "grid": thalren_vale_map_25x25,
    "special": {
        "drunken_griffin_inn": {
            "name": "The Drunken Griffin Inn",
            "description_day": "The inn is moderately busy, with travelers enjoying a midday meal. The air smells of stew and ale.",
            "description_night": "The inn is packed, filled with boisterous laughter and the songs of a local bard. It feels like a safe haven from the dark.",
            "exits": {"out": (13, 11)}, # Exit leads back to Rivenshade Market
            "npcs": [innkeeper_gwen]
        },
        "rivenshade_jail": {
            "name": "Rivenshade Jail",
            "description_day": "You are in a cold, damp jail cell. A single barred window is high on the wall.",
            "description_night": "You are in a cold, dark jail cell. Moonlight streams through a single barred window.",
            "exits": {"out": (12, 11)}, # Exit leads back to Rivenshade
            "npcs": [jail_guard]
        }
    }
}
