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
db_name: str = getenv("NEO4J_DBNAME_WITH_OPTION")

# Создан драйвер для подключения к Neo4j
driver = GraphDatabase.driver(uri, auth=(username, password))


def visualize_graph(query, name):
    result = execute_query(query)
    if result:
        G = nx.Graph()

        for record in result:
            for key, value in record.items():
                if hasattr(value, "labels"):  # Это узел
                    node_id = value.element_id
                    node_labels = list(value.labels)
                    node_type = node_labels[0] if node_labels else "Node"
                    node_name = value.get("name", None)

                    if node_name:
                        label = f"{node_name} ({node_type})"
                    else:
                        short_id = node_id.split(":")[-1]
                        label = f"{node_type} [{short_id[:4]}]"

                    G.add_node(node_id, label=label, **dict(value.items()))

                elif hasattr(value, "type"):  # Это связь
                    start_node = value.start_node.element_id
                    end_node = value.end_node.element_id
                    edge_type = value.type
                    G.add_edge(start_node, end_node, label=edge_type, **dict(value.items()))

        pos = nx.spring_layout(G, k=0.5, iterations=50)
        labels = nx.get_node_attributes(G, "label")
        edge_labels = nx.get_edge_attributes(G, "label")

        plt.figure(figsize=(12, 10))
        nx.draw(G, pos, with_labels=True, labels=labels, node_size=2400, node_color="lightblue",
                font_size=9, font_weight="bold", edgecolors="black")
        nx.draw_networkx_edge_labels(G, pos, edge_labels=edge_labels, font_color="red", font_size=8)
        plt.subplots_adjust(left=0.05, right=0.95, top=0.95, bottom=0.05)
        plt.savefig(f"variant_pics/{name}.png", dpi=300)
        plt.close()
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
// Создание узлов для различных категорий работников
CREATE (d1:Driver {name: 'Иван Иванов', medical_check: true})
CREATE (d2:Driver {name: 'Петр Петров', medical_check: false})
CREATE (dispatcher:Dispatcher {name: 'Анна Смирнова'})
CREATE (repairman:Repairman {name: 'Сергей Кузнецов'})
CREATE (cashier:Cashier {name: 'Мария Федорова'})
CREATE (prep_staff:PreparationStaff {name: 'Ольга Николаева'})
CREATE (info_staff:InfoStaff {name: 'Дмитрий Павлов'})

// Создание отделов и бригад
CREATE (department1:Department {name: 'Отдел водителей'})
CREATE (department2:Department {name: 'Отдел диспетчеров'})
CREATE (brigade1:Brigade {name: 'Бригада водителей'})
CREATE (brigade2:Brigade {name: 'Бригада ремонтников'})

// Создание администрации
CREATE (admin:Administration {name: 'Администрация станции'})

// Создание локомотивов
CREATE (locomotive1:Locomotive {id: 'L001', status: 'active'})
CREATE (locomotive2:Locomotive {id: 'L002', status: 'maintenance'})

// Создание маршрутов
CREATE (route1:Route {type: 'внутренний', number: '001', schedule: 'ежедневно', departure: '10:00', arrival: '18:00', cost: 500})
CREATE (route2:Route {type: 'международный', number: '002', schedule: 'еженедельно', departure: '08:00', arrival: '20:00', cost: 1000})

// Создание пассажиров и билетов
CREATE (passenger1:Passenger {name: 'Елена Кузнецова'})
CREATE (ticket1:Ticket {route_id: '001', passenger_id: '1', status: 'куплен'})

// Создание отношений между узлами
// Работники принадлежат отделам и бригадам
CREATE (d1)-[:PART_OF]->(brigade1)
CREATE (d2)-[:PART_OF]->(brigade1)
CREATE (repairman)-[:PART_OF]->(brigade2)
CREATE (prep_staff)-[:PART_OF]->(brigade1)

CREATE (department1)-[:INCLUDES]->(d1)
CREATE (department1)-[:INCLUDES]->(d2)
CREATE (department2)-[:INCLUDES]->(dispatcher)

// Отделы управляются администрацией
CREATE (admin)-[:MANAGES]->(department1)
CREATE (admin)-[:MANAGES]->(department2)

// Бригады закреплены за локомотивами
CREATE (brigade1)-[:ASSIGNED_TO]->(locomotive1)
CREATE (brigade2)-[:ASSIGNED_TO]->(locomotive2)

// Водители управляют локомотивами
CREATE (d1)-[:DRIVES]->(locomotive1)

// Ремонтники осматривают и ремонтируют локомотивы
CREATE (repairman)-[:INSPECTS {date: '2025-04-10'}]->(locomotive1)
CREATE (repairman)-[:REPAIRS {date: '2025-04-11'}]->(locomotive2)

// Локомотивы обслуживают маршруты
CREATE (locomotive1)-[:SERVES]->(route1)
CREATE (locomotive2)-[:SERVES]->(route2)

// Диспетчеры управляют маршрутами
CREATE (dispatcher)-[:MANAGES]->(route1)
CREATE (dispatcher)-[:MANAGES]->(route2)

// Кассиры продают билеты
CREATE (cashier)-[:SELLS]->(ticket1)

// Пассажиры бронируют билеты
CREATE (passenger1)-[:BOOKS]->(ticket1)

// Справочная служба помогает пассажирам
CREATE (info_staff)-[:ASSISTS]->(passenger1)

