# Java Programming Fundamentals

## What is Java?

Java is a high-level, object-oriented programming language developed by Sun Microsystems (now Oracle) in 1995. It follows the principle "Write Once, Run Anywhere" (WORA) - code compiled on one platform runs on any platform with a Java Virtual Machine (JVM).

## Key Features

- **Platform Independent**: Bytecode runs on any JVM
- **Object-Oriented**: Everything is an object
- **Strongly Typed**: Compile-time type checking
- **Automatic Memory Management**: Garbage collection
- **Multi-threaded**: Built-in concurrency support
- **Secure**: Sandboxed execution environment

## Basic Syntax

### Hello World
```java
public class HelloWorld {
    public static void main(String[] args) {
        System.out.println("Hello, World!");
    }
}
```

### Variables and Data Types

#### Primitive Types
```java
// Integer types
byte b = 127;           // 8-bit
short s = 32767;        // 16-bit
int i = 2147483647;     // 32-bit
long l = 9223372036854775807L;  // 64-bit

// Floating-point types
float f = 3.14f;        // 32-bit
double d = 3.14159265;  // 64-bit

// Other primitives
boolean flag = true;    // true or false
char c = 'A';           // 16-bit Unicode
```

#### Reference Types
```java
String name = "EduSmartLearn";
int[] numbers = {1, 2, 3, 4, 5};
ArrayList<String> list = new ArrayList<>();
```

### Operators
```java
// Arithmetic: +, -, *, /, %
int sum = 10 + 5;

// Comparison: ==, !=, <, >, <=, >=
boolean isEqual = (a == b);

// Logical: &&, ||, !
boolean result = (a > 0) && (b > 0);

// Assignment: =, +=, -=, *=, /=
x += 5;  // x = x + 5
```

## Control Flow

### Conditional Statements
```java
// if-else
if (score >= 90) {
    grade = 'A';
} else if (score >= 80) {
    grade = 'B';
} else {
    grade = 'C';
}

// switch (enhanced in Java 14+)
String day = switch (dayNum) {
    case 1 -> "Monday";
    case 2 -> "Tuesday";
    default -> "Unknown";
};
```

### Loops
```java
// for loop
for (int i = 0; i < 10; i++) {
    System.out.println(i);
}

// enhanced for loop
for (String item : items) {
    System.out.println(item);
}

// while loop
while (condition) {
    // code
}

// do-while loop
do {
    // code
} while (condition);
```

## Object-Oriented Programming

### Classes and Objects
```java
public class Student {
    // Fields (attributes)
    private String name;
    private int age;
    
    // Constructor
    public Student(String name, int age) {
        this.name = name;
        this.age = age;
    }
    
    // Methods
    public String getName() {
        return name;
    }
    
    public void setName(String name) {
        this.name = name;
    }
}

// Creating objects
Student student = new Student("Alice", 20);
```

### Inheritance
```java
public class Animal {
    protected String name;
    
    public void speak() {
        System.out.println("Animal speaks");
    }
}

public class Dog extends Animal {
    @Override
    public void speak() {
        System.out.println("Woof!");
    }
}
```

### Interfaces
```java
public interface Drawable {
    void draw();
    default void print() {
        System.out.println("Printing...");
    }
}

public class Circle implements Drawable {
    @Override
    public void draw() {
        System.out.println("Drawing circle");
    }
}
```

### Abstract Classes
```java
public abstract class Shape {
    abstract double area();
    
    public void display() {
        System.out.println("Area: " + area());
    }
}
```

## Collections Framework

### List
```java
List<String> list = new ArrayList<>();
list.add("Apple");
list.add("Banana");
list.get(0);  // "Apple"
list.remove(1);
```

### Set
```java
Set<Integer> set = new HashSet<>();
set.add(1);
set.add(2);
set.add(1);  // Duplicate ignored
set.contains(1);  // true
```

### Map
```java
Map<String, Integer> map = new HashMap<>();
map.put("Alice", 90);
map.put("Bob", 85);
map.get("Alice");  // 90
map.containsKey("Bob");  // true
```

