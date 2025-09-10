import textwrap

def print_bordered(title, content_lines, width=80):
    """Prints a title and a list of content lines inside a box."""
    # Header
    title_text = f" {title} "
    if len(title_text) > width - 2: # Truncate if title is too long
        title_text = title_text[:width - 7] + "... "
    
    padding_total = (width - 2) - len(title_text)
    padding_left = padding_total // 2
    padding_right = padding_total - padding_left
    print("\n" + "╔" + ("═" * padding_left) + title_text + ("═" * padding_right) + "╗")

    # Content
    if not content_lines:
        print("║" + " " * (width - 2) + "║")
    else:
        for line in content_lines:
            # Wrap long lines to fit within the border
            wrapped_lines = textwrap.wrap(line, width=width - 4)
            if not wrapped_lines: # Handle empty lines for spacing
                print("║" + " " * (width - 2) + "║")
                continue
            for wrapped_line in wrapped_lines:
                padding = width - 4 - len(wrapped_line)
                print("║ " + wrapped_line + " " * padding + " ║")
    
    # Footer
    print("╚" + "═" * (width - 2) + "╝")