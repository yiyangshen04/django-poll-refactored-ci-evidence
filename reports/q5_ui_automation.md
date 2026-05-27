# Q5 Web UI Automation

用 Playwright (Python 绑定) + pytest + pytest-django 写了 5 个端到端 UI 测试，跑真浏览器（Chromium headless）+ 真 Django dev server（pytest-django 的 `live_server` fixture）。

## 跑法

```
pytest qa_tests/ui/
```

要看浏览器加 `--headed`：

```
pytest qa_tests/ui/ --headed --slowmo 300
```

跑过的样子：

![pytest 输出](../screenshots/q5_pytest_run.png)

5 个测试 3.84 秒跑完。

## 目录与配置

```
qa_tests/
└── ui/
    ├── __init__.py
    ├── conftest.py
    ├── test_register_then_login.py
    ├── test_create_poll.py
    ├── test_vote_increments_count.py
    ├── test_double_vote_blocked.py
    └── test_owner_deletes_choice.py
```

pytest 配置在 [`pyproject.toml`](../pyproject.toml) 里：

```toml
[tool.pytest.ini_options]
DJANGO_SETTINGS_MODULE = "pollme.settings"
python_files = ["test_*.py"]
testpaths = ["qa_tests"]
```

[`conftest.py`](../qa_tests/ui/conftest.py) 顶上设了 `DJANGO_ALLOW_ASYNC_UNSAFE=true`，这是 Playwright sync API + Django ORM 同时用必须的环境变量（Playwright 在 asyncio loop 里跑 sync wrapper，Django 检测到 async context 会拒绝 sync ORM 调用）。conftest 里另外给了三个 fixture：

- `alice` — 一个有 `polls.add_poll` 权限的预设用户
- `sample_poll` — 一个 alice 拥有的 poll，含 Python / JavaScript 两个选项
- `screenshot_dir` — `screenshots/q5_ui/` 路径，5 个测试各存一张到这里

外加一个普通函数 `login_via_ui(page, base, username, password)`，走真实的 `/accounts/login/` 表单登录，被 4 个需要登录态的测试复用。

## 5 个测试

### Test 1：`test_register_then_login.py`

**测什么**：注册新账号 → 重定向到 login → 用新账号登录 → navbar 出现 Logout。完整跑通 [register → login → 已登录] 状态机。

**关键断言**：
```python
expect(page).to_have_url(f"{base}/accounts/login/")
...
expect(page.get_by_role("link", name="Logout")).to_be_visible()
```

截图：`screenshots/q5_ui/01_register_then_login.png`

### Test 2：`test_create_poll.py`

**测什么**：登录后访问 `/polls/add/`，填 text + 两个 choice，提交。跳到 list 后能看到新 poll 的文字。

**关键操作**：
```python
page.locator("textarea[name='text']").fill("Best language?")
page.locator("input[name='choice1']").fill("Python")
page.locator("input[name='choice2']").fill("JavaScript")
page.locator("button:has-text('Add Poll')").click()
```

注意 `text` 字段是 `Textarea` widget，所以 selector 用 `textarea[name='text']` 而不是 `input`。

截图：`screenshots/q5_ui/02_create_poll.png`

### Test 3：`test_vote_increments_count.py`

**测什么**：进 poll detail，选第一个 choice，submit。结果页应该显示 "Total: 1 votes"。

**关键断言**：
```python
expect(page.get_by_text(f"Result for: {sample_poll.text}")).to_be_visible()
expect(page.get_by_text("Total: 1 votes")).to_be_visible()
```

截图：`screenshots/q5_ui/03_vote_result.png`

![vote 结果页](../screenshots/q5_ui/03_vote_result.png)

### Test 4：`test_double_vote_blocked.py`

**测什么**：DB 里先种一条 Vote（alice 投过 Python），然后从 UI 再去 vote 一次 → 期望被 view 层拦下，重定向到 list，flash "You already voted this poll!"。

**setup 直接 ORM 种数据**：
```python
Vote.objects.create(user=alice, poll=sample_poll, choice=first_choice)
```

这种"ORM 种状态 + UI 跑业务"的混合模式比"UI 投一次再 UI 投一次"快很多——测试焦点是"第二次会不会被挡"，第一次怎么进来的不重要。

截图：`screenshots/q5_ui/04_double_vote_blocked.png`

### Test 5：`test_owner_deletes_choice.py`

**测什么**：作为 poll owner 进 edit 页，删一个 choice，edit 页 choice 列表条目数从 2 减到 1。

**关键断言**：
```python
expect(page.locator(".choices li.list-group-item")).to_have_count(2)
... 删了一个 choice
expect(page.locator(".choices li.list-group-item")).to_have_count(1)
expect(page.get_by_text("Choice Deleted successfully.")).to_be_visible()
```

这里 delete 是 view 的 URL `/polls/delete/choice/<id>/` 直接 GET 触发（poll_edit.html 里就是用 `<a href>` 没专门 form），所以测试是 `page.goto(delete_url)` 然后断言。

截图：`screenshots/q5_ui/05_owner_deletes_choice.png`

## 截图清单

| 测试 | 浏览器截图 |
|---|---|
| 1 | `screenshots/q5_ui/01_register_then_login.png` |
| 2 | `screenshots/q5_ui/02_create_poll.png` |
| 3 | `screenshots/q5_ui/03_vote_result.png` |
| 4 | `screenshots/q5_ui/04_double_vote_blocked.png` |
| 5 | `screenshots/q5_ui/05_owner_deletes_choice.png` |

5 张都是 Playwright 在测试最后通过 `page.screenshot(path=...)` 自动存的，分辨率 1280×800。

## 几个踩过的坑

1. **`SynchronousOnlyOperation` 错误**：Playwright sync API 在 asyncio 上下文里跑，Django ORM 默认拒绝 sync 调用。解决：conftest.py 顶上 `os.environ.setdefault("DJANGO_ALLOW_ASYNC_UNSAFE", "true")`。这个 env 必须在 Django 任何 ORM import 触发前就被设上，所以放在 conftest.py 模块最顶。

2. **`text` 字段不是 `<input>` 是 `<textarea>`**：PollAddForm 里 text widget 是 `forms.Textarea`，原本以为是 input 一直定位不到，看了 template 才发现要用 `textarea[name='text']`。

3. **`polls.add_poll` 权限**：`polls_add` view 里有 `if request.user.has_perm('polls.add_poll'):`，光 `User.objects.create_user` 出来的用户没这个权限，会被 403 一样的 "Sorry but you don't have permission" 拦下。在 alice fixture 里手动 `user.user_permissions.add(perm)`。
