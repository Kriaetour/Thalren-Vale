"""
This file contains the raw data for the 25x25 world map of Thalren Vale.
"""

# This is a large data structure. To make it manageable, we'll define a
# helper function to create a base tile, then populate the grid.
def create_tile(name, type, description, enemies=None, rare_creatures=None, quests=None, night_enemies=None, npcs=None, night_npcs=None, dialogue_night=None):
    return {
        "name": name,
        "type": type,
        "description_day": description,
        "description_night": description, # Defaulting to same description for now
        "dialogue_night": dialogue_night,
        "npcs": npcs or [],
        "night_npcs": night_npcs or [],
        "enemies": enemies or [],
        "night_enemies": night_enemies or [],
        "rare_creatures": rare_creatures or [],
        "quests": quests or []
    }

# Initialize an empty 25x25 grid
thalren_vale_map_25x25 = [[{} for _ in range(25)] for _ in range(25)]

# Default tile for empty areas
plains_tile = lambda: create_tile("Rolling Plains", "plains", "Open, grassy plains stretch out before you.", enemies=['wild_boar'])

for r in range(25):
    for c in range(25):
        thalren_vale_map_25x25[r][c] = plains_tile()

# Northwest: Silverwood Forest (0-7, 0-7)
for r in range(8):
    for c in range(8):
        thalren_vale_map_25x25[r][c] = create_tile("Silverwood Forest", "forest", "Ancient, silver-barked trees create a dense, whispering canopy.", enemies=['giant_spider', 'wild_boar'])
thalren_vale_map_25x25[2][3] = create_tile("Haunted Ruins of Silverwood", "ruins", "The crumbling stones of an ancient manor are being reclaimed by the forest.", enemies=[], night_enemies=['spectral_wolf'], rare_creatures=['ancient_guardian'], quests=['The Forgotten Pact'])
thalren_vale_map_25x25[6][2] = create_tile("Secluded Grove", "forest_edge", "A quiet, hidden grove, sheltered by ancient trees. A small, well-kept hut sits in the center.", quests=["The Hermit's Warning"])
thalren_vale_map_25x25[5][5] = create_tile("Moonpetal Clearing", "forest_edge", "A clearing where rare, glowing flowers bloom. The air hums with faint magic.", enemies=[], quests=['Songs of the Wordbinders'])

# West: Silverwood Outskirts (8-16, 0-7)
for r in range(8, 17):
    for c in range(8):
        thalren_vale_map_25x25[r][c] = create_tile("Silverwood Outskirts", "forest_edge", "The dense forest begins to thin here, dotted with logging camps and bandit hideouts.", enemies=['bandit', 'wild_boar'])
thalren_vale_map_25x25[12][3] = create_tile("Bandit Hideout", "camp", "A well-hidden camp used by local bandits as a base of operations.", enemies=['bandit'], rare_creatures=['bandit_leader'], quests=['Shadows at the Crossroads'])
thalren_vale_map_25x25[15][5] = create_tile("Timberfall Village", "village", "A small village of lumberjacks who work the Silverwood.", enemies=[], quests=['The War of Coin and Claw'])

# Southwest: Grasslands & Lakes (17-24, 0-7)
for r in range(17, 25):
    for c in range(8):
        thalren_vale_map_25x25[r][c] = create_tile("Southern Grasslands", "plains", "Wide, open grasslands perfect for grazing. Nomadic camps are sometimes seen here.", enemies=['wild_boar'])
thalren_vale_map_25x25[19][4] = create_tile("The Azure Lake", "river", "A stunningly clear blue lake, rumored to have magical properties.", enemies=[], rare_creatures=['lake_serpent'])
thalren_vale_map_25x25[22][2] = create_tile("Nomad Camp", "camp", "A temporary camp set up by the nomads of the southern plains.", enemies=[], quests=['The Nomad\'s Trial'])
thalren_vale_map_25x25[23][6] = create_tile("Sunken Ruins", "ruins", "The tops of ancient buildings jut out from the marshy ground.", enemies=['river_serpent'], quests=['The Ruins Below'])

