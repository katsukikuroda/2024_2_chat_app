import os
import random


import django
from dateutil import tz
from faker import Faker


os.environ.setdefault("DJANGO_SETTINGS_MODULE", "chat_app.settings")
django.setup()


from main.models import Talk, User


fakegen = Faker(["ja_JP"])


def create_users(n):
    """
    ダミーのユーザーとチャットの文章を作る。
    n: 作成するユーザーの人数
    """
    # Userオブジェクトの生成と格納
    users = [
        User(username=fakegen.user_name(), email=fakegen.ascii_safe_email())
        for _ in range(n)
    ]
    # データベースへの登録
    User.objects.bulk_create(users, ignore_conflicts=True)


    # getの引数部分を自分が登録しているid（だいたいadmin）に変更せよ
    my_id = User.objects.get(username="admin").id


    # values_list メソッドを使うと、User オブジェクトから特定のフィールドのみ取り出すことができます。
    # 返り値はユーザー id のリストになります。
    user_ids = User.objects.exclude(id=my_id).values_list("id", flat=True)


    talks = []
    for _ in range(len(user_ids)):
        sent_talk = Talk(
            sender_id=my_id,
            receiver_id=random.choice(user_ids),
            message=fakegen.text(),
        )
        received_talk = Talk(
            sender_id=random.choice(user_ids),
            receiver_id=my_id,
            message=fakegen.text(),
        )
        talks.extend([sent_talk, received_talk])
        # リストのextendメソッド




    """
    リストのextendメソッド
   
    リストを拡張することができる
    ↓例
    l = [0, 1, 2]
    l.extend([10, 11, 12])
    print(l)
    # [0, 1, 2, 10, 11, 12]


   
    bulk_create:モデルに変更を加える
    第一引数：モデルのインスタンスを格納したリスト
    """
    Talk.objects.bulk_create(talks, ignore_conflicts=True)


    # Talk の time フィールドは auto_now_add が指定されているため、bulk_create をするときに
    # time フィールドが自動的に現在の時刻に設定されてしまいます。
    # 最新の 2 * len(user_ids) 個分は先程作成した Talk なので、これらを改めて取得し、
    # time フィールドを明示的に更新します。


    # -timeは時間の降順、つまり最新の順番に書く
    # このスライスは何のためにある？
    talks = Talk.objects.order_by("-time")[: 2 * len(user_ids)]
    for talk in talks:
        talk.time = fakegen.date_time_this_year(tzinfo=tz.gettz("Asia/Tokyo"))
    Talk.objects.bulk_update(talks, fields=["time"])


if __name__ == "__main__":
    print("creating users ... ", end="")
    create_users(5)
    print("done")