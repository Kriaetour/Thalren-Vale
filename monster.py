from character import Character
from ability import Ability
from item import Item, Weapon, Armor, pouch_of_gold

# --- Monster-specific Abilities ---
goblin_shank = Ability("Shank", "A quick, nasty stab.", mana_cost=4, effect={'type': 'damage', 'amount': 12})
orc_smash = Ability("Smash", "A powerful, armor-crushing blow.", mana_cost=10, effect={'type': 'damage', 'amount': 25})
troll_regen = Ability("Regenerate", "The troll's flesh knits itself back together.", mana_cost=8, effect={'type': 'heal', 'amount': 20})
specter_drain = Ability("Life Drain", "A chilling touch that saps your life force.", mana_cost=6, effect={'type': 'damage', 'amount': 18})
shadowflame = Ability("Shadowflame", "Unleashes a wave of dark fire.", mana_cost=20, effect={'type': 'damage', 'amount': 50})
mountains_wrath = Ability("Mountain's Wrath", "Slams the ground, causing a shockwave that stuns.", mana_cost=15, status_effect={'type': 'stun', 'duration': 1})
slime_poison = Ability("Poison Spit", "Spits a glob of acidic poison.", mana_cost=5, status_effect={'type': 'poison', 'damage': 5, 'duration': 3})

# --- Crafting Components ---
goblin_scraps = Item("Goblin Scraps", "Tattered bits of leather and cloth.", value=1)
iron_ore = Item("Iron Ore", "A chunk of unrefined iron.", value=5)

# --- Boss Loot ---
obsidian_blade = Weapon("Obsidian Blade", "A sword forged from the heart of the mountain, humming with dark energy.", value=1000, attack_bonus=25)
shadow_plate = Armor("Shadow-Forged Plate", "Armor crafted from solidified shadows, offering immense protection.", value=1200, defense_bonus=20)

class Monster(Character):
    """
    Base class for all monsters in the game.
    """
    def __init__(self, name, health, attack_power, defense, xp_yield=0, description="A fearsome monster."):
        super().__init__(name, health, attack_power, defense, description)
        self.xp_yield = xp_yield

class Goblin(Monster):
    """A small, weak, but mischievous monster."""
    def __init__(self, name="Goblin"):
        super().__init__(
            name=name,
            health=30,
            attack_power=8,
            defense=2,
            xp_yield=25,
            description="A small, green-skinned creature with a mischievous and cruel glint in its eyes."
        )
        self.loot_table.append(goblin_scraps)
        self.abilities.append(goblin_shank)

class Orc(Monster):
    """A large, brutish monster with high attack power."""
    def __init__(self, name="Orc"):
        super().__init__(
            name=name,
            health=80,
            attack_power=15,
            defense=5,
            xp_yield=100,
            description="A hulking, brutish humanoid with green-grey skin and prominent tusks."
        )
        self.loot_table.append(iron_ore)
        self.abilities.append(orc_smash)

class Slime(Monster):
    """A gooey creature that is difficult to damage effectively."""
    def __init__(self, name="Slime"):
        super().__init__(
            name=name,            # Slimes have a chance to apply poison
            health=50,
            attack_power=5,
            defense=10,
            xp_yield=15,
            description="A gelatinous, amorphous blob that quivers and shifts. It seems to be made of a corrosive substance."
        )
        self.abilities.append(slime_poison)

class Skeleton(Monster):
    """A reanimated skeleton, brittle but persistent."""
    def __init__(self, name="Skeleton"):
        super().__init__(
            name=name,
            health=40,
            attack_power=10,
            defense=3,
            xp_yield=30,
            description="A clattering collection of bones, held together by dark magic."
        )

class Zombie(Monster):
    """A slow, decaying undead creature."""
    def __init__(self, name="Zombie"):
        super().__init__(
            name=name,
            health=70,
            attack_power=10,
            defense=1,
            xp_yield=40,
            description="A slow, decaying corpse that groans with an insatiable hunger."
        )

class DireWolf(Monster):
    """A large and aggressive wolf with a powerful bite."""
    def __init__(self, name="Dire Wolf"):
        super().__init__(
            name=name,
            health=60,
            attack_power=18,
            defense=4,
            xp_yield=75,
            description="A large and aggressive wolf with a powerful bite and matted grey fur."
        )

class Troll(Monster):
    """A hulking troll with immense strength and resilience."""
    def __init__(self, name="Troll"):
        super().__init__(
            name=name,
            health=120,
            attack_power=12,
            defense=8,
            xp_yield=250,
            description="A hulking troll with immense strength and tough, green skin."
        )
        self.loot_table.append(Item("Word of Bolt", "A rune carved in the shape of a lightning strike.", value=100))
        self.abilities.append(troll_regen)

