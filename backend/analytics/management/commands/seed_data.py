"""
Management command: python manage.py seed_data
Создаёт тестовые данные для HRM-системы.
"""
import random
from datetime import date, timedelta
from django.core.management.base import BaseCommand
from django.contrib.auth.models import User


class Command(BaseCommand):
    help = 'Заполняет базу тестовыми данными'

    def handle(self, *args, **kwargs):
        self.stdout.write('Создаю тестовые данные...')
        departments = self._create_departments()
        positions = self._create_positions(departments)
        employees = self._create_employees(departments, positions)
        self._create_role_users(employees)
        self._create_leaves(employees)
        self._create_timesheets(employees)
        self._create_historical_data(employees)
        vacancies = self._create_vacancies(departments, positions)
        self._create_candidates(vacancies)
        self._create_public_vacancies(vacancies)
        self._create_training_data(employees)
        self._create_audit_logs(employees)
        self.stdout.write(self.style.SUCCESS('Тестовые данные успешно созданы!'))
        self.stdout.write('Пользователи:')
        self.stdout.write('  admin      / admin123  — DIRECTOR')
        self.stdout.write('  hr         / hr123     — HR_MANAGER')
        self.stdout.write('  ivanov     / ivanov123 — EMPLOYEE')
        self.stdout.write('  superadmin / super123  — ADMIN')

    def _create_role_users(self, employees):
        from accounts.models import UserProfile
        from employees.models import Employee

        ivanov_emp = Employee.objects.filter(email='ivanov@hrm.ru').first()

        special_users = [
            ('admin',      'admin123',  'Admin',  'Director', True,  'DIRECTOR',   None),
            ('hr',         'hr123',     'HR',     'Manager',  False, 'HR_MANAGER', None),
            ('ivanov',     'ivanov123', 'Алексей','Иванов',   False, 'EMPLOYEE',   ivanov_emp),
            ('superadmin', 'super123',  'Super',  'Admin',    False, 'ADMIN',      None),
        ]
        for username, password, first, last, is_super, role, emp in special_users:
            user, created = User.objects.get_or_create(username=username)
            user.set_password(password)
            user.first_name = first
            user.last_name = last
            user.is_staff = is_super
            user.is_superuser = is_super
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': role, 'employee': emp},
            )
            action = 'Создан' if created else 'Обновлён'
            self.stdout.write(f'  {action}: {username} ({role})')

        # Create a Django user for every employee (username = email prefix)
        special_emails = {'ivanov@hrm.ru'}
        emp_count = 0
        for emp in employees:
            if emp.email in special_emails:
                continue
            username = emp.email.split('@')[0]
            user, created = User.objects.get_or_create(username=username)
            user.set_password(username + '123')
            user.first_name = emp.first_name
            user.last_name = emp.last_name
            user.is_staff = False
            user.is_superuser = False
            user.save()
            UserProfile.objects.update_or_create(
                user=user,
                defaults={'role': 'EMPLOYEE', 'employee': emp},
            )
            emp_count += 1
        self.stdout.write(f'  Пользователей сотрудников: {emp_count}')

    def _create_departments(self):
        from employees.models import Department
        data = [
            ('Разработка', 'Отдел программной разработки'),
            ('HR', 'Отдел управления персоналом'),
            ('Финансы', 'Финансово-экономический отдел'),
            ('Маркетинг', 'Отдел маркетинга и рекламы'),
            ('Продажи', 'Коммерческий отдел'),
        ]
        depts = []
        for name, desc in data:
            dept, _ = Department.objects.get_or_create(name=name, defaults={'description': desc})
            depts.append(dept)
        self.stdout.write(f'  Отделов: {len(depts)}')
        return depts

    def _create_positions(self, departments):
        from employees.models import Position
        dept_map = {d.name: d for d in departments}
        data = [
            ('Разработчик Python',     'Разработка', 90000, 150000),
            ('Frontend-разработчик',   'Разработка', 80000, 130000),
            ('Тимлид',                 'Разработка', 130000, 200000),
            ('HR-менеджер',            'HR',          60000,  90000),
            ('Рекрутер',               'HR',          55000,  80000),
            ('Финансовый аналитик',    'Финансы',     85000, 120000),
            ('Бухгалтер',              'Финансы',     65000,  90000),
            ('Маркетолог',             'Маркетинг',   70000, 110000),
            ('Менеджер по продажам',   'Продажи',     60000, 120000),
            ('Аккаунт-менеджер',       'Продажи',     65000, 100000),
        ]
        positions = []
        for title, dept_name, s_min, s_max in data:
            pos, _ = Position.objects.get_or_create(
                title=title,
                defaults={'department': dept_map[dept_name], 'salary_min': s_min, 'salary_max': s_max},
            )
            positions.append(pos)
        self.stdout.write(f'  Должностей: {len(positions)}')
        return positions

    def _create_employees(self, departments, positions):
        from employees.models import Employee
        # Колонки: last, first, middle, email, gender, birth_date, hire_date,
        #          dept_i, pos_i, salary, ot, dist, ncomp, years, train,
        #          awards, days_award, bonus, has_bonus
        # (hours_fulfillment вычисляется автоматически из табеля)
        # Целевое распределение риска: 1 высокий / 3 средних / 14 низких
        employees_data = [
            # ── НИЗКИЙ РИСК (14 сотрудников) ─────────────────────────────────────
            ('Иванов',    'Алексей',    'Сергеевич',    'ivanov@hrm.ru',    'M', date(1990, 5, 15),  date(2020, 3, 1),   0, 0, 110000,  3, 10, 1,  6, 3,  2,  60, 0.20, True),
            ('Петрова',   'Мария',      'Андреевна',    'petrova@hrm.ru',   'F', date(1988, 8, 22),  date(2018, 7, 15),  1, 3,  78000,  5,  5, 1,  8, 3,  3,  45, 0.18, True),
            ('Козлова',   'Анна',       'Павловна',     'kozlova@hrm.ru',   'F', date(1993, 11, 30), date(2021, 4, 5),   3, 7,  82000,  1,  3, 1,  5, 4,  3,  30, 0.25, True),
            ('Морозова',  'Елена',      'Владимировна', 'morozova@hrm.ru',  'F', date(1991, 3, 7),   date(2019, 11, 20), 0, 1, 105000,  6, 15, 2,  7, 3,  2,  90, 0.18, True),
            ('Соколова',  'Ирина',      'Борисовна',    'sokolova@hrm.ru',  'F', date(1986, 12, 14), date(2016, 2, 15),  1, 3,  72000,  3,  5, 1, 10, 5,  3,  55, 0.22, True),
            ('Лебедева',  'Ольга',      'Сергеевна',    'lebedeva@hrm.ru',  'F', date(1989, 4, 19),  date(2017, 5, 1),   3, 7,  82000,  3,  6, 1,  9, 3,  2,  45, 0.20, True),
            ('Волков',    'Андрей',     'Николаевич',   'volkov@hrm.ru',    'M', date(1997, 9, 25),  date(2023, 6, 1),   0, 0,  88000,  3,  8, 1,  3, 3,  2,  50, 0.25, True),
            ('Давыдова',  'Светлана',   'Игоревна',     'davydova@hrm.ru',  'F', date(1984, 7, 11),  date(2013, 3, 15),  4, 9,  95000,  3,  6, 1, 13, 4,  2, 420, 0.28, True),
            ('Фролов',    'Виктор',     'Андреевич',    'frolov@hrm.ru',    'M', date(1992, 9, 3),   date(2021, 8, 1),   2, 5,  98000,  4,  8, 1,  5, 3,  2,  50, 0.18, True),
            ('Крылов',    'Денис',      'Андреевич',    'krylov@hrm.ru',    'M', date(1993, 5, 20),  date(2022, 3, 1),   0, 0,  92000,  4,  7, 1,  7, 3,  2,  45, 0.18, True),
            ('Новиков',   'Сергей',     'Михайлович',   'novikov@hrm.ru',   'M', date(1979, 6, 18),  date(2012, 9, 1),   4, 8, 125000,  8, 12, 3, 13, 3,  1, 200, 0.16, True),
            ('Медведев',  'Илья',       'Романович',    'medvedev@hrm.ru',  'M', date(1998, 11, 8),  date(2025, 1, 10),  1, 4,  88000,  3,  8, 1,  5, 3,  3,  30, 0.15, True),
            ('Романов',   'Константин', 'Витальевич',   'romanov@hrm.ru',   'M', date(1996, 4, 22),  date(2024, 2, 1),   0, 0,  90000,  3,  7, 1,  5, 4,  3,  25, 0.15, True),
            ('Климова',   'Виктория',   'Петровна',     'klimova@hrm.ru',   'F', date(1993, 1, 15),  date(2025, 5, 1),   3, 7,  85000,  2,  6, 1,  2, 3,  3,  20, 0.18, True),
            # ── СРЕДНИЙ РИСК (3 сотрудника) ───────────────────────────────────────
            ('Зайцев',    'Николай',    'Александрович','zaitsev@hrm.ru',   'M', date(1994, 7, 3),   date(2020, 8, 10),  2, 6,  92000, 17, 20, 2,  5, 2,  1, 250, 0.08, False),
            ('Сорокин',   'Игорь',      'Олегович',     'sorokin@hrm.ru',   'M', date(1991, 6, 14),  date(2021, 9, 1),   1, 4,  84000, 18, 12, 3,  4, 2,  1, 230, 0.06, False),
            ('Тимофеева', 'Наталья',    'Сергеевна',    'timofeeva@hrm.ru', 'F', date(1989, 3, 28),  date(2020, 6, 15),  3, 7,  71000, 16, 14, 3,  6, 3,  1, 260, 0.09, False),
            # ── ВЫСОКИЙ РИСК (1 сотрудник) ────────────────────────────────────────
            ('Сидоров',   'Дмитрий',    'Игоревич',     'sidorov@hrm.ru',   'M', date(1995, 2, 10),  date(2024, 1, 10),  2, 5,  85000, 35, 25, 7,  1, 1,  0, 450, 0.05, False),
        ]

        dept_list = list(departments)
        pos_list = list(positions)
        updated = []

        for row in employees_data:
            (last, first, middle, email, gender, bday, hday,
             dept_i, pos_i, salary, ot, dist, ncomp, years, train,
             awards, days_award, bonus, has_bonus) = row

            dept = dept_list[dept_i % len(dept_list)]
            pos = pos_list[pos_i % len(pos_list)]

            emp, _ = Employee.objects.update_or_create(
                email=email,
                defaults={
                    'last_name': last, 'first_name': first, 'middle_name': middle,
                    'gender': gender, 'birth_date': bday, 'hire_date': hday,
                    'department': dept, 'position': pos, 'salary': salary,
                    'status': 'active',
                    'overtime_hours': ot, 'distance_from_home': dist,
                    'num_companies_worked': ncomp, 'years_at_company': years,
                    'training_times_last_year': train,
                    'awards_last_year': awards,
                    'days_since_last_award': days_award,
                    'bonus_share': bonus,
                    'has_bonus_program': has_bonus,
                },
            )
            updated.append(emp)

        # Назначаем менеджера всем кроме первого
        if len(updated) >= 2:
            for emp in updated[1:]:
                if emp.manager_id != updated[0].id:
                    emp.manager = updated[0]
                    emp.save(update_fields=['manager'])

        self.stdout.write(f'  Сотрудников: {len(updated)}')
        return updated

    def _create_leaves(self, employees):
        from leaves.models import LeaveRequest, SickLeaveDetails
        leave_data = [
            # Будущие / текущие заявки
            (0, 'annual', date(2026, 6, 1),  date(2026, 6, 14),  'approved'),
            (1, 'sick',   date(2026, 4, 3),  date(2026, 4, 7),   'approved'),
            (2, 'annual', date(2026, 7, 15), date(2026, 7, 28),  'pending'),
            (3, 'study',  date(2026, 5, 20), date(2026, 5, 23),  'pending'),
            (4, 'unpaid', date(2026, 3, 10), date(2026, 3, 12),  'approved'),
            (5, 'annual', date(2026, 8, 1),  date(2026, 8, 14),  'pending'),
            (6, 'sick',   date(2026, 5, 1),  date(2026, 5, 3),   'rejected'),
            (7, 'annual', date(2026, 9, 1),  date(2026, 9, 14),  'pending'),
            # Одобренные отпуска в мае 2026 (отображаются в табеле)
            (4, 'annual', date(2026, 5, 12), date(2026, 5, 15),  'approved'),  # Соколова, вт-пт
            (7, 'annual', date(2026, 5, 26), date(2026, 5, 29),  'approved'),  # Давыдова, вт-пт
            # Исторические одобренные ежегодные отпуска (последний год) → vacation_days_used
            (0,  'annual', date(2025, 7, 1),  date(2025, 7, 14),  'approved'),  # 14 дн.
            (1,  'annual', date(2025, 8, 4),  date(2025, 8, 17),  'approved'),  # 14 дн.
            (2,  'annual', date(2025, 6, 9),  date(2025, 6, 22),  'approved'),  # 14 дн.
            (3,  'annual', date(2025, 9, 1),  date(2025, 9, 7),   'approved'),  # 7 дн.
            (5,  'annual', date(2025, 7, 21), date(2025, 8, 3),   'approved'),  # 14 дн.
            (6,  'annual', date(2025, 10, 6), date(2025, 10, 12), 'approved'),  # 7 дн.
            (8,  'annual', date(2025, 8, 18), date(2025, 8, 24),  'approved'),  # 7 дн.
            (9,  'annual', date(2025, 11, 3), date(2025, 11, 9),  'approved'),  # 7 дн.
            (10, 'annual', date(2025, 9, 15), date(2025, 9, 28),  'approved'),  # 14 дн.
            (14, 'annual', date(2025, 7, 7),  date(2025, 7, 13),  'approved'),  # 7 дн.  — Зайцев
            (16, 'annual', date(2025, 8, 25), date(2025, 9, 7),   'approved'),  # 14 дн. — Тимофеева
        ]
        sick_details_data = {
            # (employee_idx, start_date): (sick_leave_number, issue_date, close_date, medical_institution, diagnosis_code)
            (1, date(2026, 4, 3)): ('123456789012', date(2026, 4, 3), date(2026, 4, 7), 'ГБУЗ Городская поликлиника №1', 'J06.9'),
            (6, date(2026, 5, 1)): ('987654321098', date(2026, 5, 1), date(2026, 5, 3), 'ГБУЗ Городская больница №3', 'K29.7'),
        }
        count = 0
        for emp_i, lt, sd, ed, st in leave_data:
            if emp_i < len(employees):
                leave, _ = LeaveRequest.objects.get_or_create(
                    employee=employees[emp_i],
                    start_date=sd,
                    defaults={'leave_type': lt, 'end_date': ed, 'status': st},
                )
                if lt == 'sick':
                    key = (emp_i, sd)
                    if key in sick_details_data:
                        num, idate, cdate, inst, code = sick_details_data[key]
                        SickLeaveDetails.objects.get_or_create(
                            leave_request=leave,
                            defaults={
                                'sick_leave_number': num,
                                'issue_date': idate,
                                'close_date': cdate,
                                'medical_institution': inst,
                                'diagnosis_code': code,
                            },
                        )
                    else:
                        SickLeaveDetails.objects.get_or_create(leave_request=leave)
                count += 1
        self.stdout.write(f'  Заявок на отпуск: {count}')

    def _create_timesheets(self, employees):
        from timesheets.models import Timesheet
        from leaves.models import LeaveRequest

        # Сидоров (idx=17) — burnout/перегрузка: 9.5ч/день + сверхурочные → hf ≈ 120 %
        HIGH_RISK_IDX   = 17
        HIGH_RISK_HOURS = 9.5

        # Госпраздники России в мае 2026
        HOLIDAYS_MAY = {
            date(2026, 5, 1),   # День труда
            date(2026, 5, 2),   # Праздничный выходной
            date(2026, 5, 3),   # Праздничный выходной
            date(2026, 5, 9),   # День Победы
        }

        # Переработки в мае: средний риск (14-16) и высокий (17 — Сидоров, систематические)
        OVERTIME_MAY = {
            14: {6: 1.5, 13: 1.5, 20: 1.0, 27: 1.0},    # Зайцев
            15: {5: 2.0, 12: 2.0, 19: 1.5, 26: 1.5},    # Сорокин
            16: {7: 1.5, 14: 1.0, 21: 1.5, 28: 1.0},    # Тимофеева
            17: {6: 2.0, 13: 2.5, 20: 2.0, 27: 2.5},    # Сидоров — тяжёлые переработки
        }

        # Одобренные отпуска по месяцам: {employee_id: set[date]}
        def _leave_days_for(start, end):
            ld: dict = {}
            for lv in LeaveRequest.objects.filter(
                status='approved', start_date__lte=end, end_date__gte=start,
            ):
                cur = max(lv.start_date, start)
                fin = min(lv.end_date, end)
                while cur <= fin:
                    ld.setdefault(lv.employee_id, set()).add(cur)
                    cur += timedelta(days=1)
            return ld

        leave_apr = _leave_days_for(date(2026, 4, 1), date(2026, 4, 30))
        leave_may = _leave_days_for(date(2026, 5, 1), date(2026, 5, 31))

        # Больничные в апреле 2026 (весенний сезон)
        SICK_APR = {
            0:  [date(2026, 4, 2),  date(2026, 4, 3)],
            2:  [date(2026, 4, 7)],
            5:  [date(2026, 4, 14), date(2026, 4, 15), date(2026, 4, 16)],
            8:  [date(2026, 4, 22)],
            11: [date(2026, 4, 28)],
            14: [date(2026, 4, 9),  date(2026, 4, 10)],
        }

        count = 0
        for idx, emp in enumerate(employees):
            base_hours = HIGH_RISK_HOURS if idx == HIGH_RISK_IDX else 8.0
            sick_days_apr = set(SICK_APR.get(idx, []))

            # ── Апрель 2026 ────────────────────────────────────────────────
            for day_num in range(1, 31):
                d  = date(2026, 4, day_num)
                wd = d.weekday()
                if wd >= 5:
                    dtype, hw, ot = 'WEEKEND', 0.0, 0.0
                elif d in sick_days_apr:
                    dtype, hw, ot = 'SICK', 0.0, 0.0
                elif d in leave_apr.get(emp.id, set()):
                    dtype, hw, ot = 'VACATION', 0.0, 0.0
                else:
                    dtype, hw, ot = 'WORK', base_hours, 0.0
                Timesheet.objects.update_or_create(
                    employee=emp, work_date=d,
                    defaults={'day_type': dtype, 'hours_worked': hw, 'overtime_hours': ot},
                )
                count += 1

            # ── Май 2026 ────────────────────────────────────────────────────
            ot_map = {
                date(2026, 5, d): h
                for d, h in OVERTIME_MAY.get(idx, {}).items()
            }
            for day_num in range(1, 32):
                d  = date(2026, 5, day_num)
                wd = d.weekday()
                if d in HOLIDAYS_MAY:
                    dtype, hw, ot = 'HOLIDAY', 0.0, 0.0
                elif wd >= 5:
                    dtype, hw, ot = 'WEEKEND', 0.0, 0.0
                elif d in leave_may.get(emp.id, set()):
                    dtype, hw, ot = 'VACATION', 0.0, 0.0
                else:
                    ot    = ot_map.get(d, 0.0)
                    hw    = base_hours + ot
                    dtype = 'WORK'
                Timesheet.objects.update_or_create(
                    employee=emp, work_date=d,
                    defaults={'day_type': dtype, 'hours_worked': hw, 'overtime_hours': ot},
                )
                count += 1

        self.stdout.write(f'  Записей табеля: {count}')

    def _create_historical_data(self, employees):
        """Генерирует 24 месяца исторических данных для SARIMA по всем 5 метрикам."""
        import calendar
        from timesheets.models import Timesheet
        from employees.models import Employee, Department, Position

        rng = random.Random(42)

        # May 2024 – March 2026 (23 months); April + May 2026 covered by _create_timesheets
        months = []
        y, m = 2024, 5
        for _ in range(23):
            months.append(date(y, m, 1))
            m += 1
            if m > 12:
                m = 1
                y += 1

        ts_count = 0

        for month_date in months:
            year, month = month_date.year, month_date.month
            last_day = calendar.monthrange(year, month)[1]

            # Seasonal sick-day probability (% of workdays per employee)
            # Winter peak Nov–Feb, mild shoulder Mar/Oct, summer low
            sick_p = 0.12 if month in (11, 12, 1, 2) else 0.06 if month in (3, 10) else 0.03

            # Quarterly overtime pressure multiplier (Q4 crunch, Q3 holiday dip)
            ot_scale = 1.6 if month in (10, 11, 12) else 0.6 if month in (6, 7, 8) else 1.0

            eligible = [e for e in employees if e.hire_date <= date(year, month, last_day)]

            for emp in eligible:
                used = set()

                # ── Sick days ──────────────────────────────────────────────
                n_sick = max(0, round(rng.gauss(sick_p * 22, 0.8)))
                for _ in range(min(n_sick, 6)):
                    day = rng.randint(1, last_day)
                    d = date(year, month, day)
                    if d.weekday() < 5 and day not in used:
                        used.add(day)
                        _, created = Timesheet.objects.get_or_create(
                            employee=emp, work_date=d,
                            defaults={'day_type': 'SICK', 'hours_worked': 0.0, 'overtime_hours': 0.0},
                        )
                        if created:
                            ts_count += 1

                # ── Overtime work days ─────────────────────────────────────
                if rng.random() < 0.35:
                    n_ot = rng.randint(1, 3)
                    for _ in range(n_ot):
                        day = rng.randint(1, last_day)
                        d = date(year, month, day)
                        if d.weekday() < 5 and day not in used:
                            used.add(day)
                            ot = round(rng.uniform(0.5, 3.0) * ot_scale, 1)
                            _, created = Timesheet.objects.get_or_create(
                                employee=emp, work_date=d,
                                defaults={'day_type': 'WORK', 'hours_worked': 8.0 + ot, 'overtime_hours': ot},
                            )
                            if created:
                                ts_count += 1

        self.stdout.write(f'  Исторических записей табеля: {ts_count}')

        # ── Terminated employees: headcount grows 2023-2025, then drops ──
        depts = list(Department.objects.all())
        positions = list(Position.objects.all())

        terminated = [
            # first, last, middle, gender, hire_date, email, salary, has_bonus
            ('Дмитрий',  'Уваров',   'Сергеевич', 'M', date(2023, 3,  1), 'uvarov.hist@hrm.ru',    68000, True),
            ('Марина',   'Белова',   'Андреевна',  'F', date(2023, 7,  1), 'belova.hist@hrm.ru',    71000, False),
            ('Кирилл',   'Гусев',    'Олегович',   'M', date(2022, 11, 1), 'gusev.hist@hrm.ru',     64000, False),
            ('Алина',    'Романова', 'Дмитриевна', 'F', date(2024, 2,  1), 'romanova.hist@hrm.ru',  73000, True),
            ('Николай',  'Фомин',    'Александрович','M',date(2023, 5,  1), 'fomin.hist@hrm.ru',    66000, False),
            ('Светлана', 'Крылова',  'Павловна',   'F', date(2024, 6,  1), 'krylova.hist@hrm.ru',   75000, True),
            ('Антон',    'Казаков',  'Витальевич', 'M', date(2023, 9,  1), 'kazakov.hist@hrm.ru',   69000, False),
            ('Юлия',     'Лазарева', 'Николаевна', 'F', date(2022, 8,  1), 'lazareva.hist@hrm.ru',  72000, True),
            ('Роман',    'Денисов',  'Игоревич',   'M', date(2024, 4,  1), 'denisov.hist@hrm.ru',   67000, False),
            ('Ирина',    'Панова',   'Сергеевна',  'F', date(2023, 12, 1), 'panova.hist@hrm.ru',    70000, True),
            ('Вадим',    'Алексеев', 'Михайлович', 'M', date(2024, 8,  1), 'alekseev.hist@hrm.ru',  74000, False),
            ('Татьяна',  'Борисова', 'Юрьевна',    'F', date(2025, 1,  1), 'borisova.hist@hrm.ru',  76000, True),
        ]

        term_count = 0
        for first, last, middle, gender, hire_date, email, salary, has_bonus in terminated:
            dept = rng.choice(depts)
            pos  = rng.choice([p for p in positions if p.department_id == dept.id] or positions)
            _, created = Employee.objects.get_or_create(
                email=email,
                defaults={
                    'first_name':              first,
                    'last_name':               last,
                    'middle_name':             middle,
                    'gender':                  gender,
                    'hire_date':               hire_date,
                    'department':              dept,
                    'position':                pos,
                    'salary':                  salary,
                    'status':                  'inactive',
                    'num_companies_worked':    rng.randint(2, 6),
                    'years_at_company':        rng.randint(1, 4),
                    'overtime_hours':          round(rng.uniform(2.0, 18.0), 1),
                    'distance_from_home':      rng.randint(5, 60),
                    'training_times_last_year':rng.randint(0, 3),
                    'awards_last_year':        rng.randint(0, 2),
                    'days_since_last_award':   rng.randint(90, 730),
                    'bonus_share':             round(rng.uniform(0.05, 0.20), 2),
                    'has_bonus_program':       has_bonus,
                },
            )
            if created:
                term_count += 1

        self.stdout.write(f'  Уволенных сотрудников добавлено: {term_count}')
        self.stdout.write(self.style.SUCCESS('  Исторические данные для SARIMA готовы!'))

    def _create_vacancies(self, departments, positions):
        from recruitment.models import Vacancy
        dept_list = list(departments)
        vac_data = [
            dict(
                title='Senior Python Developer',
                dept_i=0, status='open', employment_type='hybrid',
                experience_years=3, salary_from=180000, salary_to=280000,
                required_skills=['Python', 'Django', 'FastAPI', 'PostgreSQL', 'Redis', 'Docker', 'REST API', 'Git', 'pytest', 'CI/CD'],
                description=(
                    'Ищем опытного Python backend-разработчика для развития высоконагруженной платформы. '
                    'Вы войдёте в продуктовую команду и будете проектировать микросервисы, REST API, '
                    'работать с базами данных и участвовать в code review.'
                ),
                requirements=(
                    'Обязательно: Python 3+ от 3 лет, Django или FastAPI, PostgreSQL, Docker, Git, REST API, pytest. '
                    'Желательно: микросервисная архитектура, Redis, Kafka, scikit-learn, CI/CD (GitLab CI / GitHub Actions).'
                ),
                responsibilities=(
                    'Проектирование и разработка backend-микросервисов на Python. '
                    'Создание REST API и интеграции со сторонними сервисами. '
                    'Написание unit- и интеграционных тестов. '
                    'Участие в code review и проектировании архитектуры. '
                    'Оптимизация запросов к PostgreSQL и Redis.'
                ),
                conditions=(
                    'Зарплата 180 000 — 280 000 руб. gross. '
                    'Гибридный формат: 3 дня в офисе, 2 дня удалённо. '
                    'ДМС со стоматологией с первого месяца. '
                    'Ноутбук и оборудование за счёт компании. '
                    '28 дней отпуска. Конференции за счёт компании.'
                ),
            ),
            dict(
                title='Vue.js Frontend Developer',
                dept_i=0, status='open', employment_type='hybrid',
                experience_years=2, salary_from=140000, salary_to=220000,
                required_skills=['Vue.js', 'TypeScript', 'Pinia', 'Vite', 'HTML', 'CSS', 'REST API', 'Git'],
                description=(
                    'Ищем Frontend-разработчика на Vue.js 3 для работы над продуктовым веб-приложением. '
                    'Задачи разнообразные: от реализации UI-компонентов до работы с дизайн-системой и оптимизации производительности.'
                ),
                requirements=(
                    'Обязательно: Vue.js 3 (Composition API) от 2 лет, TypeScript, Pinia, Vite или Webpack, HTML/CSS, REST API, Git. '
                    'Желательно: Nuxt.js SSR, Jest/Vitest, React, компонентные библиотеки.'
                ),
                responsibilities=(
                    'Разработка компонентов на Vue 3 Composition API. '
                    'Интеграция с REST API и работа с Pinia-хранилищами. '
                    'Оптимизация производительности приложения. '
                    'Разработка и поддержка дизайн-системы. '
                    'Code review и менторинг junior-разработчиков.'
                ),
                conditions=(
                    'Зарплата 140 000 — 220 000 руб. gross. '
                    'Гибридный формат работы, ДМС с 3-го месяца. '
                    'Гибкое начало рабочего дня (9–11). '
                    'Возможность перейти на fulltime remote после 6 месяцев. '
                    'Бюджет на обучение и конференции.'
                ),
            ),
            dict(
                title='HR Business Partner',
                dept_i=1, status='open', employment_type='full_time',
                experience_years=4, salary_from=120000, salary_to=180000,
                required_skills=['Рекрутинг', 'Адаптация', 'KPI', 'Оценка персонала', 'HRIS', '1С ЗУП', 'Трудовое законодательство'],
                description=(
                    'HR Business Partner для стратегической поддержки бизнес-подразделений IT-компании. '
                    'Вы будете работать с топ-менеджерами, формировать кадровую стратегию и автоматизировать HR-процессы.'
                ),
                requirements=(
                    'Опыт HR от 4 лет (из них минимум 2 года как HRBP). '
                    'Знание рекрутинга, адаптации, оценки персонала (STAR, BARS). '
                    'Знание трудового законодательства и кадрового делопроизводства. '
                    'Опыт работы с HRIS-системами (1С ЗУП, Bamboo HR). '
                    'Опыт в IT-компаниях — сильное преимущество.'
                ),
                responsibilities=(
                    'Полный цикл подбора ключевых IT- и бизнес-специалистов. '
                    'Онбординг и адаптация новых сотрудников. '
                    'Разработка и внедрение систем KPI и оценки. '
                    'Консультирование руководителей по HR-вопросам. '
                    'Анализ текучести и вовлечённости, ведение кадровой документации в 1С ЗУП.'
                ),
                conditions=(
                    'Зарплата 120 000 — 180 000 руб. gross. '
                    'Полная занятость, офис. ДМС с первого месяца. '
                    'Корпоративные курсы и сертификации. '
                    '14 дней дополнительного отпуска.'
                ),
            ),
            dict(
                title='Data Analyst',
                dept_i=2, status='on_hold', employment_type='full_time',
                experience_years=2, salary_from=100000, salary_to=160000,
                required_skills=['Python', 'pandas', 'SQL', 'Excel', 'Power BI', 'numpy', 'статистика'],
                description=(
                    'Аналитик данных в финансово-экономический отдел. '
                    'Работа с большими объёмами данных, построение дашбордов, управленческая отчётность.'
                ),
                requirements=(
                    'Обязательно: Python (pandas, numpy), SQL (PostgreSQL или MySQL), Excel на продвинутом уровне, статистика. '
                    'Желательно: Power BI или Tableau, 1С, SAP, опыт финансового моделирования от 2 лет.'
                ),
                responsibilities=(
                    'Анализ финансовых и операционных данных компании. '
                    'Построение дашбордов в Power BI и Tableau. '
                    'Разработка прогнозных моделей на Python (pandas, numpy). '
                    'Подготовка управленческой отчётности. '
                    'Работа с SQL-базами данных, автоматизация отчётов.'
                ),
                conditions=(
                    'Зарплата 100 000 — 160 000 руб. Полная занятость, офис. '
                    'ДМС. Годовые бонусы по KPI (до 3 окладов). '
                    'Курсы за счёт компании. Современный офис в центре.'
                ),
            ),
            dict(
                title='Sales Manager',
                dept_i=4, status='open', employment_type='full_time',
                experience_years=2, salary_from=80000, salary_to=150000,
                required_skills=['B2B продажи', 'CRM', 'Bitrix24', 'AmoCRM', 'холодные звонки', 'переговоры'],
                description=(
                    'Менеджер по активным B2B продажам для работы с корпоративными клиентами. '
                    'Продукт — SaaS-платформа для автоматизации HR-процессов. Клиенты — компании от 50 сотрудников.'
                ),
                requirements=(
                    'Опыт B2B продаж от 2 лет. Уверенная работа с CRM (Bitrix24 или AmoCRM). '
                    'Навыки холодных звонков, переговоров, работы с возражениями. '
                    'Умение проводить демо-презентации. Нацеленность на результат.'
                ),
                responsibilities=(
                    'Поиск и привлечение новых корпоративных клиентов. '
                    'Проведение холодных звонков и онлайн-демо продукта. '
                    'Ведение воронки продаж в CRM Bitrix24, заключение сделок. '
                    'Выполнение и перевыполнение плана продаж.'
                ),
                conditions=(
                    'Оклад 80 000 руб. + % от продаж (OTE 150 000+). '
                    'Бонусы за перевыполнение плана. Корпоративный телефон и ноутбук. '
                    'Обучение продукту и техникам продаж. '
                    'Карьерный рост до старшего менеджера или руководителя отдела.'
                ),
            ),
        ]
        created = []
        for v in vac_data:
            dept_i = v.pop('dept_i')
            vac, created_now = Vacancy.objects.get_or_create(
                title=v['title'],
                defaults={'department': dept_list[dept_i],
                           **{k: val for k, val in v.items() if k != 'title'}},
            )
            if not created_now:
                for field, val in v.items():
                    if field != 'title':
                        setattr(vac, field, val)
                vac.save()
            created.append(vac)
        self.stdout.write(f'  Вакансий: {len(created)}')
        return created

    def _create_candidates(self, vacancies):
        from recruitment.models import Candidate
        candidates_data = [
            dict(
                vac_i=0, last_name='Смирнов', first_name='Павел',
                email='smirnov@mail.ru', stage='interview', rating=4,
                cover_letter=(
                    'Здравствуйте! Я опытный Python-разработчик с 5-летним стажем. '
                    'Особенно силён в высоконагруженных системах и микросервисной архитектуре. '
                    'Хотел бы присоединиться к вашей команде.'
                ),
                resume_text=(
                    'Смирнов Павел Андреевич. Senior Python Developer. Опыт работы 5 лет.\n\n'
                    'ОПЫТ РАБОТЫ:\n'
                    'ООО "ТехноЛаб" (2021-2024), Senior Python Developer.\n'
                    'Разрабатывал высоконагруженные backend-сервисы на Django и FastAPI.\n'
                    'Проектировал и оптимизировал PostgreSQL-схемы до 50 млн записей.\n'
                    'Настраивал Redis-кеширование, снизил время ответа API на 60 процентов.\n'
                    'Реализовывал микросервисную архитектуру с Kafka и Docker.\n'
                    'Покрывал код тестами pytest (coverage 85 процентов), настраивал GitLab CI/CD.\n'
                    'Участвовал в code review, менторил Junior-разработчиков.\n\n'
                    'ООО "СофтДев" (2019-2021), Python Developer.\n'
                    'Разрабатывал REST API на Django REST Framework.\n'
                    'Писал скрипты парсинга данных и интеграции с внешними сервисами.\n'
                    'Работал с PostgreSQL, Git, Docker.\n\n'
                    'НАВЫКИ:\n'
                    'Python (5 лет), Django, FastAPI, PostgreSQL, Redis, Docker, Kafka, '
                    'REST API, микросервисы, pytest, CI/CD (GitLab, GitHub Actions), '
                    'scikit-learn, pandas, Git, Linux.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'МГТУ им. Баумана, Факультет информатики и систем управления, бакалавриат (2019).\n\n'
                    'ДОПОЛНИТЕЛЬНО:\n'
                    'Участник PyCon Russia 2022 и 2023. Ментор на CodeMentor. '
                    'Готов к гибридному формату работы, имею опыт удалённой работы в международных командах.'
                ),
            ),
            dict(
                vac_i=0, last_name='Кузнецов', first_name='Роман',
                email='kuznetsov@mail.ru', stage='screening', rating=3,
                cover_letter=(
                    'Здравствуйте! Я Python-разработчик с 2-летним опытом. '
                    'Работал с Django REST Framework и PostgreSQL. Хочу развиваться и учиться у опытных коллег.'
                ),
                resume_text=(
                    'Кузнецов Роман Сергеевич. Python Backend Developer. Опыт работы 2 года.\n\n'
                    'ОПЫТ РАБОТЫ:\n'
                    'ООО "ВебСтарт" (2022-2024), Python Developer.\n'
                    'Разрабатывал REST API на Django REST Framework для веб-сервиса.\n'
                    'Работал с PostgreSQL: писал SQL-запросы, оптимизировал выборки.\n'
                    'Настраивал Docker-контейнеры для разработки и деплоя на сервер.\n'
                    'Работал с Git: ветки, pull request, merge, code review.\n'
                    'Писал unit-тесты на pytest для бизнес-логики приложения.\n\n'
                    'ООО "ФрилансПрокси" (2022), Junior Python Developer.\n'
                    'Разрабатывал скрипты автоматизации на Python.\n'
                    'Работал с REST API сторонних сервисов.\n\n'
                    'НАВЫКИ:\n'
                    'Python (2 года), Django, Django REST Framework, PostgreSQL, '
                    'Docker, Git, pytest, REST API, HTML, CSS, JavaScript (базово).\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'НИУ ВШЭ, Прикладная математика и информатика, бакалавриат (2022).\n\n'
                    'ЦЕЛИ:\n'
                    'Хочу развиваться в backend-разработке, глубже изучить FastAPI, '
                    'микросервисную архитектуру и Redis. Открыт к обучению и менторству. '
                    'Интересует работа в продуктовой компании с современным технологическим стеком.'
                ),
            ),
            dict(
                vac_i=1, last_name='Попова', first_name='Виктория',
                email='popova@mail.ru', stage='offer', rating=5,
                cover_letter=(
                    'Здравствуйте! Я Senior Frontend Developer с фокусом на Vue.js 3. '
                    'Строила дизайн-системы, SSR на Nuxt, имею опыт менторинга. Очень заинтересована в вакансии.'
                ),
                resume_text=(
                    'Попова Виктория Александровна. Senior Frontend Developer (Vue.js). Опыт 4 года.\n\n'
                    'ОПЫТ РАБОТЫ:\n'
                    'ООО "ПродуктЛаб" (2022-2024), Senior Frontend Developer.\n'
                    'Архитектор фронтенда SaaS-платформы на Vue.js 3, Composition API, Pinia.\n'
                    'Создала с нуля дизайн-систему (40+ компонентов) на TypeScript и Vite.\n'
                    'Реализовала SSR на Nuxt.js 3, улучшила LCP с 4.5 до 1.8 секунды.\n'
                    'Настроила Vitest и Cypress e2e тестирование (coverage 70 процентов).\n'
                    'Интегрировала REST API, WebSocket, работала с OpenAPI спецификацией.\n'
                    'Менторила 2 junior-разработчиков, проводила code review регулярно.\n\n'
                    'ООО "ДизайнДев" (2020-2022), Frontend Developer.\n'
                    'Разработка компонентов на Vue.js 2 и миграция на Vue.js 3 Composition API.\n'
                    'Работа с Vuex и переход на Pinia, Webpack и переход на Vite.\n\n'
                    'НАВЫКИ:\n'
                    'Vue.js 3 (4 года), TypeScript, Composition API, Pinia, Vite, Webpack, '
                    'Nuxt.js, HTML5, CSS3, SASS/SCSS, REST API, WebSocket, Vitest, Cypress, '
                    'Git, Docker (базово), React (изучаю), Figma.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'МГУ, Факультет вычислительной математики и кибернетики (2020).'
                ),
            ),
            dict(
                vac_i=1, last_name='Федоров', first_name='Илья',
                email='fedorov@mail.ru', stage='new', rating=2,
                cover_letter=(
                    'Добрый день! Я изучаю Vue.js самостоятельно и ищу первую работу. '
                    'Понимаю, что опыта мало, но готов учиться и вкладывать много усилий.'
                ),
                resume_text=(
                    'Федоров Илья Дмитриевич. Junior Frontend Developer (начинающий). Без коммерческого опыта.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'Самообучение (2023-2024):\n'
                    'Курс JavaScript с нуля на Udemy (2023).\n'
                    'Курс Vue.js 3 для начинающих по YouTube (2024).\n'
                    'Прочитал официальную документацию Vue.js 3 и гайды.\n\n'
                    'УЧЕБНЫЕ ПРОЕКТЫ:\n'
                    'Todo-приложение на Vue.js 3 с Composition API и Pinia (выложено на GitHub).\n'
                    'Лендинг для личного портфолио на HTML, CSS и JavaScript.\n\n'
                    'НАВЫКИ:\n'
                    'HTML (хорошо), CSS (хорошо), JavaScript (базово), '
                    'Vue.js 3 (базово, Composition API знаю теорию и немного практики).\n\n'
                    'ЦЕЛИ:\n'
                    'Ищу первую работу в frontend-разработке. '
                    'Готов работать под наставничеством опытных разработчиков. '
                    'Нацелен на долгосрочное сотрудничество и профессиональный рост. '
                    'Понимаю важность TypeScript и готов его освоить в процессе работы.'
                ),
            ),
            dict(
                vac_i=2, last_name='Орлова', first_name='Наталья',
                email='orlova@mail.ru', stage='interview', rating=4,
                cover_letter=(
                    'Здравствуйте! Я Senior HRBP с 6-летним опытом в IT-компаниях. '
                    'Специализируюсь на рекрутинге технических специалистов и развитии HR-систем.'
                ),
                resume_text=(
                    'Орлова Наталья Владимировна. HR Business Partner. Опыт 6 лет.\n\n'
                    'ОПЫТ РАБОТЫ:\n'
                    'ООО "АйТиКорп" (2021-2024), Senior HR Business Partner.\n'
                    'Полный цикл рекрутинга IT-специалистов (Python, Java, Go, Frontend, DevOps).\n'
                    'Разработала систему адаптации и онбординга, снизила текучесть в первый год на 35 процентов.\n'
                    'Внедрила систему KPI для 150+ сотрудников, провела 3 цикла оценки по методологии BARS.\n'
                    'Работала с HRIS-системами (1С ЗУП, Bamboo HR), вела кадровое делопроизводство.\n'
                    'Консультировала топ-менеджеров по вопросам мотивации и удержания персонала.\n'
                    'Проводила exit-интервью, анализировала причины текучести кадров.\n\n'
                    'ООО "ГлобалСервис" (2018-2021), HR Manager.\n'
                    'Рекрутинг и адаптация: подбор до 10 вакансий одновременно.\n'
                    'Проведение структурированных интервью STAR, проверка рекомендаций, оффер-менеджмент.\n\n'
                    'НАВЫКИ:\n'
                    'Рекрутинг (полный цикл), адаптация персонала, оценка по KPI, BARS, '
                    'трудовое законодательство, 1С ЗУП, Bamboo HR, HRIS, HR-аналитика, '
                    'Excel (продвинутый), интервью по компетенциям, онбординг.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'РЭУ им. Плеханова, HR-менеджмент, магистратура (2018).'
                ),
            ),
            dict(
                vac_i=3, last_name='Михайлов', first_name='Антон',
                email='mikhailov@mail.ru', stage='screening', rating=3,
                cover_letter=(
                    'Здравствуйте! Я финансовый аналитик с 3-летним опытом работы с данными. '
                    'Умею соединять финансовую экспертизу с Python и SQL.'
                ),
                resume_text=(
                    'Михайлов Антон Олегович. Data Analyst / Financial Analyst. Опыт 3 года.\n\n'
                    'ОПЫТ РАБОТЫ:\n'
                    'ООО "ФинСтарт" (2021-2024), Financial Data Analyst.\n'
                    'Финансовое моделирование в Excel: сложные формулы, Power Query, сводные таблицы.\n'
                    'Анализ данных на Python: pandas, numpy, matplotlib для визуализации.\n'
                    'Разработка SQL-запросов в PostgreSQL и MySQL для выгрузки аналитических отчётов.\n'
                    'Построение интерактивных дашбордов в Power BI: подключение к БД, DAX-формулы.\n'
                    'Бюджетирование, план-факт анализ, подготовка управленческой отчётности.\n'
                    'Работал с 1С Бухгалтерия и SAP FI при подготовке финансовой отчётности.\n\n'
                    'НАВЫКИ:\n'
                    'Python (pandas, numpy, matplotlib, openpyxl), SQL (PostgreSQL, MySQL), '
                    'Excel (продвинутый, Power Query), Power BI, Tableau (базово), '
                    '1С, SAP, статистический анализ данных, финансовое моделирование.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'Финансовый университет при Правительстве РФ, Экономика (2021).\n\n'
                    'ДОПОЛНИТЕЛЬНО:\n'
                    'Сертификат Python for Data Science (Coursera, 2022). '
                    'Изучаю machine learning с использованием scikit-learn. '
                    'Интересует переход в Data Science с сохранением финансовой экспертизы.'
                ),
            ),
            dict(
                vac_i=4, last_name='Захарова', first_name='Юлия',
                email='zakharova@mail.ru', stage='new', rating=3,
                cover_letter=(
                    'Здравствуйте! Я опытный B2B sales manager с хорошим знанием Bitrix24 и AmoCRM. '
                    'Выполняю и перевыполняю план. Очень хочу работать с вашим продуктом.'
                ),
                resume_text=(
                    'Захарова Юлия Михайловна. Sales Manager B2B. Опыт 3 года.\n\n'
                    'ОПЫТ РАБОТЫ:\n'
                    'ООО "СофтСейлз" (2021-2024), Менеджер по продажам B2B.\n'
                    'Активный поиск и привлечение корпоративных клиентов для SaaS-продукта.\n'
                    'Выполнение и перевыполнение плана продаж (110-130 процентов ежеквартально).\n'
                    'Ведение клиентской базы в CRM Bitrix24: воронка продаж, задачи, сделки.\n'
                    'Холодные звонки, проведение онлайн-демо продукта, переговоры с клиентами.\n'
                    'Работа с возражениями, закрытие сделок, подписание договоров.\n'
                    'Сопровождение клиентов после продажи, up-sell и cross-sell.\n'
                    'Ранее работала с AmoCRM в стартапе на аналогичной позиции.\n\n'
                    'НАВЫКИ:\n'
                    'B2B продажи (3 года), CRM (Bitrix24, AmoCRM), холодные звонки, '
                    'переговоры, работа с возражениями, презентации, оффер-менеджмент, '
                    'выполнение KPI, MS Office, Zoom и Teams для онлайн-переговоров.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'РУДН, Менеджмент, бакалавриат (2021).\n\n'
                    'ДОСТИЖЕНИЯ:\n'
                    'Лучший менеджер по продажам третий квартал 2023 года. '
                    'Закрыла крупнейшую сделку года на сумму 3.2 млн рублей в 2023 году.'
                ),
            ),
            dict(
                vac_i=4, last_name='Соловьёв', first_name='Максим',
                email='soloviev@mail.ru', stage='rejected', rating=2,
                cover_letter=(
                    'Добрый день! Я студент 3 курса и хочу попробовать себя в продажах. '
                    'Нет опыта, но готов учиться.'
                ),
                resume_text=(
                    'Соловьёв Максим Евгеньевич. Студент, ищу первую работу в продажах.\n\n'
                    'ОБРАЗОВАНИЕ:\n'
                    'РЭУ им. Плеханова, Маркетинг, 3 курс, очная форма обучения.\n\n'
                    'ОПЫТ:\n'
                    'Коммерческого опыта в продажах нет.\n'
                    'Подрабатывал промоутером в торговом центре две недели в 2023 году.\n'
                    'Участвовал в студенческой олимпиаде по маркетингу, занял третье место.\n\n'
                    'НАВЫКИ:\n'
                    'MS Office (Word, Excel базово), интернет, социальные сети.\n'
                    'Теорию продаж изучил по книгам Чалдини и Карнеги.\n\n'
                    'ЦЕЛИ:\n'
                    'Ищу первую работу в продажах или маркетинге. '
                    'Готов работать за небольшую зарплату на начальном этапе. '
                    'Есть желание обучаться и развиваться в профессии.'
                ),
            ),
        ]
        # Emails for which we'll generate PDF resumes
        PDF_EMAILS = {'smirnov@mail.ru', 'popova@mail.ru', 'orlova@mail.ru', 'zakharova@mail.ru'}

        count = 0
        created_objs = []
        for d in candidates_data:
            vac_i = d.pop('vac_i')
            if vac_i < len(vacancies):
                obj, created = Candidate.objects.get_or_create(
                    email=d['email'], vacancy=vacancies[vac_i],
                    defaults={
                        'last_name': d['last_name'], 'first_name': d['first_name'],
                        'stage': d['stage'], 'rating': d['rating'],
                        'resume_text': d['resume_text'],
                        'cover_letter': d.get('cover_letter', ''),
                    },
                )
                if not created:
                    obj.resume_text = d['resume_text']
                    obj.cover_letter = d.get('cover_letter', '')
                    obj.save(update_fields=['resume_text', 'cover_letter'])
                created_objs.append((obj, d))
                count += 1

        # Generate PDFs for selected candidates
        pdf_count = self._generate_resume_pdfs(created_objs, PDF_EMAILS)
        self.stdout.write(f'  Кандидатов: {count} (PDF резюме: {pdf_count})')

    def _generate_resume_pdfs(self, candidate_objs, target_emails):
        import io
        from pathlib import Path
        from django.conf import settings
        from django.core.files.base import ContentFile

        try:
            from reportlab.lib.pagesizes import A4
            from reportlab.lib.styles import getSampleStyleSheet, ParagraphStyle
            from reportlab.lib.units import cm
            from reportlab.lib import colors
            from reportlab.platypus import (
                SimpleDocTemplate, Paragraph, Spacer, HRFlowable, Table, TableStyle,
            )
            from reportlab.pdfbase import pdfmetrics
            from reportlab.pdfbase.ttfonts import TTFont
        except ImportError:
            self.stdout.write('  reportlab не установлен — PDF не созданы')
            return 0

        # Try to register a font that supports Cyrillic
        # reportlab ships with Helvetica (Latin only); use a system font fallback
        CYRILLIC_FONT = 'Helvetica'
        try:
            import os
            font_candidates = [
                r'C:\Windows\Fonts\arial.ttf',
                r'C:\Windows\Fonts\times.ttf',
                '/usr/share/fonts/truetype/dejavu/DejaVuSans.ttf',
                '/usr/share/fonts/truetype/liberation/LiberationSans-Regular.ttf',
            ]
            for fp in font_candidates:
                if os.path.exists(fp):
                    fname = os.path.basename(fp).split('.')[0]
                    pdfmetrics.registerFont(TTFont(fname, fp))
                    CYRILLIC_FONT = fname
                    break
        except Exception:
            pass

        def _make_styles():
            styles = getSampleStyleSheet()
            normal_font = CYRILLIC_FONT
            name_style = ParagraphStyle(
                'Name', fontName=normal_font, fontSize=18, leading=22,
                textColor=colors.HexColor('#1e293b'), spaceAfter=4,
            )
            title_style = ParagraphStyle(
                'Title', fontName=normal_font, fontSize=12, leading=16,
                textColor=colors.HexColor('#6366f1'), spaceAfter=2,
            )
            section_style = ParagraphStyle(
                'Section', fontName=normal_font, fontSize=11, leading=14,
                textColor=colors.HexColor('#1e293b'), spaceBefore=10, spaceAfter=4,
                borderPad=2,
            )
            body_style = ParagraphStyle(
                'Body', fontName=normal_font, fontSize=10, leading=14,
                textColor=colors.HexColor('#334155'), spaceAfter=2,
            )
            bullet_style = ParagraphStyle(
                'Bullet', fontName=normal_font, fontSize=10, leading=13,
                textColor=colors.HexColor('#475569'), leftIndent=12, spaceAfter=1,
                bulletIndent=4,
            )
            return name_style, title_style, section_style, body_style, bullet_style

        def _build_pdf(cand, resume_text):
            buf = io.BytesIO()
            doc = SimpleDocTemplate(
                buf, pagesize=A4,
                leftMargin=2*cm, rightMargin=2*cm,
                topMargin=2*cm, bottomMargin=2*cm,
            )
            name_style, title_style, section_style, body_style, bullet_style = _make_styles()
            story = []
            fn = CYRILLIC_FONT

            # Header — name block
            full_name = f'{cand.last_name} {cand.first_name}'
            story.append(Paragraph(full_name, name_style))

            # Parse resume_text sections
            lines = resume_text.strip().split('\n')
            # Second line is usually the job title
            if len(lines) > 0:
                story.append(Paragraph(lines[0].split('.', 1)[-1].strip() if '.' in lines[0] else '', title_style))

            # Contact line
            story.append(Paragraph(f'Email: {cand.email}', body_style))
            story.append(Spacer(1, 6))
            story.append(HRFlowable(width='100%', thickness=1.5, color=colors.HexColor('#6366f1')))
            story.append(Spacer(1, 8))

            # Parse sections from resume_text
            current_section = None
            section_items = []

            def flush_section():
                nonlocal current_section, section_items
                if current_section and section_items:
                    story.append(Paragraph(current_section, section_style))
                    story.append(HRFlowable(width='100%', thickness=0.5, color=colors.HexColor('#e2e8f0')))
                    story.append(Spacer(1, 4))
                    for item in section_items:
                        item = item.strip()
                        if not item:
                            continue
                        if item.startswith('•') or item.startswith('-'):
                            story.append(Paragraph(f'• {item.lstrip("•-").strip()}', bullet_style))
                        else:
                            story.append(Paragraph(item, body_style))
                    story.append(Spacer(1, 6))
                current_section = None
                section_items = []

            section_keywords = ('ОПЫТ', 'НАВЫКИ', 'ОБРАЗОВАНИЕ', 'ДОПОЛНИТЕЛЬНО', 'ЦЕЛИ', 'ДОСТИЖЕНИЯ', 'УЧЕБНЫЕ')

            for line in lines[1:]:
                stripped = line.strip()
                if not stripped:
                    continue
                upper = stripped.upper()
                is_section = any(upper.startswith(kw) for kw in section_keywords)
                if is_section:
                    flush_section()
                    current_section = stripped.rstrip(':')
                else:
                    if current_section is not None:
                        section_items.append(stripped)

            flush_section()

            doc.build(story)
            buf.seek(0)
            return buf.read()

        media_resumes = Path(settings.MEDIA_ROOT) / 'resumes'
        media_resumes.mkdir(parents=True, exist_ok=True)

        count = 0
        for obj, d in candidate_objs:
            if obj.email not in target_emails:
                continue
            # Skip if file already exists and is non-empty
            if obj.resume and obj.resume.name:
                try:
                    if obj.resume.size > 0:
                        count += 1
                        continue
                except Exception:
                    pass
            try:
                pdf_bytes = _build_pdf(obj, d['resume_text'])
                fname = f'resume_{obj.last_name.lower()}_{obj.first_name.lower()}.pdf'
                obj.resume.save(fname, ContentFile(pdf_bytes), save=True)
                count += 1
            except Exception as e:
                self.stdout.write(f'  PDF error for {obj.email}: {e}')
        return count

    def _create_public_vacancies(self, vacancies):
        from datetime import date
        from recruitment.models import VacancyQuestion, Candidate, CandidateAnswer

        # Make first two vacancies public with questions
        public_configs = [
            {
                'vac_i': 0,
                'application_deadline': date(2026, 8, 31),
                'questions': [
                    {'question_text': 'Какой у вас суммарный опыт работы с Python (лет)?', 'question_type': 'single',
                     'options': ['Менее 1 года', '1–2 года', '3–4 года', '5+ лет'], 'is_required': True, 'order': 1},
                    {'question_text': 'Какими фреймворками вы владеете?', 'question_type': 'multiple',
                     'options': ['Django', 'FastAPI', 'Flask', 'aiohttp', 'Другое'], 'is_required': True, 'order': 2},
                    {'question_text': 'Опишите ваш самый сложный технический проект за последний год.', 'question_type': 'text',
                     'options': [], 'is_required': False, 'order': 3},
                ],
                'candidates': [
                    dict(last_name='Тарасов', first_name='Евгений', email='tarasov.public@mail.ru',
                         stage='new', rating=4,
                         cover_letter='Откликаюсь через публичную форму. Python-разработчик с 4-летним опытом в Django и FastAPI.',
                         resume_text=(
                             'Тарасов Евгений Петрович. Backend Python Developer. Опыт 4 года.\n\n'
                             'ОПЫТ:\nООО "ИнтегроТех" (2020-2024), Python Developer.\n'
                             'Разработка REST API на Django и FastAPI для B2B SaaS-платформы.\n'
                             'Оптимизация PostgreSQL-запросов, кеширование Redis.\n'
                             'Контейнеризация Docker, деплой через GitLab CI/CD.\n\n'
                             'НАВЫКИ: Python, Django, FastAPI, PostgreSQL, Redis, Docker, REST API, pytest, Git.\n\n'
                             'ОБРАЗОВАНИЕ: МГТУ им. Баумана, Информатика и системы управления (2020).'
                         ),
                         answers={1: '3–4 года', 2: 'Django, FastAPI', 3: 'Разрабатывал систему интеграции с внешними ERP через REST API с очередями Celery.'}),
                    dict(last_name='Белова', first_name='Анастасия', email='belova.public@mail.ru',
                         stage='screening', rating=3,
                         cover_letter='Нашла вашу вакансию на сайте. Опыт Python 2 года, хочу расти.',
                         resume_text=(
                             'Белова Анастасия Игоревна. Junior/Middle Python Developer. Опыт 2 года.\n\n'
                             'ОПЫТ:\nООО "ВебДев" (2022-2024), Python Backend Developer.\n'
                             'Работала с Django REST Framework, PostgreSQL, Docker.\n'
                             'Писала автоматизированные тесты pytest, поддерживала CI/CD пайплайн.\n\n'
                             'НАВЫКИ: Python, Django, REST API, PostgreSQL, Docker, Git, pytest.\n\n'
                             'ОБРАЗОВАНИЕ: СПбГУ, Прикладная математика (2022).'
                         ),
                         answers={1: '1–2 года', 2: 'Django', 3: ''}),
                ],
            },
            {
                'vac_i': 1,
                'application_deadline': date(2026, 7, 31),
                'questions': [
                    {'question_text': 'Ваш опыт работы с Vue.js (лет)?', 'question_type': 'single',
                     'options': ['Менее 1 года', '1–2 года', '3–4 года', '5+ лет'], 'is_required': True, 'order': 1},
                    {'question_text': 'Вы использовали TypeScript в коммерческих проектах?', 'question_type': 'single',
                     'options': ['Да, активно', 'Да, иногда', 'Нет'], 'is_required': True, 'order': 2},
                    {'question_text': 'Ссылка на GitHub или портфолио (необязательно):', 'question_type': 'text',
                     'options': [], 'is_required': False, 'order': 3},
                ],
                'candidates': [
                    dict(last_name='Григорьев', first_name='Кирилл', email='grigoriev.public@mail.ru',
                         stage='interview', rating=4,
                         cover_letter='Откликаюсь на вакансию Vue.js Frontend Developer. Опыт Vue.js 3 года с TypeScript.',
                         resume_text=(
                             'Григорьев Кирилл Алексеевич. Frontend Developer (Vue.js). Опыт 3 года.\n\n'
                             'ОПЫТ:\nООО "ФронтЛаб" (2021-2024), Frontend Developer.\n'
                             'Разработка SPA на Vue.js 3, Composition API, Pinia, TypeScript.\n'
                             'Интеграция с REST API, настройка Vite, работа с CSS/SCSS.\n'
                             'Code review, участие в планировании спринтов.\n\n'
                             'НАВЫКИ: Vue.js 3, TypeScript, Pinia, Vite, HTML5, CSS3, REST API, Git.\n\n'
                             'ОБРАЗОВАНИЕ: ИТМО, Программная инженерия (2021).'
                         ),
                         answers={1: '3–4 года', 2: 'Да, активно', 3: 'https://github.com/kgrigoriev'}),
                ],
            },
        ]

        q_created = 0
        c_created = 0
        for cfg in public_configs:
            vac_i = cfg['vac_i']
            if vac_i >= len(vacancies):
                continue
            vac = vacancies[vac_i]
            vac.is_public = True
            vac.application_deadline = cfg['application_deadline']
            vac.save(update_fields=['is_public', 'application_deadline'])

            # Create questions (map local order → DB id)
            order_to_question = {}
            for qdata in cfg['questions']:
                order = qdata['order']
                q, _ = VacancyQuestion.objects.get_or_create(
                    vacancy=vac,
                    question_text=qdata['question_text'],
                    defaults={k: v for k, v in qdata.items() if k != 'question_text'},
                )
                order_to_question[order] = q
                q_created += 1

            # Create public candidates with answers
            for cdata in cfg['candidates']:
                answers = cdata.pop('answers', {})
                obj, created_now = Candidate.objects.get_or_create(
                    email=cdata['email'], vacancy=vac,
                    defaults={
                        'last_name': cdata['last_name'], 'first_name': cdata['first_name'],
                        'stage': cdata['stage'], 'rating': cdata['rating'],
                        'resume_text': cdata['resume_text'],
                        'cover_letter': cdata.get('cover_letter', ''),
                        'source': 'public',
                    },
                )
                if not created_now:
                    obj.source = 'public'
                    obj.resume_text = cdata['resume_text']
                    obj.cover_letter = cdata.get('cover_letter', '')
                    obj.save(update_fields=['source', 'resume_text', 'cover_letter'])
                for order, answer_val in answers.items():
                    q = order_to_question.get(order)
                    if q:
                        CandidateAnswer.objects.get_or_create(
                            candidate=obj, question=q,
                            defaults={'answer_text': answer_val},
                        )
                c_created += 1

        self.stdout.write(f'  Публичных вакансий: 2, вопросов: {q_created}, публичных кандидатов: {c_created}')

    def _create_training_data(self, employees):
        import uuid
        from datetime import date
        from django.utils import timezone
        from training.models import Course, CourseAssignment, Certificate

        # ── Lesson content ────────────────────────────────────────────────
        LESSONS = {
            0: [  # Основы информационной безопасности
                {'id': 1, 'order': 1, 'title': 'Угрозы информационной безопасности',
                 'content': (
                     'Информационная безопасность (ИБ) — защита информации от несанкционированного доступа, '
                     'утечки и разрушения. Каждый сотрудник является первой линией защиты компании.\n\n'
                     'Основные типы угроз:\n'
                     '• Фишинг — поддельные письма и сайты для кражи учётных данных. Признаки: срочный тон, '
                     'подозрительный адрес отправителя, ссылки с опечатками в домене.\n'
                     '• Вредоносное ПО — вирусы, трояны, программы-вымогатели (ransomware). Проникают '
                     'через вложения в письмах, заражённые сайты и USB-носители.\n'
                     '• Социальная инженерия — манипуляции с людьми: звонки от «IT-поддержки» или '
                     '«руководства» с просьбой назвать пароль или установить программу.\n'
                     '• Инсайдерские угрозы — намеренные или случайные действия собственных сотрудников.\n\n'
                     'Золотое правило: если что-то кажется подозрительным — это подозрительно. '
                     'Всегда проверяйте подлинность запроса через официальные каналы. '
                     'При обнаружении угрозы немедленно сообщите в IT-отдел.'
                 ),
                 'questions': [
                     {'question': 'Что такое фишинг?',
                      'options': ['Антивирусная программа для защиты ПК',
                                  'Поддельные письма и сайты для кражи учётных данных',
                                  'Метод шифрования корпоративных данных'],
                      'correct': 1,
                      'explanation': 'Фишинг — создание поддельных писем и сайтов для обмана пользователей '
                                     'и кражи их учётных данных или паролей.'},
                     {'question': 'Что такое социальная инженерия в контексте ИБ?',
                      'options': ['Разработка корпоративных социальных сетей',
                                  'Психологические манипуляции с людьми для получения конфиденциальных данных',
                                  'Вид вредоносного программного обеспечения'],
                      'correct': 1,
                      'explanation': 'Социальная инженерия — манипуляции с людьми, например звонки '
                                     'от «IT-поддержки» с просьбой назвать пароль или установить программу.'},
                 ]},
                {'id': 2, 'order': 2, 'title': 'Защита данных и управление паролями',
                 'content': (
                     'Пароль — ваш главный ключ к корпоративным системам. Слабый пароль открывает '
                     'дверь злоумышленникам за секунды.\n\n'
                     'Правила надёжного пароля:\n'
                     '• Длина не менее 12 символов\n'
                     '• Комбинация букв (верхний и нижний регистр), цифр и специальных символов\n'
                     '• Уникальный для каждого сервиса — один пароль для всего недопустим\n'
                     '• Не используйте личные данные: имя, дату рождения, название компании\n\n'
                     'Менеджер паролей (KeePass, Bitwarden) хранит и генерирует сложные пароли — '
                     'вам нужно помнить только один мастер-пароль.\n\n'
                     'Двухфакторная аутентификация (2FA) добавляет второй уровень защиты: '
                     'код из SMS или приложения-аутентификатора. Включите 2FA на всех корпоративных сервисах.\n\n'
                     'Никогда не передавайте пароли: ни коллегам, ни IT-специалистам, ни руководству. '
                     'Легитимные системы никогда не запрашивают ваш пароль.'
                 ),
                 'questions': [
                     {'question': 'Какова минимальная рекомендуемая длина надёжного пароля?',
                      'options': ['6 символов', '8 символов', '12 символов'],
                      'correct': 2,
                      'explanation': 'Минимальная длина надёжного пароля — 12 символов. '
                                     'Более короткие пароли подбираются перебором за секунды.'},
                     {'question': 'Можно ли передать корпоративный пароль IT-специалисту по его запросу?',
                      'options': ['Да, если он представился из IT-отдела',
                                  'Да, но только через зашифрованный мессенджер',
                                  'Нет — легитимные системы никогда не запрашивают пароль'],
                      'correct': 2,
                      'explanation': 'Никогда не передавайте пароли — ни коллегам, ни IT-специалистам, '
                                     'ни руководству. Это основное правило безопасности.'},
                 ]},
                {'id': 3, 'order': 3, 'title': 'Безопасность рабочего места',
                 'content': (
                     'Физическая безопасность так же важна, как и цифровая. '
                     'Незащищённое рабочее место — возможность для утечки данных.\n\n'
                     'Правила рабочего места:\n'
                     '• Блокируйте компьютер при уходе: Win+L на Windows, Ctrl+Cmd+Q на Mac\n'
                     '• Политика чистого стола: конфиденциальные документы убирайте в ящик\n'
                     '• Не оставляйте ноутбук без присмотра в общественных местах\n'
                     '• Используйте корпоративный VPN при работе вне офиса\n'
                     '• Не подключайте неизвестные USB-устройства\n\n'
                     'Шифрование диска (BitLocker/FileVault) защищает данные при краже ноутбука. '
                     'Убедитесь, что шифрование включено на вашем рабочем устройстве.\n\n'
                     'Корпоративные данные должны храниться только в корпоративных системах. '
                     'Не копируйте рабочие файлы в личные облачные хранилища (Google Drive, Dropbox).\n\n'
                     'Экран блокировки с паролем — обязателен даже на рабочем телефоне.'
                 ),
                 'questions': [
                     {'question': 'Какая комбинация клавиш мгновенно блокирует экран на Windows?',
                      'options': ['Ctrl+Alt+Del', 'Win+L', 'Alt+F4'],
                      'correct': 1,
                      'explanation': 'Win+L мгновенно блокирует экран на Windows. '
                                     'Ctrl+Alt+Del открывает меню, Alt+F4 закрывает текущую программу.'},
                     {'question': 'Где разрешено хранить корпоративные рабочие файлы?',
                      'options': ['В любом облачном хранилище (Google Drive, Dropbox)',
                                  'Только в корпоративных системах',
                                  'На личном USB-накопителе для удобства'],
                      'correct': 1,
                      'explanation': 'Корпоративные данные должны храниться только в корпоративных системах. '
                                     'Личные облачные хранилища не контролируются службой безопасности.'},
                 ]},
                {'id': 4, 'order': 4, 'title': 'Инциденты ИБ: обнаружение и реагирование',
                 'content': (
                     'Инцидент ИБ — любое событие, реально или потенциально нарушающее '
                     'конфиденциальность, целостность или доступность информации.\n\n'
                     'Примеры инцидентов:\n'
                     '• Вы открыли подозрительное вложение или перешли по фишинговой ссылке\n'
                     '• Компьютер ведёт себя необычно: замедлился, появились незнакомые программы\n'
                     '• Вы получили запрос на передачу конфиденциальных данных\n'
                     '• Потеря или кража устройства с корпоративными данными\n\n'
                     'Алгоритм действий при инциденте:\n'
                     '1. Не паникуйте и не пытайтесь решить проблему самостоятельно\n'
                     '2. Отключите компьютер от сети (выньте кабель или отключите Wi-Fi)\n'
                     '3. Немедленно сообщите в IT-отдел или службу ИБ\n'
                     '4. Зафиксируйте детали: что произошло, когда, какие данные были доступны\n'
                     '5. Не обсуждайте инцидент с коллегами до официального уведомления\n\n'
                     'Своевременное сообщение об инциденте — ваша обязанность, а не признание ошибки. '
                     'Каждая минута промедления увеличивает потенциальный ущерб для компании.'
                 ),
                 'questions': [
                     {'question': 'Что нужно сделать в первую очередь при инциденте ИБ?',
                      'options': ['Самостоятельно попытаться устранить проблему',
                                  'Рассказать коллегам, чтобы они были в курсе',
                                  'Отключить компьютер от сети и немедленно сообщить в IT-отдел'],
                      'correct': 2,
                      'explanation': 'Первые действия: отключить компьютер от сети, чтобы остановить '
                                     'распространение угрозы, и немедленно уведомить IT-отдел или службу ИБ.'},
                 ]},
            ],
            1: [  # Эффективные коммуникации
                {'id': 1, 'order': 1, 'title': 'Принципы эффективной коммуникации',
                 'content': (
                     'Коммуникация — это не просто передача слов. Эффективная коммуникация означает, '
                     'что получатель понял ваше сообщение именно так, как вы задумали.\n\n'
                     'Четыре основных принципа:\n'
                     '• Ясность — формулируйте мысли конкретно, избегайте двусмысленности и жаргона\n'
                     '• Краткость — уважайте время собеседника, сразу переходите к сути\n'
                     '• Активное слушание — не просто слышать слова, а понимать смысл и эмоции\n'
                     '• Обратная связь — убедитесь, что вас поняли правильно\n\n'
                     'Активное слушание на практике:\n'
                     '• Смотрите на собеседника, не отвлекайтесь на телефон\n'
                     '• Не перебивайте, дождитесь паузы\n'
                     '• Перефразируйте: «Правильно ли я понял, что...»\n'
                     '• Задавайте уточняющие вопросы\n\n'
                     'Важно: 55% общения — язык тела, 38% — тон голоса, только 7% — слова. '
                     'Следите за невербальными сигналами: открытая поза, зрительный контакт '
                     'и умеренная жестикуляция усиливают доверие к вашим словам.'
                 ),
                 'questions': [
                     {'question': 'Какой процент в общении составляет язык тела?',
                      'options': ['7%', '38%', '55%'],
                      'correct': 2,
                      'explanation': 'По исследованиям Мерабяна: 55% общения — язык тела, '
                                     '38% — тон голоса, и лишь 7% — сами слова.'},
                     {'question': 'Что включает в себя активное слушание?',
                      'options': ['Быстро давать советы, не дожидаясь конца рассказа',
                                  'Перефразировать сказанное и задавать уточняющие вопросы',
                                  'Слышать слова, обдумывая свой ответ параллельно'],
                      'correct': 1,
                      'explanation': 'Активное слушание — это понимание смысла и эмоций, '
                                     'перефразирование («Правильно ли я понял...») и уточняющие вопросы.'},
                 ]},
                {'id': 2, 'order': 2, 'title': 'Деловая переписка и email-этикет',
                 'content': (
                     'Email остаётся основным инструментом деловой коммуникации. '
                     'Грамотное письмо создаёт профессиональный образ и экономит время.\n\n'
                     'Структура делового письма:\n'
                     '• Тема — конкретная и информативная: «Согласование бюджета Q2 — дедлайн 15.05» '
                     'вместо просто «Вопрос»\n'
                     '• Приветствие — «Здравствуйте, Имя» для коллег\n'
                     '• Суть с первого предложения — не заставляйте читать три абзаца до главного\n'
                     '• Конкретный призыв к действию — что нужно сделать и к какому сроку\n'
                     '• Подпись с контактами\n\n'
                     'Правила email-этикета:\n'
                     '• Отвечайте в течение 24 часов в рабочие дни\n'
                     '• Используйте «Ответить всем» только когда это нужно всем адресатам\n'
                     '• Не пишите ЗАГЛАВНЫМИ — это воспринимается как крик\n'
                     '• Прочитайте письмо перед отправкой: тон, опечатки, правильность адресата\n'
                     '• Конфиденциальную информацию не отправляйте на личные почты\n\n'
                     'В мессенджерах (Slack, Teams) допустим более неформальный тон, '
                     'но уважение к времени коллег остаётся обязательным.'
                 ),
                 'questions': [
                     {'question': 'В какой срок принято отвечать на деловые письма?',
                      'options': ['В течение 1 часа',
                                  'В течение 24 часов в рабочие дни',
                                  'В течение 3 рабочих дней'],
                      'correct': 1,
                      'explanation': 'Деловой этикет предполагает ответ на письмо в течение 24 часов '
                                     'в рабочие дни. Это уважение к времени отправителя.'},
                     {'question': 'Что категорически не рекомендуется делать в деловых письмах?',
                      'options': ['Указывать конкретный дедлайн для ответа',
                                  'Писать ЗАГЛАВНЫМИ БУКВАМИ',
                                  'Формулировать суть в начале письма'],
                      'correct': 1,
                      'explanation': 'ЗАГЛАВНЫЕ БУКВЫ воспринимаются как крик и нарушают деловой этикет. '
                                     'Пишите обычным регистром для сохранения профессионального тона.'},
                 ]},
                {'id': 3, 'order': 3, 'title': 'Проведение встреч и презентаций',
                 'content': (
                     'Неэффективные встречи — главный похититель рабочего времени. '
                     'Хорошо организованная встреча завершается с чёткими итогами и следующими шагами.\n\n'
                     'До встречи:\n'
                     '• Определите цель: какое решение нужно принять\n'
                     '• Составьте повестку и отправьте участникам заранее\n'
                     '• Пригласите только тех, кто действительно нужен\n'
                     '• Установите временные рамки для каждого пункта\n\n'
                     'Во время встречи:\n'
                     '• Начинайте вовремя, не ждите опаздывающих\n'
                     '• Ведите протокол: решения, ответственные, сроки\n'
                     '• Управляйте дискуссией: возвращайте к теме при отклонениях\n'
                     '• Завершайте чётким резюме следующих шагов\n\n'
                     'Структура презентации (принцип «пирамиды Минто»):\n'
                     '• Главный вывод — сразу, в первых слайдах\n'
                     '• Аргументы и данные — в поддержку вывода\n'
                     '• Детали — в приложении для заинтересованных\n\n'
                     'Правило 10-20-30: не более 10 слайдов, 20 минут, шрифт не меньше 30pt.'
                 ),
                 'questions': [
                     {'question': 'Что означает правило 10-20-30 для презентаций?',
                      'options': ['10 участников, 20 слайдов, 30 минут',
                                  'Не более 10 слайдов, 20 минут, шрифт не менее 30pt',
                                  '10 задач, 20 минут обсуждения, 30 слайдов'],
                      'correct': 1,
                      'explanation': 'Правило 10-20-30 от Гая Кавасаки: не более 10 слайдов, '
                                     'не более 20 минут выступления, шрифт не менее 30pt.'},
                     {'question': 'Когда следует начинать встречу?',
                      'options': ['Подождать 5-10 минут, пока все соберутся',
                                  'Начинать вовремя, не ждать опаздывающих',
                                  'Начинать только после того, как все участники присутствуют'],
                      'correct': 1,
                      'explanation': 'Начинайте вовремя — это уважение к тем, кто пришёл пунктуально, '
                                     'и мотивация для остальных не опаздывать.'},
                 ]},
                {'id': 4, 'order': 4, 'title': 'Конструктивная обратная связь',
                 'content': (
                     'Обратная связь — инструмент развития, а не критики. '
                     'Правильная обратная связь мотивирует и направляет, неправильная — демотивирует.\n\n'
                     'Модель SBI (Ситуация — Поведение — Влияние):\n'
                     '• Ситуация: «На вчерашней встрече с клиентом...»\n'
                     '• Поведение: «...ты трижды перебил его во время презентации...»\n'
                     '• Влияние: «...клиент стал менее открытым, и мы не закрыли сделку»\n\n'
                     'Правила обратной связи:\n'
                     '• О поведении, не о личности: «ты опоздал» vs «ты безответственный»\n'
                     '• Конкретность: избегайте «всегда», «никогда», «постоянно»\n'
                     '• Своевременность: давайте обратную связь как можно скорее\n'
                     '• Приватно для критики, публично для похвалы\n\n'
                     'Как принимать обратную связь:\n'
                     '• Слушайте без защитной реакции и оправданий\n'
                     '• Задавайте уточняющие вопросы: «Что именно я мог сделать иначе?»\n'
                     '• Поблагодарите за обратную связь, даже если она неприятна\n'
                     '• Дайте себе время обдумать, прежде чем реагировать'
                 ),
                 'questions': [
                     {'question': 'Что означает аббревиатура SBI в модели обратной связи?',
                      'options': ['Стандарт — Бюджет — Инвестиции',
                                  'Ситуация — Поведение — Влияние',
                                  'Система — Бизнес — Интеграция'],
                      'correct': 1,
                      'explanation': 'SBI: Ситуация (контекст события), Поведение (конкретные действия), '
                                     'Влияние (последствия для команды или результата).'},
                     {'question': 'Как правильно давать критическую обратную связь?',
                      'options': ['Публично, чтобы все коллеги слышали и учились',
                                  'Приватно, фокусируясь на поведении, а не на личности',
                                  'В момент инцидента при всех присутствующих'],
                      'correct': 1,
                      'explanation': 'Критика — только приватно и о поведении («ты опоздал»), '
                                     'а не о личности («ты безответственный»). Похвала — публично.'},
                 ]},
                {'id': 5, 'order': 5, 'title': 'Управление конфликтами',
                 'content': (
                     'Конфликт — нормальная часть рабочей жизни. Важно не избегать конфликта, '
                     'а управлять им конструктивно.\n\n'
                     'Типы конфликтов:\n'
                     '• Конфликт интересов — разные цели или приоритеты\n'
                     '• Информационный конфликт — разное понимание фактов\n'
                     '• Межличностный конфликт — разные стили работы и ценности\n\n'
                     'Техника разрешения (метод Гарвардских переговоров):\n'
                     '1. Разделите людей и проблему — вы работаете против проблемы, не против человека\n'
                     '2. Сфокусируйтесь на интересах, а не позициях — «зачем вам это нужно?»\n'
                     '3. Генерируйте варианты — ищите решения, выгодные обеим сторонам\n'
                     '4. Используйте объективные критерии — данные, стандарты, прецеденты\n\n'
                     'I-сообщения вместо ты-обвинений:\n'
                     '«Я чувствую стресс, когда дедлайны меняются без предупреждения» — '
                     'вместо «Ты всегда всё меняешь в последний момент»\n\n'
                     'Обращайтесь к руководителю, если конфликт влияет на работу команды '
                     'или переходит в личные нападки.'
                 ),
                 'questions': [
                     {'question': 'В чём суть метода Гарвардских переговоров?',
                      'options': ['Давить на оппонента для получения максимальных уступок',
                                  'Фокусироваться на интересах сторон, а не на их позициях',
                                  'Избегать конфликта любой ценой'],
                      'correct': 1,
                      'explanation': 'Гарвардский метод: разделяйте людей и проблему, фокусируйтесь '
                                     'на интересах (зачем?), а не позициях (что?), ищите взаимовыгодные решения.'},
                     {'question': 'Что такое «I-сообщение» в управлении конфликтами?',
                      'options': ['Официальная жалоба руководству в письменной форме',
                                  'Выражение своих чувств и потребностей без обвинений в адрес другого',
                                  'Перечисление ошибок коллеги от первого лица'],
                      'correct': 1,
                      'explanation': 'I-сообщение: «Я чувствую стресс, когда...» — описывает ваши чувства '
                                     'без обвинений. Это снижает защитную реакцию собеседника.'},
                 ]},
            ],
            2: [  # Python для анализа данных
                {'id': 1, 'order': 1, 'title': 'Основы Python: структуры данных',
                 'content': (
                     'Python — наиболее популярный язык для анализа данных благодаря '
                     'читаемому синтаксису и богатой экосистеме библиотек.\n\n'
                     'Ключевые структуры данных:\n'
                     '• Список (list): [1, 2, 3] — упорядоченная изменяемая коллекция\n'
                     '• Словарь (dict): {"name": "Иван", "age": 30} — пары ключ-значение\n'
                     '• Кортеж (tuple): (1, 2, 3) — неизменяемая последовательность\n'
                     '• Множество (set): {1, 2, 3} — уникальные элементы без порядка\n\n'
                     'Управляющие конструкции:\n'
                     'Цикл for: for emp in employees: print(emp["name"])\n'
                     'Включение списка: salaries = [e["salary"] for e in employees if e["active"]]\n'
                     'Функция: def avg_salary(data): return sum(d["salary"] for d in data) / len(data)\n\n'
                     'Работа с файлами:\n'
                     'import csv\n'
                     'with open("data.csv") as f:\n'
                     '    reader = csv.DictReader(f)\n'
                     '    rows = list(reader)\n\n'
                     'Установка библиотек: pip install pandas matplotlib scikit-learn'
                 ),
                 'questions': [
                     {'question': 'Какая структура данных Python хранит пары ключ-значение?',
                      'options': ['Список (list)', 'Словарь (dict)', 'Кортеж (tuple)'],
                      'correct': 1,
                      'explanation': 'Словарь (dict) хранит пары ключ-значение: {"name": "Иван", "age": 30}. '
                                     'Это основная структура для работы с именованными данными.'},
                     {'question': 'Что создаёт выражение [e["salary"] for e in employees if e["active"]]?',
                      'options': ['Удаляет неактивных сотрудников из исходного списка',
                                  'Новый список зарплат только активных сотрудников',
                                  'Считает среднюю зарплату активных сотрудников'],
                      'correct': 1,
                      'explanation': 'Включение списка (list comprehension) создаёт новый список, '
                                     'применяя выражение к каждому элементу с условием фильтрации.'},
                 ]},
                {'id': 2, 'order': 2, 'title': 'pandas: загрузка и обработка данных',
                 'content': (
                     'pandas — основная библиотека для работы с табличными данными в Python. '
                     'DataFrame — это таблица с именованными столбцами и индексом строк.\n\n'
                     'Загрузка данных:\n'
                     'import pandas as pd\n'
                     'df = pd.read_csv("employees.csv")\n'
                     'df = pd.read_excel("report.xlsx")\n\n'
                     'Основные операции:\n'
                     '• Просмотр: df.head(), df.info(), df.describe()\n'
                     '• Фильтрация: df[df["department"] == "Разработка"]\n'
                     '• Выбор столбцов: df[["name", "salary"]]\n'
                     '• Группировка: df.groupby("department")["salary"].mean()\n'
                     '• Сортировка: df.sort_values("salary", ascending=False)\n\n'
                     'Обработка пропусков:\n'
                     '• Найти: df.isnull().sum()\n'
                     '• Заполнить средним: df["salary"].fillna(df["salary"].mean())\n'
                     '• Удалить строки: df.dropna(subset=["salary"])\n\n'
                     'Добавление столбца:\n'
                     'df["bonus"] = df["salary"] * 0.1\n'
                     'df["risk"] = df["overtime"] > 20'
                 ),
                 'questions': [
                     {'question': 'Как правильно загрузить CSV-файл в pandas?',
                      'options': ['pd.load("data.csv")',
                                  'pd.read_csv("data.csv")',
                                  'DataFrame.open("data.csv")'],
                      'correct': 1,
                      'explanation': 'pd.read_csv() — стандартная функция pandas для загрузки '
                                     'CSV-файлов в объект DataFrame.'},
                     {'question': 'Как посчитать среднюю зарплату по каждому отделу в pandas?',
                      'options': ['df["salary"].mean()',
                                  'df.groupby("department")["salary"].mean()',
                                  'df.sort_values("department")["salary"]'],
                      'correct': 1,
                      'explanation': 'groupby() группирует строки по значению столбца, затем '
                                     'применяет агрегирующую функцию (mean, sum, count) к нужному столбцу.'},
                 ]},
                {'id': 3, 'order': 3, 'title': 'Визуализация данных с matplotlib и seaborn',
                 'content': (
                     'Визуализация — ключ к пониманию данных. Графики выявляют паттерны, '
                     'выбросы и зависимости, которые не видны в числах.\n\n'
                     'matplotlib — базовая библиотека:\n'
                     'import matplotlib.pyplot as plt\n'
                     'plt.figure(figsize=(10, 6))\n'
                     'plt.hist(df["salary"], bins=20, color="steelblue")\n'
                     'plt.xlabel("Зарплата"); plt.ylabel("Количество")\n'
                     'plt.title("Распределение зарплат")\n'
                     'plt.show()\n\n'
                     'seaborn — статистическая визуализация поверх matplotlib:\n'
                     'import seaborn as sns\n'
                     'sns.boxplot(data=df, x="department", y="salary")  # распределение по отделам\n'
                     'sns.heatmap(df.corr(), annot=True, cmap="coolwarm")  # корреляционная матрица\n'
                     'sns.scatterplot(data=df, x="overtime", y="performance", hue="department")\n\n'
                     'Выбор типа графика:\n'
                     '• Гистограмма — распределение одной переменной\n'
                     '• Ящик с усами — распределение и выбросы\n'
                     '• Точечная диаграмма — связь двух переменных\n'
                     '• Тепловая карта — корреляции нескольких переменных\n'
                     '• Столбчатая — сравнение категорий'
                 ),
                 'questions': [
                     {'question': 'Какой тип графика лучше всего подходит для отображения корреляций между переменными?',
                      'options': ['Гистограмма (histogram)',
                                  'Тепловая карта (heatmap)',
                                  'Столбчатая диаграмма (bar chart)'],
                      'correct': 1,
                      'explanation': 'Тепловая карта (sns.heatmap с df.corr()) отображает матрицу корреляций — '
                                     'связи между всеми парами переменных одновременно в цветовом формате.'},
                 ]},
                {'id': 4, 'order': 4, 'title': 'Введение в машинное обучение с scikit-learn',
                 'content': (
                     'Машинное обучение позволяет строить модели, обучающиеся на данных '
                     'и делающие предсказания без явного программирования правил.\n\n'
                     'Типы задач:\n'
                     '• Классификация — предсказать категорию (уволится / не уволится)\n'
                     '• Регрессия — предсказать число (зарплата через год)\n'
                     '• Кластеризация — разбить на группы без меток (KMeans)\n\n'
                     'Процесс ML-проекта:\n'
                     '1. Подготовка данных: заполнить пропуски, кодировать категории\n'
                     '2. Разделение: X_train, X_test, y_train, y_test = train_test_split(X, y)\n'
                     '3. Обучение: model.fit(X_train, y_train)\n'
                     '4. Оценка: accuracy_score(y_test, model.predict(X_test))\n\n'
                     'Пример — предсказание текучести:\n'
                     'from sklearn.ensemble import RandomForestClassifier\n'
                     'from sklearn.metrics import classification_report\n'
                     'model = RandomForestClassifier(n_estimators=100, random_state=42)\n'
                     'model.fit(X_train, y_train)\n'
                     'print(classification_report(y_test, model.predict(X_test)))\n\n'
                     'Важность признаков (Feature Importance) показывает, '
                     'какие факторы сильнее всего влияют на предсказание.'
                 ),
                 'questions': [
                     {'question': 'Какие задачи относятся к обучению с учителем (supervised learning)?',
                      'options': ['Только классификация',
                                  'Классификация и регрессия',
                                  'Кластеризация и визуализация'],
                      'correct': 1,
                      'explanation': 'Обучение с учителем включает классификацию (предсказание категорий) '
                                     'и регрессию (предсказание чисел). Кластеризация — обучение без учителя.'},
                     {'question': 'Что показывает Feature Importance в Random Forest?',
                      'options': ['Важность алгоритма для бизнеса',
                                  'Вклад каждого признака в точность предсказания модели',
                                  'Количество деревьев в модели'],
                      'correct': 1,
                      'explanation': 'Feature Importance показывает, насколько каждый признак (переменная) '
                                     'влияет на точность предсказания модели — какие факторы наиболее важны.'},
                 ]},
                {'id': 5, 'order': 5, 'title': 'Практический проект: анализ HR-данных',
                 'content': (
                     'В этом уроке мы пройдём полный цикл анализа данных на примере '
                     'HR-аналитики: от загрузки до выводов.\n\n'
                     'Постановка задачи: выявить факторы, влияющие на текучесть кадров.\n\n'
                     'Шаг 1 — Загрузка и исследование:\n'
                     'df = pd.read_csv("hr_data.csv")\n'
                     'print(df["attrition"].value_counts(normalize=True))  # доля уволившихся\n\n'
                     'Шаг 2 — Визуализация ключевых зависимостей:\n'
                     'sns.boxplot(data=df, x="attrition", y="overtime_hours")\n'
                     'sns.boxplot(data=df, x="attrition", y="performance_score")\n\n'
                     'Шаг 3 — Построение модели:\n'
                     'features = ["overtime_hours", "performance_score", "years_at_company",\n'
                     '            "salary", "distance_from_home"]\n'
                     'X = df[features]; y = (df["attrition"] == "Yes").astype(int)\n'
                     'model = RandomForestClassifier().fit(X_train, y_train)\n\n'
                     'Шаг 4 — Интерпретация:\n'
                     'importances = pd.Series(model.feature_importances_, index=features)\n'
                     'importances.sort_values().plot(kind="barh")\n\n'
                     'Выводы оформляются в отчёт с рекомендациями по снижению текучести кадров.'
                 ),
                 'questions': [
                     {'question': 'Каков правильный порядок шагов в аналитическом ML-проекте?',
                      'options': ['Сначала строим модель, затем смотрим на данные',
                                  'Загрузка и исследование → визуализация → модель → интерпретация',
                                  'Формируем отчёт, затем собираем данные под него'],
                      'correct': 1,
                      'explanation': 'Правильный порядок: сначала понять данные (EDA), затем визуализировать '
                                     'зависимости, построить модель и в конце интерпретировать результаты.'},
                 ]},
            ],
            3: [  # Управление проектами (Agile/Scrum)
                {'id': 1, 'order': 1, 'title': 'Agile-манифест и принципы',
                 'content': (
                     'Agile — это набор ценностей и принципов для гибкого управления проектами. '
                     'Манифест Agile был подписан в 2001 году 17 разработчиками.\n\n'
                     'Четыре ценности Agile:\n'
                     '1. Люди и взаимодействие важнее процессов и инструментов\n'
                     '2. Работающий продукт важнее исчерпывающей документации\n'
                     '3. Сотрудничество с заказчиком важнее согласования условий контракта\n'
                     '4. Готовность к изменениям важнее следования первоначальному плану\n\n'
                     'Ключевые принципы:\n'
                     '• Ранняя и непрерывная поставка работающего продукта\n'
                     '• Изменения требований приветствуются на любом этапе\n'
                     '• Рабочий продукт поставляется часто (каждые 1-4 недели)\n'
                     '• Ежедневное общение разработчиков и заказчиков\n'
                     '• Самоорганизующиеся команды создают лучшие решения\n'
                     '• Регулярная рефлексия и адаптация процессов\n\n'
                     'Agile не отменяет планирование — он делает планирование более гибким '
                     'и адаптивным к реальным изменениям.'
                 ),
                 'questions': [
                     {'question': 'Сколько ценностей содержит Agile-манифест?',
                      'options': ['3', '4', '12'],
                      'correct': 1,
                      'explanation': 'Agile-манифест содержит 4 ценности и 12 принципов, '
                                     'сформулированных 17 разработчиками в 2001 году.'},
                     {'question': 'Что важнее согласно второй ценности Agile-манифеста?',
                      'options': ['Исчерпывающая документация',
                                  'Работающий программный продукт',
                                  'Строгое следование первоначальному плану'],
                      'correct': 1,
                      'explanation': 'Вторая ценность Agile: работающий продукт важнее исчерпывающей '
                                     'документации. Agile не запрещает документацию, но не ставит её выше результата.'},
                 ]},
                {'id': 2, 'order': 2, 'title': 'Scrum: роли и артефакты',
                 'content': (
                     'Scrum — наиболее популярный Agile-фреймворк. '
                     'Основан на итеративной разработке спринтами длиной 1-4 недели.\n\n'
                     'Три роли в Scrum:\n'
                     '• Product Owner (PO) — владелец продукта. Определяет что делать и в каком '
                     'порядке. Ведёт и приоритизирует Product Backlog. Отвечает за ценность продукта.\n'
                     '• Scrum Master (SM) — фасилитатор. Убирает препятствия, следит за соблюдением '
                     'Scrum, обучает команду. Не является менеджером.\n'
                     '• Development Team — 3-9 человек. Кросс-функциональная, самоорганизующаяся. '
                     'Полностью отвечает за поставку инкремента.\n\n'
                     'Три артефакта:\n'
                     '• Product Backlog — упорядоченный список всех желаемых изменений продукта\n'
                     '• Sprint Backlog — задачи, выбранные на текущий спринт\n'
                     '• Increment — работающий, потенциально поставляемый продукт после спринта\n\n'
                     'Definition of Done (DoD) — чёткие критерии того, что задача завершена. '
                     'Без DoD невозможно объективно оценить прогресс.'
                 ),
                 'questions': [
                     {'question': 'Кто в Scrum отвечает за приоритизацию Product Backlog?',
                      'options': ['Scrum Master',
                                  'Product Owner',
                                  'Development Team'],
                      'correct': 1,
                      'explanation': 'Product Owner ведёт и приоритизирует Product Backlog, '
                                     'определяет порядок выполнения задач и отвечает за ценность продукта.'},
                     {'question': 'Какова главная задача Scrum Master?',
                      'options': ['Назначать задачи разработчикам и контролировать их выполнение',
                                  'Убирать препятствия и следить за соблюдением Scrum-процесса',
                                  'Согласовывать бюджет проекта с руководством'],
                      'correct': 1,
                      'explanation': 'Scrum Master — фасилитатор, а не менеджер. Он убирает блокеры, '
                                     'помогает команде работать по Scrum и защищает её от внешних помех.'},
                 ]},
                {'id': 3, 'order': 3, 'title': 'Scrum-церемонии',
                 'content': (
                     'Четыре обязательных события (церемонии) структурируют работу в Scrum. '
                     'Все они таймбоксированы — имеют строгое максимальное время.\n\n'
                     'Sprint Planning (до 8 часов на 4-недельный спринт):\n'
                     '• Команда отвечает на вопросы: «Что мы сделаем?» и «Как мы это сделаем?»\n'
                     '• PO объясняет цель спринта, команда оценивает задачи и принимает их\n\n'
                     'Daily Scrum (15 минут ежедневно):\n'
                     '• Что я сделал вчера? Что буду делать сегодня? Есть ли препятствия?\n'
                     '• Для синхронизации команды, не для отчёта менеджеру\n\n'
                     'Sprint Review (до 4 часов):\n'
                     '• Демонстрация готового инкремента стейкхолдерам\n'
                     '• Получение обратной связи, обновление Product Backlog\n\n'
                     'Sprint Retrospective (до 3 часов):\n'
                     '• Что прошло хорошо? Что можно улучшить? Какие действия предпримем?\n'
                     '• Непрерывное совершенствование процесса команды\n\n'
                     'Backlog Refinement — регулярная работа по уточнению и оценке задач бэклога, '
                     'занимает не более 10% времени команды.'
                 ),
                 'questions': [
                     {'question': 'Сколько времени занимает Daily Scrum?',
                      'options': ['30 минут', '15 минут', '1 час'],
                      'correct': 1,
                      'explanation': 'Daily Scrum строго таймбоксирован — 15 минут ежедневно. '
                                     'Это инструмент синхронизации команды, а не статус-митинг для менеджера.'},
                     {'question': 'Что обсуждается на Sprint Retrospective?',
                      'options': ['Демонстрация готового продукта для стейкхолдеров',
                                  'Что прошло хорошо, что улучшить и какие действия предпримем',
                                  'Планирование задач следующего спринта'],
                      'correct': 1,
                      'explanation': 'Ретроспектива фокусируется на процессе работы команды, а не на продукте. '
                                     'Демонстрация продукта — это Sprint Review.'},
                 ]},
                {'id': 4, 'order': 4, 'title': 'Kanban: визуализация потока работ',
                 'content': (
                     'Kanban — метод управления работой через визуализацию потока задач. '
                     'Подходит для операционной работы с непредсказуемым входящим потоком.\n\n'
                     'Основные принципы Kanban:\n'
                     '1. Визуализируйте работу — вся работа на доске\n'
                     '2. Ограничивайте WIP (Work In Progress) — не берите больше, чем можете сделать\n'
                     '3. Управляйте потоком — стремитесь к равномерному прохождению задач\n'
                     '4. Делайте политики явными — правила на доске\n'
                     '5. Измеряйте и улучшайте\n\n'
                     'Метрики Kanban:\n'
                     '• Lead Time — время от постановки до выполнения задачи\n'
                     '• Cycle Time — время активной работы над задачей\n'
                     '• Throughput — количество задач, завершённых за период\n\n'
                     'Типичные колонки Kanban-доски:\n'
                     'Backlog → To Do → In Progress → Review → Done\n\n'
                     'Kanban vs Scrum: Kanban не имеет спринтов и строгих ролей, '
                     'он более гибкий и подходит для поддержки и DevOps-процессов.'
                 ),
                 'questions': [
                     {'question': 'Что означает принцип «ограничения WIP» в Kanban?',
                      'options': ['Выполнять только задачи высокого приоритета',
                                  'Не брать в работу больше задач, чем команда способна выполнить одновременно',
                                  'Завершать спринт только при выполнении всех задач'],
                      'correct': 1,
                      'explanation': 'WIP (Work In Progress) — ограничение числа одновременно выполняемых задач. '
                                     'Это предотвращает перегрузку команды и ускоряет поставку каждой задачи.'},
                 ]},
                {'id': 5, 'order': 5, 'title': 'Запуск Agile в команде',
                 'content': (
                     'Внедрение Agile — изменение культуры, а не просто инструментов. '
                     'Большинство трансформаций терпят неудачу из-за сопротивления изменениям.\n\n'
                     'Первые шаги:\n'
                     '1. Объясните зачем — какую проблему решает Agile для команды\n'
                     '2. Начните с одной команды, не меняйте всю организацию сразу\n'
                     '3. Найдите Scrum Master или Agile-коуча для поддержки\n'
                     '4. Проведите первый Sprint Planning и определите DoD\n\n'
                     'Распространённые ошибки:\n'
                     '• «Cargo cult Scrum» — формальное соблюдение церемоний без понимания цели\n'
                     '• Scrum Master как статус-репортёр, а не фасилитатор\n'
                     '• Отсутствие Product Owner — команда работает без чёткого приоритета\n'
                     '• Слишком длинные спринты (более 4 недель) — теряется гибкость\n\n'
                     'Признаки успешного Agile:\n'
                     '• Команда сама планирует и берёт ответственность\n'
                     '• Стейкхолдеры видят прогресс каждые 1-2 недели\n'
                     '• Ретроспективы приводят к реальным изменениям\n'
                     '• Команда не боится говорить о проблемах'
                 ),
                 'questions': [
                     {'question': 'С чего рекомендуется начинать внедрение Agile в организации?',
                      'options': ['Сразу трансформировать всю организацию',
                                  'Начать с одной пилотной команды и постепенно распространять опыт',
                                  'Нанять внешних консультантов и поручить всё им'],
                      'correct': 1,
                      'explanation': 'Лучшая практика — начать с одной команды, накопить опыт '
                                     'и постепенно распространять изменения. Это снижает риски и сопротивление.'},
                     {'question': 'Что такое «Cargo cult Scrum»?',
                      'options': ['Неправильная настройка Scrum-инструментов (Jira, Trello)',
                                  'Формальное соблюдение церемоний Scrum без понимания их цели',
                                  'Слишком частые ретроспективы, которые мешают работе'],
                      'correct': 1,
                      'explanation': 'Cargo cult Scrum: команда проводит все церемонии формально, '
                                     'но не понимает их цели — поэтому они не дают реального результата.'},
                 ]},
            ],
            4: [  # Трудовой кодекс
                {'id': 1, 'order': 1, 'title': 'Трудовой договор: виды и содержание',
                 'content': (
                     'Трудовой договор — основной документ, регулирующий отношения '
                     'между работником и работодателем в РФ.\n\n'
                     'Виды трудовых договоров:\n'
                     '• Бессрочный (неопределённый срок) — основной вид\n'
                     '• Срочный (до 5 лет) — только в случаях, предусмотренных ст. 59 ТК РФ\n\n'
                     'Обязательные условия договора (ст. 57 ТК РФ):\n'
                     '• Место работы (адрес организации)\n'
                     '• Трудовая функция (должность по штатному расписанию)\n'
                     '• Дата начала работы\n'
                     '• Условия оплаты труда (оклад, надбавки, порядок выплаты)\n'
                     '• Режим рабочего времени\n'
                     '• Гарантии и компенсации за работу во вредных условиях\n\n'
                     'Испытательный срок:\n'
                     '• Общий случай — до 3 месяцев\n'
                     '• Руководители — до 6 месяцев\n'
                     '• Временные работники (до 2 месяцев) — испытание не устанавливается\n\n'
                     'Изменение условий договора — только по соглашению сторон в письменной форме '
                     '(ст. 72 ТК РФ). Одностороннее изменение условий работодателем — нарушение закона.'
                 ),
                 'questions': [
                     {'question': 'Каков максимальный испытательный срок для рядового сотрудника по ТК РФ?',
                      'options': ['1 месяц', '3 месяца', '6 месяцев'],
                      'correct': 1,
                      'explanation': 'Общий испытательный срок — до 3 месяцев (ст. 70 ТК РФ). '
                                     'Для руководителей и главных бухгалтеров — до 6 месяцев.'},
                     {'question': 'Как законно изменить условия трудового договора?',
                      'options': ['Работодатель может изменить условия в одностороннем порядке',
                                  'Только по соглашению обеих сторон в письменной форме',
                                  'Устной договорённостью при свидетелях'],
                      'correct': 1,
                      'explanation': 'Изменение условий договора — только по соглашению сторон в письменной '
                                     'форме (ст. 72 ТК РФ). Одностороннее изменение работодателем незаконно.'},
                 ]},
                {'id': 2, 'order': 2, 'title': 'Рабочее время, отпуска и больничные',
                 'content': (
                     'Трудовой кодекс строго регулирует нормы рабочего времени '
                     'для защиты здоровья работников.\n\n'
                     'Нормы рабочего времени:\n'
                     '• Стандартная рабочая неделя — 40 часов (ст. 91 ТК РФ)\n'
                     '• Сокращённая — для несовершеннолетних, инвалидов, вредных условий\n'
                     '• Сверхурочная работа — с письменного согласия, не более 4 ч. в 2 дня '
                     'и 120 ч. в год; оплачивается: первые 2 ч. — в 1,5 раза, далее — в 2 раза\n\n'
                     'Ежегодный оплачиваемый отпуск:\n'
                     '• Минимум 28 календарных дней (ст. 115 ТК РФ)\n'
                     '• Право на отпуск возникает после 6 месяцев работы\n'
                     '• Перенос отпуска по инициативе работодателя — только с согласия работника\n'
                     '• Компенсация за неиспользованный отпуск — только при увольнении\n\n'
                     'Больничный лист:\n'
                     '• Первые 3 дня — за счёт работодателя\n'
                     '• С 4-го дня — за счёт ФСС\n'
                     '• Размер: до 5 лет стажа — 60%, 5-8 лет — 80%, свыше 8 лет — 100% '
                     'среднего заработка'
                 ),
                 'questions': [
                     {'question': 'Какой минимальный ежегодный оплачиваемый отпуск гарантирован ТК РФ?',
                      'options': ['14 календарных дней', '21 календарный день', '28 календарных дней'],
                      'correct': 2,
                      'explanation': 'Статья 115 ТК РФ гарантирует минимум 28 календарных дней '
                                     'ежегодного оплачиваемого отпуска для всех работников.'},
                     {'question': 'Как оплачиваются первые 2 часа сверхурочной работы?',
                      'options': ['В обычном (одинарном) размере',
                                  'В полуторном размере (×1,5)',
                                  'В двойном размере (×2)'],
                      'correct': 1,
                      'explanation': 'Первые 2 часа сверхурочной работы — в 1,5-кратном размере, '
                                     'последующие часы — в 2-кратном (ст. 152 ТК РФ).'},
                 ]},
                {'id': 3, 'order': 3, 'title': 'Оплата труда: права и гарантии',
                 'content': (
                     'Оплата труда — обязанность работодателя и право работника. '
                     'Нарушения в оплате труда — одно из самых частых нарушений ТК РФ.\n\n'
                     'Минимальный размер оплаты труда (МРОТ):\n'
                     '• Зарплата не может быть ниже МРОТ\n'
                     '• Региональный МРОТ может быть выше федерального\n'
                     '• В МРОТ включаются надбавки и доплаты, но не доплаты за сверхурочные\n\n'
                     'Порядок выплаты:\n'
                     '• Не реже двух раз в месяц (ст. 136 ТК РФ)\n'
                     '• Аванс — не позднее 30-го числа, зарплата — не позднее 15-го числа\n'
                     '• Задержка зарплаты — компенсация 1/150 ключевой ставки ЦБ за каждый день\n\n'
                     'Удержания из зарплаты:\n'
                     '• НДФЛ 13% (15% с доходов свыше 5 млн руб./год)\n'
                     '• По исполнительным листам — до 50%, в некоторых случаях до 70%\n'
                     '• Общий размер удержаний — не более 20% зарплаты\n\n'
                     'Материальная ответственность работника — только в размере среднемесячного '
                     'заработка, если иное не предусмотрено договором о полной матответственности.'
                 ),
                 'questions': [
                     {'question': 'Как часто работодатель обязан выплачивать заработную плату?',
                      'options': ['Один раз в месяц',
                                  'Не реже двух раз в месяц',
                                  'Один раз в квартал'],
                      'correct': 1,
                      'explanation': 'Статья 136 ТК РФ: зарплата выплачивается не реже двух раз в месяц. '
                                     'Аванс — до 30-го числа, основная зарплата — до 15-го следующего.'},
                     {'question': 'Какая стандартная ставка НДФЛ применяется к доходам сотрудника?',
                      'options': ['10%', '13%', '20%'],
                      'correct': 1,
                      'explanation': 'Стандартная ставка НДФЛ — 13%. С доходов свыше 5 млн руб./год '
                                     'применяется повышенная ставка 15%.'},
                 ]},
                {'id': 4, 'order': 4, 'title': 'Дисциплинарная ответственность и увольнение',
                 'content': (
                     'Работодатель вправе привлекать работников к дисциплинарной ответственности '
                     'за нарушение трудовой дисциплины.\n\n'
                     'Виды дисциплинарных взысканий (ст. 192 ТК РФ):\n'
                     '• Замечание\n'
                     '• Выговор\n'
                     '• Увольнение по соответствующим основаниям\n\n'
                     'Порядок применения взыскания:\n'
                     '1. Работник обязан написать объяснительную (2 рабочих дня)\n'
                     '2. Издаётся приказ в течение 1 месяца с момента обнаружения\n'
                     '3. Нельзя применить два взыскания за один проступок\n'
                     '4. Снимается автоматически через год, если нет новых взысканий\n\n'
                     'Основания для увольнения по инициативе работодателя:\n'
                     '• Ликвидация / сокращение штата — с уведомлением за 2 месяца\n'
                     '• Прогул (отсутствие более 4 часов без уважительной причины)\n'
                     '• Появление в состоянии опьянения\n'
                     '• Разглашение охраняемой тайны\n'
                     '• Грубое нарушение охраны труда\n\n'
                     'Защита прав: работник может обратиться в Государственную инспекцию труда '
                     'или суд в течение 1 месяца со дня вручения приказа об увольнении.'
                 ),
                 'questions': [
                     {'question': 'Сколько рабочих дней есть у работника для написания объяснительной?',
                      'options': ['1 рабочий день', '2 рабочих дня', '5 рабочих дней'],
                      'correct': 1,
                      'explanation': 'По статье 193 ТК РФ работодатель обязан запросить объяснение, '
                                     'а работник имеет 2 рабочих дня для его предоставления.'},
                     {'question': 'Через какое время автоматически снимается дисциплинарное взыскание?',
                      'options': ['6 месяцев', '1 год', '2 года'],
                      'correct': 1,
                      'explanation': 'Дисциплинарное взыскание снимается автоматически через 1 год, '
                                     'если за это время не последовало новых взысканий (ст. 194 ТК РФ).'},
                 ]},
            ],
        }

        def _done_lessons(progress_pct, total):
            if progress_pct >= 100:
                return list(range(1, total + 1))
            count = round(progress_pct / 100 * total)
            return list(range(1, max(0, count) + 1))

        # ── Create courses with lessons ────────────────────────────────────
        courses_data = [
            ('Основы информационной безопасности',
             'Обязательный курс по ИБ для всех сотрудников: угрозы, защита данных, политики.',
             'mandatory', 4, date(2026, 12, 31), LESSONS[0]),
            ('Эффективные коммуникации',
             'Развитие навыков деловой переписки, публичных выступлений и обратной связи.',
             'development', 8, date(2026, 9, 30), LESSONS[1]),
            ('Python для анализа данных',
             'Технический курс: pandas, numpy, matplotlib, scikit-learn — от основ до ML.',
             'technical', 20, date(2026, 8, 31), LESSONS[2]),
            ('Управление проектами (Agile/Scrum)',
             'Методологии Scrum, Kanban, основы PMI; роли, церемонии, артефакты.',
             'development', 12, date(2026, 10, 31), LESSONS[3]),
            ('Трудовой кодекс и кадровое делопроизводство',
             'Обязательный курс по трудовому законодательству РФ и оформлению кадровых документов.',
             'mandatory', 6, date(2026, 7, 31), LESSONS[4]),
        ]

        courses = []
        for title, desc, cat, dur, dl, lessons in courses_data:
            c, _ = Course.objects.update_or_create(
                title=title,
                defaults={'description': desc, 'category': cat, 'duration_hours': dur,
                          'deadline': dl, 'status': 'active', 'lessons': lessons},
            )
            courses.append(c)

        # ── Create assignments with completed_lessons ──────────────────────
        # (emp_idx, course_idx, raw_progress, status)
        now = timezone.now()
        assignments_data = [
            (0,  0, 100, 'completed', now),
            (0,  2,  60, 'in_progress', None),
            (1,  0, 100, 'completed', now),
            (1,  1,  80, 'in_progress', None),
            (2,  3,  60, 'in_progress', None),
            (3,  4, 100, 'completed', now),
            (3,  1,  40, 'in_progress', None),
            (4,  4, 100, 'completed', now),
            (5,  0, 100, 'completed', now),
            (5,  1,  20, 'in_progress', None),
            (6,  2,  20, 'in_progress', None),
            (7,  1,  80, 'in_progress', None),
            (7,  3,  40, 'in_progress', None),
            (8,  4,   0, 'assigned', None),
            (9,  2,  80, 'in_progress', None),
            (10, 0,   0, 'assigned', None),
            (11, 1,  20, 'in_progress', None),
            (12, 4,   0, 'assigned', None),
            (13, 0,  25, 'in_progress', None),
            (14, 3,   0, 'assigned', None),
            (15, 1,  20, 'in_progress', None),
            (16, 4,   0, 'assigned', None),
            (17, 0,   0, 'assigned', None),
        ]
        asgn_count = 0
        for emp_i, course_i, raw_prog, status, completed_at in assignments_data:
            if emp_i >= len(employees) or course_i >= len(courses):
                continue
            course      = courses[course_i]
            total       = len(course.lessons or [])
            completed   = _done_lessons(raw_prog, total) if total else []
            actual_prog = round(len(completed) / total * 100) if total else raw_prog
            CourseAssignment.objects.update_or_create(
                employee=employees[emp_i],
                course=course,
                defaults={
                    'progress':          actual_prog,
                    'status':            status,
                    'completed_at':      completed_at,
                    'completed_lessons': completed,
                },
            )
            asgn_count += 1

        # ── Certificates for completed assignments ─────────────────────────
        cert_data = [(0, 0), (1, 0), (3, 4), (4, 4)]
        cert_count = 0
        for emp_i, course_i in cert_data:
            if emp_i < len(employees) and course_i < len(courses):
                _, created = Certificate.objects.get_or_create(
                    employee=employees[emp_i],
                    course=courses[course_i],
                    defaults={
                        'issued_at':          date.today(),
                        'certificate_number': f'CERT-{uuid.uuid4().hex[:8].upper()}',
                    },
                )
                if created:
                    cert_count += 1

        self.stdout.write(f'  Курсов: {len(courses)}')
        self.stdout.write(f'  Назначений курсов: {asgn_count}')
        self.stdout.write(f'  Сертификатов создано: {cert_count}')

    def _create_audit_logs(self, employees):
        from datetime import datetime, timedelta
        from django.utils.timezone import make_aware
        from django.contrib.auth.models import User as DjUser
        from audit.models import AuditLog

        AuditLog.objects.all().delete()

        try:
            admin_user = DjUser.objects.get(username='admin')
            hr_user    = DjUser.objects.get(username='hr')
            ivanov     = DjUser.objects.get(username='ivanov')
        except DjUser.DoesNotExist:
            return

        now = datetime.now()
        def dt(days=0, hours=0, _=0):
            return make_aware(now - timedelta(days=days, hours=hours))

        entries = [
            # Логины
            dict(user=admin_user,  action='LOGIN',  model_name='User',      object_id=str(admin_user.id),
                 object_repr='admin', changes=None, ip_address='127.0.0.1',
                 details='Успешный вход: admin', timestamp=dt(0, 1)),
            dict(user=hr_user,     action='LOGIN',  model_name='User',      object_id=str(hr_user.id),
                 object_repr='hr',    changes=None, ip_address='127.0.0.1',
                 details='Успешный вход: hr', timestamp=dt(0, 2)),
            dict(user=ivanov,      action='LOGIN',  model_name='User',      object_id=str(ivanov.id),
                 object_repr='ivanov', changes=None, ip_address='192.168.1.10',
                 details='Успешный вход: ivanov', timestamp=dt(1)),
            # CREATE сотрудника
            dict(user=admin_user, action='CREATE', model_name='Employee',
                 object_id='18', object_repr='Сидоров Дмитрий',
                 changes={'salary': 85000, 'department': 'Разработка', 'position': 'Разработчик Python'},
                 ip_address='127.0.0.1', details='Создан Employee id=18', timestamp=dt(2)),
            # UPDATE зарплаты
            dict(user=admin_user, action='UPDATE', model_name='Employee',
                 object_id='14', object_repr='Зайцев Николай',
                 changes={'updated_fields': {'salary': 95000}},
                 ip_address='127.0.0.1', details='Изменён Employee id=14', timestamp=dt(2, 2)),
            # CREATE заявки на отпуск
            dict(user=hr_user, action='CREATE', model_name='LeaveRequest',
                 object_id='1', object_repr='Петрова — sick',
                 changes={'leave_type': 'sick', 'start_date': '2026-04-03', 'end_date': '2026-04-07'},
                 ip_address='127.0.0.1', details='Создан LeaveRequest id=1', timestamp=dt(3)),
            # UPDATE статуса заявки
            dict(user=admin_user, action='UPDATE', model_name='LeaveRequest',
                 object_id='1', object_repr='LeaveRequest #1',
                 changes={'updated_fields': {'status': 'approved'}},
                 ip_address='127.0.0.1', details='Изменён LeaveRequest id=1', timestamp=dt(3, 1)),
            # DELETE кандидата
            dict(user=hr_user, action='DELETE', model_name='Candidate',
                 object_id='3', object_repr='Кандидат #3',
                 changes=None, ip_address='127.0.0.1',
                 details='Удалён Candidate id=3', timestamp=dt(5)),
            # Выход
            dict(user=admin_user, action='LOGOUT', model_name='User',
                 object_id=str(admin_user.id), object_repr='admin',
                 changes=None, ip_address='127.0.0.1',
                 details='Выход из системы: admin', timestamp=dt(1, 0, )),
            # Изменение роли
            dict(user=admin_user, action='UPDATE', model_name='User',
                 object_id=str(ivanov.id), object_repr='ivanov',
                 changes={'updated_fields': {'role': 'EMPLOYEE'}},
                 ip_address='127.0.0.1', details='Изменён User id=' + str(ivanov.id), timestamp=dt(7)),
            # CREATE вакансии
            dict(user=hr_user, action='CREATE', model_name='Vacancy',
                 object_id='1', object_repr='Разработчик Python',
                 changes={'title': 'Разработчик Python', 'department': 'Разработка'},
                 ip_address='127.0.0.1', details='Создан Vacancy id=1', timestamp=dt(10)),
        ]

        for e in entries:
            ts = e.pop('timestamp')
            obj = AuditLog(**e)
            obj.save()
            # Override auto_now_add
            AuditLog.objects.filter(pk=obj.pk).update(timestamp=ts)

        self.stdout.write(f'  Записей аудита: {len(entries)}')
