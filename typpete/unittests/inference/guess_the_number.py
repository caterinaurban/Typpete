guesses_made = 0

print('Hello! What is your name?\n')
name = input()

number = 233
print('Well ' + name + ',I am thinking of a number between 1 and 20.')

guess = -1
while guesses_made < 6:

    print('Take a guess: ')
    guess = int(input())

    guesses_made += 1

    if guess < number:
        print('Your guess is too low.')

    if guess > number:
        print('Your guess is too high.')

    if guess == number:
        break

if guess == number:
    print('Good job, ' + name + '! You guessed my number in ' + str(guesses_made) + ' guesses!')
else:
    print('Nope. The number I was thinking of was {0}')


# guesses_made := int
# guess := int
# name := str
# number := int