class Specter(Monster):
    """An ethereal ghost that drains life force and is hard to defend against."""
    def __init__(self, name="Specter"):
        super().__init__(
            name=name,
            health=40,
            attack_power=20,
            defense=0,
            xp_yield=150,
            description="An ethereal, translucent figure that drifts silently, its eyes burning with cold light."
        )
        self.loot_table.append(Item("Word of Fire", "A rune that hums with intense heat.", value=100))
        self.abilities.append(specter_drain)
        
class GiantSpider(Monster):
    """A large, venomous spider."""
    def __init__(self, name="Giant Spider"):
        super().__init__(
            name=name,
            health=45,
            attack_power=10,
            defense=3,
            xp_yield=50,
            description="A monstrous arachnid, its many eyes gleam with malice and its fangs drip with venom."
        )
        self.loot_table.append(Item("Word of Venom", "A rune that drips with a dark, magical toxin.", value=100))
        self.abilities.append(Ability("Venomous Bite", "A bite that injects a potent venom.", mana_cost=0, status_effect={'type': 'poison', 'damage': 3, 'duration': 4}))

class Bandit(Monster):
    """A human brigand, quick and cunning."""
    def __init__(self, name="Bandit"):
        super().__init__(
            name=name,
            health=55,
            attack_power=12,
            defense=4,
            xp_yield=60,
            description="A rough-looking human, clad in worn leather armor, with a glint of desperation in their eyes."
        )
        self.loot_table.append(Item("Lockpick", "A slender piece of metal used for picking locks.", value=10))

class RiverSerpent(Monster):
    """A large, aquatic reptile."""
    def __init__(self, name="River Serpent"):
        super().__init__(
            name=name,
            health=70,
            attack_power=14,
            defense=6,
            xp_yield=80,
            description="A massive, scaled serpent that glides silently through the water, its eyes fixed on prey."
        )
        self.loot_table.append(Item("Word of Water", "A rune that feels cool and damp to the touch.", value=100))

class WildBoar(Monster):
    """A ferocious wild boar."""
    def __init__(self, name="Wild Boar"):
        super().__init__(
            name=name,
            health=60,
            attack_power=11,
            defense=5,
            xp_yield=55,
            description="A large, aggressive boar with sharp tusks and a bad temper."
        )
        self.loot_table.append(Item("Leather", "A piece of cured animal hide.", value=10))

class AshboundCultist(Monster):
    """A fanatical cultist, empowered by dark magic."""
    def __init__(self, name="Ashbound Cultist"):
        super().__init__(
            name=name,
            health=65,
            attack_power=13,
            defense=3,
            xp_yield=90,
            description="A robed figure muttering incantations, their eyes burning with fanaticism."
        )
        self.loot_table.append(Item("Word of Shadow", "A rune that seems to absorb the light around it.", value=100))
        self.abilities.append(Ability("Dark Bolt", "Hurls a bolt of dark energy.", mana_cost=7, effect={'type': 'damage', 'amount': 15}))

class FireSpirit(Monster):
    """An elemental spirit of fire."""
    def __init__(self, name="Fire Spirit"):
        super().__init__(
            name=name,
            health=50,
            attack_power=16,
            defense=2,
            xp_yield=110,
            description="A swirling vortex of flame and smoke, radiating intense heat."
        )
        self.loot_table.append(Item("Word of Fire", "A rune that hums with intense heat.", value=100))
        self.abilities.append(Ability("Cinder Blast", "Unleashes a burst of fiery cinders.", mana_cost=8, effect={'type': 'damage', 'amount': 20}))

class GiantEagle(Monster):
    """A majestic but territorial giant eagle."""
    def __init__(self, name="Giant Eagle"):
        super().__init__(
            name=name,
            health=75,
            attack_power=17,
            defense=6,
            xp_yield=130,
            description="A magnificent eagle with a wingspan of twenty feet, its talons look razor sharp."
        )
        self.loot_table.append(Item("Word of Air", "A rune that feels light and seems to float in your palm.", value=100))
        self.loot_table.append(Item("Word of Bolt", "A rune carved in the shape of a lightning strike.", value=100))

