# Python Basics - Fundamental Concepts

# 1. Variables and Data Types
name = "Divyansh"
age = 21
cgpa = 8.2
is_student = True

print("Name:", name)
print("Age:", age)
print("CGPA:", cgpa)
print("Student:", is_student)


# 2. Arithmetic Operations
a = 20
b = 10

print("Addition:", a + b)
print("Subtraction:", a - b)
print("Multiplication:", a * b)
print("Division:", a / b)


# 3. User Input
number = int(input("Enter a number: "))
print("Square:", number ** 2)


# 4. Conditional Statements
if number > 0:
    print("Positive number")
elif number < 0:
    print("Negative number")
else:
    print("Zero")


# 5. Loops
print("Numbers from 1 to 5:")

for i in range(1, 6):
    print(i)


# 6. Lists
subjects = ["Python", "AI", "Machine Learning"]

print("Subjects:", subjects)
print("First subject:", subjects[0])


# 7. Functions
def calculate_average(x, y):
    return (x + y) / 2


result = calculate_average(80, 90)
print("Average:", result)


# 8. String Operations
message = "Artificial Intelligence"

print("Uppercase:", message.upper())
print("Length:", len(message))


# 9. Dictionary
student = {
    "name": "Divyansh",
    "course": "B.Tech CSE",
    "year": 4
}

print("Student Details:", student)