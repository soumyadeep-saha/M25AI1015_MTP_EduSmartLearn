# Python Programming Fundamentals

## What is Python?

Python is a high-level, interpreted programming language created by Guido van Rossum in 1991. Known for its clean syntax and readability, Python emphasizes code readability and allows programmers to express concepts in fewer lines of code.

## Key Features

- **Easy to Learn**: Clean, readable syntax
- **Interpreted**: No compilation needed
- **Dynamically Typed**: No explicit type declarations
- **Multi-paradigm**: Supports OOP, functional, procedural
- **Extensive Libraries**: Rich standard library and packages
- **Cross-platform**: Runs on Windows, Mac, Linux

## Basic Syntax

### Hello World
```python
print("Hello, World!")
```

### Variables and Data Types
```python
# Numbers
integer_num = 42
float_num = 3.14
complex_num = 3 + 4j

# Strings
name = "EduSmartLearn"
multiline = """This is a
multiline string"""

# Boolean
is_active = True

# None
value = None

# Type checking
print(type(integer_num))  # <class 'int'>
```

### Collections

#### Lists (Mutable, Ordered)
```python
fruits = ["apple", "banana", "cherry"]
fruits.append("date")
fruits[0] = "apricot"
fruits.pop()
sliced = fruits[1:3]

# List comprehension
squares = [x**2 for x in range(10)]
evens = [x for x in range(20) if x % 2 == 0]
```

#### Tuples (Immutable, Ordered)
```python
coordinates = (10, 20, 30)
x, y, z = coordinates  # Unpacking
```

#### Dictionaries (Key-Value Pairs)
```python
student = {
    "name": "Alice",
    "age": 20,
    "grades": [90, 85, 88]
}

student["email"] = "alice@example.com"
name = student.get("name", "Unknown")

# Dictionary comprehension
squared = {x: x**2 for x in range(5)}
```

#### Sets (Unique, Unordered)
```python
unique_nums = {1, 2, 3, 3, 4}  # {1, 2, 3, 4}
unique_nums.add(5)
unique_nums.remove(1)

# Set operations
a = {1, 2, 3}
b = {2, 3, 4}
print(a | b)  # Union: {1, 2, 3, 4}
print(a & b)  # Intersection: {2, 3}
print(a - b)  # Difference: {1}
```

## Control Flow

### Conditional Statements
```python
score = 85

if score >= 90:
    grade = "A"
elif score >= 80:
    grade = "B"
elif score >= 70:
    grade = "C"
else:
    grade = "F"

# Ternary operator
result = "Pass" if score >= 60 else "Fail"
```

### Loops
```python
# for loop
for i in range(5):
    print(i)

for fruit in fruits:
    print(fruit)

for index, value in enumerate(fruits):
    print(f"{index}: {value}")

# while loop
count = 0
while count < 5:
    print(count)
    count += 1

# Loop control
for i in range(10):
    if i == 3:
        continue  # Skip this iteration
    if i == 7:
        break  # Exit loop
    print(i)
```

## Functions

### Basic Functions
```python
def greet(name):
    """Greet a person by name."""
    return f"Hello, {name}!"

# Default parameters
def greet(name, greeting="Hello"):
    return f"{greeting}, {name}!"

# *args and **kwargs
def flexible(*args, **kwargs):
    print(f"Args: {args}")
    print(f"Kwargs: {kwargs}")

flexible(1, 2, 3, name="Alice", age=20)
```

### Lambda Functions
```python
square = lambda x: x ** 2
add = lambda a, b: a + b

# With built-in functions
numbers = [1, 2, 3, 4, 5]
squared = list(map(lambda x: x**2, numbers))
evens = list(filter(lambda x: x % 2 == 0, numbers))
```

### Decorators
```python
def timer(func):
    import time
    def wrapper(*args, **kwargs):
        start = time.time()
        result = func(*args, **kwargs)
        end = time.time()
        print(f"{func.__name__} took {end-start:.2f}s")
        return result
    return wrapper

@timer
def slow_function():
    import time
    time.sleep(1)
```

## Object-Oriented Programming

