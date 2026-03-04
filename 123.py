def createCounter():
    count = 0
    def increment():
        nonlocal count
        count += 1
        return count
    return increment

counter1 = createCounter()
counter2 = createCounter()
print(counter1())  # 1
print(counter2())  # 2
print(counter1())  # 3
print(counter2())  # 4
