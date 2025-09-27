from neo4j import GraphDatabase
from dotenv import load_dotenv
from time import sleep
from os import getenv

import networkx as nx
import matplotlib.pyplot as plt

# Загрузка переменных окружения
load_dotenv()

# Получены значения переменных
uri: str = getenv("NEO4J_URI")
username: str = getenv("NEO4J_USERNAME")
password: str = getenv("NEO4J_PASSWORD")
db_name: str = getenv("NEO4J_DBNAME")

# Создан драйвер для подключения к Neo4j
driver = GraphDatabase.driver(uri, auth=(username, password))


def visualize_graph(query, name):
    result = execute_query(query)
    if result:
        # Создание графа
        G = nx.Graph()

        for record in result:
            for key, value in record.items():
                if hasattr(value, "labels"):  # Если это узел
                    node_id = value.element_id
                    node_label = value.get("userName", value.get("prName", f"Node {node_id}"))
                    G.add_node(node_id, label=node_label, **dict(value.items()))
                elif hasattr(value, "type"):  # Если это связь
                    start_node = value.start_node.element_id
                    end_node = value.end_node.element_id
                    edge_type = value.type
                    G.add_edge(start_node, end_node, label=edge_type, **dict(value.items()))

        # Визуализация графа
        pos = nx.spring_layout(G)  # Расположение узлов
        labels = nx.get_node_attributes(G, "label")
        edge_labels = nx.get_edge_attributes(G, "label")

        plt.figure(figsize=(10, 8))
        nx.draw(G, pos, with_labels=True, labels=labels, node_size=2000, node_color="lightblue", font_size=10,
                font_weight="bold")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red")
        plt.savefig(f"pictures/{name}.png")
    else:
        print("Запрос не вернул результатов.")


def print_database():
    query = """
    MATCH (n) OPTIONAL MATCH (n)-[r]->(m)
    RETURN n, r, m
    """
    result = execute_query(query)
    if result:
        for record in result:
            node_n = record["n"]
            relationship = record["r"]
            node_m = record["m"]

            # Вывод узла
            if node_n:
                print(f"Узел: {node_n.labels} - {dict(node_n.items())}")

            # Вывод связи
            if relationship:
                print(f"Связь: {relationship.type} - {dict(relationship.items())}")

            # Вывод связанного узла
            if node_m:
                print(f"Связанный узел: {node_m.labels} - {dict(node_m.items())}")

            print("-" * 40)  # Разделитель для удобства чтения
    else:
        print("База данных пуста или произошла ошибка.")


# Функция для удаления БД
def drop_db():
    with driver.session() as session:
        query = f"DROP DATABASE {db_name} IF EXISTS"
        result = session.run(query)
        return result


# Функция для создания БД
def create_db():
    with driver.session() as session:
        query = f"CREATE DATABASE {db_name} IF NOT EXISTS"
        result = session.run(query)
        return result


# Функция для проверки существования БД
def check_db_exists():
    with driver.session() as session:
        query = "SHOW DATABASES"
        result = session.run(query)
        databases = [record["name"] for record in result]
        return db_name in databases


# Функция, выполняющая запросы
def execute_query(query):
    with driver.session(database=db_name) as session:
        try:
            result = session.run(query)
            return [record for record in result]
        except Exception as e:
            print("Ошибка:", e)
            return None


