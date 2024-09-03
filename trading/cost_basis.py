LEVELS = {
    532: 40,
    545.51: 30,
    555.06: 18
}

# Calculate the total cost and total quantity
total_cost = sum(price * quantity for price, quantity in LEVELS.items())
total_quantity = sum(LEVELS.values())

# Calculate the cost basis
cost_basis = total_cost / total_quantity

print(f"Cost Basis: {cost_basis:.2f}")
