class HedgeFund:
    def __init__(self, manager_name, initial_fund_size, manager_stake=1):
        # Initialize the hedge fund with manager's details and the initial fund size
        self.manager_name = manager_name
        self.total_fund_value = initial_fund_size
        self.stakes = {
            manager_name: manager_stake
        }  # Manager has an initial 50% stake by default
        self.cash_available = {manager_name: initial_fund_size * manager_stake}

    def get_stake(self, participant):
        # Returns the current stake percentage of a participant
        return self.stakes.get(participant, 0)

    def update_fund_value(self, new_value):
        # Updates the total value of the hedge fund (after profits or losses)
        self.total_fund_value = new_value
        for participant, stake in self.stakes.items():
            self.cash_available[participant] = new_value * stake

    def adjust_stake(self, participant, stake_change_percentage):
        # Adjust the stake of the participant while ensuring total stake equals 100%
        current_stake = self.get_stake(participant)

        if current_stake >= 0.5:
            new_stake = current_stake + stake_change_percentage * (
                1 - (current_stake - 0.5) * 2
            )
        else:
            new_stake = current_stake + stake_change_percentage

        # Cap new stake between 0 and 1 (100%)
        new_stake = min(max(new_stake, 0), 1)

        # Update or remove the participant's stake
        if new_stake == 0 and participant in self.stakes:
            del self.stakes[participant]
            del self.cash_available[participant]
        else:
            self.stakes[participant] = new_stake

        # After adjusting the stake, normalize to ensure total stake equals 100%
        self.normalize_stakes()

    def normalize_stakes(self):
        # Normalize the stakes so that the total is exactly 100%
        total_stakes = sum(self.stakes.values())
        if total_stakes == 0:
            return  # Prevent division by zero if no stakes exist

        for participant in self.stakes:
            self.stakes[participant] /= total_stakes
            self.cash_available[participant] = (
                self.stakes[participant] * self.total_fund_value
            )

    def buy_stake(self, participant, amount):
        # Ensure the participant exists in the stakes and cash_available dictionaries
        if participant not in self.stakes:
            self.stakes[participant] = 0
            self.cash_available[participant] = 0

        # Increase the total fund value by the amount the participant invests
        self.total_fund_value += amount

        # Calculate the stake change percentage
        stake_change_percentage = amount / self.total_fund_value

        # Adjust the participant's stake based on the purchase
        self.adjust_stake(participant, stake_change_percentage)

    def sell_stake(self, participant, amount):
        # Ensure participant has a stake before selling
        if participant not in self.stakes:
            raise ValueError("Participant does not have a stake to sell.")

        # Calculate the stake change percentage based on the amount to be sold
        stake_change_percentage = -amount / self.total_fund_value

        # Adjust the participant's stake based on the sale
        self.adjust_stake(participant, stake_change_percentage)

    def __str__(self):
        # Provides a summary of fund participants and their stakes
        fund_summary = f"Total Fund Value: ${self.total_fund_value}\nParticipants:\n"
        for participant, stake in self.stakes.items():
            fund_summary += f"{participant}: {stake * 100:.2f}% stake (${self.cash_available[participant]:,.2f})\n"
        return fund_summary


# Example Usage
if __name__ == "__main__":
    # Creating a fund with the manager "Cole" and a total fund size of $10M
    fund = HedgeFund(manager_name="Cole", initial_fund_size=10_000)

    # Other participants can buy stakes
    fund.buy_stake("Nana", 10_000)  # Nana buys a $10,000 stake
    fund.buy_stake("Nana", 10_000)  # Nana buys a $10,000 stake

    # Print current fund status
    print(fund)
