import sys
try:
    from app.services import email
    print("Syntax OK")
except Exception as e:
    print(f"Error: {e}")
except SyntaxError as e:
    print(f"Syntax Error: {e}")
