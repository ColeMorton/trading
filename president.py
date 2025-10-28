from abc import ABC, abstractmethod
from dataclasses import dataclass
from enum import Enum
import random


class Rank(Enum):
    THREE = 3
    FOUR = 4
    FIVE = 5
    SIX = 6
    SEVEN = 7
    EIGHT = 8
    NINE = 9
    TEN = 10
    JACK = 11
    QUEEN = 12
    KING = 13
    ACE = 14
    TWO = 15  # 2 is highest in President

    def __str__(self):
        return self.name


class Suit(Enum):
    HEARTS = "♥"
    DIAMONDS = "♦"
    CLUBS = "♣"
    SPADES = "♠"


@dataclass
class Card:
    rank: Rank
    suit: Suit

    def __str__(self):
        return f"{self.rank.name} of {self.suit.name}"


class Deck:
    def __init__(self):
        self.cards: list[Card] = []
        self.reset()

    def reset(self):
        """Create a new deck of 52 cards."""
        self.cards = [Card(rank, suit) for rank in Rank for suit in Suit]

    def shuffle(self):
        """Shuffle the deck."""
        random.shuffle(self.cards)

    def deal(self, num_players: int) -> list[list[Card]]:
        """Deal cards evenly to all players."""
        hands = [[] for _ in range(num_players)]
        for i, card in enumerate(self.cards):
            hands[i % num_players].append(card)
        return hands


class CustomRule(ABC):
    def __init__(self, name: str, description: str):
        self.name = name
        self.description = description
        self.enabled = False

    @abstractmethod
    def apply(self, game: "Game", player: "Player", *args, **kwargs) -> bool:
        """Apply the rule's effect. Return True if the rule was applied."""
        pass


class RoyalTaxRule(CustomRule):
    def __init__(self):
        super().__init__(
            "Royal Tax",
            "President must give their two lowest cards to Scum, who gives their two highest cards",
        )

    def apply(self, game: "Game", player: "Player", *args, **kwargs) -> bool:
        if not game.rankings:  # Only apply after first round
            return False

        president = game.get_player_by_rank("President")
        scum = game.get_player_by_rank("Scum")

        if not (president and scum):
            return False

        # Sort cards by rank
        president_cards = sorted(president.hand, key=lambda c: c.rank.value)
        scum_cards = sorted(scum.hand, key=lambda c: c.rank.value)

        # Exchange cards
        if len(president_cards) >= 2 and len(scum_cards) >= 2:
            # Take lowest two cards from president
            cards_to_scum = president_cards[:2]
            # Take highest two cards from scum
            cards_to_president = scum_cards[-2:]

            # Perform the exchange
            for card in cards_to_scum:
                president.hand.remove(card)
                scum.hand.append(card)

            for card in cards_to_president:
                scum.hand.remove(card)
                president.hand.append(card)

            return True
        return False


class Player:
    def __init__(self, name: str, is_ai: bool = False):
        self.name = name
        self.hand: list[Card] = []
        self.is_ai = is_ai
        self.rank: str | None = None

    def add_cards(self, cards: list[Card]):
        """Add cards to player's hand."""
        self.hand.extend(cards)

    def remove_cards(self, cards: list[Card]):
        """Remove cards from player's hand."""
        for card in cards:
            self.hand.remove(card)

    def can_play(self, cards: list[Card], current_play: list[Card] | None) -> bool:
        """Check if the player can play the selected cards."""
        if not cards:
            return False

        # All cards must be of the same rank
        if not all(card.rank == cards[0].rank for card in cards):
            return False

        # If there's no current play, any valid set is playable
        if not current_play:
            return True

        # Check if the play is valid against the current play
        if len(cards) != len(current_play):
            return False

        # Check if the rank is higher than the current play
        # Note: 2s are highest and can be played on anything
        if cards[0].rank == Rank.TWO:
            return True

        return cards[0].rank.value >= current_play[0].rank.value

    def get_valid_plays(self, current_play: list[Card] | None) -> list[list[Card]]:
        """Get all valid plays available to the player."""
        valid_plays = []

        # Group cards by rank using a defaultdict-like approach
        rank_groups: dict[Rank, list[Card]] = {}
        for card in self.hand:
            rank_groups.setdefault(card.rank, []).append(card)

        # If there's no current play, any group is valid
        if not current_play:
            valid_plays.extend(cards[:] for cards in rank_groups.values())
            return valid_plays

        # Must match the number of cards in current play
        required_count = len(current_play)
        current_rank_value = current_play[0].rank.value

        for rank, cards in rank_groups.items():
            if len(cards) >= required_count:
                if rank == Rank.TWO or rank.value >= current_rank_value:
                    valid_plays.append(cards[:required_count])

        return valid_plays


