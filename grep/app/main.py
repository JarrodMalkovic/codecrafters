import sys


def get_first_non_char_index(string, char):
    for index, c in enumerate(string):
        if c != char:
            return index

    return -1


def match_here(text, pattern):
    # Base case
    if pattern == "":
        return True, text, pattern

    # Base case
    if text == "":
        return (True, text, pattern) if pattern == "$" else (False, text, pattern)

    if pattern.startswith("\d"):
        if text[0].isdigit():
            return match_here(text[1:], pattern[2:])
        else:
            return match_here(text[1:], pattern)

    if pattern.startswith("\w"):
        if text[0].isalnum():
            return match_here(text[1:], pattern[2:])
        else:
            return match_here(text[1:], pattern)

    if pattern.startswith("[^"):
        index_of_closing_bracket = pattern.index("]")
        if not text[0] in list(pattern[2:index_of_closing_bracket]):
            return match_here(
                text[1:],
                pattern[index_of_closing_bracket + 1 :],
            )
        else:
            return False, text, pattern
    elif pattern.startswith("["):
        index_of_closing_bracket = pattern.index("]")
        if text[0] in list(pattern[2:index_of_closing_bracket]):
            return match_here(
                text[1:],
                pattern[index_of_closing_bracket + 1 :],
            )
        else:
            return False, text, pattern

    if pattern.startswith("("):
        index_of_closing_bracket = pattern.index(")")
        alternations = pattern[1:index_of_closing_bracket].split("|")

        for alternation in alternations:
            if text.startswith(alternation):
                return match_here(
                    text[len(alternation) :], pattern[index_of_closing_bracket + 1 :]
                )

        return False, text, pattern

    if pattern[0] == ".":
        return match_here(text[1:], pattern[1:])

    if pattern[0].isalnum() or pattern[0] == " ":
        if len(pattern) > 1 and pattern[1] == "?":
            if pattern[0] == text[0]:
                return match_here(text[1:], pattern[2:])
            else:
                return match_here(text, pattern[2:])

        if pattern[0] == text[0]:
            if len(pattern) > 1 and pattern[1] == "+":
                first_non_matching_char = get_first_non_char_index(text, text[0])

                if first_non_matching_char < 0:
                    return True, text, pattern

                return match_here(text[first_non_matching_char:], pattern[2:])

            return match_here(text[1:], pattern[1:])

    return False, text, pattern


def match_pattern(text, pattern):
    if pattern[0] == "^":
        found_match, text, pattern = match_here(text, pattern[1:])
        return found_match

    found_match, text, pattern = match_here(text, pattern)

    while text and pattern:
        if found_match:
            return True

        if pattern == "$":
            return False

        found_match, text, pattern = match_here(text[1:], pattern)

    return found_match


def main():
    pattern = sys.argv[2]
    input_line = sys.stdin.read()

    if sys.argv[1] != "-E":
        print("Expected first argument to be '-E'")
        exit(1)

    if match_pattern(input_line, pattern):
        exit(0)
    else:
        exit(1)


if __name__ == "__main__":
    main()
