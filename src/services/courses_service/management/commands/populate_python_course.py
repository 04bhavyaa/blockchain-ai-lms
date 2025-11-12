"""
Django management command to populate Introduction to Python course with lessons and quizzes
"""
from django.core.management.base import BaseCommand
from src.services.courses_service.models import Course, Lesson, Quiz, Question, Answer


class Command(BaseCommand):
    help = 'Populate Introduction to Python course with lessons and quizzes'

    def handle(self, *args, **options):
        self.stdout.write('Populating Introduction to Python course...')

        # Find the Introduction to Python course
        try:
            course = Course.objects.get(title__icontains='Introduction to Python')
        except Course.DoesNotExist:
            self.stdout.write(self.style.ERROR('Introduction to Python course not found!'))
            self.stdout.write('Available courses:')
            for c in Course.objects.all():
                self.stdout.write(f'  - {c.title}')
            return

        # Clear existing lessons and quizzes for this course
        Lesson.objects.filter(course=course).delete()
        Quiz.objects.filter(course=course).delete()

        self.stdout.write(f'Found course: {course.title} (ID: {course.id})')

        # Create Module 1: Python Basics
        self.stdout.write('\nCreating Module 1: Python Basics')
        
        lesson1 = Lesson.objects.create(
            course=course,
            module_number=1,
            lesson_number=1,
            title='Getting Started with Python',
            content='''
# Getting Started with Python

Welcome to the world of Python programming! Python is one of the most popular programming languages today.

## What is Python?

Python is a high-level, interpreted programming language known for its simplicity and readability. Created by Guido van Rossum and first released in 1991, Python has become one of the most widely used programming languages in the world.

## Why Learn Python?

1. **Easy to Learn**: Python's syntax is clear and intuitive, making it perfect for beginners
2. **Versatile**: Used in web development, data science, AI, automation, and more
3. **Strong Community**: Extensive libraries and helpful community support
4. **High Demand**: Python developers are in high demand across industries

## Your First Python Program

Let's write the classic "Hello, World!" program:

```python
print("Hello, World!")
```

When you run this code, it will display: `Hello, World!`

## Python Syntax Basics

Python uses indentation to define code blocks. Here's an example:

```python
# This is a comment
name = "Alice"
age = 25

if age >= 18:
    print(f"{name} is an adult")
else:
    print(f"{name} is a minor")
```

## Setting Up Python

1. Download Python from python.org
2. Install Python (check "Add Python to PATH")
3. Open terminal/command prompt
4. Type `python --version` to verify installation

You're now ready to start coding in Python!
            ''',
            duration_minutes=15,
            order=1
        )
        self.stdout.write(f'  ✓ Created: {lesson1.title}')

        lesson2 = Lesson.objects.create(
            course=course,
            module_number=1,
            lesson_number=2,
            title='Variables and Data Types',
            content='''
# Variables and Data Types

In Python, variables are containers for storing data values. Python has several built-in data types.

## Creating Variables

Python has no command for declaring a variable. A variable is created when you first assign a value to it:

```python
x = 5
y = "Hello"
z = 3.14
```

## Basic Data Types

### 1. Numbers
Python supports integers, floating-point numbers, and complex numbers:

```python
# Integer
age = 25

# Float
price = 19.99

# Complex
complex_num = 3 + 4j
```

### 2. Strings
Strings are sequences of characters enclosed in quotes:

```python
name = "Alice"
message = 'Hello, World!'
multiline = """This is
a multiline
string"""
```

### 3. Boolean
Boolean values are either True or False:

```python
is_student = True
has_graduated = False
```

### 4. None
None represents the absence of a value:

```python
result = None
```

## Type Checking

Use the `type()` function to check variable types:

```python
x = 5
print(type(x))  # <class 'int'>

name = "Alice"
print(type(name))  # <class 'str'>
```

## Type Conversion

Convert between types using built-in functions:

```python
# String to int
age = int("25")

# Int to string
age_str = str(25)

# String to float
price = float("19.99")
```

## Practice Exercise

Try this code:

```python
# Create variables
name = "Bob"
age = 30
height = 5.9
is_programmer = True

# Print variable information
print(f"Name: {name}, Type: {type(name)}")
print(f"Age: {age}, Type: {type(age)}")
print(f"Height: {height}, Type: {type(height)}")
print(f"Is Programmer: {is_programmer}, Type: {type(is_programmer)}")
```
            ''',
            duration_minutes=20,
            order=2
        )
        self.stdout.write(f'  ✓ Created: {lesson2.title}')

        lesson3 = Lesson.objects.create(
            course=course,
            module_number=1,
            lesson_number=3,
            title='Operators and Expressions',
            content='''
# Operators and Expressions

Operators are special symbols that perform operations on variables and values.

## Arithmetic Operators

```python
a = 10
b = 3

print(a + b)  # Addition: 13
print(a - b)  # Subtraction: 7
print(a * b)  # Multiplication: 30
print(a / b)  # Division: 3.333...
print(a // b) # Floor division: 3
print(a % b)  # Modulus: 1
print(a ** b) # Exponentiation: 1000
```

## Comparison Operators

```python
x = 5
y = 10

print(x == y)  # Equal to: False
print(x != y)  # Not equal: True
print(x < y)   # Less than: True
print(x > y)   # Greater than: False
print(x <= y)  # Less than or equal: True
print(x >= y)  # Greater than or equal: False
```

## Logical Operators

```python
age = 25
has_license = True

# AND operator
can_drive = age >= 18 and has_license
print(can_drive)  # True

# OR operator
is_student = False
is_senior = False
gets_discount = is_student or is_senior
print(gets_discount)  # False

# NOT operator
is_adult = age >= 18
is_minor = not is_adult
print(is_minor)  # False
```

## Assignment Operators

```python
x = 10

x += 5  # Same as: x = x + 5
print(x)  # 15

x *= 2  # Same as: x = x * 2
print(x)  # 30

x -= 10  # Same as: x = x - 10
print(x)  # 20
```

## String Operations

```python
# Concatenation
first_name = "John"
last_name = "Doe"
full_name = first_name + " " + last_name
print(full_name)  # John Doe

# Repetition
laugh = "Ha" * 3
print(laugh)  # HaHaHa

# Membership
text = "Hello, World!"
print("Hello" in text)  # True
print("Python" in text)  # False
```

## Practice Challenge

Calculate the area and perimeter of a rectangle:

```python
length = 10
width = 5

area = length * width
perimeter = 2 * (length + width)

print(f"Area: {area}")
print(f"Perimeter: {perimeter}")
```
            ''',
            duration_minutes=25,
            order=3
        )
        self.stdout.write(f'  ✓ Created: {lesson3.title}')

        # Create Module 2: Control Flow
        self.stdout.write('\nCreating Module 2: Control Flow')
        
        lesson4 = Lesson.objects.create(
            course=course,
            module_number=2,
            lesson_number=1,
            title='Conditional Statements',
            content='''
# Conditional Statements

Conditional statements allow your program to make decisions and execute different code based on conditions.

## If Statement

```python
age = 18

if age >= 18:
    print("You are an adult")
```

## If-Else Statement

```python
temperature = 25

if temperature > 30:
    print("It's hot outside")
else:
    print("It's not too hot")
```

## If-Elif-Else Statement

```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
elif score >= 60:
    grade = "D"
else:
    grade = "F"

print(f"Your grade is: {grade}")
```

## Nested If Statements

```python
age = 20
has_id = True

if age >= 18:
    if has_id:
        print("Entry granted")
    else:
        print("ID required")
else:
    print("Too young to enter")
```

## Multiple Conditions

```python
username = "alice"
password = "secret123"

if username == "alice" and password == "secret123":
    print("Login successful")
else:
    print("Invalid credentials")
```

## Ternary Operator

Python also supports a shorthand if-else:

```python
age = 20
status = "Adult" if age >= 18 else "Minor"
print(status)
```

## Practice Exercise

Create a simple calculator:

```python
num1 = 10
num2 = 5
operation = "+"

if operation == "+":
    result = num1 + num2
elif operation == "-":
    result = num1 - num2
elif operation == "*":
    result = num1 * num2
elif operation == "/":
    result = num1 / num2
else:
    result = "Invalid operation"

print(f"{num1} {operation} {num2} = {result}")
```
            ''',
            duration_minutes=20,
            order=4
        )
        self.stdout.write(f'  ✓ Created: {lesson4.title}')

        lesson5 = Lesson.objects.create(
            course=course,
            module_number=2,
            lesson_number=2,
            title='Loops in Python',
            content='''
# Loops in Python

Loops allow you to execute a block of code repeatedly.

## For Loop

The for loop iterates over a sequence (list, tuple, string, etc.):

```python
# Loop through a list
fruits = ["apple", "banana", "cherry"]
for fruit in fruits:
    print(fruit)

# Loop through a string
for char in "Python":
    print(char)

# Loop through a range
for i in range(5):
    print(i)  # Prints 0, 1, 2, 3, 4
```

## Range Function

The range() function generates a sequence of numbers:

```python
# range(stop)
for i in range(5):
    print(i)  # 0, 1, 2, 3, 4

# range(start, stop)
for i in range(2, 7):
    print(i)  # 2, 3, 4, 5, 6

# range(start, stop, step)
for i in range(0, 10, 2):
    print(i)  # 0, 2, 4, 6, 8
```

## While Loop

The while loop continues as long as a condition is true:

```python
count = 0
while count < 5:
    print(count)
    count += 1
```

## Break Statement

The break statement exits the loop early:

```python
for i in range(10):
    if i == 5:
        break
    print(i)  # Prints 0, 1, 2, 3, 4
```

## Continue Statement

The continue statement skips the current iteration:

```python
for i in range(5):
    if i == 2:
        continue
    print(i)  # Prints 0, 1, 3, 4
```

## Nested Loops

```python
for i in range(3):
    for j in range(3):
        print(f"({i}, {j})")
```

## Loop with Else

Python allows an else clause with loops:

```python
for i in range(5):
    print(i)
else:
    print("Loop completed!")
```

## Practice Exercises

### Sum of numbers
```python
total = 0
for i in range(1, 11):
    total += i
print(f"Sum of 1 to 10: {total}")
```

### Multiplication table
```python
num = 5
for i in range(1, 11):
    print(f"{num} x {i} = {num * i}")
```

### Countdown
```python
count = 10
while count > 0:
    print(count)
    count -= 1
print("Blast off!")
```
            ''',
            duration_minutes=25,
            order=5
        )
        self.stdout.write(f'  ✓ Created: {lesson5.title}')

        # Create Quiz 1
        self.stdout.write('\nCreating Quiz 1: Python Basics')
        
        quiz1 = Quiz.objects.create(
            course=course,
            title='Python Basics Quiz',
            description='Test your knowledge of Python basics, variables, and operators',
            passing_score=70,
            duration_minutes=15,
            order=1
        )

        # Quiz 1 Questions
        q1 = Question.objects.create(
            quiz=quiz1,
            text='What will be the output of: print(type(5))?',
            question_type='multiple_choice',
            points=10,
            order=1
        )
        Answer.objects.create(question=q1, text="<class 'int'>", is_correct=True, order=1)
        Answer.objects.create(question=q1, text="<class 'float'>", is_correct=False, order=2)
        Answer.objects.create(question=q1, text="<class 'str'>", is_correct=False, order=3)
        Answer.objects.create(question=q1, text="integer", is_correct=False, order=4)

        q2 = Question.objects.create(
            quiz=quiz1,
            text='Which operator is used for exponentiation in Python?',
            question_type='multiple_choice',
            points=10,
            order=2
        )
        Answer.objects.create(question=q2, text='**', is_correct=True, order=1)
        Answer.objects.create(question=q2, text='^', is_correct=False, order=2)
        Answer.objects.create(question=q2, text='*', is_correct=False, order=3)
        Answer.objects.create(question=q2, text='pow', is_correct=False, order=4)

        q3 = Question.objects.create(
            quiz=quiz1,
            text='What is the result of: 10 // 3 in Python?',
            question_type='multiple_choice',
            points=10,
            order=3
        )
        Answer.objects.create(question=q3, text='3', is_correct=True, order=1)
        Answer.objects.create(question=q3, text='3.33', is_correct=False, order=2)
        Answer.objects.create(question=q3, text='3.0', is_correct=False, order=3)
        Answer.objects.create(question=q3, text='4', is_correct=False, order=4)

        q4 = Question.objects.create(
            quiz=quiz1,
            text='Which of the following is a valid variable name in Python?',
            question_type='multiple_choice',
            points=10,
            order=4
        )
        Answer.objects.create(question=q4, text='my_variable', is_correct=True, order=1)
        Answer.objects.create(question=q4, text='2nd_variable', is_correct=False, order=2)
        Answer.objects.create(question=q4, text='my-variable', is_correct=False, order=3)
        Answer.objects.create(question=q4, text='my variable', is_correct=False, order=4)

        q5 = Question.objects.create(
            quiz=quiz1,
            text='What does the "not" operator do in Python?',
            question_type='multiple_choice',
            points=10,
            order=5
        )
        Answer.objects.create(question=q5, text='Reverses the boolean value', is_correct=True, order=1)
        Answer.objects.create(question=q5, text='Checks inequality', is_correct=False, order=2)
        Answer.objects.create(question=q5, text='Performs subtraction', is_correct=False, order=3)
        Answer.objects.create(question=q5, text='Deletes a variable', is_correct=False, order=4)

        self.stdout.write(f'  ✓ Created: {quiz1.title} with 5 questions')

        # Create Quiz 2
        self.stdout.write('\nCreating Quiz 2: Control Flow')
        
        quiz2 = Quiz.objects.create(
            course=course,
            title='Control Flow Quiz',
            description='Test your understanding of if statements and loops',
            passing_score=70,
            duration_minutes=15,
            order=2
        )

        # Quiz 2 Questions
        q6 = Question.objects.create(
            quiz=quiz2,
            text='Which keyword is used to exit a loop early?',
            question_type='multiple_choice',
            points=10,
            order=1
        )
        Answer.objects.create(question=q6, text='break', is_correct=True, order=1)
        Answer.objects.create(question=q6, text='continue', is_correct=False, order=2)
        Answer.objects.create(question=q6, text='exit', is_correct=False, order=3)
        Answer.objects.create(question=q6, text='stop', is_correct=False, order=4)

        q7 = Question.objects.create(
            quiz=quiz2,
            text='What is the output of: range(2, 10, 2)?',
            question_type='multiple_choice',
            points=10,
            order=2
        )
        Answer.objects.create(question=q7, text='2, 4, 6, 8', is_correct=True, order=1)
        Answer.objects.create(question=q7, text='2, 4, 6, 8, 10', is_correct=False, order=2)
        Answer.objects.create(question=q7, text='0, 2, 4, 6, 8', is_correct=False, order=3)
        Answer.objects.create(question=q7, text='2, 3, 4, 5, 6, 7, 8, 9', is_correct=False, order=4)

        q8 = Question.objects.create(
            quiz=quiz2,
            text='Which loop is best when you know the exact number of iterations?',
            question_type='multiple_choice',
            points=10,
            order=3
        )
        Answer.objects.create(question=q8, text='for loop', is_correct=True, order=1)
        Answer.objects.create(question=q8, text='while loop', is_correct=False, order=2)
        Answer.objects.create(question=q8, text='do-while loop', is_correct=False, order=3)
        Answer.objects.create(question=q8, text='infinite loop', is_correct=False, order=4)

        q9 = Question.objects.create(
            quiz=quiz2,
            text='What does the continue statement do?',
            question_type='multiple_choice',
            points=10,
            order=4
        )
        Answer.objects.create(question=q9, text='Skips the rest of the current iteration', is_correct=True, order=1)
        Answer.objects.create(question=q9, text='Exits the loop completely', is_correct=False, order=2)
        Answer.objects.create(question=q9, text='Restarts the loop from beginning', is_correct=False, order=3)
        Answer.objects.create(question=q9, text='Pauses the loop', is_correct=False, order=4)

        q10 = Question.objects.create(
            quiz=quiz2,
            text='In Python, elif is short for:',
            question_type='multiple_choice',
            points=10,
            order=5
        )
        Answer.objects.create(question=q10, text='else if', is_correct=True, order=1)
        Answer.objects.create(question=q10, text='elseif', is_correct=False, order=2)
        Answer.objects.create(question=q10, text='else-if', is_correct=False, order=3)
        Answer.objects.create(question=q10, text='alternate if', is_correct=False, order=4)

        self.stdout.write(f'  ✓ Created: {quiz2.title} with 5 questions')

        # Summary
        self.stdout.write(self.style.SUCCESS('\n✅ Course population complete!'))
        self.stdout.write(f'\nSummary:')
        self.stdout.write(f'  Course: {course.title}')
        self.stdout.write(f'  Lessons created: {Lesson.objects.filter(course=course).count()}')
        self.stdout.write(f'  Quizzes created: {Quiz.objects.filter(course=course).count()}')
        self.stdout.write(f'  Total questions: {Question.objects.filter(quiz__course=course).count()}')
        self.stdout.write(f'\nYou can now enroll in this course and complete it to earn a certificate!')
