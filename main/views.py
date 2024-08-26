from django.shortcuts import render, redirect, get_object_or_404
from django.http import HttpResponse
from django.contrib import auth
# ↓FriendsSearchFormをユーザー検索機能の回で追加
# ↓IconChangeFormをアイコン追加機能の回で追加
from .forms import (
    SignUpForm, LoginForm, TalkForm, UsernameChangeForm, EmailChangeForm, 
    FriendsSearchForm, IconChangeForm,)
from django.contrib.auth import views as auth_views
from django.contrib.auth.decorators import login_required
from .models import User, Talk
from django.db.models import Q
from django.urls import reverse_lazy
from django.db.models import Max
from django.db.models.functions import Greatest, Coalesce
from django.views.generic.base import TemplateView
# ↓下２つはクラスベースビューの回で追加
from django.contrib.auth.mixins import LoginRequiredMixin
from django.views.generic.list import ListView


def index(request):
    return render(request, "main/index.html")


def signup(request):
    # もしリクエストメソッドがGETなら、空のSignUpFormを生成して、会員登録ページに表示
    if request.method == "GET":
        form = SignUpForm()
    # そうでなくもしリクエストメソッドがPOSTなら、SignUpFormを生成して、ユーザーの入力データを保持
    elif request.method == "POST":
        form = SignUpForm(request.POST)
        # 入力データが妥当かチェック、もし妥当ならTrueを返して、新しいユーザーをデータベースに保存
        # 妥当でなければFalseを返して、signup.htmlにフォームのエラーメッセージを表示
        if form.is_valid():
            form.save()
            username = form.cleaned_data["username"]
            password = form.cleaned_data["password1"]
            user = auth.authenticate(username=username, password=password)
            # authenticate()関数に、チェックを通過したusernameとpasswordを渡して、新しいユーザーを認証
            # 認証に成功したら、対応するUserオブジェクトを返して、ログイン状態でindexページに自動転送
            if user:
                auth.login(request, user)
            return redirect("index")
    context = {"form": form}
    return render(request, "main/signup.html", context)


class LoginView(auth_views.LoginView):
    authentication_form = LoginForm
    template_name = "main/login.html"



# friends関数はクラスベースビューの回で削除
# @login_required
# def friends(request):
#     friends = User.objects.exclude(id=request.user.id).annotate(
#         sent_talk__time__max=Max(
#             "sent_talk__time", filter=Q(sent_talk__receiver=request.user)
#         ),
#         received_talk__time__max=Max(
#             "received_talk__time",
#             filter=Q(received_talk__sender=request.user),
#         ),
#         time_max=Greatest(
#             "sent_talk__time__max", "received_talk__time__max"
#         ),
#         last_talk_time=Coalesce(
#             "time_max", "sent_talk__time__max", "received_talk__time__max"
#         ),
#     ).order_by("-last_talk_time").values("id", "username", "last_talk_time")

#     context = {"friends": friends}
#     return render(request, "main/friends.html", context)

@login_required
def settings(request):
    return render(request, "main/settings.html")


@login_required
def talk_room(request, user_id):
    friend = get_object_or_404(User, id=user_id)
    # 送信者がユーザーで、受信者がトーク画面のフレンドであるデータ、
    # または、送信者がトーク画面のフレンドで、受信者がユーザーであるデータをすべて取得
    # Qオブジェクトは、&（and）|（or）など複数条件で、filter()やexclude()が使用可能
    talks = Talk.objects.filter(
        Q(sender=request.user, receiver=friend)
        | Q(sender=friend, receiver=request.user)
    ).order_by("time")
    if request.method == "GET":
        form = TalkForm()
    elif request.method == "POST":
        form = TalkForm(request.POST)
        if form.is_valid():
            # 新しいトークの保存を一時的に避けて、関連データを設定後、データベースに保存
            new_talk = form.save(commit=False)
            new_talk.sender = request.user
            new_talk.receiver = friend
            new_talk.save()
            return redirect("talk_room", user_id)
    context = {
        "form": form,
        "friend": friend,
        "talks": talks,
    }
    return render(request, "main/talk_room.html", context)


@login_required
def username_change(request):
    if request.method == "GET":
        # instanceを指定すると、指定したインスタンスのデータにアクセス可能
        form = UsernameChangeForm(instance=request.user)
    elif request.method == "POST":
        form = UsernameChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("username_change_done")
    context = {"form": form}
    return render(request, "main/username_change.html", context)


@login_required
def username_change_done(request):
    return render(request, "main/username_change_done.html")


@login_required
def email_change(request):
    if request.method == "GET":
        # instanceを指定すると、指定したインスタンスのデータにアクセス可能
        form = EmailChangeForm(instance=request.user)
    elif request.method == "POST":
        form = EmailChangeForm(request.POST, instance=request.user)
        if form.is_valid():
            form.save()
            return redirect("email_change_done")
    context = {"form": form}
    return render(request, "main/email_change.html", context)


@login_required
def email_change_done(request):
    return render(request, "main/email_change_done.html")


class PasswordChangeView(auth_views.PasswordChangeView):
    template_name = "main/password_change.html"
    success_url = reverse_lazy("password_change_done")


class PasswordChangeDoneView(auth_views.PasswordChangeDoneView):
    template_name = "main/password_change_done.html"


class LogoutView(auth_views.LogoutView):
    pass

# ↓クラスベースビューの回のお試し用
class MyView(TemplateView):
    template_name = "main/my_site.html"

# FriendsViewはクラスベースビューの回で追加
class FriendsView(LoginRequiredMixin, ListView):
    template_name = "main/friends.html"
    paginate_by = 7
    context_object_name = "friends"

    def get_queryset(self):
        queryset = User.objects.exclude(id=self.request.user.id).annotate(
            sent_talk__time__max=Max(
                "sent_talk__time",
                filter=Q(sent_talk__receiver=self.request.user),
            ),
            received_talk__time__max=Max(
                "received_talk__time",
                filter=Q(received_talk__sender=self.request.user),
            ),
            time_max=Greatest(
                "sent_talk__time__max", "received_talk__time__max"
            ),
            last_talk_time=Coalesce(
                "time_max",
                "sent_talk__time__max",
                "received_talk__time__max",
            ),
        # アイコン追加機能の際に、order_byより後の.valuesを削除
        ).order_by("-last_talk_time")

        # ↓ユーザー検索機能の回で追加
        form = FriendsSearchForm(self.request.GET)
        if form.is_valid():
            keyword = form.cleaned_data["keyword"]
            if keyword:
                queryset = queryset.filter(username__icontains=keyword)
        # ↑ここまで追加

        return queryset

# ↓ユーザー検索機能の回で追加
    def get_context_data(self, **kwargs):
        context = super().get_context_data(**kwargs)

        form = FriendsSearchForm(self.request.GET)
        if form.is_valid():
            context["keyword"] = form.cleaned_data["keyword"]

        context["form"] = form
        return context    
    

# ↓アイコン追加機能の回で追加
@login_required
def icon_change(request):
    if request.method == "GET":
        form = IconChangeForm(instance=request.user)
    elif request.method == "POST":
        form = IconChangeForm(
            request.POST, request.FILES, instance=request.user
        )
        if form.is_valid():
            form.save()
            return redirect("icon_change_done")
    context = {
        "form": form,
    }
    return render(request, "main/icon_change.html", context)
@login_required
def icon_change_done(request):
    return render(request, "main/icon_change_done.html")