class Game:
    def __init__(self):
        self.players: list[Player] = []
        self.deck = Deck()
        self.current_player_idx = 0
        self.current_play: list[Card] | None = None
        self.passed_players: set[int] = set()
        self.finished_players: list[Player] = []
        self.custom_rules: list[CustomRule] = []
        self.rankings: dict[str, str] = {}  # Player name to rank mapping

    def add_player(self, player: Player):
        """Add a player to the game."""
        self.players.append(player)

    def setup_game(self):
        """Initialize the game state."""
        self.deck.reset()
        self.deck.shuffle()
        hands = self.deck.deal(len(self.players))
        for player, hand in zip(self.players, hands, strict=False):
            player.hand = hand
        self.current_player_idx = 0
        self.current_play = None
        self.passed_players.clear()
        self.finished_players.clear()

    def get_player_by_rank(self, rank: str) -> Player | None:
        """Get a player by their rank."""
        for player in self.players:
            if player.rank == rank:
                return player
        return None

    def play_cards(self, player: Player, cards: list[Card]) -> bool:
        """Attempt to play cards. Return True if successful."""
        if not player.can_play(cards, self.current_play):
            return False

        player.remove_cards(cards)
        self.current_play = cards

        # Check if player is out of cards
        if not player.hand:
            self.finished_players.append(player)

        # Reset passed players if 2s are played
        if cards[0].rank == Rank.TWO:
            self.passed_players.clear()
            self.current_play = None

        return True

    def pass_turn(self, player: Player):
        """Player passes their turn."""
        self.passed_players.add(self.current_player_idx)

    def next_turn(self):
        """Advance to the next player's turn."""
        self.current_player_idx = (self.current_player_idx + 1) % len(self.players)

        # If everyone has passed, reset the play
        if len(self.passed_players) >= len(self.players) - len(self.finished_players):
            self.current_play = None
            self.passed_players.clear()

    def assign_rankings(self):
        """Assign rankings based on order of finishing."""
        num_players = len(self.players)
        rankings = {
            0: "President",
            1: "Vice President",
            num_players - 2: "Vice Scum",
            num_players - 1: "Scum",
        }

        for i, player in enumerate(self.finished_players):
            if i in rankings:
                player.rank = rankings[i]
            else:
                player.rank = f"Neutral {i+1}"

    def play_round(self):
        """Play a complete round of the game."""
        self.setup_game()

        # Apply pre-round rules
        for rule in self.custom_rules:
            if rule.enabled:
                rule.apply(self, None)

        while len(self.finished_players) < len(self.players) - 1:
            current_player = self.players[self.current_player_idx]

            # Skip finished players
            if current_player in self.finished_players:
                self.next_turn()
                continue

            valid_plays = current_player.get_valid_plays(self.current_play)

            print(f"\n{current_player.name}'s turn")
            # Display hand in a more readable format
            print("Current hand:")
            hand_str = ", ".join(str(card) for card in current_player.hand)
            # Split long lines for readability
            while len(hand_str) > 80:
                split_idx = hand_str.rfind(",", 0, 80)
                if split_idx == -1:
                    split_idx = 80
                print("  " + hand_str[:split_idx])
                hand_str = hand_str[
                    split_idx + (2 if hand_str[split_idx] == "," else 0) :
                ].strip()
            if hand_str:
                print("  " + hand_str)
            if self.current_play:
                print(
                    "Current play:", ", ".join(str(card) for card in self.current_play)
                )

            if current_player.is_ai:
                # Simple AI: play the lowest valid cards or pass
                if valid_plays:
                    chosen_play = valid_plays[0]
                    self.play_cards(current_player, chosen_play)
                    print(
                        f"{current_player.name} plays: {', '.join(str(card) for card in chosen_play)}"
                    )
                else:
                    self.pass_turn(current_player)
                    print(f"{current_player.name} passes")
            # Human player interaction
            elif valid_plays:
                print("\nValid plays:")
                for i, play in enumerate(valid_plays):
                    print(f"{i+1}: {', '.join(str(card) for card in play)}")
                print("0: Pass")

                while True:
                    try:
                        choice = input(
                            "Enter your choice (0 to pass, or number to play): "
                        )
                        if choice == "0":
                            self.pass_turn(current_player)
                            print(f"{current_player.name} passes")
                            break
                        choice_idx = int(choice) - 1
                        if 0 <= choice_idx < len(valid_plays):
                            chosen_play = valid_plays[choice_idx]
                            self.play_cards(current_player, chosen_play)
                            print(
                                f"{current_player.name} plays: {', '.join(str(card) for card in chosen_play)}"
                            )
                            break
                        print("Invalid choice. Please try again.")
                    except ValueError:
                        print("Invalid input. Please enter a number.")
            else:
                print("No valid plays available - passing")
                self.pass_turn(current_player)

            # Check if this was the last play
            if len(self.finished_players) >= len(self.players) - 1:
                break

            self.next_turn()
            input("Press Enter to continue...")  # Pause between turns

        # Add remaining players to finished_players in reverse order of cards left
        remaining_players = [p for p in self.players if p not in self.finished_players]
        remaining_players.sort(key=lambda p: len(p.hand), reverse=True)
        self.finished_players.extend(remaining_players)

        # Assign rankings
        self.assign_rankings()

        # Print round summary
        print("\n" + "=" * 40)
        print("Round Complete!".center(40))
        print("=" * 40)
        print("\nFinal hands:")
        for player in self.players:
            cards_str = ", ".join(str(card) for card in player.hand)
            print(f"{player.name}: {cards_str}")
        print("\nPress Enter to see final rankings...")
        input()