class SpectralWolf(Monster):
    """A ghostly wolf that phases in and out of existence."""
    def __init__(self, name="Spectral Wolf"):
        super().__init__(
            name=name,
            health=40,
            attack_power=15,
            defense=0, # Spectral, so physical defense is low
            xp_yield=120,
            description="A translucent, shimmering wolf, its howls send shivers down your spine."
        )
        self.abilities.append(Ability("Spirit Rend", "A ghostly attack that bypasses some defenses.", mana_cost=0, effect={'type': 'damage', 'amount': 15}))

class Thalraxos(Monster):
    """The final boss of the deep mountain dungeon."""
    def __init__(self, name="Thalraxos"):
        super().__init__(
            name=name,
            health=500,
            attack_power=35,
            defense=15,
            xp_yield=2000,
            description="A colossal, ancient golem of obsidian and shadow, its eyes burn with a malevolent, purple light. This is Thalraxos, the Shadow of the Mountain."
        )
        self.abilities.append(shadowflame)
        self.abilities.append(mountains_wrath)
        self.loot_table.append(obsidian_blade)
        self.loot_table.append(shadow_plate)
        self.loot_table.append(Item("Word of Power", "A rune that crackles with raw, untamed energy.", value=500))

class Mimic(Monster):
    """A devious creature that disguises itself as a treasure chest."""
    def __init__(self, name="Mimic"):
        super().__init__(
            name=name,
            health=100,
            attack_power=20,
            defense=12,
            xp_yield=300,
            description="A monstrous predator with a cavernous mouth lined with sharp teeth, perfectly disguised as an ordinary chest."
        )
        self.loot_table.append(pouch_of_gold)

class ShadowWolf(Monster):
    """A spectral wolf infused with deeper shadow magic, making it faster and more dangerous."""
    def __init__(self, name="Shadow-Marked Wolf"):
        super().__init__(
            name=name,
            health=60,
            attack_power=18,
            defense=2,
            xp_yield=150,
            description="A ghostly wolf, its form flickering like a dying flame. Dark, shifting symbols mark its ethereal fur."
        )
        self.abilities.append(Ability("Shadow Bite", "A chilling bite that seems to drain your resolve.", mana_cost=5, status_effect={'type': 'attack_debuff', 'amount': 2, 'duration': 3}))

class ShadowCultist(Monster):
    """A cultist who has delved deeper into shadow magic."""
    def __init__(self, name="Shadow-Marked Cultist"):
        super().__init__(
            name=name,
            health=80,
            attack_power=16,
            defense=5,
            xp_yield=180,
            description="This cultist is adorned with glowing, shifting runes. They wield the shadows with terrifying ease."
        )
        self.abilities.append(Ability("Shadow Bolt", "Hurls a bolt of pure shadow that chills to the bone.", mana_cost=10, effect={'type': 'damage', 'amount': 25}))

class CultFanatic(Monster):
    """A powerful cultist who wields dangerous wordbinding magic."""
    def __init__(self, name="Cult Fanatic"):
        super().__init__(
            name=name,
            health=150,
            attack_power=20,
            defense=10,
            xp_yield=400,
            description="Clad in dark robes adorned with glowing, shifting runes, this fanatic crackles with raw power. They are a master of the cult's dark arts."
        )
        self.abilities.append(Ability("Shadowflame", "Unleashes a wave of dark fire.", mana_cost=20, effect={'type': 'damage', 'amount': 50}))
        self.abilities.append(Ability("Word of Pain", "A cursed word that inflicts ongoing shadow damage.", mana_cost=15, status_effect={'type': 'poison', 'damage': 10, 'duration': 3}))

class CultistBandit(Monster):
    """A bandit who has been swayed by the promises of the cult."""
    def __init__(self, name="Cultist-Aligned Bandit"):
        super().__init__(
            name=name,
            health=70,
            attack_power=14,
            defense=5,
            xp_yield=100,
            description="This bandit's eyes have a wild, fanatical gleam. They wear a strange, dark talisman around their neck."
        )
        self.loot_table.append(Item("Cult-marked Talisman", "A dark stone talisman carved with the cult's unsettling symbol.", value=0, quest_item=True))

class BanditLeader(Monster):
    """A charismatic and dangerous bandit leader."""
    def __init__(self, name="Bandit Leader"):
        super().__init__(
            name=name,
            health=100,
            attack_power=15,
            defense=8,
            xp_yield=150,
            description="A cunning-looking leader, clad in stolen finery over worn leather. They command respect and fear."
        )
        self.loot_table.append(pouch_of_gold)
        self.abilities.append(Ability("Rallying Cry", "A shout that inspires nearby allies, increasing their attack.", mana_cost=10, status_effect={'type': 'attack_buff', 'amount': 3, 'duration': 3}))