# Q2 User Acceptance Testing

## 10 个 user story

| ID | User story |
|---|---|
| US-01 | As a guest, I want to register so I can vote on polls. |
| US-02 | As a registered user, I want to log in so I can access poll features. |
| US-03 | As a logged-in user, I want to log out so my session is cleared. |
| US-04 | As a user with poll-add permission, I want to create a poll with at least two choices. |
| US-05 | As a poll owner, I want to edit the poll text. |
| US-06 | As a poll owner, I want to add, edit, and delete choices on my poll. |
| US-07 | As a logged-in user, I want to vote on an active poll exactly once. |
| US-08 | As any user, I want to see live results with vote count and percentage for each choice. |
| US-09 | As any user, I want to browse / search / sort polls so I can find one to vote on. |
| US-10 | As a poll owner, I want to end my poll so no further votes can be cast. |

## Given-When-Then 验收条件

**US-01 Register**

- Given 我没登陆
- When 我提交 5-100 字符的 username、合法 email、相同密码两次
- Then 系统创建用户，跳转 `/accounts/login/`，flash 一条 `Thanks for registering <username>.`

**US-02 Login**

- Given 我已注册
- When 我用正确账号密码 POST 到 `/accounts/login/`
- Then 我被重定向到 `next` 参数指定页（默认 `home`），navbar 显示 Logout

**US-03 Logout**

- Given 我已登录
- When 我点 navbar 的 Logout
- Then session 清空，跳回 `/`，navbar 重新显示 Login / Register

**US-04 Create poll**

- Given 我已登录且具有 `polls.add_poll` 权限
- When 我提交 poll text + choice1 + choice2 都非空的表单
- Then 创建一个 Poll + 两个 Choice，跳转 `/polls/list/`，新 poll 出现在列表

**US-05 Edit poll**

- Given 我是 poll 的 owner
- When 我提交修改后的 text
- Then 列表与详情页都显示新文字

**US-06 Manage choices**

- Given 我是 poll 的 owner
- When 我点 Add Choice / 编辑某个 choice / 删除某个 choice
- Then 编辑页 choice 列表数量随之 +1 / 不变 / -1

**US-07 Vote once**

- Given 一个 poll 是 active 状态，我没投过
- When 我在详情页选一个 choice 提交
- Then Vote 行被写入数据库，结果页对应 choice 的 num_votes +1。再次投票会被拦下并显示 `You already voted this poll!`

**US-08 View results**

- Given 一个 poll 有 ≥1 票
- When 我访问该 poll 的结果页
- Then 每个 choice 显示其票数和百分比；总数为 0 时所有 choice 百分比都是 0

**US-09 Browse / search / sort**

- Given 至少有 7 个 poll（触发分页）
- When 我用 query string `?name` / `?date` / `?vote` / `?search=xxx`
- Then 列表按对应字段排序或按关键字过滤；分页保持

**US-10 End poll**

- Given 我是 poll 的 owner，poll 是 active
- When 我访问 `/polls/end/<id>/`
- Then `poll.active=False`，详情页此后只渲染 result 模板（vote form 消失）

## 4 种黑盒技术 + 用来推哪些 case

| Technique | 应用场景 | 派生的测试用例 |
|---|---|---|
| Equivalence Partitioning (EP) | username 长度划分（<5 / 5-100 / >100）、poll 创建输入是否合法 | UAT-001, UAT-002, UAT-015 |
| Boundary Value Analysis (BVA) | username 的 4/5/100/101 四个边界点 | UAT-003, UAT-004, UAT-005, UAT-006 |
| State Transition (ST) | logged_out→logged_in→logged_out、not_voted→voted、active→ended 三条状态机 | UAT-011, UAT-012, UAT-014 |
| Decision Table (DT) | 注册三条件（密码匹配 × username 唯一 × email 唯一）的真值表 + 投票决策（active × already-voted） | UAT-007, UAT-008, UAT-009, UAT-010, UAT-013 |

