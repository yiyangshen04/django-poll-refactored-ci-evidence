# Django Poll App — SQA Assignment

基于 [devmahmud/Django-Poll-App](https://github.com/devmahmud/Django-Poll-App) 做的 QA 作业。重构了几处可测性问题，写了完整的测试体系：lint、单测、集成测、UI 自动化、性能测试，外加 CI/CD pipeline。

## 跑起来

```bash
# 1) 创建 venv 装依赖
uv venv .venv
source .venv/bin/activate
uv pip install -r requirements.txt ruff coverage pytest pytest-django pytest-playwright openpyxl Pillow
playwright install chromium

# 2) DB
python manage.py migrate

# 3) 起 dev server (可选)
python manage.py runserver
```

## 跑测试

| 想跑啥 | 命令 |
|---|---|
| ruff lint | `ruff check .` |
| 单元测试 | `python manage.py test qa_tests.test_unit` |
| 集成测试 | `python manage.py test qa_tests.test_integration` |
| Playwright UI | `pytest qa_tests/ui/` |
| Coverage | `coverage run --source=polls,accounts manage.py test qa_tests.test_unit && coverage report` |
| k6 perf | 先起 dev server，然后 `k6 run performance/load.js` |
| 一次跑全部 (Q3 + Q7) | `python manage.py test qa_tests` |

## 作业产物索引

每道题独立 writeup 在 `reports/`：

| 题 | Writeup | 主要工件 |
|---|---|---|
| Q1 Linter | [q1_lint.md](reports/q1_lint.md) | [pyproject.toml](pyproject.toml), [q1_ruff_full_output.txt](reports/q1_ruff_full_output.txt) |
| Q2 UAT | [q2_uat.md](reports/q2_uat.md) | [uat/uat_test_cases.xlsx](uat/uat_test_cases.xlsx), [uat/uat_data.py](uat/uat_data.py) |
| Q3 Unit tests | [q3_unit_tests.md](reports/q3_unit_tests.md) | [qa_tests/test_unit.py](qa_tests/test_unit.py), [htmlcov/](reports/htmlcov/index.html) |
| Q4 Performance | [q4_performance.md](reports/q4_performance.md) | [performance/load.js](performance/load.js), [performance/stress.js](performance/stress.js) |
| Q5 UI Auto | [q5_ui_automation.md](reports/q5_ui_automation.md) | [qa_tests/ui/](qa_tests/ui/) + 5 张 Playwright 截图 |
| Q6 Smoke Plan | [q6_smoke_plan.md](reports/q6_smoke_plan.md) | (纯文档) |
| Q7 Integration | [q7_integration_tests.md](reports/q7_integration_tests.md) | [qa_tests/test_integration.py](qa_tests/test_integration.py) |
| Q8 Code Smells | [q8_smells.md](reports/q8_smells.md) | (纯 review，对应 R1/R4/R6 重构) |
| Q9 CI/CD | [q9_ci_cd.md](reports/q9_ci_cd.md) | [.github/workflows/ci.yml](.github/workflows/ci.yml) |

## 重构清单

四处为可测性做的重构，每条对应一个或多个题：

| ID | 文件 | 改了啥 | 服务哪几题 |
|---|---|---|---|
| R1 | `polls/models.py` + `polls/services.py` (新) | 拆 `get_result_dict` 为 `compute_poll_results` + `attach_alert_classes`，RNG 注入 | Q3 (stub/fake), Q8 (long method) |
| R3 | `polls/views.py` + `polls/migrations/0003_*` | 修 `poll_vote` 3 bug + 加 `Vote` UniqueConstraint | Q1 (lint), Q7 (DB constraint test) |
| R4 | `pollme/messages.py` (新) | 抽 `SUCCESS_TAGS` / `WARNING_TAGS` 公共常量 | Q8 (duplicated code) |
| R6 | `accounts/forms.py` + `accounts/views.py` | 注册校验从 view 搬到 Form.clean_* | Q3 (mock), Q8 (feature envy) |

## 测试数量

- **9 个单元测试**（其中 5 个用 test double：1 fake / 1 stub / 1 mock / 1 spy + 1 zero-vote 边界）
- **2 个集成测试**（view↔DB 投票去重 + form↔User 表注册）
- **5 个 Playwright UI 测试**（register/login/create/vote/double-vote/delete-choice）
- **2 个 k6 性能脚本**（load 50 VU 30s + stress 1→200 VU 60s）
- **15 个 UAT 测试用例**（覆盖 4 种黑盒技术，3+4+3+5 分布）
- **总自动化测试 16 个 + 手动 UAT 15 条**

## 目录结构

```
django_poll_refactored/
├── .github/workflows/ci.yml          # Q9
├── accounts/                          # 上游 + R6 重构
├── polls/                             # 上游 + R1 R3 重构
│   ├── services.py                    # R1 新增
│   └── migrations/0003_vote_unique_user_poll.py  # R3 新增
├── pollme/
│   └── messages.py                    # R4 新增
├── performance/
│   ├── load.js                        # Q4
│   └── stress.js                      # Q4
├── qa_tests/
│   ├── test_unit.py                   # Q3
│   ├── test_integration.py            # Q7
│   └── ui/                            # Q5
│       ├── conftest.py
│       └── test_*.py (5 个)
├── reports/                           # 所有 writeup
├── screenshots/                       # 所有截图
├── scripts/                           # 渲终端图的小工具
├── uat/
│   ├── uat_data.py                    # Q2 数据源
│   ├── generate.py                    # Q2 xlsx 生成器
│   └── uat_test_cases.xlsx            # Q2 主交付
└── pyproject.toml                     # ruff + pytest 配置
```

## CI/CD 演示流程

1. 创建 GitHub repo
2. `git remote add origin` + `git push -u origin main`
3. GitHub Actions 自动跑 → 因为 27 条 ruff finding 故意没修，**第一次跑会红**
4. `ruff check --fix .` + 手动修剩下几条 → push → **第二次跑会绿**
5. 各截一张图存到 `screenshots/q9_{red,green}_run.png`

详细步骤见 [reports/q9_ci_cd.md](reports/q9_ci_cd.md)。
