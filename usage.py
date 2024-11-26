from tempus import Tempus

# Create instance
tempus = Tempus()

# Example Latin sentence
latin = "et nos praeterierint. homines enim sumus et occupati officiis subsicivisque temporibus ista curamus"

# Get and print analysis
print(tempus.analyze(latin)) 