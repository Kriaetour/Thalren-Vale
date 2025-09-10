# Welcome to Thalren Vale

This is a classic text-based role-playing game (RPG) built with Python, set in the world of Thalren Vale. Explore a dynamic world, fight dangerous monsters, interact with unique characters, and develop your skills in a persistent world that changes from day to night.

## Features

*   **Dynamic World:** Experience a living world with a full day/night cycle that affects which monsters and NPCs are available.
*   **Deep Skill System:** Level up a wide range of skills including Attack, Defense, Agility, Magic, Mining, Smithing, Fishing, Woodcutting, Thieving, Herblore, and more.
*   **Unique Wordbinding System:** Discover rare Words of Power from fallen enemies. Combine them using the `bind` command to create powerful and unique new spells. The higher your Wordbinding skill, the more words you can combine at once!
*   **Robust Crafting:** Gather raw materials through mining, woodcutting, and fishing. Refine them through smelting and craft them into powerful weapons and armor.
*   **Engaging Quests:** Talk to NPCs to receive quests that will guide you through the world of Thalren Vale and reward you with experience and gold.
*   **Tactical Combat:** Engage in turn-based combat where you can attack, cast spells, or attempt a daring escape.
*   **Save & Load:** Your progress is automatically saved, and you can load your game to continue your adventure at any time.

## How to Run

1.  Ensure you have Python 3 installed.
2.  Navigate to the project's `src` directory in your terminal.
3.  Run the game using the following command:
    ```sh
    python main.py
    ```

## Getting Started: Beginner's Guide

Welcome to Thalren Vale! Here are a few tips to start your adventure:

1.  **Explore the Town Square:** Your journey begins here. Use the `look` command to see what's around you. You'll find exits to other locations and people to talk to.
2.  **Get Your First Quest:** Use the `talk to <npc name>` command to speak with the people in town. **Captain Valerius** in the Town Square is looking for help with a bandit problem.
3.  **Arm Yourself:** A true adventurer needs supplies. Head `west` from the Town Square to the **Rivenshade Market**. `talk to Boris` to see what he has for sale. You'll need tools like a `pickaxe` or `axe` for gathering skills.
4.  **Check Your Status:** Use the `status` or `stats` command frequently to check your health, mana, and skill levels. Use `inventory` or `i` to see what you're carrying.
5.  **Be Wary of the Dark:** Time passes as you move. When night falls, more dangerous creatures emerge in the wilderness. It might be wise to head `west` from the market to the **Drunken Griffin Inn** and `rest` for a small fee to heal up and wait for morning.

## Command List

Here is a full list of commands available in the game. Use `help` at any time to see this list.

### Movement
*   **go \<direction\>** - Move to a new location (e.g., `go north`).
*   **north, south, etc.** - Shortcut for movement.

### Interaction
*   **look** - Examine your current location.
*   **look at \<target\>** - Examine an item, NPC, or monster (e.g., `look at sword`).
*   **take \<item\>** - Pick up an item from the ground.
*   **drop \<item\>** - Drop an item from your inventory.
*   **use \<item\>** - Use an item from your inventory (e.g., `use healing potion`).
*   **talk to \<npc\>** - Speak with a person (e.g., `talk to elara`).
*   **wait** - Pass a short amount of time (e.g., to serve a jail sentence).
*   **rest** - Rest at a tavern to heal (costs gold).

### Gathering & Crafting
*   **mine \<vein\>** - Mine an ore vein (e.g., `mine copper`).
*   **chop \<tree\>** - Chop a tree (e.g., `chop tree`).
*   **fish \<spot\>** - Fish at a fishing spot (e.g., `fish spot`).
*   **cook \<item\>** - Cook raw food at a campfire or range.
*   **brew \<potion\>** - Brew a potion from herbs.
*   **smelt \<bar\>** - Smelt ore into a bar at a forge.
*   **craft \<item\>** - Craft a new item from materials.
*   **recipes** - Show a list of known crafting recipes.
*   **bind \<word1\> ...** - Attempt to bind words of power into a new spell.

### Thievery
*   **pickpocket \<npc\>** - Attempt to steal from an NPC.
*   **lockpick** - Attempt to pick the lock of your jail cell.
*   **bribe** - Attempt to bribe a guard to get out of jail.

### Magic & Combat
*   **attack \<monster\>** - Engage a monster in combat.
*   **cast \<spell_number\>** - Cast a known spell during combat.
*   **defend** - Take a defensive stance to block damage.
*   **parry** - Attempt to parry an attack, reducing damage and possibly counter-attacking.
*   **flee** - Attempt to escape from combat (chance-based).

### Character & Inventory
*   **inventory (i)** - View the items you are carrying.
*   **map (m)** - Display the world map.
*   **status (stats)** - View your character's stats and skills.
*   **quests (journal)** - View your active quests.
*   **equip \<item\>** - Equip a weapon or armor from your inventory.
*   **unequip \<slot\>** - Unequip an item ('weapon' or 'armor').

### Banking & Game
*   **bank** - View your bank balance.
*   **deposit/withdraw** - Manage your bank account (e.g., `deposit gold 100`).
*   **save** - Save your progress.
*   **quit** - Exit the game.