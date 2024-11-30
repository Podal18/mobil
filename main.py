import sqlite3
from kivy.app import App
from kivy.uix.boxlayout import BoxLayout
from kivy.uix.button import Button
from kivy.uix.label import Label
from kivy.uix.textinput import TextInput
from kivy.uix.popup import Popup
from kivy.uix.screenmanager import ScreenManager, Screen
from kivy.uix.spinner import Spinner
from datetime import datetime
from kivy.uix.recycleview import RecycleView
from kivy.uix.recycleview.views import RecycleDataViewBehavior
from kivy.uix.behaviors import FocusBehavior
from kivy.properties import StringProperty, BooleanProperty
from kivy.uix.scrollview import ScrollView
from kivy.uix.gridlayout import GridLayout
from kivy.core.window import Window
from kivy.uix.checkbox import CheckBox

Window.size = (400, 600)
# Шаг 1: Работа с базой данных
def create_db():
    conn = sqlite3.connect('deadlibe.db')
    cursor = conn.cursor()

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS users (
            id_user INTEGER PRIMARY KEY AUTOINCREMENT,
            login TEXT UNIQUE NOT NULL,
            password TEXT NOT NULL,
            role TEXT NOT NULL,
            verification_code TEXT,
            name_user TEXT
        )
        ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS tasks (
            id_task INTEGER PRIMARY KEY AUTOINCREMENT,        
            task_name text,
            deadline datetime NOT NULL,
            status TEXT DEFAULT 'Выполняется'
        )
        ''')

    cursor.execute('''
            CREATE TABLE IF NOT EXISTS students (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            name TEXT NOT NULL
        )
            ''')

    cursor.execute('''
        CREATE TABLE IF NOT EXISTS user_to_task (
            id INTEGER PRIMARY KEY AUTOINCREMENT,
            id_user INTEGER NOT NULL,
            is_task INTEGER NOT NULL,
            FOREIGN KEY (id_user) REFERENCES students(id),
            FOREIGN KEY (is_task) REFERENCES tasks(id_task)
        )
        ''')

    conn.commit()
    conn.close()


# Вызовем функцию для создания базы данных
create_db()


# Шаг 2: Функции для работы с пользователями
def add_user_with_verification_code(login, password, role, verification_code):
    conn = sqlite3.connect('deadlibe.db')
    cursor = conn.cursor()

    try:
        cursor.execute('''
        INSERT INTO users (login, password, role, verification_code)
        VALUES (?, ?, ?, ?)
        ''', (login, password, role, verification_code))

        conn.commit()
        print(f"Пользователь {login} зарегистрирован с кодом {verification_code}.")
    except sqlite3.IntegrityError:
        print("Ошибка: Пользователь с таким логином уже существует.")
    finally:
        conn.close()


def recover_password(login, verification_code, new_password):
    conn = sqlite3.connect('deadlibe.db')
    cursor = conn.cursor()

    cursor.execute('''
    SELECT * FROM users WHERE login = ? AND verification_code = ?
    ''', (login, verification_code))

    user = cursor.fetchone()

    if user:
        cursor.execute('''
        UPDATE users SET password = ? WHERE login = ?
        ''', (new_password, login))

        conn.commit()
        print("Пароль успешно изменён.")
    else:
        print("Неверный код верификации.")

    conn.close()


current_user_id = None

# Шаг 3: Окна приложения

class LoginScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Заголовок
        layout.add_widget(Label(text='Авторизация', font_size=24, size_hint=(1, 0.2)))

        # Поле для ввода логина
        self.username_input = TextInput(hint_text='Логин', multiline=False)
        layout.add_widget(self.username_input)

        # Поле для ввода пароля
        self.password_input = TextInput(hint_text='Пароль', password=True, multiline=False)
        layout.add_widget(self.password_input)

        # Кнопка входа
        login_button = Button(text='Войти', size_hint=(1, 0.2))
        login_button.bind(on_press=self.login)
        layout.add_widget(login_button)

        # Кнопка регистрации
        register_button = Button(text='Зарегистрироваться', size_hint=(1, 0.2))
        register_button.bind(on_press=self.go_to_register)
        layout.add_widget(register_button)

        # Кнопка восстановления пароля
        forgot_password_button = Button(text='Забыли пароль?', size_hint=(1, 0.2))
        forgot_password_button.bind(on_press=self.go_to_forgot_password)
        layout.add_widget(forgot_password_button)

        self.add_widget(layout)

    def login(self, instance):
        global current_user_id
        login = self.username_input.text
        password = self.password_input.text

        conn = sqlite3.connect('deadlibe.db')
        cursor = conn.cursor()
        cursor.execute('''SELECT * FROM users WHERE login = ? AND password = ?''', (login, password))
        user = cursor.fetchone()

        if user:
            current_user_id = user[0]  # Здесь current_user_id равен id_user из таблицы users
            user_role = user[3]  # Роль пользователя (index 3)
            if user_role == 'Teacher':  # Если роль Teacher
                self.manager.current = 'task_manager'  # Переход на экран задач
                self.show_popup("Успех", "Добро пожаловать, Teacher!")
            elif user_role == 'Student':  # Если роль Student
                self.manager.current = 'student_screen'  # Переход на экран студента
                self.show_popup("Успех", "Добро пожаловать, Student!")
            else:
                self.show_popup("Ошибка", "Неверная роль пользователя.")
        else:
            self.show_popup("Ошибка", "Неверный логин или пароль.")

        conn.close()

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()

    def go_to_register(self, instance):
        self.manager.current = 'register'

    def go_to_forgot_password(self, instance):
        self.manager.current = 'forgot_password'


# Экран с задачами (TaskManager)
class TaskManagerScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = TaskManagerLayout(screen_manager=self.manager)
        layout.show_tasks_button.bind(on_press=self.show_tasks)
        self.add_widget(layout)

    def show_tasks(self, instance):
        """Переключение на экран со списком задач"""
        self.manager.current = 'task_list'


class RegistrationScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Заголовок
        layout.add_widget(Label(text='Регистрация', font_size=24, size_hint=(1, 0.2)))

        # Поле для ввода логина
        self.username_input = TextInput(hint_text='Логин', multiline=False)
        layout.add_widget(self.username_input)

        # Поле для ввода пароля
        self.password_input = TextInput(hint_text='Пароль', password=True, multiline=False)
        layout.add_widget(self.password_input)

        # Поле для ввода имени пользователя
        self.name_user_input = TextInput(hint_text='Имя', multiline=False)
        layout.add_widget(self.name_user_input)

        # Поле для ввода кода верификации
        self.verification_code_input = TextInput(hint_text='Код верификации', multiline=False)
        layout.add_widget(self.verification_code_input)

        # Спиннер для выбора роли
        self.role_spinner = Spinner(
            text='Выберите роль',
            values=('Student', 'Teacher'),
            size_hint=(None, None),
            size=(200, 44)
        )
        layout.add_widget(self.role_spinner)

        # Кнопка регистрации
        register_button = Button(text='Зарегистрироваться', size_hint=(1, 0.3))
        register_button.bind(on_press=self.register)
        layout.add_widget(register_button)

        # Кнопка назад
        back_button = Button(text='Назад', size_hint=(1, 0.3))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def register(self, instance):
        # Получаем данные из полей
        login = self.username_input.text
        password = self.password_input.text
        verification_code = self.verification_code_input.text
        name_user = self.name_user_input.text
        role = self.role_spinner.text  # Получаем выбранную роль

        if role == 'Выберите роль':  # Если роль не выбрана
            self.show_popup("Ошибка", "Пожалуйста, выберите роль.")
            return

        if not name_user:  # Если имя не введено
            self.show_popup("Ошибка", "Пожалуйста, введите имя пользователя.")
            return

        # Добавляем пользователя с выбранной ролью в базу данных
        self.add_user_with_verification_code(login, password, role, verification_code, name_user)
        self.show_popup("Успех", f"Пользователь {login} зарегистрирован с кодом {verification_code} и ролью {role}.")

    def add_user_with_verification_code(self, username, password, role, verification_code, name_user):
        """Добавляет пользователя в базу данных и при необходимости добавляет студента в таблицу students"""
        try:
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()

            # Вставляем пользователя в таблицу Users
            cursor.execute("""
                INSERT INTO Users (login, password, role, verification_code, name_user)
                VALUES (?, ?, ?, ?, ?)
            """, (username, password, role, verification_code, name_user))

            user_id = cursor.lastrowid

            if role == "Student":
                cursor.execute("""
                    INSERT INTO students (name)
                    VALUES (?)
                """, (name_user,))

            # Подтверждаем изменения
            conn.commit()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
        finally:
            conn.close()

    def go_back(self, instance):
        """Возвращаемся на экран авторизации"""
        self.manager.current = 'login'

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()

class ForgotPasswordScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Заголовок
        layout.add_widget(Label(text='Восстановление пароля', font_size=24, size_hint=(1, 0.2)))

        # Поле для ввода логина
        self.username_input = TextInput(hint_text='Логин', multiline=False)
        layout.add_widget(self.username_input)

        # Поле для ввода кода верификации
        self.verification_code_input = TextInput(hint_text='Код верификации', multiline=False)
        layout.add_widget(self.verification_code_input)

        # Поле для нового пароля
        self.new_password_input = TextInput(hint_text='Новый пароль', password=True, multiline=False)
        layout.add_widget(self.new_password_input)

        # Кнопка восстановления пароля
        recover_button = Button(text='Восстановить пароль', size_hint=(1, 0.3))
        recover_button.bind(on_press=self.recover_password)
        layout.add_widget(recover_button)

        # Кнопка назад
        back_button = Button(text='Назад', size_hint=(1, 0.3))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def recover_password(self, instance):
        login = self.username_input.text
        verification_code = self.verification_code_input.text
        new_password = self.new_password_input.text

        recover_password(login, verification_code, new_password)
        self.show_popup("Успех", "Пароль успешно восстановлен.")

    def go_back(self, instance):
        """Возвращаемся на экран авторизации"""
        self.manager.current = 'login'

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()


def load_students():
    conn = sqlite3.connect('deadlibe.db')
    cursor = conn.cursor()
    cursor.execute('''SELECT id, name FROM students''')
    students = cursor.fetchall()
    conn.close()
    return students


# Функция для назначения задачи студенту
def assign_task_to_student(task_id, student_id):
    conn = sqlite3.connect('deadlibe.db')
    cursor = conn.cursor()
    cursor.execute('''
    INSERT INTO user_to_task (id_user, is_task)
    VALUES (?, ?)
    ''', (student_id, task_id))
    conn.commit()
    conn.close()
    print(f"Задача {task_id} назначена студенту {student_id}.")


class TaskRow(RecycleDataViewBehavior, BoxLayout):
    """Одна строка задачи в списке."""
    task_name = StringProperty("")
    selected = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        """Обновление отображаемых данных."""
        self.task_name = data["task_name"]
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Выбор строки при нажатии."""
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            self.selected = not self.selected
            return True
        return False



class TaskRow(RecycleDataViewBehavior, BoxLayout):
    """Одна строка задачи в списке."""
    task_name = StringProperty("")
    selected = BooleanProperty(False)

    def refresh_view_attrs(self, rv, index, data):
        """Обновление отображаемых данных."""
        self.task_name = data["task_name"]
        return super().refresh_view_attrs(rv, index, data)

    def on_touch_down(self, touch):
        """Выбор строки при нажатии."""
        if super().on_touch_down(touch):
            return True
        if self.collide_point(*touch.pos):
            self.selected = not self.selected
            return True
        return False


class TaskListRecycleView(RecycleView):
    """Список задач."""
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        self.data = []

    def get_selected_task(self):
        """Возвращает имя выделенной задачи."""
        for item in self.data:
            if item.get("selected", False):
                return item["task_name"]
        return None


class TaskManagerLayout(BoxLayout):
    """Основной интерфейс для учителя."""

    def __init__(self, screen_manager, **kwargs):
        super().__init__(**kwargs)
        self.screen_manager = screen_manager  # Сохраняем ссылку на ScreenManager
        self.orientation = "vertical"

        # Спиннер для выбора студента
        self.students_spinner = Spinner(
            text='Выберите студента',
            values=[student[1] for student in load_students()],
            size_hint=(None, None),
            size=(200, 44)
        )
        self.add_widget(self.students_spinner)

        # Метка и поле ввода для Названия задачи
        self.add_widget(Label(text="Название задачи:"))
        self.task_name_input = TextInput(hint_text="Введите название задачи", multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.task_name_input)

        # Метка и поле ввода для Дедлайна
        self.add_widget(Label(text="Дедлайн (ГГГГ-ММ-ДД ЧЧ:ММ:СС):"))
        self.deadline_input = TextInput(hint_text="Введите дедлайн", multiline=False, size_hint_y=None, height=40)
        self.add_widget(self.deadline_input)

        # Спиннер для выбора задачи
        self.tasks_spinner = Spinner(
            text='Выберите задачу',
            values=[],  # Список задач будет заполняться динамически
            size_hint=(None, None),
            size=(200, 44)
        )
        self.add_widget(self.tasks_spinner)

        # Кнопки
        self.add_task_btn = Button(text="Добавить задачу", size_hint_y=None, height=50)
        self.remove_task_btn = Button(text="Удалить задачу", size_hint_y=None, height=50)
        self.view_deadline_btn = Button(text="Посмотреть дедлайн", size_hint_y=None, height=50)
        self.view_status_btn = Button(text="Посмотреть статус", size_hint_y=None, height=50)
        self.exit_btn = Button(text="Выйти", size_hint_y=None, height=50)

        # Привязываем обработчики событий
        self.add_task_btn.bind(on_press=self.add_task)
        self.remove_task_btn.bind(on_press=self.remove_task)
        self.view_deadline_btn.bind(on_press=self.view_deadline)
        self.view_status_btn.bind(on_press=self.view_status)
        self.exit_btn.bind(on_press=self.exit_to_login)

        # Добавляем виджеты в layout
        self.add_widget(self.add_task_btn)
        self.add_widget(self.remove_task_btn)
        self.add_widget(self.view_deadline_btn)
        self.add_widget(self.view_status_btn)
        self.add_widget(self.exit_btn)

        # Обновление задач в спинере
        self.update_tasks_spinner()

    def add_task(self, instance):
        """Добавляет задачу и назначает ее студенту."""
        task_name = self.task_name_input.text.strip()
        deadline_str = self.deadline_input.text.strip()

        if task_name and deadline_str:
            try:
                # Преобразование строки дедлайна в datetime
                deadline_obj = datetime.strptime(deadline_str, "%Y-%m-%d %H:%M:%S")
                remaining_time = deadline_obj - datetime.now()
                if remaining_time.total_seconds() > 0:
                    # Добавляем задачу в таблицу tasks
                    conn = sqlite3.connect('deadlibe.db')
                    cursor = conn.cursor()

                    cursor.execute('''
                        INSERT INTO tasks (task_name, deadline)
                        VALUES (?, ?)
                    ''', (task_name, deadline_str))
                    conn.commit()
                    task_id = cursor.lastrowid  # Получаем ID только что добавленной задачи

                    # Связываем задачу с выбранным студентом
                    selected_student_name = self.students_spinner.text
                    students = load_students()
                    selected_student_id = next(
                        student[0] for student in students if student[1] == selected_student_name)

                    # Добавляем запись в таблицу user_to_task
                    cursor.execute('''
                        INSERT INTO user_to_task (id_user, is_task)
                        VALUES (?, ?)
                    ''', (selected_student_id, task_id))
                    conn.commit()

                    conn.close()

                    self.show_popup("Успех", f"Задача '{task_name}' назначена студенту {selected_student_name}.")
                else:
                    self.show_popup("Ошибка", "Дедлайн не может быть задним числом.")
            except ValueError:
                self.show_popup("Ошибка", "Введите корректный формат даты и времени.")
        else:
            self.show_popup("Ошибка", "Введите название задачи и дедлайн.")

    def remove_task(self, instance):
        """Удаляет задачу, выбранную в спинере задач."""
        selected_task = self.tasks_spinner.text
        if selected_task != 'Выберите задачу':
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()
            cursor.execute('''
                DELETE FROM tasks WHERE task_name = ?
            ''', (selected_task,))
            conn.commit()

            # Обновляем список задач в спинере
            self.update_tasks_spinner()
            conn.close()
            self.show_popup("Успех", f"Задача '{selected_task}' удалена успешно.")
        else:
            self.show_popup("Ошибка", "Выберите задачу для удаления.")

    def view_deadline(self, instance):
        """Показывает дедлайн для выбранной задачи."""
        selected_task = self.tasks_spinner.text
        if selected_task != 'Выберите задачу':
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT deadline FROM tasks WHERE task_name = ?
            ''', (selected_task,))
            task = cursor.fetchone()
            if task:
                self.show_popup("Дедлайн", f"Дедлайн для задачи '{selected_task}': {task[0]}")
            conn.close()
        else:
            self.show_popup("Ошибка", "Выберите задачу для просмотра дедлайна.")

    def view_status(self, instance):
        """Показывает статус для выбранной задачи."""
        selected_task = self.tasks_spinner.text
        if selected_task != 'Выберите задачу':
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()
            cursor.execute('''
                SELECT status FROM tasks WHERE task_name = ?
            ''', (selected_task,))
            task = cursor.fetchone()
            if task:
                self.show_popup("Статус", f"Статус задачи '{selected_task}': {task[0]}")
            conn.close()
        else:
            self.show_popup("Ошибка", "Выберите задачу для просмотра статуса.")

    def exit_to_login(self, instance):
        """Переход к экрану авторизации."""
        self.screen_manager.current = 'login'

    def update_tasks_spinner(self):
        """Обновляет список задач в спинере задач."""
        conn = sqlite3.connect('deadlibe.db')
        cursor = conn.cursor()
        cursor.execute('SELECT task_name FROM tasks')
        tasks = cursor.fetchall()

        task_names = [task[0] for task in tasks]
        task_names.insert(0, 'Выберите задачу')  # Добавляем placeholder для выбора

        self.tasks_spinner.values = task_names
        conn.close()

    def show_popup(self, title, message):
        """Показывает попап с сообщением."""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()

class TaskListScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)

        self.selected_task_id = None  # Переменная для хранения ID выбранной задачи

        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Заголовок
        layout.add_widget(Label(text='Все Задачи', font_size=24, size_hint=(1, 0.2)))

        # Скроллируемый список задач
        self.scroll_view = ScrollView(size_hint=(1, 0.6))
        self.task_list_layout = GridLayout(cols=1, spacing=10, size_hint_y=None)
        self.task_list_layout.bind(minimum_height=self.task_list_layout.setter('height'))
        self.scroll_view.add_widget(self.task_list_layout)
        layout.add_widget(self.scroll_view)

        # Кнопка "Выполнить"
        complete_button = Button(text='Выполнить', size_hint=(1, 0.2))
        complete_button.bind(on_press=self.complete_task)
        layout.add_widget(complete_button)

        # Кнопка "Посмотреть Дедлайн"
        deadline_button = Button(text='Посмотреть Дедлайн', size_hint=(1, 0.2))
        deadline_button.bind(on_press=self.view_deadline)
        layout.add_widget(deadline_button)

        # Кнопка "Назад"
        back_button = Button(text='Назад', size_hint=(1, 0.2))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def update_task_list(self):
        """Обновляет список всех задач с именами студентов, которым они назначены."""
        self.task_list_layout.clear_widgets()  # Очищаем текущий список задач
        self.selected_task_id = None  # Сбрасываем выбор задачи

        try:
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()

            # Запрос для получения всех задач с именами студентов
            cursor.execute('''
                SELECT tasks.id_task, tasks.task_name, tasks.status, students.name
                FROM tasks
                LEFT JOIN user_to_task ON tasks.id_task = user_to_task.is_task
                LEFT JOIN students ON user_to_task.id_user = students.id
            ''')

            tasks = cursor.fetchall()

            for task_id, task_name, status, student_name in tasks:
                # Создаем горизонтальный layout для задачи
                task_layout = BoxLayout(orientation='horizontal', size_hint_y=None, height=40)

                # Чекбокс для выбора задачи
                checkbox = CheckBox(size_hint_x=None, width=40)
                checkbox.bind(active=lambda checkbox, is_active, t_id=task_id: self.select_task(t_id, is_active))

                # Метка с текстом задачи и имени студента
                task_label = Label(
                    text=f"{task_name} - Статус: {status} - Студент: {student_name if student_name else 'Не назначен'}",
                    size_hint_x=0.8
                )

                # Добавляем чекбокс и метку в горизонтальный layout
                task_layout.add_widget(checkbox)
                task_layout.add_widget(task_label)

                # Добавляем горизонтальный layout в основной список задач
                self.task_list_layout.add_widget(task_layout)

            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")
            self.show_popup("Ошибка", "Не удалось загрузить задачи.")

    def select_task(self, task_id, is_active):
        """Выбирает задачу при активации чекбокса."""
        if is_active:
            self.selected_task_id = task_id
        else:
            self.selected_task_id = None

    def complete_task(self, instance):
        """Отмечает выбранную задачу как 'Выполнена'."""
        if self.selected_task_id is None:
            self.show_popup("Ошибка", "Выберите задачу для выполнения.")
            return

        try:
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()

            # Обновляем статус выбранной задачи
            cursor.execute("UPDATE tasks SET status = 'Выполнена' WHERE id_task = ?", (self.selected_task_id,))
            conn.commit()

            self.show_popup("Успех", f"Задача с ID {self.selected_task_id} отмечена как 'Выполнена'.")
            self.update_task_list()  # Обновляем список задач
            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def view_deadline(self, instance):
        """Показывает дедлайн для выбранной задачи."""
        if self.selected_task_id is None:
            self.show_popup("Ошибка", "Выберите задачу для просмотра дедлайна.")
            return

        try:
            conn = sqlite3.connect('deadlibe.db')
            cursor = conn.cursor()

            # Получаем дедлайн выбранной задачи
            cursor.execute("SELECT task_name, deadline FROM tasks WHERE id_task = ?", (self.selected_task_id,))
            task = cursor.fetchone()

            if task:
                self.show_popup("Дедлайн", f"Задача: {task[0]}\nДедлайн: {task[1]}")
            else:
                self.show_popup("Ошибка", "Задача не найдена.")

            conn.close()
        except sqlite3.Error as e:
            print(f"Database error: {e}")

    def go_back(self, instance):
        """Возвращаемся на предыдущий экран"""
        self.manager.current = 'student_screen'

    def show_popup(self, title, message):
        """Показываем попап с сообщением"""
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()