# North-central: Rolling Hills (0-7, 8-16)
for r in range(8):
    for c in range(8, 17):
        thalren_vale_map_25x25[r][c] = create_tile("Northern Rolling Hills", "hills", "Gentle, grassy hills stretch to the horizon. The old caravan route winds through here.", enemies=['wild_boar', 'bandit'])
thalren_vale_map_25x25[10][8] = create_tile("Hunter's Lodge", "camp", "A large, rustic lodge made of timber and stone. The smell of woodsmoke and roasting meat hangs in the air.", quests=['Hunting Task'])
thalren_vale_map_25x25[10][15] = create_tile("Caravan Crossroads", "plains", "A dusty crossroads where the north-south and east-west roads meet.", quests=['A Trade of Shadows'])
thalren_vale_map_25x25[9][15] = create_tile("Contested Campfire", "camp", "A campfire crackles, surrounded by a tense standoff between a merchant and a hunter.", quests=['Campfire Allegiances'])
thalren_vale_map_25x25[11][16] = create_tile("Mountain Chokepoint", "hills", "A narrow pass through the hills, perfect for an ambush. A group of bandits blocks the way.", enemies=['Cultist-Aligned Bandit'], quests=['Securing the Road'])
thalren_vale_map_25x25[4][13] = create_tile("Abandoned Watchtower", "ruins", "A crumbling stone watchtower overlooks the old caravan route. It has been abandoned for years.", enemies=['bandit'], quests=['Shadows at the Crossroads'])
thalren_vale_map_25x25[8][14] = create_tile("Wrecked Caravan", "plains", "The splintered remains of several wagons lie strewn across the road. It looks like a recent attack.", enemies=['bandit'], quests=['The Lost Caravan'])

# South-central: Farmlands & Swamps (17-24, 8-16)
for r in range(17, 25):
    for c in range(8, 17):
        thalren_vale_map_25x25[r][c] = create_tile("Fertile Farmlands", "plains", "Rich fields of crops stretch out, feeding the heart of the vale.", enemies=['wild_boar'])
for r in range(20, 24):
    for c in range(13, 17):
        thalren_vale_map_25x25[r][c] = create_tile("Whispering Fen", "swamp", "A murky swamp filled with strange plants and stranger creatures.", enemies=['river_serpent', 'giant_spider'])
thalren_vale_map_25x25[22][14] = create_tile("Smuggler's Path", "swamp", "A hidden path through the swamp, used by those who wish to avoid the main roads.", enemies=['bandit'])

# Center: The Heart of the Vale (10-14, 10-14)
# Adding more detail to the central region to make it feel more alive
thalren_vale_map_25x25[11][10] = create_tile("Rivenshade Farms", "plains", "Fertile fields that supply the town with food.", enemies=['wild_boar'])
thalren_vale_map_25x25[11][11] = create_tile("Rivenshade West Gate", "town", "The western approach to Rivenshade, watched by guards.", enemies=[])
thalren_vale_map_25x25[11][13] = create_tile("Rivenshade East Gate", "town", "The eastern gate of Rivenshade, leading towards the plains.", enemies=[])
thalren_vale_map_25x25[12][13] = create_tile("East Rivenshade Road", "plains", "The road leading east from Rivenshade across the plains.", enemies=['wild_boar'])
thalren_vale_map_25x25[13][10] = create_tile("South Rivenshade Fields", "plains", "The fields south of the market are lush and well-tended.", enemies=['wild_boar'])
thalren_vale_map_25x25[13][13] = create_tile("Path to Fallowmere", "plains", "A well-trodden path connecting Rivenshade to Fallowmere village.", enemies=[])
thalren_vale_map_25x25[14][10] = create_tile("Southern Farmlands", "plains", "Rolling fields of grain sway gently in the breeze.", enemies=[])
thalren_vale_map_25x25[14][11] = create_tile("Southern Farmlands", "plains", "More farms stretch out, their windmills turning slowly.", enemies=[])
thalren_vale_map_25x25[14][14] = create_tile("Fallowmere Fields", "plains", "The fields surrounding Fallowmere are known for their sweet melons.", enemies=[])
thalren_vale_map_25x25[12][11] = create_tile("Rivenshade", "town", "The main hub of Thalren Vale. A bustling town with shops, an inn, and many people.", quests=['The Stranger in the Vale'])
thalren_vale_map_25x25[13][11] = create_tile("Rivenshade Market", "town", "The bustling market square of Rivenshade. Merchants hawk their wares from colorful stalls.", quests=['The Merchant’s Plea'])
thalren_vale_map_25x25[14][13] = create_tile("Fallowmere Village", "village", "A small, peaceful farming village that relies on the fertile plains.", quests=['Fishing for Knowledge'])
thalren_vale_map_25x25[11][14] = create_tile("Stonewatch Outpost", "fort", "A military fort guarding the pass between the plains and the mountains.", quests=['Siege of Ashspire'])

