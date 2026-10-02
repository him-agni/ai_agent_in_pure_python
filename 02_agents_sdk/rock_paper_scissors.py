import random
import time

CHOICES = ["rock", "paper", "scissors"]

EMOJIS = {
    "rock": "🪨",
    "paper": "📄",
    "scissors": "✂️"
}

WINNING_COMBOS = {
    "rock": "scissors",
    "paper": "rock",
    "scissors": "paper"
}

INPUT_MAP = {
    "1": "rock",
    "r": "rock",
    "rock": "rock",
    "2": "paper",
    "p": "paper",
    "paper": "paper",
    "3": "scissors",
    "s": "scissors",
    "scissors": "scissors"
}


def print_header():
    print("=" * 45)
    print("   🎮 ROCK, PAPER, SCISSORS GAME 🎮   ")
    print("=" * 45)


def get_user_choice():
    while True:
        print("\nChoose your move:")
        print("  1. Rock     (r / 1)")
        print("  2. Paper    (p / 2)")
        print("  3. Scissors (s / 3)")
        print("  Q. Quit     (q)")
        
        user_input = input("\nYour choice: ").strip().lower()
        
        if user_input in ["q", "quit", "exit"]:
            return None
        
        if user_input in INPUT_MAP:
            return INPUT_MAP[user_input]
        
        print("\n❌ Invalid choice! Please try again.")


def determine_winner(player, computer):
    if player == computer:
        return "tie"
    elif WINNING_COMBOS[player] == computer:
        return "player"
    else:
        return "computer"


def play_game():
    player_score = 0
    computer_score = 0
    ties = 0
    round_num = 1

    print_header()

    while True:
        print(f"\n--- Round {round_num} ---")
        player_choice = get_user_choice()

        if player_choice is None:
            print("\nThanks for playing!")
            break

        computer_choice = random.choice(CHOICES)

        print("\nRock... Paper... Scissors... Shoot! 💥")
        time.sleep(0.5)

        print(f"\n You chose:     {player_choice.capitalize()} {EMOJIS[player_choice]}")
        print(f" Computer chose: {computer_choice.capitalize()} {EMOJIS[computer_choice]}")

        winner = determine_winner(player_choice, computer_choice)

        if winner == "tie":
            print("\n🤝 It's a tie!")
            ties += 1
        elif winner == "player":
            print("\n🎉 You win this round!")
            player_score += 1
        else:
            print("\n💻 Computer wins this round!")
            computer_score += 1

        print(f"\nScoreboard -> You: {player_score} | Computer: {computer_score} | Ties: {ties}")
        round_num += 1

    print("\n" + "=" * 45)
    print("               FINAL SCORE               ")
    print(f" You: {player_score}  |  Computer: {computer_score}  |  Ties: {ties}")
    
    if player_score > computer_score:
        print("🏆 Congratulations! You beat the computer!")
    elif computer_score > player_score:
        print("🤖 Computer wins the match! Better luck next time!")
    else:
        print("🤝 The overall game ended in a tie!")
    print("=" * 45 + "\n")


if __name__ == "__main__":
    play_game()
