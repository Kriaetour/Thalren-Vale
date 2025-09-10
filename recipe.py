class Recipe:
    """
    Defines a crafting recipe, including ingredients and the resulting item.
    """
    def __init__(self, name, ingredients, result, station=None, skill_req=None):
        """
        Initializes a Recipe object.
        :param name: The name of the item to be crafted.
        :param ingredients: A dictionary of required item names and their quantities.
        :param result: The Item object that is created.
        :param station: The name of the station required to craft (e.g., "Forge").
        :param skill_req: A tuple containing the required skill and level (e.g., ("Crafting", 5)).
        """
        self.name = name
        self.ingredients = ingredients
        self.result = result
        self.station = station
        self.skill_req = skill_req