# Glimmering River (flowing North-South through center)
for r in range(25):
    if 10 <= r <= 15: # Wider near the center
        thalren_vale_map_25x25[r][12] = create_tile("Glimmering River", "river", "The wide, central stretch of the Glimmering River, good for fishing.", enemies=['river_serpent'])
    else:
        thalren_vale_map_25x25[r][12] = create_tile("Glimmering River", "river", "The Glimmering River flows swiftly here.", enemies=['river_serpent'])

# Northeast: Ashfall Plains (0-7, 17-24)
for r in range(8):
    for c in range(17, 25):
        thalren_vale_map_25x25[r][c] = create_tile("Ashfall Plains", "ash_plains", "The ground is cracked and blackened, covered in a fine layer of ash.", enemies=['fire_spirit', 'ashbound_cultist'])
thalren_vale_map_25x25[3][20] = create_tile("Cultist Lookout Post", "ash_plains", "A crude wooden tower where cultists watch over the plains.", enemies=['ashbound_cultist'], quests=['The Eclipse Rising'])
thalren_vale_map_25x25[6][22] = create_tile("Volcanic Fissure", "ash_plains", "A deep crack in the earth glows with a malevolent red light.", enemies=['fire_spirit'], rare_creatures=['ash_titan'])

# East: Expanding Ashfall (8-16, 17-24)
for r in range(8, 17):
    for c in range(17, 25):
        thalren_vale_map_25x25[r][c] = create_tile("Ashfall Plains", "ash_plains", "A vast, empty expanse of grey ash. The wind howls mournfully.", enemies=['fire_spirit', 'ashbound_cultist'])
thalren_vale_map_25x25[12][15] = create_tile("Ashen Road", "ash_plains", "The road here is choked with ash, and the air is heavy with the smell of sulfur. A lone, powerful-looking figure blocks the path.", enemies=['Cult Fanatic'], quests=['Ashes on the Road'])
thalren_vale_map_25x25[15][20] = create_tile("Ashbound Cult Camp", "camp", "The main camp of the Ashbound Cult. A large bonfire burns at its center.", enemies=['ashbound_cultist'], rare_creatures=['cult_master'])
thalren_vale_map_25x25[13][22] = create_tile("The Ritual Circle", "ruins", "A circle of blackened stones where cultists perform dark rituals.", enemies=['ashbound_cultist', 'fire_spirit'], quests=['The Forgotten Pact'])

# Southeast: Cragspire Mountains (17-24, 17-24)
for r in range(17, 25):
    for c in range(17, 25):
        thalren_vale_map_25x25[r][c] = create_tile("Cragspire Foothills", "hills", "The rolling hills begin to rise sharply here, becoming the Cragspire Mountains.", enemies=['troll'])
for r in range(19, 25):
    for c in range(19, 25):
        thalren_vale_map_25x25[r][c] = create_tile("Cragspire Mountains", "mountains", "Jagged peaks loom over you, their tops lost in the clouds.", enemies=['troll', 'giant_eagle'])
thalren_vale_map_25x25[20][20] = create_tile("Cragspire Mines Entrance", "special", "The main entrance to the once-great dwarven mines of Cragspire.", enemies=[], quests=['The Lost Expedition'])
thalren_vale_map_25x25[22][22] = create_tile("Eagle's Nest Peak", "mountains", "A towering peak where giant eagles make their nests.", enemies=['giant_eagle'], rare_creatures=['roc'])
thalren_vale_map_25x25[24][24] = create_tile("The Sealed Mountain", "special", "A dark, foreboding mountain peak, sealed with ancient magic.", enemies=[], quests=['The Sealed Mountain'])