# =========================
# ОПРЕДЕЛЕНИЕ УЗЛА СПИСКА
# =========================

class Node:
    def __init__(self, value, next=None):
        self.value = value
        self.next = next


# =========================
# СОЗДАНИЕ СПИСКА
# =========================

head = None  # пустой список


# =========================
# ВСТАВКА
# =========================

# Вставка в начало (O(1))
def insert_head(head, value):
    return Node(value, head)


# Вставка в конец (O(n))
def insert_tail(head, value):
    new_node = Node(value)

    if head is None:
        return new_node

    current = head
    while current.next:
        current = current.next

    current.next = new_node
    return head


# Вставка по индексу
def insert_at(head, index, value):
    if index == 0:
        return Node(value, head)

    current = head
    for _ in range(index - 1):
        if current is None:
            raise IndexError("Index out of bounds")
        current = current.next

    new_node = Node(value, current.next)
    current.next = new_node
    return head


# =========================
# ПРОСМОТР СПИСКА
# =========================

def print_list(head):
    current = head
    while current:
        print(current.value, end=" -> ")
        current = current.next
    print("None")


# =========================
# ПОИСК ЭЛЕМЕНТА
# =========================

def find(head, value):
    current = head
    while current:
        if current.value == value:
            return True
        current = current.next
    return False


# =========================
# УДАЛЕНИЕ ЭЛЕМЕНТА
# =========================

def delete(head, value):
    if head is None:
        return None

    # удаление головы
    if head.value == value:
        return head.next

    current = head
    while current.next:
        if current.next.value == value:
            current.next = current.next.next
            return head
        current = current.next

    return head


# =========================
# СРАВНЕНИЕ СПИСКОВ
# =========================

def compare_lists(a, b):
    while a and b:
        if a.value != b.value:
            return False
        a = a.next
        b = b.next

    return a is None and b is None


# =========================
# ПРИМЕР ИСПОЛЬЗОВАНИЯ
# =========================

if __name__ == "__main__":
    head = None

    # Создание списка: 1 -> 2 -> 3
    head = insert_head(head, 3)
    head = insert_head(head, 2)
    head = insert_head(head, 1)

    print("Начальный список:")
    print_list(head)

    # Вставка в конец
    head = insert_tail(head, 4)
    print("После вставки в конец (4):")
    print_list(head)

    # Вставка по индексу
    head = insert_at(head, 2, 99)
    print("После вставки 99 на позицию 2:")
    print_list(head)

    # Поиск
    print("Поиск 3:", find(head, 3))
    print("Поиск 100:", find(head, 100))

    # Удаление
    head = delete(head, 2)
    print("После удаления 2:")
    print_list(head)

    # Сравнение
    head2 = None
    head2 = insert_head(head2, 4)
    head2 = insert_head(head2, 99)
    head2 = insert_head(head2, 3)
    head2 = insert_head(head2, 1)

    print("Сравнение списков:", compare_lists(head, head2))