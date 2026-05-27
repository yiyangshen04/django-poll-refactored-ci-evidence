# Q9 CI/CD Pipeline

平台：**GitHub Actions**。配置在 [`.github/workflows/ci.yml`](../.github/workflows/ci.yml)，单 workflow 单 job，按作业要求把 Q1 / Q3 / Q4 / Q5 / Q7 全部跑一遍。

## Pipeline 步骤

| 顺序 | 步骤 | 对应作业题 | Fail 条件 |
|---|---|---|---|
| 1 | checkout + setup Python 3.12 + uv | 基础 | uv/Python 装不上 |
| 2 | 装项目 + dev 依赖 | 基础 | requirements 装不上 |
| 3 | `playwright install --with-deps chromium` | Q5 | 浏览器装不上 |
| 4 | `ruff check .` | **Q1** | 任何 lint warning |
| 5 | `python manage.py migrate` | 基础 | migration 报错 |
| 6 | `coverage run manage.py test qa_tests.test_unit` + `coverage report` | **Q3** | 任意 unit 测试失败 |
| 7 | `python manage.py test qa_tests.test_integration` | **Q7** | 集成测试失败 |
| 8 | `pytest qa_tests/ui/` | **Q5** | Playwright 测试失败 |
| 9 | 装 k6 + seed poll + 起 dev server | Q4 准备 | dev server 起不来 |
| 10 | `k6 run performance/load.js` | **Q4** | p95 > 500ms 或 p99 > 1000ms 或 error rate > 1% |

每一步任一 fail 整条 pipeline 红，符合"fail the build on … failures"的要求。

## Trigger

```yaml
on:
  push:
    branches: [main]
  pull_request:
```

- main 分支每次 push 触发
- 所有 PR 创建 / 更新触发

## Artifacts

两个 artifact 在每次 run 后可下载（即便 fail 也上传，方便诊断）：

| Artifact | 内容 |
|---|---|
| `coverage-html` | `reports/htmlcov/` 整套，含 line-by-line 覆盖率页面 |
| `playwright-screenshots` | `screenshots/q5_ui/` 5 张 |

## 怎么演示 1 绿 + 1 红

作业要求"trigger it at least two times: at least one passing run and at least one failing run"。最快的演示路径：

### 1. 准备 GitHub repo

在 GitHub 上 New repository → 取名（比如 `sqa-django-poll`）→ 不要勾任何初始化文件。然后在本地：

```bash
cd /Users/hanson/Desktop/sqa/django_poll_refactored
git remote add origin git@github.com:<你的用户名>/sqa-django-poll.git
git checkout -b main
git add .
git commit -m "init: refactor + tests + ci"
git push -u origin main
```

push 完，GitHub Actions 自动跑第一次 workflow。

### 2. 第一次：故意红一次

**当前 repo 状态本身就会失败 ruff 检查**（有 27 条 finding 故意留着），所以**第一次 push 直接就是 red run**。

GitHub Actions → 进 Actions tab → 看 workflow run → 找 "Ruff lint (Q1)" 步骤会显示红叉。截图存到 `screenshots/q9_red_run.png`。

### 3. 修一下，第二次：跑成绿

把 `reports/q1_lint.md` 提到的 5 个 finding 修掉（最快用 `ruff check --fix .` 自动改大部分，剩下 `if poll.active is True:` 手动改成 `if poll.active:`）。

```bash
ruff check --fix .          # 自动修 15 个可自动 fix 的
# 手动改 polls/views.py:217 把 `is True` 去掉
git add -A
git commit -m "fix: address ruff lint findings"
git push
```

GitHub Actions 重新触发，这次全绿。截图存到 `screenshots/q9_green_run.png`。

### 4. 截图清单

需要交两张：

| 文件名 | 内容 |
|---|---|
| `screenshots/q9_green_run.png` | Actions UI 显示绿勾 + 所有 step 绿 |
| `screenshots/q9_red_run.png` | Actions UI 显示 lint step 红叉，build fail |

## 本地复现

如果 push 之前想先本地验证 pipeline 各步骤能跑：

```bash
ruff check .
python manage.py migrate
coverage run --source=polls,accounts manage.py test qa_tests.test_unit
coverage report
python manage.py test qa_tests.test_integration
pytest qa_tests/ui/
python manage.py runserver 127.0.0.1:8000 --noreload &
sleep 3
k6 run performance/load.js
pkill -f runserver
```

跟 CI yml 里的命令逐步对应。任何一步本地失败，CI 也会失败。

## 没做的事 / Trade-offs

- **没拆 job 并行**：unit / integration / UI 都串在一个 job 里。拆开能更快但 yaml 复杂度上升；对学生项目这个 trade-off 不值。
- **没缓存 Playwright 浏览器**：每次 run 都重装 Chromium（~30 秒）。生产 pipeline 可以加 `actions/cache@v4` 缓存 `~/.cache/ms-playwright`。
- **没分 deploy stage**：作业范围只到 CI（test 自动化），CD 没要求所以没写部署到 staging / prod 的 step。
- **perf 在 CI 跑可能 flaky**：GitHub runner 的 CPU 资源有限，相同 50 VU 的 load 测试在不同 run 之间 p95 可能波动 ±50%。CI 阈值（p95<500ms）已经留了很宽容差，但偶尔 flake 也属正常。