15 条用例 / 4 种技术分布：EP 3 条，BVA 4 条，ST 3 条，DT 5 条。

## UAT 测试用例（15 条骨架）

完整字段（含 description、preconditions、steps、expected、actual、pass/fail）在 [`uat/uat_test_cases.xlsx`](../uat/uat_test_cases.xlsx)。下面是摘要表。Actual / Pass-Fail 列会在手动跑完之后填入。

| ID | Name | Story | Technique | Expected |
|---|---|---|---|---|
| UAT-001 | Register with valid mid-range username | US-01 | Equivalence Partitioning | Redirect to login, success message |
| UAT-002 | Register with too-short username | US-01 | Equivalence Partitioning | Form rejects, no User row |
| UAT-003 | Register username = 4 chars | US-01 | Boundary Value Analysis | Form rejects (min_length) |
| UAT-004 | Register username = 5 chars | US-01 | Boundary Value Analysis | Registration succeeds |
| UAT-005 | Register username = 100 chars | US-01 | Boundary Value Analysis | Registration succeeds |
| UAT-006 | Register username = 101 chars | US-01 | Boundary Value Analysis | Form rejects (max_length) |
| UAT-007 | Register all-valid (DT happy path) | US-01 | Decision Table | User created, redirect to login |
| UAT-008 | Register duplicate username | US-01 | Decision Table | Form rejects with 'Username already exists!' |
| UAT-009 | Register duplicate email | US-01 | Decision Table | Form rejects with 'Email already registered!' |
| UAT-010 | Register password mismatch | US-01 | Decision Table | Form rejects with 'Password did not match!' |
| UAT-011 | Login then logout transitions state | US-02, US-03 | State Transition | Navbar reflects all 3 states correctly |
| UAT-012 | Cast first vote on active poll | US-07 | State Transition | Vote recorded, results page updated |
| UAT-013 | Block second vote attempt | US-07 | Decision Table | Redirect to list with warning, no new Vote row |
| UAT-014 | End an active poll | US-10 | State Transition | poll.active=False, result template renders |
| UAT-015 | Create poll with two choices | US-04 | Equivalence Partitioning | Redirect to list, new poll visible |

## 注册决策表（UAT-007 ~ UAT-010 的依据）

| Condition | UAT-007 | UAT-008 | UAT-009 | UAT-010 |
|---|---|---|---|---|
| Password match | T | T | T | F |
| Username unique | T | F | T | (任意) |
| Email unique | T | T | F | (任意) |
| Action | Create user, redirect login | Reject: username exists | Reject: email exists | Reject: password mismatch |

## 投票决策表（UAT-012 / UAT-013 的依据）

| Condition | UAT-012 | UAT-013 |
|---|---|---|
| Poll active | T | T |
| Already voted | F | T |
| Action | Allow vote, render result | Block, redirect with warning |

## 状态机图（UAT-011 / UAT-014 的依据）

Auth 状态机（US-02, US-03）：

```
logged_out --(submit valid creds)--> logged_in
logged_in  --(click logout)-------> logged_out
```

Poll 状态机（US-07, US-10）：

```
                  +-- (vote) --> voted
active (poll)----+
                  +-- (owner end_poll) --> ended (no more votes accepted)
```

## 数据源与生成

UAT 用例的数据写在 [`uat/uat_data.py`](../uat/uat_data.py)，单一来源。运行：

```
python uat/generate.py
```

会重新输出 [`uat/uat_test_cases.xlsx`](../uat/uat_test_cases.xlsx)，包含两个 sheet：Test Cases（15 行）和 User Stories（10 行）。修改测试用例时改 `uat_data.py` 即可，不要直接动 xlsx。

## 执行记录（待补）

15 条用例会按上面顺序手动跑一遍。每跑完一条：

1. 在浏览器 / Django dev server 上完成 Steps
2. 截图（保存到 `screenshots/uat/UAT-XXX.png`）
3. 在 `uat_data.py` 里填 `actual` 和 `result` 字段
4. 重跑 `python uat/generate.py` 同步到 xlsx