// Водители проходят медосмотр
CREATE (d1)-[:PASSED_MEDICAL_CHECK {year: 2025}]->(admin)
CREATE (d2)-[:FAILED_MEDICAL_CHECK {year: 2025}]->(admin)

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

    # Выполнение запросов
    # имена водителей и идентификаторы локомотивов
    query = """
    MATCH (d:Driver)-[:DRIVES]->(l:Locomotive) RETURN d.name AS DriverName, l.id AS LocomotiveID;
    """
    print("_" * 30 + "Имена водителей и идентификаторы локомотивов, которые они водят" + 30 * "_")
    print(execute_query(query))

    # идентификаторы локомотивов и номера маршрутов
    query = """
    MATCH (r:Route)<-[:SERVES]-(l:Locomotive) RETURN l.id AS LocomotiveID, r.number AS RouteNumber, r.type AS RouteType;
    """
    print("_" * 30 + "Идентификаторы локомотивов и номера маршрутов, которые они обслуживают, а также тип маршрута" + 30 * "_")
    for x in execute_query(query):
        print(x)

    # Имена диспетчеров и номера маршрутов, которые они управляют
    query = """
    MATCH (d:Dispatcher)-[:MANAGES]->(r:Route) RETURN d.name AS DispatcherName, r.number AS RouteNumber;
    """
    print("_" * 30 + "Имена диспетчеров и номера маршрутов, которые они управляют" + 30 * "_")
    for x in execute_query(query):
        print(x)

    # Имена пассажиров, номера маршрутов, на которые они приобрели билеты, и имена кассиров, которые продали эти билеты
    query = """
    MATCH (p:Passenger)-[:BOOKS]->(t:Ticket)-[:SELLS]-(c:Cashier) RETURN p.name AS PassengerName, t.route_id AS RouteID, c.name AS CashierName;
    """
    print("_" * 30 + "Имена пассажиров, номера маршрутов, на которые они приобрели билеты, и имена кассиров, которые продали эти билеты" + 30 * "_")
    for x in execute_query(query):
        print(x)

    # Имена ремонтников, идентификаторы локомотивов, которые они осматривают или ремонтируют, а также даты этих действий
    query = """
    MATCH (rep:Repairman)-[rel:INSPECTS|REPAIRS]->(l:Locomotive) RETURN rep.name AS RepairmanName, l.id AS LocomotiveID, TYPE(rel) AS Action, rel.date AS Date;
    """
    print("_" * 30 + "Имена ремонтников, идентификаторы локомотивов, которые они осматривают или ремонтируют, а также даты этих действий" + 30 * "_")
    for x in execute_query(query):
        print(x)

    # Имена водителей, которые прошли медосмотр, и имена администраций, которые это подтвердили
    query = """
    MATCH (d:Driver)-[:PASSED_MEDICAL_CHECK]->(a:Administration) RETURN d.name AS DriverName, a.name AS AdministrationName;
    """
    print("_" * 30 + "Имена водителей, которые прошли медосмотр, и имена администраций, которые это подтвердили" + 30 * "_")
    print(execute_query(query))

    # Названия бригад и идентификаторы локомотивов, к которым они прикреплены
    query = """
    MATCH (b:Brigade)-[:ASSIGNED_TO]->(l:Locomotive) RETURN b.name AS BrigadeName, l.id AS LocomotiveID;
    """
    print("_" * 30 + "Названия бригад и идентификаторы локомотивов, к которым они прикреплены" + 30 * "_")
    for x in execute_query(query):
        print(x)

    # Названия отделов, типы работников в этих отделах и их количество

    query = """
    MATCH (dep:Department)-[:INCLUDES]->(emp) RETURN dep.name AS DepartmentName, LABELS(emp)[0] AS EmployeeType, COUNT(emp) AS EmployeeCount;
    """
    print("_" * 30 + "Названия отделов, типы работников в этих отделах и их количество" + 30 * "_")
    res = execute_query(query)
    for x in res:
        print(x)
    print("_" * 30 + "Создание диаграммы" + 30 * "_")
    plt.figure(figsize=(8, 6))
    sizes = [x[2] for x in res]
    lables = [x[1] for x in res]

    plt.pie(sizes, labels=lables, autopct='%1.1f%%', startangle=140)
    plt.title("Распределение сотрудников по типам")
    plt.axis('equal')
    plt.savefig("variant_pics/диаграмма.png")
    plt.show()
    print("_" * 30 + "Диаграмма сохранена" + 30 * "_")

    # Количество проданных билетов
    query = """
    MATCH (t:Ticket) WHERE t.status = 'куплен' RETURN COUNT(t) AS SoldTickets;
    """
    print("_" * 30 + "Количество проданных билетов" + 30 * "_")
    print(execute_query(query)[0][0])

    # Идентификаторы локомотивов и имена водителей, которые не прошли медосмотр
    query = """
    MATCH (l:Locomotive)<-[:DRIVES]-(d:Driver) WHERE d.medical_check = false RETURN l.id AS LocomotiveID, d.name AS DriverName;
    """
    print("_" * 30 + "Идентификаторы локомотивов и имена водителей, которые не прошли медосмотр" + 30 * "_")
    result = execute_query(query)
    if len(result) == 0:
        print("Отсутствуют")
    else:
        for x in result:
            print(x)

