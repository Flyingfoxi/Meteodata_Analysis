import matplotlib.pyplot as plt
import numpy as np

# Sample data
x = np.linspace(0, 10, 100)
y = np.sin(x)

# Create the plot
plt.plot(x, y)

# Define the y-tick positions
y_ticks = [-1, -0.5, 0, 0.5, 1]

# Create labels that combine numbers and text
y_labels = [f'{tick} Low' if tick == -1 else
            f'{tick} Neutral' if tick == 0 else
            f'{tick} High' if tick == 1 else
            f"{tick}" for tick in y_ticks]

# Set the y-ticks and labels
plt.yticks(y_ticks, y_labels)

# Label the axes
plt.xlabel('X-axis')
plt.ylabel('Y-axis (Custom Labels with Numbers)')

# Show the plot
plt.show()
