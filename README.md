# Thalren Vale: A Text-Based RPG Engine

Welcome to Thalren Vale, a classic text-based RPG with a modern, extensible engine written in Python. Explore a dynamic world, make meaningful choices that impact factions and storylines, and develop your character through a deep, multi-faceted skill system.

## Core Features

*   **Classic RPG Gameplay:** Explore a grid-based world, interact with NPCs, fight monsters, and complete quests.
*   **Dynamic World:** The world of Thalren Vale features a full day/night cycle that affects monster spawns and NPC availability.
*   **ASCII Viewport:** An immersive pseudo-graphical viewport renders the player's immediate surroundings using colored ASCII sprites, complete with indicators for available exits.
*   **Deep Skill System:** Level up 16 unique skills, from `Attack` and `Defense` to `Wordbinding`, `Herblore`, and `Thieving`.
*   **Complex Crafting:** Gather resources using skills like `Mining`, `Woodcutting`, and `Fishing`, then use them to `Craft`, `Cook`, `Smelt`, and `Brew` powerful items and consumables.
*   **Branching Quests:** Engage in a rich narrative with quests that feature meaningful choices, affecting faction reputation and story outcomes.
*   **Tactical Combat:** Fight enemies in a turn-based combat system that includes a variety of spells and status effects like poison, stuns, and stat-boosting buffs.
*   **Robust Save/Load System:** Your progress is saved in a human-readable JSON format, ensuring safety and portability across different systems and game versions.

## Advanced Engine Architecture

Thalren Vale is built on a modern, modular architecture designed for easy expansion.

### Event-Driven System

The game engine uses a powerful event manager to decouple core logic from specific gameplay consequences. Hooks like `on_kill`, `on_item_pickup`, and `on_talk` allow new content and mechanics to be "plugged in" without modifying the main game loop. This makes adding new quests and interactions clean and simple.

### Procedural Content Generation

*   **Procedural Questing:** A quest generator can create dynamic tasks for the player, including "hunt," "fetch," and "sabotage" missions. This system is fully extensible to support new objective types.
*   **Procedural World Events:** The world can change dynamically through faction events. The "Bandit Raid" system, for example, can temporarily change a peaceful village into a hostile area, clearing out NPCs and spawning bandits until the threat is resolved.

### Modular Command Handling

All player commands are processed through a dedicated `command_handler.py` module. This separates the "what" of a player's action from the "how" of the game's execution, keeping the main loop clean and making it easy to add or modify player abilities.

## How to Run

The primary entry point for the game is the `main.py` script.

```bash
python "c:\Users\brand\OneDrive\Documents\Py3 Files\Project 1 - Text-Based RPG\Thalren-Vale\src\main.py"
```

An experimental Tkinter-based GUI is also under development (`gui_main.py`).

## Project Documentation

For a detailed overview of the game's narrative, see the WALKTHROUGH.md file.

---

*This project is an ongoing effort to build a feature-rich and technically robust RPG engine.*