class StudentScreen(Screen):
    def __init__(self, **kwargs):
        super().__init__(**kwargs)
        layout = BoxLayout(orientation='vertical', padding=20, spacing=10)

        # Кнопка "Мои Задачи"
        my_tasks_button = Button(text='Мои Задачи', size_hint=(1, 0.3))
        my_tasks_button.bind(on_press=self.show_tasks)
        layout.add_widget(my_tasks_button)

        # Кнопка "Назад"
        back_button = Button(text='Назад', size_hint=(1, 0.3))
        back_button.bind(on_press=self.go_back)
        layout.add_widget(back_button)

        self.add_widget(layout)

    def show_tasks(self, instance):
        """Отображает все задачи."""
        task_list_screen = self.manager.get_screen('task_list')
        task_list_screen.update_task_list()  # Просто вызываем метод без параметров
        self.manager.current = 'task_list'

    def go_back(self, instance):
        """Возврат на экран авторизации"""
        self.manager.current = 'login'

    def show_popup(self, title, message):
        popup = Popup(
            title=title,
            content=Label(text=message),
            size_hint=(0.8, 0.4),
        )
        popup.open()


class MyApp(App):
    def build(self):
        # Создаем экранный менеджер для переключения между экранами
        sm = ScreenManager()

        # Добавляем экран авторизации и другие экраны
        sm.add_widget(LoginScreen(name='login'))
        sm.add_widget(RegistrationScreen(name='register'))
        sm.add_widget(ForgotPasswordScreen(name='forgot_password'))
        sm.add_widget(StudentScreen(name='student_screen'))

        task_manager_layout = TaskManagerLayout(screen_manager=sm)

        task_manager_screen = Screen(name='task_manager')
        task_manager_screen.add_widget(task_manager_layout)
        sm.add_widget(task_manager_screen)

        task_list_screen = TaskListScreen(name='task_list')
        sm.add_widget(task_list_screen)

        return sm



if __name__ == '__main__':
    MyApp().run()


