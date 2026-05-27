# Q1 Linter / Static Review

## 选的工具：ruff

用 ruff 是因为它一个二进制就把 pyflakes、pycodestyle、isort 和一部分 pylint 规则都覆盖了，配置只要 `pyproject.toml` 一段就够，CI 跑也快（一次扫整个 repo 不到 1 秒）。原本想 flake8 + 几个 plugin，但配置散在 `.flake8` 和 `setup.cfg`，懒得维护。

## 配置

`pyproject.toml`:

```toml
[tool.ruff]
target-version = "py312"
line-length = 88
exclude = [
    ".venv",
    "*/migrations/*",
    "db.sqlite3",
]

[tool.ruff.lint]
select = ["E", "F", "W", "I", "SIM", "B"]
```

跑法：

```
ruff check .
```

跑下来一共 27 条 finding，分布在 7 个不同规则类型。下面挑 5 个不同种类的写出来。

---

## 发现 1：未使用的 import (F401)

文件：`accounts/admin.py`，第 1 行

原始代码：

```python
from django.contrib import admin

# Register your models here.
```

ruff 输出：

```
F401 [*] `django.contrib.admin` imported but unused
 --> accounts/admin.py:1:28
  |
1 | from django.contrib import admin
  |                            ^^^^^
2 |
3 | # Register your models here.
  |
help: Remove unused import: `django.contrib.admin`
```

改之后：

```python
# Register your models here.
```

这是上游 cookie-cutter 留下来的占位 import，整个文件都没用到。

---

## 发现 2：可以直接返回 bool 表达式 (SIM103)

文件：`polls/models.py`，第 14–23 行

原始代码：

```python
def user_can_vote(self, user):
    """
    Return False if user already voted.
    """
    user_votes = user.vote_set.all()
    qs = user_votes.filter(poll=self)
    if qs.exists():
        return False
    return True
```

ruff 输出：

```
SIM103 Return the condition `not qs.exists()` directly
  --> polls/models.py:21:9
   |
19 |           user_votes = user.vote_set.all()
20 |           qs = user_votes.filter(poll=self)
21 | /         if qs.exists():
22 | |             return False
23 | |         return True
   | |___________________^
help: Replace with `return not qs.exists()`
```

改之后：

```python
def user_can_vote(self, user):
    """
    Return False if user already voted.
    """
    user_votes = user.vote_set.all()
    qs = user_votes.filter(poll=self)
    return not qs.exists()
```

少两行 + 更直接。这种 if-else 包 bool 是新手最常见的写法，ruff 抓得很准。

---

## 发现 3：变量赋值但从来没用 (F841)

文件：`seeder.py`，第 21 行

原始代码：

```python
for _ in range(num_entries):
    first_name = fake.first_name()
    last_name = fake.last_name()
    u = User.objects.create_user(
        first_name=first_name,
        last_name=last_name,
        email=first_name + "." + last_name + "@fakermail.com",
        username=first_name + last_name,
        password="password"
    )
    count += 1
```

ruff 输出：

```
F841 Local variable `u` is assigned to but never used
  --> seeder.py:21:9
   |
21 |         u = User.objects.create_user(
   |         ^
help: Remove assignment to unused variable `u`
```

改之后：

```python
for _ in range(num_entries):
    first_name = fake.first_name()
    last_name = fake.last_name()
    User.objects.create_user(
        first_name=first_name,
        last_name=last_name,
        email=first_name + "." + last_name + "@fakermail.com",
        username=first_name + last_name,
        password="password"
    )
    count += 1
```

`u` 接住返回值之后下面一行都没用，删掉就好。同一个 seeder.py 还有两处 `c = Choice(...)` 和 `v = Vote(...)` 是一样的 pattern，一并能修。

---

## 发现 4：单行太长 (E501)

文件：`polls/views.py`，第 73 行（91 字符）

原始代码：

```python
messages.success(
    request, "Poll & Choices added successfully.", extra_tags=SUCCESS_TAGS)
```

ruff 输出：

```
E501 Line too long (91 > 88)
  --> polls/views.py:73:89
   |
73 |                     request, "Poll & Choices added successfully.", extra_tags=SUCCESS_TAGS)
   |                                                                                         ^^^
```

改之后：

```python
messages.success(
    request,
    "Poll & Choices added successfully.",
    extra_tags=SUCCESS_TAGS,
)
```

每个参数独占一行，顺便加 trailing comma。

---

## 发现 5：文件末尾没换行 (W292)

文件：`accounts/urls.py`，第 10 行

原始代码（末尾没有换行符）：

```python
urlpatterns=[
    path('login/', views.login_user, name='login'),
    path('logout/', views.logout_user, name='logout'),
    path('register/', views.create_user, name='register'),
]
```

ruff 输出：

```
W292 [*] No newline at end of file
  --> accounts/urls.py:10:2
   |
 8 |     path('logout/', views.logout_user, name='logout'),
 9 |     path('register/', views.create_user, name='register'),
10 | ]
   |  ^
help: Add trailing newline
```

改之后：在 `]` 后面加一个换行。这个 git diff 里基本看不出来，但有些工具（cat、合并 diff）会因为缺尾换行而显示成 `\ No newline at end of file`。

---

## 截图

终端跑 `ruff check .` 的完整输出存在 `reports/q1_ruff_full_output.txt`，每条 finding 单独跑的命令：

```
ruff check --select F401 accounts/admin.py
ruff check --select SIM103 polls/models.py
ruff check --select F841 seeder.py
ruff check --select E501 polls/views.py
ruff check --select W292 accounts/urls.py
```

跑这些然后截图就行。

## 五条 finding 规则类型一览

| 序号 | 规则 | 类型 | 修复方式 |
|------|------|------|------|
| 1 | F401 | 未使用 import | 删 |
| 2 | SIM103 | 代码可简化 | 改写表达式 |
| 3 | F841 | 未使用变量 | 删赋值 |
| 4 | E501 | 行太长 | 换行 |
| 5 | W292 | 文件末尾缺换行 | 加换行 |

五条规则分别来自 Pyflakes (F)、flake8-simplify (SIM)、pycodestyle (E/W)，类型不重，覆盖了 import、idiom、dead code、style、file format 五个方向。