## Exception Handling

```java
try {
    int result = 10 / 0;
} catch (ArithmeticException e) {
    System.out.println("Cannot divide by zero");
} catch (Exception e) {
    System.out.println("Error: " + e.getMessage());
} finally {
    System.out.println("Cleanup code");
}

// Throwing exceptions
public void validate(int age) throws IllegalArgumentException {
    if (age < 0) {
        throw new IllegalArgumentException("Age cannot be negative");
    }
}
```

## Java 8+ Features

### Lambda Expressions
```java
// Before Java 8
Runnable r = new Runnable() {
    @Override
    public void run() {
        System.out.println("Hello");
    }
};

// With Lambda
Runnable r = () -> System.out.println("Hello");

// With parameters
Comparator<String> comp = (a, b) -> a.compareTo(b);
```

### Stream API
```java
List<Integer> numbers = Arrays.asList(1, 2, 3, 4, 5);

// Filter and map
List<Integer> doubled = numbers.stream()
    .filter(n -> n > 2)
    .map(n -> n * 2)
    .collect(Collectors.toList());

// Reduce
int sum = numbers.stream()
    .reduce(0, Integer::sum);
```

### Optional
```java
Optional<String> optional = Optional.ofNullable(getValue());
String result = optional.orElse("default");
optional.ifPresent(System.out::println);
```

## File I/O

```java
// Reading file
try (BufferedReader reader = new BufferedReader(new FileReader("file.txt"))) {
    String line;
    while ((line = reader.readLine()) != null) {
        System.out.println(line);
    }
}

// Writing file
try (BufferedWriter writer = new BufferedWriter(new FileWriter("output.txt"))) {
    writer.write("Hello, World!");
}

// Java NIO (modern approach)
Path path = Paths.get("file.txt");
List<String> lines = Files.readAllLines(path);
Files.write(path, lines);
```

## Multithreading

```java
// Extending Thread
class MyThread extends Thread {
    public void run() {
        System.out.println("Thread running");
    }
}

// Implementing Runnable
class MyRunnable implements Runnable {
    public void run() {
        System.out.println("Runnable running");
    }
}

// Using ExecutorService
ExecutorService executor = Executors.newFixedThreadPool(4);
executor.submit(() -> System.out.println("Task executed"));
executor.shutdown();
```

## Best Practices

1. **Follow naming conventions**: camelCase for methods/variables, PascalCase for classes
2. **Use meaningful names**: `calculateTotal()` not `calc()`
3. **Keep methods small**: Single responsibility
4. **Handle exceptions properly**: Don't catch and ignore
5. **Use generics**: Type safety at compile time
6. **Prefer composition over inheritance**
7. **Make fields private**: Use getters/setters
8. **Use StringBuilder for string concatenation in loops**
9. **Close resources**: Use try-with-resources
10. **Write unit tests**: JUnit, TestNG

## Design Patterns

### Creational Patterns

#### Singleton
Ensures only one instance of a class exists.
```java
public class Singleton {
    private static Singleton instance;
    
    private Singleton() {}
    
    public static synchronized Singleton getInstance() {
        if (instance == null) {
            instance = new Singleton();
        }
        return instance;
    }
}
```

#### Factory Method
Creates objects without specifying exact class.
```java
public interface Animal {
    void speak();
}

public class AnimalFactory {
    public static Animal createAnimal(String type) {
        return switch (type) {
            case "dog" -> new Dog();
            case "cat" -> new Cat();
            default -> throw new IllegalArgumentException("Unknown animal");
        };
    }
}
```

#### Builder
Constructs complex objects step by step.
```java
public class User {
    private final String name;
    private final int age;
    private final String email;
    
    private User(Builder builder) {
        this.name = builder.name;
        this.age = builder.age;
        this.email = builder.email;
    }
    
    public static class Builder {
        private String name;
        private int age;
        private String email;
        
        public Builder name(String name) {
            this.name = name;
            return this;
        }
        
        public Builder age(int age) {
            this.age = age;
            return this;
        }
        
        public Builder email(String email) {
            this.email = email;
            return this;
        }
        
        public User build() {
            return new User(this);
        }
    }
}

// Usage
User user = new User.Builder()
    .name("Alice")
    .age(25)
    .email("alice@example.com")
    .build();
```

