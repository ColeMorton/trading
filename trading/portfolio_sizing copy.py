import numpy as np
import matplotlib.pyplot as plt

# Define parameters
TOTAL_PORTFOLIO_VALUE = 30000  # Example total portfolio value
ASSET_1_LEVERAGE = 4.7  # Example leverage factor for Asset 1
ASSET_2_LEVERAGE = 9.5  # Example leverage factor for Asset 2

# Generate x-axis values (from 0 to TOTAL_PORTFOLIO_VALUE, divided into 1000 points)
x = np.linspace(0, TOTAL_PORTFOLIO_VALUE, 1000)

# Calculate Leveraged Values
leveraged_value_1 = ASSET_1_LEVERAGE * x
leveraged_value_2 = ASSET_2_LEVERAGE * x

# Calculate the reversed second line
reversed_leveraged_value_2 = leveraged_value_2[::-1]

# Find the intersection point by minimizing the absolute difference
diff = np.abs(leveraged_value_1 - reversed_leveraged_value_2)
intersection_index = np.argmin(diff)

initial_asset_1_value = x[intersection_index]
initial_asset_2_value = TOTAL_PORTFOLIO_VALUE - initial_asset_1_value
total_leveraged_value = leveraged_value_1[intersection_index]

print(f"Asset 1 Initial (pre-leverage) value: ${initial_asset_1_value:.6f}")
print(f"Asset 1 Leveraged value: ${initial_asset_1_value*ASSET_1_LEVERAGE:.6f}")
print(f"Asset 2 Initial (pre-leverage) value: ${initial_asset_2_value:.6f}")
print(f"Asset 2 Leveraged value: ${initial_asset_2_value*ASSET_2_LEVERAGE:.6f}")
print(f"Total Leveraged Portfolio Value: ${total_leveraged_value:.6f}")

# Plotting the results
plt.figure(figsize=(10, 6))

# Plot for Asset 1
plt.plot(x, leveraged_value_1, label=f'Leveraged Value (Leverage = {ASSET_1_LEVERAGE})', color='b')

# Plot for Asset 2
plt.plot(x, reversed_leveraged_value_2, label=f'Leveraged Value (Leverage = {ASSET_2_LEVERAGE})', color='r')

# Plot the intersection point
plt.scatter(initial_asset_1_value, total_leveraged_value, color='g', zorder=5)
plt.text(initial_asset_1_value, total_leveraged_value, 
         f'Intersection: ({initial_asset_1_value:.6f}, {total_leveraged_value:.6f})',
         horizontalalignment='left', verticalalignment='bottom', color='green')

# Adding labels and title
plt.xlabel('Total Portfolio Value')
plt.ylabel('Leveraged Value')
plt.title('Leveraged Value vs Total Portfolio Value')
plt.legend()
plt.grid(True)

# Show the plot
plt.show()