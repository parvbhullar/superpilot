import os
import sys
import asyncio
import time

sys.path.insert(0, os.path.abspath(os.path.join(os.path.dirname(__file__), "../..")))

from superpilot.examples.email.super_email import SuperEmail

email = r"C:\Users\hp\Downloads\sample.eml"
super_email = SuperEmail(thread_id="thread1234567891011121314151617", email=email)
print(super_email.process_email())