### Classes
```python
class Student:
    # Class variable
    school = "EduSmartLearn"
    
    def __init__(self, name, age):
        # Instance variables
        self.name = name
        self.age = age
        self._grade = None  # Protected (convention)
    
    def study(self, subject):
        return f"{self.name} is studying {subject}"
    
    @property
    def grade(self):
        return self._grade
    
    @grade.setter
    def grade(self, value):
        if 0 <= value <= 100:
            self._grade = value
        else:
            raise ValueError("Grade must be 0-100")
    
    @classmethod
    def from_dict(cls, data):
        return cls(data["name"], data["age"])
    
    @staticmethod
    def is_adult(age):
        return age >= 18
    
    def __str__(self):
        return f"Student({self.name}, {self.age})"
    
    def __repr__(self):
        return f"Student(name='{self.name}', age={self.age})"

# Usage
student = Student("Alice", 20)
print(student.study("Python"))
```

### Inheritance
```python
class Person:
    def __init__(self, name):
        self.name = name
    
    def introduce(self):
        return f"I am {self.name}"

class Student(Person):
    def __init__(self, name, student_id):
        super().__init__(name)
        self.student_id = student_id
    
    def introduce(self):
        return f"{super().introduce()}, ID: {self.student_id}"

# Multiple inheritance
class TeachingAssistant(Student, Teacher):
    pass
```

### Abstract Classes
```python
from abc import ABC, abstractmethod

class Shape(ABC):
    @abstractmethod
    def area(self):
        pass
    
    @abstractmethod
    def perimeter(self):
        pass

class Rectangle(Shape):
    def __init__(self, width, height):
        self.width = width
        self.height = height
    
    def area(self):
        return self.width * self.height
    
    def perimeter(self):
        return 2 * (self.width + self.height)
```

## Exception Handling

```python
try:
    result = 10 / 0
except ZeroDivisionError as e:
    print(f"Cannot divide by zero: {e}")
except Exception as e:
    print(f"Error: {e}")
else:
    print("No exception occurred")
finally:
    print("Cleanup code")

# Raising exceptions
def validate_age(age):
    if age < 0:
        raise ValueError("Age cannot be negative")
    return age

# Custom exceptions
class ValidationError(Exception):
    def __init__(self, message, field):
        super().__init__(message)
        self.field = field
```

## File Handling

```python
# Reading files
with open("file.txt", "r") as f:
    content = f.read()
    # or line by line
    lines = f.readlines()

# Writing files
with open("output.txt", "w") as f:
    f.write("Hello, World!")

# JSON
import json

data = {"name": "Alice", "age": 20}
with open("data.json", "w") as f:
    json.dump(data, f, indent=2)

with open("data.json", "r") as f:
    loaded = json.load(f)
```

## Modules and Packages

```python
# Importing
import math
from datetime import datetime, timedelta
from collections import defaultdict, Counter
import numpy as np

# Creating modules
# mymodule.py
def my_function():
    pass

# main.py
from mymodule import my_function
```

## Popular Libraries

### Data Science
- **NumPy**: Numerical computing
- **Pandas**: Data manipulation
- **Matplotlib/Seaborn**: Visualization
- **Scikit-learn**: Machine learning

### Web Development
- **Flask**: Lightweight web framework
- **Django**: Full-featured web framework
- **FastAPI**: Modern async API framework

### AI/ML
- **TensorFlow**: Deep learning
- **PyTorch**: Deep learning
- **Transformers**: NLP models

## Best Practices

1. **Follow PEP 8**: Python style guide
2. **Use virtual environments**: `venv` or `conda`
3. **Write docstrings**: Document functions and classes
4. **Use type hints**: `def greet(name: str) -> str:`
5. **Handle exceptions properly**: Be specific
6. **Use context managers**: `with` statement
7. **Prefer list comprehensions**: When readable
8. **Use f-strings**: For string formatting
9. **Write tests**: `pytest`, `unittest`
10. **Use linters**: `flake8`, `pylint`, `black`

## Python Zen
```python
import this
# The Zen of Python, by Tim Peters
# Beautiful is better than ugly.
# Explicit is better than implicit.
# Simple is better than complex.
# Readability counts.
# ...
```

## Advanced Python Concepts

### Generators
Memory-efficient iterators that yield values one at a time.
```python
def fibonacci(n):
    a, b = 0, 1
    for _ in range(n):
        yield a
        a, b = b, a + b

# Usage
for num in fibonacci(10):
    print(num)

# Generator expression
squares = (x**2 for x in range(1000000))  # Memory efficient
```

### Context Managers
Manage resources with `__enter__` and `__exit__`.
```python
class FileManager:
    def __init__(self, filename, mode):
        self.filename = filename
        self.mode = mode
        self.file = None
    
    def __enter__(self):
        self.file = open(self.filename, self.mode)
        return self.file
    
    def __exit__(self, exc_type, exc_val, exc_tb):
        self.file.close()
        return False  # Don't suppress exceptions

# Using contextlib
from contextlib import contextmanager

@contextmanager
def timer():
    import time
    start = time.time()
    yield
    print(f"Elapsed: {time.time() - start:.2f}s")

with timer():
    # code to time
    pass
```

