# Q3 Unit Tests

## 工具

- Django 自带 test runner（`python manage.py test`）跑测试
- `coverage` 测覆盖率，HTML 报告输出到 `reports/htmlcov/`
- `unittest.mock` 做 mock
- 自己写的 stub / fake / spy 类，集中在 [`qa_tests/test_unit.py`](../qa_tests/test_unit.py) 顶部

测试文件结构：

```
qa_tests/
├── __init__.py
└── test_unit.py
```

写在 `qa_tests/` 而不是 `polls/tests.py` 或 `accounts/tests.py` 是为了不污染上游本来就在的 4 个测试。

## 跑测试

```
python manage.py test qa_tests.test_unit -v 2
```

跑 coverage：

```
coverage run --source=polls,accounts manage.py test qa_tests.test_unit
coverage report          # 终端摘要
coverage html -d reports/htmlcov  # HTML 报告
```

## 9 个测试一览

| # | 测试方法 | 测什么 | 是否用 double | Double 类型 |
|---|---|---|---|---|
| 1 | `test_percentages_match_vote_distribution` | `compute_poll_results` 算出来的票数百分比 | 是 | Fake |
| 2 | `test_zero_total_votes_returns_zero_percentage` | 总票数为 0 时百分比都返回 0（边界） | 是 | Fake |
| 3 | `test_uses_injected_rng_for_each_result` | `attach_alert_classes` 用注入的 rng 配色 | 是 | Stub |
| 4 | `test_clean_username_rejects_duplicate` | `UserRegistrationForm.clean_username` 查重失败 | 是 | Mock |
| 5 | `test_filters_vote_set_by_poll` | `Poll.user_can_vote` 调用 user.vote_set 的方式 | 是 | Spy |
| 6 | `test_password_mismatch_attaches_error_to_password2` | 注册表单两次密码不一致 | 否 | — |
| 7 | `test_poll_str_returns_text` | `Poll.__str__` | 否 | — |
| 8 | `test_choice_str_truncates_poll_and_choice_text_to_25` | `Choice.__str__` 25 字符截断 | 否 | — |
| 9 | `test_vote_str_format` | `Vote.__str__` 拼接格式 | 否 | — |

9 个测试，5 个用 double，4 种类型（fake / stub / mock / spy），满足作业要求（≥8 测试，≥4 用 double，≥3 种类型）。

## 每个 Double 测试的 4 元组

### 测试 1 + 2：`ComputePollResultsTests` — **Fake**

- **类型**：Fake
- **替代的真实依赖**：Django ORM 返回的 Poll/Choice 模型实例以及 `poll.choice_set.all()` 这个 reverse manager（`RelatedManager.all()`）
- **为什么用 Fake**：`compute_poll_results` 的逻辑是纯算术（票数除以总数乘 100），但参数 `poll` 是 Django model 对象，构造它要么走 ORM（hit DB），要么 stub 一堆属性。手写 `FakePoll`/`FakeChoiceSet`/`FakeChoice` 三个小类实现"choice_set.all() 返回 list + .get_vote_count 直接返回 int"这个最小契约，比 mock 整套 manager 简单得多
- **如何隔离**：测试里完全不 import `Poll` 模型，也不 touch DB。被测的 `compute_poll_results` 不知道它拿到的是真 Poll 还是 FakePoll，只要响应 `get_vote_count` 和 `choice_set.all()` 就行。

### 测试 3：`AttachAlertClassesTests` — **Stub**

- **类型**：Stub
- **替代的真实依赖**：`random.Random` 实例的 `.choice(seq)` 方法（默认 `attach_alert_classes` 没传 rng 时会 new 一个新的 `random.Random()`）
- **为什么用 Stub**：随机源会让"alert_class 等于什么"在每次跑都不一样，测试根本写不出确定的断言。Stub 强行让 `.choice(seq)` 永远返回固定值，断言才能写死
- **如何隔离**：通过依赖注入。`attach_alert_classes(results, rng=stub)` 把 stub 当 rng 传进去，被测函数内部用 `rng.choice(classes)`，不知道也不关心拿到的是真 `random.Random` 还是 StubRNG。这种"把外部不可控依赖通过参数传进去"的 seam 是 R1 重构时专门留的。

