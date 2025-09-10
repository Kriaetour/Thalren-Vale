import random

def enemy_decision(enemy_hp, enemy_max_hp, player_last_action):
    """
    Determines the enemy's action based on weighted probabilities.

    :param enemy_hp: Current HP of the enemy.
    :param enemy_max_hp: Maximum HP of the enemy.
    :param player_last_action: The player's last action ('a', 'd', 'p').
    :return: A tuple containing the chosen action ('attack', 'defend', 'parry') and the final weights.
    """
    # Base weights
    weights = {
        'attack': 50,
        'defend': 25,
        'parry': 25
    }

    # Modify weights based on context
    # 1. Enemy HP is low
    if (enemy_hp / enemy_max_hp) < 0.3:
        weights['defend'] += 20

    # 2. Player's last action
    if player_last_action == 'a':
        weights['defend'] += 15
    elif player_last_action == 'd':
        weights['parry'] += 15
    elif player_last_action == 'p':
        weights['attack'] += 15

    # Normalize weights to ensure they sum to 100
    total_weight = sum(weights.values())
    normalized_weights = {action: (weight / total_weight) for action, weight in weights.items()}

    # Randomly select an action based on the normalized weights
    actions = list(normalized_weights.keys())
    probabilities = list(normalized_weights.values())
    
    chosen_action = random.choices(actions, weights=probabilities, k=1)[0]

    # For debugging, let's format the final weights as percentages
    final_weights_percent = {action: f"{prob:.1%}" for action, prob in normalized_weights.items()}

    return chosen_action, final_weights_percent