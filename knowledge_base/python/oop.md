# Object-Oriented Programming in Python

## Core Idea

Object-oriented programming organizes software around objects that combine
data with behavior. A class is a blueprint that describes which attributes and
methods its objects have. An object is a concrete instance of that class.

Python classes are created with the `class` keyword. Instance methods receive
the current object through the conventional `self` parameter.

```python
class Book:
    def __init__(self, title: str) -> None:
        self.title = title

    def describe(self) -> str:
        return f"Book: {self.title}"
```

`Book("Clean Code")` creates an object whose `title` attribute belongs to that
instance.

## Main Principles

- **Encapsulation** groups related state and behavior behind a clear interface.
- **Inheritance** allows a class to reuse or specialize another class.
- **Polymorphism** lets different objects respond to the same operation in
  their own way.
- **Composition** builds larger behavior by placing objects inside other
  objects.

Composition is often easier to change than deep inheritance hierarchies.
Classes are useful when data and behavior naturally belong together; simple
functions and data structures may be clearer for smaller tasks.
