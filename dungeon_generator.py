import random
from item import Key, pouch_of_gold, healing_potion, mana_potion

class DungeonGenerator:
    """Generates procedural dungeon maps."""

    def __init__(self, monster_mapping):
        self.monster_mapping = monster_mapping
        self.room_descriptions = [
            "A vast cavern glitters with strange, phosphorescent crystals.",
            "A narrow passage echoes with the constant drip of water from unseen stalactites.",
            "A chasm splits the floor of this chamber, crossed by a rickety-looking stone bridge.",
            "The air here is unnaturally cold. Ancient, indecipherable runes are carved into the walls.",
            "This room is filled with the skeletal remains of previous adventurers. A grim warning."
        ]
        self.end_game_monsters = ["troll", "giant_eagle"]
        self.loot_pool = [
            healing_potion,
            mana_potion,
            pouch_of_gold
        ]

    def _generate_single_floor(self, num_rooms):
        """
        Generates a single, non-linear floor layout using a random walk.
        :param num_rooms: The number of rooms to generate for this floor.
        :return: A dictionary representing the floor layout with coordinate-based keys.
        """
        layout = {}
        start_pos = (0, 0)
        layout[start_pos] = {
            "name": "Cavern Entrance",
            "description_day": "The air grows colder as you descend. The path ahead is dark.",
            "description_night": "The air grows colder as you descend. The path ahead is dark.",
            "exits": {},
            "monsters": []
        }

        current_pos = start_pos
        for _ in range(num_rooms - 1):
            possible_directions = ["north", "south", "east", "west"]
            random.shuffle(possible_directions)
            
            moved = False
            for direction in possible_directions:
                next_pos = self._get_next_pos(current_pos, direction)
                if next_pos not in layout:
                    layout[next_pos] = {
                        "name": "Deep Cavern",
                        "description_day": random.choice(self.room_descriptions),
                        "description_night": random.choice(self.room_descriptions),
                        "exits": {},
                        "monsters": [self.monster_mapping[random.choice(self.end_game_monsters)]()],
                    }
                    # Add a chance for a chest
                    if random.random() < 0.25: # 25% chance for a chest
                        if random.random() < 0.2: # 20% of chests are mimics
                            layout[next_pos]['chest'] = {'is_mimic': True}
                        else:
                            chest_loot = [random.choice(self.loot_pool) for _ in range(random.randint(1, 2))]
                            is_trapped = random.random() < 0.5 # 50% of real chests are trapped
                            layout[next_pos]['chest'] = {
                                'trapped': is_trapped,
                                'disarmed': False,
                                'loot': chest_loot
                            }
                    opposite_direction = {"north": "south", "south": "north", "east": "west", "west": "east"}[direction]
                    layout[current_pos]["exits"][direction] = next_pos
                    layout[next_pos]["exits"][opposite_direction] = current_pos
                    current_pos = next_pos
                    moved = True
                    break
            
            if not moved:
                current_pos = random.choice(list(layout.keys()))
        
        return layout

    def generate(self, num_floors=3, rooms_per_floor=8, exit_location=(4, 2)):
        """
        Generates a multi-floor, non-linear dungeon.
        :param num_floors: The number of floors to generate.
        :param rooms_per_floor: The number of rooms on each floor.
        :param exit_location: The grid coordinates the player returns to upon exiting.
        :return: A dictionary representing the dungeon.
        """
        all_floor_layouts = [self._generate_single_floor(rooms_per_floor) for _ in range(num_floors)]

        # Link floors with stairs
        for i in range(num_floors - 1):
            floor_above, floor_below = all_floor_layouts[i], all_floor_layouts[i+1]
            
            stairs_down_pos = max(floor_above.keys(), key=lambda pos: abs(pos[0]) + abs(pos[1]))
            stairs_up_pos = (0, 0) # Entrance of the floor below

            floor_above[stairs_down_pos]["exits"]["down"] = (i + 1, stairs_up_pos)
            floor_above[stairs_down_pos]["description_day"] += " A rough-hewn staircase spirals down into darkness."
            floor_above[stairs_down_pos]["description_night"] = floor_above[stairs_down_pos]["description_day"]
            
            floor_below[stairs_up_pos]["exits"]["up"] = (i, stairs_down_pos)
            floor_below[stairs_up_pos]["description_day"] += " A rough-hewn staircase spirals up into the gloom."
            floor_below[stairs_up_pos]["description_night"] = floor_below[stairs_up_pos]["description_day"]

        # Place boss on the last floor
        last_floor_layout = all_floor_layouts[-1]
        boss_pos = max(last_floor_layout.keys(), key=lambda pos: abs(pos[0]) + abs(pos[1]))

        # Lock the door to the boss room
        parent_pos = None
        lock_direction = None
        for pos, data in last_floor_layout.items():
            for direction, dest in data["exits"].items():
                if dest == boss_pos:
                    parent_pos = pos
                    lock_direction = direction
                    break
            if parent_pos:
                break
        
        if parent_pos and lock_direction:
            boss_exit_destination = last_floor_layout[parent_pos]["exits"][lock_direction]
            last_floor_layout[parent_pos]["exits"][lock_direction] = {
                "locked": True,
                "key_id": "shadow_throne_door",
                "destination": boss_exit_destination
            }
            # Place the key on the second floor
            key_floor = all_floor_layouts[1]
            key_room_pos = random.choice(list(key_floor.keys()))
            shadow_key = Key("Shadow Key", "A heavy, ornate key made of dark metal, pulsing with faint shadow energy.", value=0, unlocks_what="shadow_throne_door")
            if "items" not in key_floor[key_room_pos]:
                key_floor[key_room_pos]["items"] = []
            key_floor[key_room_pos]["items"].append(shadow_key)

        last_floor_layout[boss_pos]["name"] = "Throne of the Shadow"
        last_floor_layout[boss_pos]["description_day"] = "You have reached the heart of the mountain. A massive, obsidian throne dominates the chamber, upon which sits the colossal form of Thalraxos."
        last_floor_layout[boss_pos]["description_night"] = last_floor_layout[boss_pos]["description_day"]
        last_floor_layout[boss_pos]["monsters"] = [self.monster_mapping["thalraxos"]()]

        # Convert coordinate-based layout to string-based keys for the game engine
        final_dungeon = {}
        coord_to_key_map = {}
        for i, layout in enumerate(all_floor_layouts):
            for coord in layout.keys():
                coord_to_key_map[(i, coord)] = f"f{i}_room_{coord[0]}_{coord[1]}"
        
        # Set the exit from the very first room
        all_floor_layouts[0][(0,0)]["exits"]["out"] = exit_location

        for i, layout in enumerate(all_floor_layouts):
            for coord, room_data in layout.items():
                room_key = coord_to_key_map[(i, coord)]
                new_exits = {}
                for direction, dest in room_data["exits"].items():
                    if isinstance(dest, dict): # Locked door
                        dest_floor, dest_coord = dest['destination']
                        dest['destination'] = coord_to_key_map[(dest_floor, dest_coord)]
                        new_exits[direction] = dest
                    elif isinstance(dest, tuple): # Standard exit
                        dest_floor, dest_coord = dest
                        new_exits[direction] = coord_to_key_map[(dest_floor, dest_coord)]
                    else: # Special exit like 'out'
                        new_exits[direction] = dest
                room_data["exits"] = new_exits
                final_dungeon[room_key] = room_data

        return final_dungeon

    def _get_next_pos(self, pos, direction):
        x, y = pos
        if direction == "north": return (x, y - 1)
        if direction == "south": return (x, y + 1)
        if direction == "east": return (x + 1, y)
        if direction == "west": return (x - 1, y)
        return pos