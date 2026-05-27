# Q6 Smoke Test Plan

## 1. Objective

Smoke passing 对这个 app 意味着：**最近一次 build 在最常用路径上没有把核心功能搞挂**，可以放心进入更深一层的回归测试。具体来说，下面 6 条用户必经路径必须都跑得通：

1. 任何人能打开首页
2. 已注册用户能正常登录
3. 登录后能看到 poll 列表
4. 能从列表进 poll 并投票成功
5. 新用户能完成注册
6. 用户能退出登录

只要有一条挂了，这次 build 就不允许进下一轮测试，直接打回让开发先修。

## 2. Scope and Coverage

**In scope**：
- 用户认证（注册 / 登录 / 退出）
- Poll 列表浏览
- 单次投票流程
- 静态首页

**Out of scope**（不在 smoke 里跑）：
- Poll CRUD（add / edit / delete）
- Choice CRUD（add / edit / delete）
- 搜索、排序、分页
- 结果页百分比计算细节
- "Already voted" 拦截逻辑
- 权限边界（owner-only 编辑）
- UI 在不同分辨率 / 浏览器下的兼容性
- 性能 / 负载

理由：smoke 只挡"build 是不是死了"，不挡"功能是不是完美"。CRUD 和边界条件是 regression 测试要覆盖的事，不该让 smoke 跑 30 分钟。

## 3. Approach

**Hybrid，4 个自动 + 2 个 manual**：

| 类别 | 用例 | 工具 |
|---|---|---|
| 自动 | Home 200、Vote、Register、Logout（其中 3 个复用 Q5 Playwright spec） | Playwright + pytest-django |
| Manual | Login、Poll list 渲染 | 浏览器 + checklist |

理由：自动测试在 CI 里 4 秒跑完，是常态；剩下两个用人眼复核的，因为它们涉及 navbar 状态切换 / 列表布局这种 selector 容易飘的视觉确认，与其写脆的 selector 不如 30 秒看一眼。

## 4. Test Cases

| ID | 类别 | 用例 | Steps | Expected | Pass / Fail 标准 |
|---|---|---|---|---|---|
| SMK-01 | auto | Home page 200 | `GET /` | 状态码 200，页面渲染 navbar + "PollMe" 标题 | HTTP 200 且 navbar 元素 visible |
| SMK-02 | manual | Login | 1) `/accounts/login/` 2) 填 seeded 用户名密码 3) 点 Login | 跳到 `/`，navbar 显示 Logout | 操作 < 5 秒完成，无 5xx |
| SMK-03 | manual | Poll list 渲染 | 1) 登录后访问 `/polls/list/` 2) 目测 | 列表至少 1 个 poll 条目，"Add" 按钮可见，分页 footer 渲染 | 列表条目数 ≥ 1，按钮 visible |
| SMK-04 | auto | Vote 流程 | 1) 登录 2) 进 poll detail 3) 选 choice 4) Submit | 跳到结果页，"Total: 1 votes" 可见，DB Vote 表 +1 | 结果页 visible，Vote count == 1 |
| SMK-05 | auto | Register 新用户 | 1) `/accounts/register/` 2) 填合法表单 3) Submit | 跳 `/accounts/login/`，DB User 表 +1 | 重定向命中 login，User row 存在 |
| SMK-06 | auto | Logout | 1) 登录态下点 navbar 的 Logout | 跳到 `/`，navbar 改成 Login / Register | navbar Login 链接 visible |

6 个用例，4 auto 全部能复用 Q5 的 Playwright spec（test_register_then_login 拆成 SMK-05 + SMK-02、test_vote_increments_count 对应 SMK-04、加一个新的 logout spec 对应 SMK-06，再加一个 home_200 简单测对应 SMK-01）。

## 5. Test Deliverables

每次 smoke 跑完会产出：

