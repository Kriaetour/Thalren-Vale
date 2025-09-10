"""
This file contains templates for generating NPC dialogue.
"""

DIALOGUE_TEMPLATES = {
    # --- General Greetings ---
    'greeting_friendly': [
        "Well met, {player_name}.",
        "Hello there, adventurer.",
        "Good to see you.",
    ],
    'greeting_neutral': [
        "What is it?",
        "Yes?",
        "Can I help you?",
    ],
    'greeting_grumpy': [
        "What do you want?",
        "Hmph. Make it quick.",
        "Don't waste my time.",
    ],

    # --- Reactionary Greetings ---
    'greeting_angry': [
        "You again? I have nothing to say to you.",
        "I haven't forgotten what you did. Be gone.",
        "Your presence is not welcome here.",
    ],
    'greeting_grateful': [
        "Ah, {player_name}! It's so good to see you again!",
        "My friend! Welcome. How can I help you?",
        "I'm glad you're here. I'll never forget your help.",
    ],

    # --- Personality Comments ---
    'comment_talkative': [
        "It's a fine day for a chat, isn't it?",
        "I was just thinking about...",
        "You know, that reminds me of a story.",
    ]
}