### Structural Patterns

#### Adapter
Converts interface of a class to another interface.
```java
public interface MediaPlayer {
    void play(String filename);
}

public class Mp3Player implements MediaPlayer {
    public void play(String filename) {
        System.out.println("Playing MP3: " + filename);
    }
}

public class Mp4PlayerAdapter implements MediaPlayer {
    private Mp4Player mp4Player = new Mp4Player();
    
    public void play(String filename) {
        mp4Player.playMp4(filename);
    }
}
```

#### Decorator
Adds behavior to objects dynamically.
```java
public interface Coffee {
    double getCost();
    String getDescription();
}

public class SimpleCoffee implements Coffee {
    public double getCost() { return 2.0; }
    public String getDescription() { return "Coffee"; }
}

public class MilkDecorator implements Coffee {
    private Coffee coffee;
    
    public MilkDecorator(Coffee coffee) {
        this.coffee = coffee;
    }
    
    public double getCost() { return coffee.getCost() + 0.5; }
    public String getDescription() { return coffee.getDescription() + ", Milk"; }
}
```

### Behavioral Patterns

#### Observer
Defines one-to-many dependency between objects.
```java
public interface Observer {
    void update(String message);
}

public class Subject {
    private List<Observer> observers = new ArrayList<>();
    
    public void addObserver(Observer o) { observers.add(o); }
    public void removeObserver(Observer o) { observers.remove(o); }
    
    public void notifyObservers(String message) {
        for (Observer o : observers) {
            o.update(message);
        }
    }
}
```

#### Strategy
Defines family of algorithms, encapsulates each one.
```java
public interface PaymentStrategy {
    void pay(double amount);
}

public class CreditCardPayment implements PaymentStrategy {
    public void pay(double amount) {
        System.out.println("Paid " + amount + " via Credit Card");
    }
}

public class PayPalPayment implements PaymentStrategy {
    public void pay(double amount) {
        System.out.println("Paid " + amount + " via PayPal");
    }
}

public class ShoppingCart {
    private PaymentStrategy strategy;
    
    public void setPaymentStrategy(PaymentStrategy strategy) {
        this.strategy = strategy;
    }
    
    public void checkout(double amount) {
        strategy.pay(amount);
    }
}
```

## Java Memory Management

### JVM Memory Structure
- **Heap**: Objects and arrays (Young Gen + Old Gen)
- **Stack**: Method calls and local variables
- **Metaspace**: Class metadata (replaced PermGen in Java 8)
- **Code Cache**: JIT compiled code

### Garbage Collection
- **Mark and Sweep**: Identify and remove unreachable objects
- **Generational GC**: Young, Old, and Permanent generations
- **GC Algorithms**: Serial, Parallel, CMS, G1, ZGC

### Memory Leaks Prevention
- Close resources properly
- Remove listeners when done
- Use weak references for caches
- Avoid static collections holding references

## Concurrency Advanced

### Synchronized Blocks
```java
public class Counter {
    private int count = 0;
    private final Object lock = new Object();
    
    public void increment() {
        synchronized (lock) {
            count++;
        }
    }
}
```

### Locks and Conditions
```java
import java.util.concurrent.locks.*;

public class BoundedBuffer<T> {
    private final Lock lock = new ReentrantLock();
    private final Condition notFull = lock.newCondition();
    private final Condition notEmpty = lock.newCondition();
    
    public void put(T item) throws InterruptedException {
        lock.lock();
        try {
            while (isFull()) notFull.await();
            // add item
            notEmpty.signal();
        } finally {
            lock.unlock();
        }
    }
}
```

### Concurrent Collections
```java
// Thread-safe collections
ConcurrentHashMap<String, Integer> map = new ConcurrentHashMap<>();
CopyOnWriteArrayList<String> list = new CopyOnWriteArrayList<>();
BlockingQueue<String> queue = new LinkedBlockingQueue<>();
```