### Metaclasses
Classes that create classes.
```python
class SingletonMeta(type):
    _instances = {}
    
    def __call__(cls, *args, **kwargs):
        if cls not in cls._instances:
            cls._instances[cls] = super().__call__(*args, **kwargs)
        return cls._instances[cls]

class Database(metaclass=SingletonMeta):
    def __init__(self):
        self.connection = "Connected"
```

### Descriptors
Control attribute access at class level.
```python
class Validator:
    def __init__(self, min_value, max_value):
        self.min_value = min_value
        self.max_value = max_value
    
    def __set_name__(self, owner, name):
        self.name = name
    
    def __get__(self, obj, objtype=None):
        return obj.__dict__.get(self.name)
    
    def __set__(self, obj, value):
        if not self.min_value <= value <= self.max_value:
            raise ValueError(f"{self.name} must be between {self.min_value} and {self.max_value}")
        obj.__dict__[self.name] = value

class Student:
    age = Validator(0, 120)
    grade = Validator(0, 100)
```

### Slots
Optimize memory by declaring fixed attributes.
```python
class Point:
    __slots__ = ['x', 'y']
    
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Uses less memory than regular class
# Cannot add new attributes dynamically
```

## Async Programming

### Asyncio Basics
```python
import asyncio

async def fetch_data(url):
    print(f"Fetching {url}")
    await asyncio.sleep(1)  # Simulate I/O
    return f"Data from {url}"

async def main():
    # Run concurrently
    results = await asyncio.gather(
        fetch_data("url1"),
        fetch_data("url2"),
        fetch_data("url3")
    )
    print(results)

asyncio.run(main())
```

### Async Context Managers
```python
import aiofiles

async def read_file_async(filename):
    async with aiofiles.open(filename, 'r') as f:
        return await f.read()
```

### Async Generators
```python
async def async_range(start, stop):
    for i in range(start, stop):
        await asyncio.sleep(0.1)
        yield i

async def main():
    async for num in async_range(0, 10):
        print(num)
```

## Data Classes (Python 3.7+)

```python
from dataclasses import dataclass, field
from typing import List

@dataclass
class Student:
    name: str
    age: int
    grades: List[float] = field(default_factory=list)
    
    @property
    def average(self) -> float:
        return sum(self.grades) / len(self.grades) if self.grades else 0.0

# Automatic __init__, __repr__, __eq__
student = Student("Alice", 20, [90, 85, 88])
print(student)  # Student(name='Alice', age=20, grades=[90, 85, 88])

# Frozen (immutable)
@dataclass(frozen=True)
class Point:
    x: float
    y: float
```

## Type Hints and Typing Module

```python
from typing import List, Dict, Optional, Union, Callable, TypeVar, Generic

# Basic type hints
def greet(name: str) -> str:
    return f"Hello, {name}"

# Optional (can be None)
def find_user(user_id: int) -> Optional[str]:
    return None

# Union types
def process(value: Union[int, str]) -> str:
    return str(value)

# Python 3.10+ union syntax
def process(value: int | str) -> str:
    return str(value)

# Callable
def apply(func: Callable[[int, int], int], a: int, b: int) -> int:
    return func(a, b)

# Generics
T = TypeVar('T')

class Stack(Generic[T]):
    def __init__(self):
        self._items: List[T] = []
    
    def push(self, item: T) -> None:
        self._items.append(item)
    
    def pop(self) -> T:
        return self._items.pop()

# TypedDict
from typing import TypedDict

class UserDict(TypedDict):
    name: str
    age: int
    email: str
```

## Testing with Pytest

```python
import pytest

# Basic test
def test_addition():
    assert 1 + 1 == 2

# Fixtures
@pytest.fixture
def sample_data():
    return {"name": "Alice", "age": 20}

def test_with_fixture(sample_data):
    assert sample_data["name"] == "Alice"

# Parametrized tests
@pytest.mark.parametrize("input,expected", [
    (1, 1),
    (2, 4),
    (3, 9),
])
def test_square(input, expected):
    assert input ** 2 == expected

# Testing exceptions
def test_division_by_zero():
    with pytest.raises(ZeroDivisionError):
        1 / 0

# Mocking
from unittest.mock import Mock, patch

def test_with_mock():
    mock_api = Mock()
    mock_api.get_data.return_value = {"status": "ok"}
    
    result = mock_api.get_data()
    assert result["status"] == "ok"
    mock_api.get_data.assert_called_once()

@patch('module.external_api')
def test_with_patch(mock_api):
    mock_api.return_value = "mocked"
    # test code
```