if __name__ == "__main__":
    # Удаление базы данных для многоразовости кода
    drop_db()
    print("База данных первично удалена")

    # Создание базы данных
    create_db()
    print("База данных создана")

    # Ожидание создания базы данных
    sleep(5)  # Подожди 5 секунд

    # Проверка существования базы данных
    if check_db_exists():
        print(f"База данных '{db_name}' существует.")
    else:
        print(f"База данных '{db_name}' не существует.")
        exit(1)  # Завершение программы, если база данных не существует

    # Заполнение базы данных
    query = """
CREATE
(user1:Users {userId:1, userName: 'Петр', userSurname:'Антошин', birthDate: date('1991-07-10')}),
(user2:Users {userId:2, userName: 'Сергей', userSurname:'Пастухов', birthDate: date('2002-03-11')}),
(user3:Users {userId:3, userName: 'Анна', userSurname:'Рокотова', birthDate: date('1999-11-17')})
CREATE
(p1:Products {prId:1, prName: 'Смартфон', prDescription:'средство связи'}),
(p2:Products {prId:2, prName: 'Ноутбук', prDescription:'рабочая станция'}),
(p3:Products {prId:3, prName: 'Телевизор', prDescription:'каналы о природе'}),
(p4:Products {prId:4, prName: 'Наушники', prDescription:'слушаем подкасты'}),
(p5:Products {prId:5, prName: 'Кондиционер', prDescription:''}),
(p6:Products {prId:6, prName: 'Кофемашина', prDescription:'для души'})
CREATE
(user1)-[:ORDER {orderId:1, orderDate:date('2024-06-03'), price:100}]->(p1),
(user2)-[:ORDER {orderId:2, orderDate:date('2024-06-11'), price:200}]->(p2),
(user2)-[:ORDER {orderId:3, orderDate:date('2024-06-11'), price:100}]->(p1),
(user1)-[:ORDER {orderId:4, orderDate:date('2024-06-18'), price:300}]->(p3),
(user1)-[:ORDER {orderId:5, orderDate:date('2024-06-19'), price:50}]->(p4),
(user3)-[:ORDER {orderId:6, orderDate:date('2024-07-10'), price:350}]->(p5),
(user3)-[:ORDER {orderId:7, orderDate:date('2024-07-10'), price:100}]->(p1)
"""
result = execute_query(query)
if result is not None:
    print("База данных заполнена")
else:
    print("Не удалось заполнить базу данных.")

print("_" * 30 + "Вывод базы данных" + 30 * "_")
print_database()
print("_" * 30 + "Окончание вывода базы данных" + 30 * "_")

# Вывод всей базы данных
query = """
    MATCH (n) OPTIONAL MATCH (n)-[r]->(m)
    RETURN n, r, m
    """
visualize_graph(query, "Вся база данных")

# Только пользователи
query = """
MATCH (n:Users) return n
"""
visualize_graph(query, "Только пользователи")

# Все пользователи, сделавшие заказ
query = """
MATCH (u:Users)-[o:ORDER] -> (p:Products) RETURN u
"""
visualize_graph(query, "Пользователи сделавшие заказ")

# Товары, которые ни разу не заказывали
query = """
MATCH (p:Products) WHERE NOT ()-[:ORDER]->(p) RETURN p
"""
visualize_graph(query, "Товары которые не заказывали")

# Общее количество заказов
query = """
MATCH (u:Users)-[o:ORDER]->(p:Products) WITH count(o) AS КоличествоЗаказов return КоличествоЗаказов
"""
print(execute_query(query))

# Пользователи, которые сделали больше 1 заказа
query = """
MATCH (u:Users)-[o:ORDER]->(p:Products) WITH u, count(o) AS prod WHERE prod>=2 RETURN u
"""
visualize_graph(query, "Пользователи больше 1 заказа")

# Максимальная цена сделки со всеми товарами
query = """
MATCH (u:Users)-[o:ORDER]->(p:Products) WITH MAX(o.price) AS max_deal_price RETURN max_deal_price;
"""
print(execute_query(query))

# Топ 3 покупателя по количеству заказов
query = """
MATCH (u:Users)-[o:ORDER]->(p:Products) WITH u, count(o) AS order_count ORDER BY order_count DESC LIMIT 3 RETURN u.userName, order_count;
"""
print("Имя", "Заказы")
for x in execute_query(query):
    print(x.items()[0][1], x.items()[1][1])

# Топ 3 человека по тратам
query = """
MATCH (u:Users)-[o:ORDER]->(p:Products) WITH u, SUM(o.price) as summa ORDER BY summa DESC LIMIT 3 RETURN u.userName, summa;
"""
print("Имя", "Сумма")
for x in execute_query(query):
    print(x.items()[0][1], x.items()[1][1])