1. **pytest 终端输出**（含每个 spec 的 PASS/FAIL）—— stdout 留档
2. **JUnit XML 报告**（`pytest --junitxml=reports/smoke.xml`）—— CI 解析用
3. **Playwright 自动截图**（失败时自动留 trace 到 `test-results/`）
4. **Manual checklist 填表结果**（SMK-02 / SMK-03 两项的执行人 + 时间戳 + Pass/Fail）
5. **缺陷单**（任何一项 Fail 时立即开）

## 6. Environment and Resources

**运行环境**：
- 与 CI 一致：Python 3.13、Django 4.2.x、SQLite（in-memory test DB）
- Playwright 用 Chromium headless
- Smoke 不连真生产数据库；用 pytest-django 的 `live_server` fixture 起独立测试 server

**测试数据**（每次 smoke 前 seed）：
- 1 个 staff 用户（用于 manual login 的种子账号）
- 1 个普通注册用户（用于 SMK-04 投票流程）
- 1 个 active poll，3 个 choice
- 这套 seed 写在 `qa_tests/ui/conftest.py` 的 fixture 里，启动测试自动建

**机器要求**：
- 任何能跑 Django + Chromium 的开发机 / CI runner
- 内存 ≥ 1 GB
- 不需要外网（除非要装依赖）

## 7. Schedule and Entry / Exit Criteria

**何时跑**：
- 每次 `git push` 到 main 分支（GitHub Actions ci.yml 自动触发，参见 Q9）
- 每次 PR 合并前（PR 触发同一 workflow）
- Release branch 切出来之前手动跑一遍
- 任何重大依赖升级后（如 Django 主版本升级）

**Entry criteria（开始跑之前必须满足）**：
- 代码已通过 ruff lint（Q1 工件）
- 项目能 `pip install -r requirements.txt` 成功
- `python manage.py migrate` 没错
- Dev server 在 `http://127.0.0.1:8000/` 能正常起

**Exit criteria（smoke 通过的判定）**：
- 6 个用例全部 Pass
- pytest 退出码 = 0
- manual checklist 两项都打 Pass

任何一项不满足 → smoke fail → build 不进下游测试 → 通知开发。

## 8. Risks and Contingency Plans

| Risk | 影响 | 应对 |
|---|---|---|
| Dev server 起不来（端口冲突 / migrate 报错） | 全部 auto 用例直接失败但不是真问题 | pre-run 健康检查脚本：`curl http://127.0.0.1:8000/` 拿到 200 才继续，否则跳过 auto 并告警 |
| Chromium 没装好 / Playwright 浏览器掉了 | auto 报错信息看起来像 app bug 实则是环境问题 | CI 加一步 `playwright install --with-deps chromium` 缓存；本地 README 写清 |
| Manual 步骤被遗漏 / 拖延 | smoke 整体延期，团队等不及合并 | checklist 进 Slack 提醒模板，每条都要在 PR comment 里 ✅ 才放行 |
| Smoke 测试本身坏掉（spec 自己有 bug） | False fail 卡住整条 pipeline | 任何 smoke 修改都要 PR review，不允许直接 push 到 main |
| 假 negative（network flake、JS 加载慢） | 偶发失败 → 信任度下降 | 失败时手动 re-run 一次；累计三次同样位置失败再判定真挂了 |
| 没人 review manual checklist 结果 | manual 形同虚设 | 把 manual 结果存到带签名的 Google Form / GitHub Issue 模板，留 audit trail |

**Contingency when smoke fails**：

1. 立刻在 GitHub 上把该 commit 标 `smoke-fail` label
2. 通知开发当事人 + QA on-call
3. 不准合任何依赖此 commit 的 PR
4. 走 hotfix 流程修，修完重跑同一个 smoke
5. 如果是测试本身的 bug，由 QA 自己提 PR 修测试

---

## 备注：这份 plan 没要求执行

按作业要求，Q6 只交计划，不交执行结果。如果要做真的 dry run 演练，按上面 §3 的工具栈 `pytest qa_tests/smoke/` 就行（spec 文件可以从 Q5 spec 直接复用 4 个）。