## NumPy Fundamentals

```python
import numpy as np

# Array creation
arr = np.array([1, 2, 3, 4, 5])
zeros = np.zeros((3, 4))
ones = np.ones((2, 3))
range_arr = np.arange(0, 10, 2)
linspace = np.linspace(0, 1, 5)

# Array operations
a = np.array([1, 2, 3])
b = np.array([4, 5, 6])

print(a + b)      # Element-wise addition
print(a * b)      # Element-wise multiplication
print(np.dot(a, b))  # Dot product

# Reshaping
arr = np.arange(12)
reshaped = arr.reshape(3, 4)

# Slicing
matrix = np.array([[1, 2, 3], [4, 5, 6], [7, 8, 9]])
print(matrix[0, :])    # First row
print(matrix[:, 1])    # Second column
print(matrix[0:2, 1:3])  # Submatrix

# Broadcasting
a = np.array([[1], [2], [3]])
b = np.array([10, 20, 30])
print(a + b)  # Broadcasting

# Aggregations
print(np.sum(arr))
print(np.mean(arr))
print(np.std(arr))
print(np.max(arr))
print(np.argmax(arr))  # Index of max
```

## Pandas Fundamentals

```python
import pandas as pd

# Creating DataFrames
df = pd.DataFrame({
    'name': ['Alice', 'Bob', 'Charlie'],
    'age': [25, 30, 35],
    'city': ['NYC', 'LA', 'Chicago']
})

# Reading data
df = pd.read_csv('data.csv')
df = pd.read_excel('data.xlsx')
df = pd.read_json('data.json')

# Basic operations
print(df.head())
print(df.info())
print(df.describe())

# Selection
print(df['name'])           # Single column
print(df[['name', 'age']])  # Multiple columns
print(df.loc[0])            # Row by label
print(df.iloc[0])           # Row by index
print(df[df['age'] > 25])   # Filtering

# Adding/modifying columns
df['senior'] = df['age'] > 30
df['age_squared'] = df['age'] ** 2

# Grouping
grouped = df.groupby('city')['age'].mean()

# Merging
df1 = pd.DataFrame({'id': [1, 2], 'name': ['A', 'B']})
df2 = pd.DataFrame({'id': [1, 2], 'value': [100, 200]})
merged = pd.merge(df1, df2, on='id')

# Pivot tables
pivot = df.pivot_table(values='age', index='city', aggfunc='mean')

# Handling missing data
df.dropna()              # Drop rows with NaN
df.fillna(0)             # Fill NaN with value
df.interpolate()         # Interpolate missing values
```

## Web Development with Flask

```python
from flask import Flask, request, jsonify, render_template

app = Flask(__name__)

@app.route('/')
def home():
    return render_template('index.html')

@app.route('/api/users', methods=['GET'])
def get_users():
    users = [{'id': 1, 'name': 'Alice'}]
    return jsonify(users)

@app.route('/api/users', methods=['POST'])
def create_user():
    data = request.json
    # Process data
    return jsonify({'status': 'created'}), 201

@app.route('/api/users/<int:user_id>')
def get_user(user_id):
    return jsonify({'id': user_id, 'name': 'Alice'})

if __name__ == '__main__':
    app.run(debug=True)
```

## Web Development with FastAPI

```python
from fastapi import FastAPI, HTTPException
from pydantic import BaseModel
from typing import List, Optional

app = FastAPI()

class User(BaseModel):
    id: Optional[int] = None
    name: str
    email: str

users_db = []

@app.get("/users", response_model=List[User])
async def get_users():
    return users_db

@app.post("/users", response_model=User)
async def create_user(user: User):
    user.id = len(users_db) + 1
    users_db.append(user)
    return user

@app.get("/users/{user_id}")
async def get_user(user_id: int):
    for user in users_db:
        if user.id == user_id:
            return user
    raise HTTPException(status_code=404, detail="User not found")

# Run with: uvicorn main:app --reload
```

## Regular Expressions

