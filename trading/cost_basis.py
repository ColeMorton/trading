LEVELS = {
    528.22: 35,
    545.21: 15,
    551.01: 7,
    558.47: 3
}

# Calculate the total cost and total quantity
total_cost = sum(price * quantity for price, quantity in LEVELS.items())
total_quantity = sum(LEVELS.values())

# Calculate the cost basis
cost_basis = total_cost / total_quantity

print(f"Cost Basis: {cost_basis:.2f}")
