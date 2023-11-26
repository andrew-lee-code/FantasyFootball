import random
import time

OWNERS = ["Andrew", "Craig", "Dalton", "Jake", "Justin", "Matt", "Mike", "Paul", "Selim", "Taylor"]
WINNER = "Selim"
WINNERS_CHOICE = 3

OWNERS.remove(WINNER)
random.shuffle(OWNERS)
OWNERS.insert(WINNERS_CHOICE - 1, WINNER)

for i in range(0, len(OWNERS)):
    time.sleep(1)  # Add dramatic pauses
    print(f"{i+1}.) {OWNERS[i]}")

# poopoo