```python
import re

text = "Contact us at support@example.com or sales@company.org"

# Search
match = re.search(r'\w+@\w+\.\w+', text)
if match:
    print(match.group())  # support@example.com

# Find all
emails = re.findall(r'\w+@\w+\.\w+', text)
print(emails)  # ['support@example.com', 'sales@company.org']

# Substitution
cleaned = re.sub(r'\d+', 'X', "Phone: 123-456-7890")
print(cleaned)  # Phone: X-X-X

# Groups
pattern = r'(\w+)@(\w+)\.(\w+)'
match = re.search(pattern, text)
if match:
    print(match.group(1))  # support
    print(match.group(2))  # example
    print(match.group(3))  # com

# Compile for reuse
email_pattern = re.compile(r'\w+@\w+\.\w+')
emails = email_pattern.findall(text)
```

## Multiprocessing and Threading

```python
import multiprocessing
import threading
from concurrent.futures import ThreadPoolExecutor, ProcessPoolExecutor

# Threading (I/O bound tasks)
def download(url):
    print(f"Downloading {url}")
    # I/O operation
    return f"Data from {url}"

with ThreadPoolExecutor(max_workers=4) as executor:
    urls = ["url1", "url2", "url3"]
    results = list(executor.map(download, urls))

# Multiprocessing (CPU bound tasks)
def compute(n):
    return sum(i * i for i in range(n))

with ProcessPoolExecutor(max_workers=4) as executor:
    numbers = [1000000, 2000000, 3000000]
    results = list(executor.map(compute, numbers))

# Using multiprocessing directly
def worker(num):
    return num ** 2

if __name__ == '__main__':
    with multiprocessing.Pool(4) as pool:
        results = pool.map(worker, range(10))
```

## Design Patterns in Python

### Singleton
```python
class Singleton:
    _instance = None
    
    def __new__(cls):
        if cls._instance is None:
            cls._instance = super().__new__(cls)
        return cls._instance
```

### Factory
```python
class Animal:
    def speak(self):
        pass

class Dog(Animal):
    def speak(self):
        return "Woof!"

class Cat(Animal):
    def speak(self):
        return "Meow!"

def animal_factory(animal_type):
    animals = {"dog": Dog, "cat": Cat}
    return animals.get(animal_type, Animal)()
```

### Observer
```python
class Subject:
    def __init__(self):
        self._observers = []
    
    def attach(self, observer):
        self._observers.append(observer)
    
    def notify(self, message):
        for observer in self._observers:
            observer.update(message)

class Observer:
    def update(self, message):
        print(f"Received: {message}")
```

### Decorator Pattern
```python
def bold(func):
    def wrapper(*args, **kwargs):
        return f"<b>{func(*args, **kwargs)}</b>"
    return wrapper

def italic(func):
    def wrapper(*args, **kwargs):
        return f"<i>{func(*args, **kwargs)}</i>"
    return wrapper

@bold
@italic
def greet(name):
    return f"Hello, {name}"

print(greet("World"))  # <b><i>Hello, World</i></b>
```

## Python Performance Tips

### Use Built-in Functions
```python
# Slow
result = []
for item in items:
    result.append(item.upper())

# Fast
result = list(map(str.upper, items))

# Even better for simple cases
result = [item.upper() for item in items]
```

### Use Local Variables
```python
# Slow (global lookup)
def slow():
    for i in range(1000):
        len([1, 2, 3])

# Fast (local lookup)
def fast():
    local_len = len
    for i in range(1000):
        local_len([1, 2, 3])
```

### Use `__slots__`
```python
class WithSlots:
    __slots__ = ['x', 'y']
    def __init__(self, x, y):
        self.x = x
        self.y = y

# Uses ~40% less memory than regular class
```

### Profile Your Code
```python
import cProfile
import pstats

cProfile.run('my_function()', 'output.prof')

stats = pstats.Stats('output.prof')
stats.sort_stats('cumulative')
stats.print_stats(10)
```

## Common Interview Questions

### Difference between `is` and `==`
- `is` checks identity (same object in memory)
- `==` checks equality (same value)

### Mutable vs Immutable
- **Mutable**: list, dict, set
- **Immutable**: int, float, str, tuple, frozenset

### GIL (Global Interpreter Lock)
- Only one thread executes Python bytecode at a time
- Use multiprocessing for CPU-bound tasks
- Threading still useful for I/O-bound tasks

### `*args` and `**kwargs`
- `*args`: Variable positional arguments (tuple)
- `**kwargs`: Variable keyword arguments (dict)

### List vs Tuple
- List: Mutable, slightly slower
- Tuple: Immutable, hashable, can be dict key