### CompletableFuture
```java
CompletableFuture<String> future = CompletableFuture
    .supplyAsync(() -> fetchData())
    .thenApply(data -> process(data))
    .thenApply(result -> format(result))
    .exceptionally(ex -> "Error: " + ex.getMessage());

String result = future.get();
```

## Java Modules (Java 9+)

### Module Declaration
```java
// module-info.java
module com.example.myapp {
    requires java.sql;
    requires transitive com.example.utils;
    
    exports com.example.myapp.api;
    opens com.example.myapp.internal to com.fasterxml.jackson.databind;
}
```

### Benefits
- Strong encapsulation
- Reliable configuration
- Improved security
- Better performance

## Records (Java 14+)

```java
// Immutable data class
public record Person(String name, int age) {
    // Compact constructor for validation
    public Person {
        if (age < 0) throw new IllegalArgumentException("Age cannot be negative");
    }
    
    // Additional methods
    public String greeting() {
        return "Hello, " + name;
    }
}

// Usage
Person p = new Person("Alice", 25);
System.out.println(p.name());  // Alice
System.out.println(p.age());   // 25
```

## Sealed Classes (Java 17+)

```java
public sealed class Shape permits Circle, Rectangle, Triangle {
    // common methods
}

public final class Circle extends Shape {
    private double radius;
}

public final class Rectangle extends Shape {
    private double width, height;
}

public non-sealed class Triangle extends Shape {
    // can be extended further
}
```

## Pattern Matching

### instanceof Pattern (Java 16+)
```java
if (obj instanceof String s) {
    System.out.println(s.length());
}
```

### Switch Pattern (Java 21+)
```java
String result = switch (obj) {
    case Integer i -> "Integer: " + i;
    case String s -> "String: " + s;
    case null -> "null";
    default -> "Unknown";
};
```

## Virtual Threads (Java 21+)

```java
// Create virtual thread
Thread.startVirtualThread(() -> {
    System.out.println("Running in virtual thread");
});

// Using executor
try (var executor = Executors.newVirtualThreadPerTaskExecutor()) {
    IntStream.range(0, 10000).forEach(i -> {
        executor.submit(() -> {
            Thread.sleep(Duration.ofSeconds(1));
            return i;
        });
    });
}
```

## Testing with JUnit 5

```java
import org.junit.jupiter.api.*;
import static org.junit.jupiter.api.Assertions.*;

class CalculatorTest {
    private Calculator calc;
    
    @BeforeEach
    void setUp() {
        calc = new Calculator();
    }
    
    @Test
    @DisplayName("Addition works correctly")
    void testAdd() {
        assertEquals(5, calc.add(2, 3));
    }
    
    @ParameterizedTest
    @ValueSource(ints = {1, 2, 3})
    void testPositive(int num) {
        assertTrue(num > 0);
    }
    
    @Test
    void testException() {
        assertThrows(ArithmeticException.class, () -> calc.divide(1, 0));
    }
}
```

## Spring Framework Basics

### Dependency Injection
```java
@Service
public class UserService {
    private final UserRepository repository;
    
    @Autowired
    public UserService(UserRepository repository) {
        this.repository = repository;
    }
}
```

### REST Controller
```java
@RestController
@RequestMapping("/api/users")
public class UserController {
    
    @GetMapping("/{id}")
    public User getUser(@PathVariable Long id) {
        return userService.findById(id);
    }
    
    @PostMapping
    public User createUser(@RequestBody User user) {
        return userService.save(user);
    }
}
```

## Common Interview Topics

### String Pool
- String literals stored in pool
- `new String()` creates new object
- `intern()` adds to pool

### equals() vs ==
- `==` compares references
- `equals()` compares content
- Override `hashCode()` when overriding `equals()`

### Immutability
- All fields final
- No setters
- Defensive copies
- Benefits: Thread-safe, cacheable

### SOLID Principles
- **S**ingle Responsibility
- **O**pen/Closed
- **L**iskov Substitution
- **I**nterface Segregation
- **D**ependency Inversion
