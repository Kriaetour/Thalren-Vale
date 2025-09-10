class ResourceNode:
    """
    Represents a gatherable resource in the world, like an ore vein or a tree.
    """
    def __init__(self, name, description, verb, skill, required_tool, item_yield, required_level, xp_yield):
        """
        Initializes a ResourceNode object.
        :param name: The name of the node (e.g., "Iron Vein").
        :param description: A description of the node.
        :param verb: The command used to gather from the node (e.g., "mine", "chop").
        :param skill: The name of the skill used for this node (e.g., "Mining", "Woodcutting").
        :param required_tool: The name of the item needed to gather from the node (e.g., "Pickaxe").
        :param item_yield: The Item object that is produced.
        :param required_level: The skill level required to gather.
        :param xp_yield: The amount of skill XP granted upon gathering.
        """
        self.name = name
        self.description = description
        self.verb = verb
        self.skill = skill
        self.required_tool = required_tool
        self.item_yield = item_yield
        self.required_level = required_level
        self.xp_yield = xp_yield