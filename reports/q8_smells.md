# Q8 Code Smells

下面三个 smell 都是在做完 lint 和单测前后翻代码翻出来的，类型都不一样（Duplicated Code / Long Method 多职责 / Feature Envy）。每个 smell 都给一段原始代码 + 文件行号，再写一句重构方向。这次只是 review，不动代码。

---

## Smell 1：Duplicated Code

| Section | Details |
|---|---|
| Code smell type | Duplicated Code |
| Location | `polls/views.py` 第 72/96/112/129/153/173/196/207 行 + `accounts/views.py` 第 43/47/51/55/57/63 行，共 14 处 |
| Why it's a smell | 同一个 Bootstrap CSS class 字符串 `alert alert-success alert-dismissible fade show` 和它的 warning 版本被原样复制粘贴了 14 次，分散在两个 view 文件里。如果哪天 Bootstrap 升到 5、要把 `fade show` 换成新的 class，得逐处去找替换；写测试时也只能用整串字符串去断言，断错一个空格就挂。 |
| Proposed improvement | Extract Constant：把这两个字符串提到一个公共模块（如 `pollme/messages.py`）的 `SUCCESS_TAGS` 和 `WARNING_TAGS`，两个 view 各 import 一次。一处改全局生效，测试也能直接断言常量身份而不是字符串字面量。 |

原始代码片段（其中两处，证明完全一样）：

`polls/views.py:71-73`

```python
messages.success(
    request, "Poll & Choices added successfully.", extra_tags='alert alert-success alert-dismissible fade show')
```

`accounts/views.py:62-64`

```python
messages.success(
    request, f'Thanks for registering {user.username}.', extra_tags='alert alert-success alert-dismissible fade show')
```

两个 view 文件这种"复制粘贴 14 次"的模式占了相当一部分代码行数。

---

## Smell 2：Long Method / Multiple Responsibilities

| Section | Details |
|---|---|
| Code smell type | Long Method (with Mixed Responsibilities) |
| Location | `polls/models.py` 第 28–45 行，`Poll.get_result_dict` 方法 |
| Why it's a smell | 一个方法干了三件事：(1) 算每个 choice 的投票数和百分比；(2) 把 Bootstrap 颜色 class 随机配给每个 choice；(3) 顺手在内部 hardcode 了颜色名 list。三件事都跟"poll 结果"有点关系但实际上是不同抽象层级的事。最严重的是它用 `secrets.choice` 选随机颜色——`secrets` 模块是 cryptographic 用途的随机源，给 UI 上色用它语义错；而且随机源直接硬编码在方法里，没有任何注入点，单元测试根本没法预期 `alert_class` 是哪一个，要么 patch 整个 `secrets` 模块要么放弃断言这一字段。 |
| Proposed improvement | Extract Method + Dependency Injection：拆成两个纯函数 `compute_poll_results(poll)`（只算数）和 `attach_alert_classes(results, rng)`（只配色，rng 可注入），原方法变成两者的 wrapper。`rng` 参数默认 `random.Random()`，测试时传一个 stub `class StubRNG: def choice(self, seq): return seq[0]` 就能让输出完全确定。 |

原始代码片段（`polls/models.py:28-45`）：

```python
def get_result_dict(self):
    res = []
    for choice in self.choice_set.all():
        d = {}
        alert_class = ['primary', 'secondary', 'success',
                       'danger', 'dark', 'warning', 'info']

        d['alert_class'] = secrets.choice(alert_class)
        d['text'] = choice.choice_text
        d['num_votes'] = choice.get_vote_count
        if not self.get_vote_count:
            d['percentage'] = 0
        else:
            d['percentage'] = (choice.get_vote_count /
                               self.get_vote_count)*100

        res.append(d)
    return res
```

---

## Smell 3：Feature Envy

| Section | Details |
|---|---|
| Code smell type | Feature Envy |
| Location | `accounts/views.py` 第 29–65 行，`create_user` view 函数体 |
| Why it's a smell | 这个 view 函数本来该只做 HTTP 编排（接 request、调 form、redirect/render），但它内部把"表单校验"这件 form 的事抢过来自己干：从 `cleaned_data` 里手动取 username/email/password1/password2，自己跑三个 `if` 检查密码匹配 + 用户名重复 + 邮箱重复，还用三个 flag 变量 `check1/check2/check3` 攒错误结果。Form 类已经定义在 `accounts/forms.py`，但所有的领域校验逻辑都被搬到 view 里。结果是：view 函数巨长（37 行），form 类反而几乎是空壳；写单测要测校验规则只能搭 HTTP request；form 自己测试不出来。 |
| Proposed improvement | Move Method：把校验逻辑搬回 `UserRegistrationForm` 的 `clean_username` / `clean_email` / `clean` 方法，再加一个 `save()` 方法封装 `User.objects.create_user`。view 瘦身成 `if form.is_valid(): form.save()` 这种 12 行的标准 Django 写法。form 也变得可以脱离 view 直接单测（patch `User.objects.filter` 即可）。 |

原始代码片段（`accounts/views.py:29-65`）：

```python
def create_user(request):
    if request.method == 'POST':
        check1 = False
        check2 = False
        check3 = False
        form = UserRegistrationForm(request.POST)
        if form.is_valid():
            username = form.cleaned_data['username']
            password1 = form.cleaned_data['password1']
            password2 = form.cleaned_data['password2']
            email = form.cleaned_data['email']

            if password1 != password2:
                check1 = True
                messages.error(request, 'Password did not match!',
                               extra_tags='alert alert-warning alert-dismissible fade show')
            if User.objects.filter(username=username).exists():
                check2 = True
                messages.error(request, 'Username already exists!',
                               extra_tags='alert alert-warning alert-dismissible fade show')
            if User.objects.filter(email=email).exists():
                check3 = True
                messages.error(request, 'Email already registered!',
                               extra_tags='alert alert-warning alert-dismissible fade show')

            if check1 or check2 or check3:
                messages.error(
                    request, "Registration Failed!", extra_tags='alert alert-warning alert-dismissible fade show')
                return redirect('accounts:register')
            else:
                user = User.objects.create_user(
                    username=username, password=password1, email=email)
                ...
```

`check1/check2/check3` 三个 flag 是 feature envy 最明显的标志——这种"在 A 模块里用本地变量缓存 B 模块的校验结果"基本一定是逻辑放错地方了。
