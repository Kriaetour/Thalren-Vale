import tkinter as tk
from tkinter import ttk, simpledialog, font, messagebox
from game_logic import Game

class App(tk.Tk):
    def __init__(self, game):
        super().__init__()
        self.game = game

        self.title("Thalren Vale")
        self.geometry("1200x800")
        self.configure(bg="#2c3e50")

        # Style configuration
        style = ttk.Style(self)
        style.theme_use('clam')
        style.configure("TFrame", background="#2c3e50")
        style.configure("TLabel", background="#2c3e50", foreground="white", font=("Helvetica", 10))
        style.configure("TButton", font=("Helvetica", 10))
        style.configure("TLabelframe", background="#34495e", bordercolor="#7f8c8d")
        style.configure("TLabelframe.Label", background="#34495e", foreground="white", font=("Helvetica", 11, "bold"))
        style.configure("Horizontal.TProgressbar", background='#27ae60')

        self.protocol("WM_DELETE_WINDOW", self.on_close)

        self.create_widgets()
        self.log_message(f"Welcome, {self.game.player.name}! Your journey begins.")
        self.update_gui()

    def create_widgets(self):
        # Main frame
        main_frame = ttk.Frame(self, padding="10")
        main_frame.pack(fill=tk.BOTH, expand=True)

        # Create the three main columns
        col1 = ttk.Frame(main_frame)
        col2 = ttk.Frame(main_frame)
        col3 = ttk.Frame(main_frame)
        col1.grid(row=0, column=0, sticky="ns", padx=5)
        col2.grid(row=0, column=1, sticky="ns", padx=5)
        col3.grid(row=0, column=2, sticky="ns", padx=5)
        main_frame.grid_columnconfigure(1, weight=1)

        # --- Column 1: Player Info, Skills, Inventory ---
        self._create_player_panel(col1)
        self._create_skills_panel(col1)
        self._create_inventory_panel(col1)

        # --- Column 2: Map, Combat, Log ---
        self._create_map_panel(col2)
        self._create_combat_panel(col2)
        self._create_log_panel(col2)

        # --- Column 3: World, NPCs, Actions ---
        self._create_world_panel(col3)
        self._create_npc_panel(col3)
        self._create_action_panel(col3)

    def _create_player_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Player Status", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        self.hp_var = tk.StringVar(value="100/100")
        self.mp_var = tk.StringVar(value="100/100")
        self.atk_var = tk.StringVar(value="10")
        self.def_var = tk.StringVar(value="5")
        self.gold_var = tk.StringVar(value="25")

        ttk.Label(frame, text="HP:").grid(row=0, column=0, sticky="w")
        self.hp_bar = ttk.Progressbar(frame, length=150, mode='determinate')
        self.hp_bar.grid(row=0, column=1, padx=5)
        ttk.Label(frame, textvariable=self.hp_var).grid(row=0, column=2)

        ttk.Label(frame, text="MP:").grid(row=1, column=0, sticky="w")
        self.mp_bar = ttk.Progressbar(frame, length=150, mode='determinate')
        self.mp_bar.grid(row=1, column=1, padx=5)
        ttk.Label(frame, textvariable=self.mp_var).grid(row=1, column=2)

        ttk.Label(frame, text="Attack:").grid(row=2, column=0, sticky="w", pady=2)
        ttk.Label(frame, textvariable=self.atk_var).grid(row=2, column=1, sticky="w", padx=5)
        ttk.Label(frame, text="Defense:").grid(row=3, column=0, sticky="w", pady=2)
        ttk.Label(frame, textvariable=self.def_var).grid(row=3, column=1, sticky="w", padx=5)
        ttk.Label(frame, text="Gold:").grid(row=4, column=0, sticky="w", pady=2)
        ttk.Label(frame, textvariable=self.gold_var).grid(row=4, column=1, sticky="w", padx=5)

    def _create_skills_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Skills", padding=10)
        frame.pack(fill=tk.X, pady=5)
        self.skills_list = tk.Listbox(frame, height=10, bg="#1c2833", fg="white", selectbackground="#2980b9")
        self.skills_list.pack(fill=tk.X, expand=True)

    def _create_inventory_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Inventory", padding=10)
        frame.pack(fill=tk.X, pady=5)
        self.inv_list = tk.Listbox(frame, height=10, bg="#1c2833", fg="white", selectbackground="#2980b9")
        self.inv_list.pack(fill=tk.X, expand=True)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Use", command=lambda: self.handle_item_action("use")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Drop", command=lambda: self.handle_item_action("drop")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Equip", command=lambda: self.handle_item_action("equip")).pack(side=tk.LEFT, padx=5)

    def _create_map_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Map", padding=10)
        frame.pack(fill=tk.BOTH, expand=True, pady=5)
        self.map_canvas = tk.Canvas(frame, width=400, height=200, bg="darkgreen", highlightthickness=0)
        self.map_canvas.pack()

    def _create_combat_panel(self, parent):
        self.combat_frame = ttk.LabelFrame(parent, text="Combat", padding=10)
        # We will .pack() this later when combat starts
        
        self.enemy_name_var = tk.StringVar()
        self.enemy_hp_var = tk.StringVar()
        ttk.Label(self.combat_frame, text="Enemy:").grid(row=0, column=0, sticky="w")
        ttk.Label(self.combat_frame, textvariable=self.enemy_name_var).grid(row=0, column=1, columnspan=2, sticky="w")
        
        ttk.Label(self.combat_frame, text="HP:").grid(row=1, column=0, sticky="w")
        self.enemy_hp_bar = ttk.Progressbar(self.combat_frame, length=150, mode='determinate')
        self.enemy_hp_bar.grid(row=1, column=1, padx=5)
        ttk.Label(self.combat_frame, textvariable=self.enemy_hp_var).grid(row=1, column=2)

        btn_frame = ttk.Frame(self.combat_frame)
        btn_frame.grid(row=2, column=0, columnspan=3, pady=5)
        ttk.Button(btn_frame, text="Attack", command=lambda: self.handle_action("combat", "a")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Defend", command=lambda: self.handle_action("combat", "d")).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Parry", command=lambda: self.handle_action("combat", "p")).pack(side=tk.LEFT, padx=5)

    def _create_log_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Log", padding=10)
        frame.pack(fill=tk.X, pady=5)
        self.log_text = tk.Text(frame, height=15, width=60, bg="#1c2833", fg="white", state="disabled", wrap="word")
        self.log_text.pack(fill=tk.BOTH, expand=True)

    def _create_world_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="World", padding=10)
        frame.pack(fill=tk.X, pady=5)
        self.loc_name_var = tk.StringVar()
        self.time_var = tk.StringVar()
        ttk.Label(frame, text="Location:").grid(row=0, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.loc_name_var).grid(row=0, column=1, sticky="w")
        ttk.Label(frame, text="Time:").grid(row=1, column=0, sticky="w")
        ttk.Label(frame, textvariable=self.time_var).grid(row=1, column=1, sticky="w")
        self.loc_desc_text = tk.Text(frame, height=5, bg="#1c2833", fg="white", state="disabled", wrap="word", relief="flat")
        self.loc_desc_text.grid(row=2, column=0, columnspan=2, sticky="ew", pady=5)

    def _create_npc_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="People", padding=10)
        frame.pack(fill=tk.X, pady=5)
        self.npc_list = tk.Listbox(frame, height=5, bg="#1c2833", fg="white", selectbackground="#2980b9")
        self.npc_list.pack(fill=tk.X, expand=True)
        btn_frame = ttk.Frame(frame)
        btn_frame.pack(pady=5)
        ttk.Button(btn_frame, text="Talk", command=self.handle_talk_action).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Insult", command=self.handle_insult_action).pack(side=tk.LEFT, padx=5)

    def _create_action_panel(self, parent):
        frame = ttk.LabelFrame(parent, text="Actions", padding=10)
        frame.pack(fill=tk.X, pady=5)
        
        move_frame = ttk.Frame(frame)
        move_frame.pack()
        ttk.Button(move_frame, text="North", command=lambda: self.handle_action("move", "north")).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="South", command=lambda: self.handle_action("move", "south")).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="East", command=lambda: self.handle_action("move", "east")).pack(side=tk.LEFT, padx=2)
        ttk.Button(move_frame, text="West", command=lambda: self.handle_action("move", "west")).pack(side=tk.LEFT, padx=2)

        other_frame = ttk.Frame(frame)
        other_frame.pack(pady=5)
        ttk.Button(other_frame, text="Enter", command=self.handle_enter_action).pack(side=tk.LEFT, padx=2)
        ttk.Button(other_frame, text="Open Chest", command=lambda: self.handle_action("open_chest", None)).pack(side=tk.LEFT, padx=2)
        ttk.Button(other_frame, text="Disarm Chest", command=lambda: self.handle_action("disarm_chest", None)).pack(side=tk.LEFT, padx=2)

        ground_items_frame = ttk.LabelFrame(parent, text="On Ground", padding=10)
        ground_items_frame.pack(fill=tk.X, pady=5)
        self.ground_list = tk.Listbox(ground_items_frame, height=5, bg="#1c2833", fg="white", selectbackground="#2980b9")
        self.ground_list.pack(fill=tk.X, expand=True)
        ttk.Button(ground_items_frame, text="Take", command=self.handle_take_action).pack(pady=5)

        game_actions_frame = ttk.LabelFrame(parent, text="Game", padding=10)
        game_actions_frame.pack(fill=tk.X, pady=5)
        btn_frame = ttk.Frame(game_actions_frame)
        btn_frame.pack()
        ttk.Button(btn_frame, text="Save Game", command=self.handle_save_game).pack(side=tk.LEFT, padx=5)
        ttk.Button(btn_frame, text="Quit Game", command=self.on_close).pack(side=tk.LEFT, padx=5)

    def handle_save_game(self):
        """Saves the game state and logs feedback."""
        feedback = self.game.save_game()
        self.log_message(feedback)

    def handle_action(self, action_type, value):
        feedback = None
        if action_type == "move":
            feedback = self.game.handle_movement(value)
        elif action_type == "combat":
            feedback = self.game.handle_combat_turn(value)
        elif action_type == "open_chest":
            feedback = self.game.handle_open_chest()
        elif action_type == "disarm_chest":
            feedback = self.game.handle_disarm_chest()

        if feedback:
            self.log_message(feedback)
        self.check_for_combat()
        self.update_gui()

    def handle_enter_action(self):
        location = self.game.get_current_location()
        feature = location.get('features', [None])[0]
        if feature:
            feedback = self.game.handle_enter(feature)
            self.log_message(feedback)
            self.update_gui()

    def handle_item_action(self, action_type):
        try:
            selected_index = self.inv_list.curselection()[0]
            item_name = self.inv_list.get(selected_index)
            
            feedback = None
            if action_type == "use":
                feedback = self.game.handle_use_item(item_name)
            elif action_type == "drop":
                feedback = self.game.handle_drop_item(item_name)
            elif action_type == "equip":
                feedback = self.game.handle_equip_item(item_name)
            
            if feedback:
                self.log_message(feedback)
            self.update_gui()
        except IndexError:
            self.log_message("You must select an item from your inventory first.")

    def handle_take_action(self):
        try:
            selected_index = self.ground_list.curselection()[0]
            item_name = self.ground_list.get(selected_index)
            feedback = self.game.handle_take_item(item_name)
            if feedback:
                self.log_message(feedback)
            self.update_gui()
        except IndexError:
            self.log_message("You must select an item from the ground to take.")

    def handle_talk_action(self):
        try:
            npc_name = self.npc_list.get(self.npc_list.curselection())
            location = self.game.get_current_location()
            npc = next((n for n in location.get("npcs", []) if n.name == npc_name), None)
            if npc:
                self.game.player.last_npc_talked_to = npc
                dialogue_lines = npc.talk(self.game.player, self.game.game_state)
                self.show_dialogue_window(npc, dialogue_lines)
        except IndexError:
            self.log_message("Select an NPC to talk to.")

    def handle_insult_action(self):
        try:
            npc_name = self.npc_list.get(self.npc_list.curselection())
            # This is a simplified interaction for now
            self.log_message(f"You shout a rather creative insult at {npc_name}.")
        except IndexError:
            self.log_message("Select an NPC to insult.")

    def check_for_combat(self):
        location = self.game.get_current_location()
        monsters = location.get('monsters', [])
        if monsters and not self.game.in_combat:
            feedback = self.game.start_combat(monsters[0])
            self.log_message(feedback)

    def update_gui(self):
        player = self.game.player
        location = self.game.get_current_location()

        self.hp_bar['maximum'] = player.max_health
        self.hp_bar['value'] = player.health
        self.hp_var.set(f'{player.health}/{player.max_health}')
        self.mp_bar['maximum'] = player.max_mana
        self.mp_bar['value'] = player.mana
        self.mp_var.set(f'{player.mana}/{player.max_mana}')
        self.atk_var.set(str(player.attack_power))
        self.def_var.set(str(player.defense))
        self.gold_var.set(str(player.money))

        self.skills_list.delete(0, tk.END)
        for name, skill in player.skills.items():
            self.skills_list.insert(tk.END, f"{name}: Lvl {skill.level} ({skill.xp}/{skill.xp_to_next_level})")

        self.inv_list.delete(0, tk.END)
        for item in player.inventory:
            self.inv_list.insert(tk.END, item.name)

        self.ground_list.delete(0, tk.END)
        for item in location.get("items", []):
            self.ground_list.insert(tk.END, item.name)

        self.loc_name_var.set(location['name'])
        self.time_var.set(f"{self.game.game_state['time_of_day']} (Turn: {self.game.game_state['turn_count']})")
        desc_key = f"description_{self.game.game_state['time_of_day'].lower()}"
        desc = location.get(desc_key, location.get('description_day', ''))
        self.loc_desc_text.config(state='normal')
        self.loc_desc_text.delete('1.0', tk.END)
        self.loc_desc_text.insert('1.0', desc)
        self.loc_desc_text.config(state='disabled')

        self.npc_list.delete(0, tk.END)
        for npc in location.get('npcs', []):
            self.npc_list.insert(tk.END, npc.name)

        self.map_canvas.delete("all")
        if isinstance(player.location, tuple):
            player_row, player_col = player.location
            for r, row_data in enumerate(self.game.world['grid']):
                for c, loc_data in enumerate(row_data):
                    char = loc_data.get('map_char', '?')
                    color = 'yellow' if (r, c) == (player_row, player_col) else 'white'
                    self.map_canvas.create_text(c * 20 + 15, r * 20 + 15, text=char, fill=color, font=('Courier New', 12, 'bold'))

        if self.game.in_combat:
            self.combat_frame.pack(fill=tk.X, pady=5, before=self.log_text.master)
            enemy = self.game.combat_target
            self.enemy_name_var.set(enemy.name)
            self.enemy_hp_bar['maximum'] = enemy.max_health
            self.enemy_hp_bar['value'] = enemy.health
            self.enemy_hp_var.set(f'{enemy.health}/{enemy.max_health}')
        else:
            self.combat_frame.pack_forget()

        if not self.game.player.is_alive():
            tk.messagebox.showinfo("Game Over", "You have been defeated.")
            self.destroy()

    def log_message(self, message):
        self.log_text.config(state='normal')
        self.log_text.insert(tk.END, message + "\n")
        self.log_text.see(tk.END)
        self.log_text.config(state='disabled')

    def show_dialogue_window(self, npc, dialogue_lines):
        dialog = tk.Toplevel(self)
        dialog.title(f"Talking to {npc.name}")
        dialog.geometry("400x300")
        dialog.configure(bg="#34495e")
        dialog.transient(self)
        dialog.grab_set()

        text_area = tk.Text(dialog, bg="#1c2833", fg="white", wrap="word", state="disabled", font=("Helvetica", 10))
        text_area.pack(padx=10, pady=10, fill=tk.BOTH, expand=True)

        is_quest_offer = dialogue_lines and dialogue_lines[-1] == "[QUEST_OFFER]"
        display_text = "\n".join(dialogue_lines[:-1] if is_quest_offer else dialogue_lines)

        text_area.config(state='normal')
        text_area.insert(tk.END, display_text)
        text_area.config(state='disabled')

        btn_frame = ttk.Frame(dialog)
        btn_frame.pack(pady=5)

        if is_quest_offer:
            def accept_quest():
                feedback = self.game.handle_accept_quest()
                self.log_message(feedback)
                self.update_gui()
                dialog.destroy()
            ttk.Button(btn_frame, text="Accept", command=accept_quest).pack(side=tk.LEFT, padx=5)

        ttk.Button(btn_frame, text="Goodbye", command=dialog.destroy).pack(side=tk.LEFT, padx=5)

    def on_close(self):
        """Handles the window closing event, asking for confirmation."""
        if tk.messagebox.askokcancel("Quit", "Do you want to quit Thalren Vale?"):
            self.destroy()

if __name__ == '__main__':
    root = tk.Tk()
    root.withdraw() # Hide the root window
    player_name = simpledialog.askstring("Welcome to Thalren Vale", "What is your name, adventurer?")
    if player_name:
        game = Game()
        game.set_player_name(player_name)
        app = App(game)
        root.destroy() # Destroy the hidden root window
        app.mainloop()
    else:
        root = tk.Tk()
        root.withdraw() # Hide the root window
        root.destroy() # Destroy the hidden root window if player cancels name entry