def create_game_with_players(num_players: int, num_ai: int = 0) -> Game:
    """Create a new game with the specified number of human and AI players."""
    game = Game()

    # Add human players
    for i in range(num_players - num_ai):
        game.add_player(Player(f"Player {i+1}"))

    # Add AI players
    for i in range(num_ai):
        game.add_player(Player(f"AI {i+1}", is_ai=True))

    # Add custom rules
    game.custom_rules = [
        RoyalTaxRule()
        # Add other custom rules here
    ]

    return game


def play_game(total_players: int, num_ai: int) -> bool:
    """Play a complete game of President. Returns True if players want to play again."""
    # Create game
    game = create_game_with_players(total_players, num_ai)

    # Enable the Royal Tax rule
    game.custom_rules[0].enabled = True

    # Print rules and start game
    print_game_rules()
    input("\nPress Enter to start the game...")

    # Play a round
    game.play_round()

    # Print final results
    print("\n" + "=" * 40)
    print("Final Results".center(40))
    print("=" * 40)
    for i, player in enumerate(game.finished_players, 1):
        print(f"{i}. {player.name}: {player.rank}")
    print("=" * 40)

    # Ask to play again
    while True:
        play_again = input("\nPlay again? (y/n): ").lower()
        if play_again in ["y", "n"]:
            return play_again == "y"
        print("Please enter 'y' or 'n'")


def print_game_rules():
    """Print the rules of President."""
    print("\n" + "=" * 40)
    print("PRESIDENT - Card Game Rules".center(40))
    print("=" * 40)
    print("\n1. Goal: Be the first to get rid of all your cards")
    print("\n2. Card Rankings:")
    print("   2 (highest) -> A -> K -> Q -> J -> 10 -> ... -> 3 (lowest)")
    print("\n3. On your turn:")
    print("   - Play cards of the same rank")
    print("   - Must play same number of cards as current play")
    print("   - Must play higher rank than current play")
    print("   - 2s are highest and can be played on anything")
    print("   - If you can't play, you must pass")
    print("\n4. Special Rules:")
    print("   - Royal Tax: President gives 2 lowest cards to Scum")
    print("     and gets 2 highest cards in return")
    print("\n" + "=" * 40)


# Example usage
if __name__ == "__main__":
    print("\n" + "=" * 40)
    print("Welcome to President!".center(40))
    print("=" * 40)

    # Get initial game settings
    while True:
        try:
            total_players = int(input("\nEnter number of players (3-6): "))
            if 3 <= total_players <= 6:
                break
            print("Please enter a number between 3 and 6.")
        except ValueError:
            print("Please enter a valid number.")

    while True:
        try:
            num_ai = int(input(f"Enter number of AI players (0-{total_players-1}): "))
            if 0 <= num_ai < total_players:
                break
            print(f"Please enter a number between 0 and {total_players-1}.")
        except ValueError:
            print("Please enter a valid number.")

    # Main game loop
    while True:
        if not play_game(total_players, num_ai):
            print("\nThanks for playing!")
            break
