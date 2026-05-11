import django, os
os.environ.setdefault('DJANGO_SETTINGS_MODULE', 'hrm.settings')
django.setup()

from django.db import connection
from employees.models import Employee
from hrm.encryption import _ENCRYPTED_PREFIX, AESEncryption

cipher = AESEncryption()

print("=== Raw DB values (must start with 'enc:') ===")
with connection.cursor() as cur:
    cur.execute("SELECT id, phone, birth_date FROM employees_employee LIMIT 5")
    for emp_id, phone, birth_date in cur.fetchall():
        phone_ok    = (not phone) or str(phone).startswith(_ENCRYPTED_PREFIX)
        bdate_ok    = (not birth_date) or str(birth_date).startswith(_ENCRYPTED_PREFIX)
        print(f"  id={emp_id}  phone_encrypted={phone_ok}  bdate_encrypted={bdate_ok}")
        if not phone_ok:
            print(f"    !!! phone NOT encrypted: {phone!r}")
        if not bdate_ok:
            print(f"    !!! birth_date NOT encrypted: {birth_date!r}")

print("\n=== ORM read (must return plaintext) ===")
for emp in Employee.objects.all()[:5]:
    print(f"  {emp.last_name}: phone={emp.phone!r}  birth_date={emp.birth_date!r}  type={type(emp.birth_date).__name__}")

print("\n=== Round-trip write+read ===")
emp = Employee.objects.first()
original_phone = emp.phone
original_bdate = emp.birth_date
from datetime import date
emp.phone = '+7 (999) 123-45-67'
emp.birth_date = date(1990, 6, 15)
emp.save(update_fields=['phone', 'birth_date'])

# Reload from DB
emp.refresh_from_db()
assert emp.phone == '+7 (999) 123-45-67', f"phone mismatch: {emp.phone!r}"
assert emp.birth_date == date(1990, 6, 15), f"bdate mismatch: {emp.birth_date!r}"
print(f"  phone:      {emp.phone!r}  ✓")
print(f"  birth_date: {emp.birth_date!r}  ✓")

# Restore
emp.phone = original_phone
emp.birth_date = original_bdate
emp.save(update_fields=['phone', 'birth_date'])

print("\n=== AESEncryption unit test ===")
for test in ['Hello', 'test@example.com', '+7(999)000-00-00', '1990-05-15']:
    enc = cipher.encrypt(test)
    dec = cipher.decrypt(enc)
    assert dec == test, f"round-trip failed for {test!r}"
    # Different IVs each time
    enc2 = cipher.encrypt(test)
    assert enc != enc2, "IVs must be random (different ciphertexts for same plaintext)"
    print(f"  {test!r} → enc[:{min(20,len(enc))}]={enc[:20]}...  decrypt OK  IV random OK")

print("\nAll checks passed.")
