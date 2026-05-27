# Q7 Integration Tests

跟 Q3 不一样，这里完全不用 test double。两个测试都跑真 Django test DB、真 URL routing、真 ORM。文件在 [`qa_tests/test_integration.py`](../qa_tests/test_integration.py)。

跑法：

```
python manage.py test qa_tests.test_integration -v 2
```

跑过 2 个测试，0.15 秒。

## 测试 1：投票去重（View ↔ ORM ↔ DB）

**集成的组件**：
- HTTP 入口 + Django session/auth + `polls.views.poll_vote` view 函数
- `polls.models.Poll.user_can_vote` 应用层校验
- Django ORM
- SQLite 上的 `polls_vote` 表 + R3 重构加上的 `UniqueConstraint('user', 'poll')`

**如果没集成好会怎样**：
- 如果 `user_can_vote` 写错了（比如老版本里 `if qs.exists(): return False; return True` 的逻辑反了），view 不会拦下第二次投票，重复 Vote 行就进数据库
- 如果只在 view 里挡，没在 DB 加唯一约束（R3 之前的状态），任何**绕过 view 的写入路径**（管理后台、数据迁移脚本、race condition）都会直接产生重复行
- 测试同时覆盖这两层："view 挡得住" + "DB 也挡得住"

**测试逻辑**：

```python
def test_second_vote_attempt_blocked_and_db_rejects_raw_duplicate(self):
    url = reverse("polls:vote", kwargs={"poll_id": self.poll.id})

    # 1) 第一次投票走完整 stack: view -> Vote(...).save() -> DB
    r1 = self.client.post(url, {"choice": self.c1.id})
    self.assertEqual(r1.status_code, 200)
    self.assertEqual(
        Vote.objects.filter(user=self.alice, poll=self.poll).count(), 1
    )

    # 2) 第二次投票被 view 层拦下: 重定向到 polls:list
    r2 = self.client.post(url, {"choice": self.c2.id})
    self.assertEqual(r2.status_code, 302)
    self.assertEqual(r2.url, reverse("polls:list"))

    # 3) 即便绕过 view 直接 ORM 写入, DB 唯一约束也会抛 IntegrityError
    with self.assertRaises(IntegrityError):
        with transaction.atomic():
            Vote.objects.create(
                user=self.alice, poll=self.poll, choice=self.c2
            )

    # 4) 表里始终只有一行
    self.assertEqual(
        Vote.objects.filter(user=self.alice, poll=self.poll).count(), 1
    )
```

裹一层 `transaction.atomic()` 是因为 `TestCase` 把每个 test method 包在事务里，一旦 `IntegrityError` 触发外层事务就坏了。内层 savepoint 被回滚之后，外层还能继续跑后续断言。

## 测试 2：注册表单写入用户表（Form ↔ User table）

**集成的组件**：
- `accounts.views.create_user` view（已经在 R6 里瘦身到 12 行）
- `accounts.forms.UserRegistrationForm`，包含 `clean_username` / `clean_email` / `clean` / `save`
- Django auth 的 `User.objects.create_user`
- SQLite 上的 `auth_user` 表

**如果没集成好会怎样**：
- 如果 form 的 `save()` 实际不调用 `User.objects.create_user`（比如有人改成 `User.objects.create(...)` 漏了密码 hash），表会有用户但是密码字段是裸文本，登录全挂
- 如果 `clean_username` 的查重逻辑只在 form 层挡但 view 里没正确处理 form invalid（提前 redirect 之类），同一个用户名能反复刷出错误 message 却不创建新行——但前提是 form 真的能挡，集成测试要确认这个挡的链路完整
- 测试一上来先看"提交合法数据 → 数据库真的多一行"，再看"重复用户名 → 数据库行数不变 + form 有错"

**测试逻辑**：

```python
def test_form_creates_user_row_and_rejects_duplicate_username(self):
    # 提交合法数据 -> form.save() -> User.objects.create_user() -> 一行写入
    r1 = self.client.post(self.URL, {
        "username": "alicia",
        "email": "alicia@example.com",
        "password1": "secret",
        "password2": "secret",
    })
    self.assertEqual(r1.status_code, 302)
    self.assertTrue(User.objects.filter(username="alicia").exists())

    # 用同样 username 再提交一次 -> 行数不变, form 抛 username 错误
    before = User.objects.count()
    r2 = self.client.post(self.URL, {
        "username": "alicia",
        "email": "someone-else@example.com",
        "password1": "secret",
        "password2": "secret",
    })
    self.assertEqual(r2.status_code, 200)
    self.assertEqual(User.objects.count(), before)
    self.assertIn(
        "Username already exists!",
        r2.context["form"].errors["username"],
    )
```

第二次提交特意把 email 换成新的——这样能确保拦下 form 的是 username 的查重，而不是 email 的查重。两个 clean_* 方法是分开的，测试要打到的是 username 那条路径。

## 跟单测的区别

Q3 用 fake/stub/mock 把 Choice/User/RNG 全替换掉，跑出来 0.002 秒；Q7 跑真 ORM 真 DB 跑出来 0.15 秒（差 75 倍）。但 Q3 测的是"我写的算法逻辑对不对"，Q7 测的是"我写的逻辑接到 Django/数据库上之后还工作不工作"——这两件事都得测，谁也替代不了谁。

## 跑通截图

```
$ python manage.py test qa_tests.test_integration -v 2
...
test_second_vote_attempt_blocked_and_db_rejects_raw_duplicate ... ok
test_form_creates_user_row_and_rejects_duplicate_username ... ok

----------------------------------------------------------------------
Ran 2 tests in 0.150s

OK
```

截图存到 `screenshots/q7_integration_passing.png`。