### 测试 4：`CleanUsernameTests` — **Mock**

- **类型**：Mock
- **替代的真实依赖**：`User.objects`（QuerySet manager）的 `.filter(...).exists()` 调用链
- **为什么用 Mock**：跑这个测试不想建用户、也不想搭测试数据库。同时还要验证 `clean_username` 调用 `filter` 时**确实把 `username='alice'` 传进去了**（不是 email 或者别的字段）。Mock 既能让 `.exists()` 返回 True 触发 ValidationError，又能用 `assert_called_once_with(username='alice')` 反向断言调用参数
- **如何隔离**：`@patch("accounts.forms.User.objects")` 替换的是 forms.py 模块里的 `User.objects` 符号，所以 clean_username 内部 `User.objects.filter(...)` 拿到的是 Mock 对象。测试不依赖任何真实 User 记录，跑得快也不会污染数据库。

### 测试 5：`UserCanVoteTests` — **Spy**

- **类型**：Spy
- **替代的真实依赖**：传入 `Poll.user_can_vote(user)` 的 `user` 对象上的 `vote_set` reverse manager（`user.vote_set.all().filter(poll=...).exists()` 这一串）
- **为什么用 Spy**：除了想让 `.exists()` 返回 False（这点 mock/stub 也能做），还想**确认**被测函数确实调用了 `user.vote_set.all()` 又调用了 `.filter(poll=self)` 而不是其它字段。Spy 在这上面比 Mock 强：可以记录调用参数列表，测试结束后回查"call history"
- **如何隔离**：`SpyVoteSet` 实现了 `all()`、`filter(**kwargs)`、`exists()` 三个方法，都返回 self（可链式调用），同时把 `filter_calls` 收到一个 list。测试断言 `spy_vote_set.filter_calls == [{"poll": poll}]` 等于把"被测代码内部用什么参数访问数据库"这件事变成了可观测事实。完全不动 DB，poll 也只是 `Poll(id=1, text='t')` 构造但没 save。

## Coverage 摘要

跑完 9 个测试后的覆盖率（完整文本在 [`reports/q3_coverage_report.txt`](q3_coverage_report.txt)，HTML 在 [`reports/htmlcov/`](htmlcov/index.html)）：

```
Name                                             Stmts   Miss  Cover
--------------------------------------------------------------------
accounts/forms.py                                   27      2    93%
accounts/views.py                                   29     21    28%
polls/forms.py                                      19      0   100%
polls/models.py                                     43      4    91%
polls/services.py                                   17      1    94%
polls/views.py                                     148    118    20%
--------------------------------------------------------------------
TOTAL                                              364    172    53%
```

总覆盖率 53%。三个被单测重点覆盖的模块（service / model / form）都在 90% 以上：

- `polls/services.py` 17 行 → 94%（只漏一行 `random.Random()` 默认实例化分支）
- `polls/models.py` 43 行 → 91%（剩下没覆盖的是 `get_vote_count` 这种属性 + `__str__` 的极端分支）
- `accounts/forms.py` 27 行 → 93%

View 的覆盖率低（polls 20% / accounts 28%）是预期之内：单元测试故意不打 HTTP，留给 Q5（Playwright E2E）和 Q7（集成测试）覆盖。

要看 line-by-line 详情：

```
open reports/htmlcov/polls_services_py.html
open reports/htmlcov/polls_models_py.html
open reports/htmlcov/accounts_forms_py.html
```

## 测试运行截图

跑通的截图（终端）：

```
$ python manage.py test qa_tests.test_unit -v 2
...
test_password_mismatch_attaches_error_to_password2 ... ok
test_uses_injected_rng_for_each_result ... ok
test_clean_username_rejects_duplicate ... ok
test_percentages_match_vote_distribution ... ok
test_zero_total_votes_returns_zero_percentage ... ok
test_choice_str_truncates_poll_and_choice_text_to_25 ... ok
test_poll_str_returns_text ... ok
test_vote_str_format ... ok
test_filters_vote_set_by_poll ... ok

----------------------------------------------------------------------
Ran 9 tests in 0.002s

OK
```

把上面跑出来截图、coverage HTML 报告首页截图，分别存到 `screenshots/q3_tests_passing.png` 和 `screenshots/q3_coverage_html.png` 即可。
