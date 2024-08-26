import os
import random


import django
from dateutil import tz

from main.models import Talk, User


def delete():
    users_id = User.object.exclude(id=admin).values_list("id", flat=True)

if __name__ == "__main__":
    print("creating users ... ", end="")
    delete(5)
    print("done")