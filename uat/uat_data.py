"""Single source of truth for Q2 UAT test cases.

Both ``generate.py`` (xlsx export) and the writeup table are derived
from the lists below, so changing a step or expected result here updates
everywhere.
"""

USER_STORIES = [
    ("US-01", "As a guest, I want to register so I can vote on polls."),
    ("US-02", "As a registered user, I want to log in so I can access poll features."),
    ("US-03", "As a logged-in user, I want to log out so my session is cleared."),
    ("US-04", "As a user with poll-add permission, I want to create a poll with at least two choices."),
    ("US-05", "As a poll owner, I want to edit the poll text."),
    ("US-06", "As a poll owner, I want to add, edit, and delete choices on my poll."),
    ("US-07", "As a logged-in user, I want to vote on an active poll exactly once."),
    ("US-08", "As any user, I want to see live results with vote count and percentage for each choice."),
    ("US-09", "As any user, I want to browse / search / sort polls so I can find one to vote on."),
    ("US-10", "As a poll owner, I want to end my poll so no further votes can be cast."),
]


# Each test case is a dict with the fields the assignment requires.
# Actual Result and Pass/Fail are left empty (to be filled after manual run).
TEST_CASES = [
    {
        "id": "UAT-001",
        "name": "Register with valid mid-range username",
        "story": "US-01",
        "description": "Registration succeeds when username length is in the valid 5-100 char range and all other fields are valid.",
        "preconditions": "No existing user with this username/email.",
        "steps": (
            "1. Open /accounts/register/\n"
            "2. Username = 'alice123' (8 chars)\n"
            "3. Email = 'alice@example.com'\n"
            "4. Password = 'secret', Confirm = 'secret'\n"
            "5. Submit"
        ),
        "expected": "Redirect to /accounts/login/, success message 'Thanks for registering alice123.'",
        "actual": "Redirected to login and showed the registration success message.",
        "result": "Pass",
        "technique": "Equivalence Partitioning",
    },
    {
        "id": "UAT-002",
        "name": "Register with too-short username",
        "story": "US-01",
        "description": "Form rejects username under 5 characters.",
        "preconditions": "None.",
        "steps": (
            "1. Open /accounts/register/\n"
            "2. Username = 'ab' (2 chars)\n"
            "3. Other fields valid\n"
            "4. Submit"
        ),
        "expected": "Form re-renders with error 'Ensure this value has at least 5 characters'. No new User row.",
        "actual": "Register form stayed open and showed the minimum length error.",
        "result": "Pass",
        "technique": "Equivalence Partitioning",
    },
    {
        "id": "UAT-003",
        "name": "Register username = 4 chars (just below lower bound)",
        "story": "US-01",
        "description": "Boundary one below the min_length of 5.",
        "preconditions": "None.",
        "steps": "Submit register form with username = 'alic' (4 chars), rest valid.",
        "expected": "Form rejects with min_length error.",
        "actual": "Register form rejected the 4-character username.",
        "result": "Pass",
        "technique": "Boundary Value Analysis",
    },
    {
        "id": "UAT-004",
        "name": "Register username = 5 chars (lower bound)",
        "story": "US-01",
        "description": "Boundary at exact min_length.",
        "preconditions": "None.",
        "steps": "Submit register form with username = 'alice' (5 chars), rest valid.",
        "expected": "Registration succeeds.",
        "actual": "Registration succeeded for the 5-character username.",
        "result": "Pass",
        "technique": "Boundary Value Analysis",
    },
    {
        "id": "UAT-005",
        "name": "Register username = 100 chars (upper bound)",
        "story": "US-01",
        "description": "Boundary at exact max_length.",
        "preconditions": "None.",
        "steps": "Submit register form with username = 'a' * 100, rest valid.",
        "expected": "Registration succeeds.",
        "actual": "Registration succeeded for the 100-character username.",
        "result": "Pass",
        "technique": "Boundary Value Analysis",
    },
    {
        "id": "UAT-006",
        "name": "Register username = 101 chars (just above upper bound)",
        "story": "US-01",
        "description": "Boundary one above max_length.",
        "preconditions": "None.",
        "steps": "Submit register form with username = 'a' * 101, rest valid.",
        "expected": "Form rejects with max_length error.",
        "actual": "Register form rejected the 101-character username.",
        "result": "Pass",
        "technique": "Boundary Value Analysis",
    },
    {
        "id": "UAT-007",
        "name": "Register all-valid (DT row: pwd-match=T, user-unique=T, email-unique=T)",
        "story": "US-01",
        "description": "Decision table happy path: all three checks pass.",
        "preconditions": "No existing user with target username/email.",
        "steps": "Submit register form with valid unique data, matching passwords.",
        "expected": "User created, redirect to /accounts/login/.",
        "actual": "Unique username, email, and matching passwords created the user.",
        "result": "Pass",
        "technique": "Decision Table",
    },
    {
        "id": "UAT-008",
        "name": "Register duplicate username (DT row: pwd-match=T, user-unique=F, email-unique=T)",
        "story": "US-01",
        "description": "Decision table: username already exists triggers form error.",
        "preconditions": "User 'alice' already exists.",
        "steps": "Submit register form with username='alice', new email, matching passwords.",
        "expected": "Form rejects with 'Username already exists!'. No new User row.",
        "actual": "Duplicate username was rejected with the expected form error.",
        "result": "Pass",
        "technique": "Decision Table",
    },
    {
        "id": "UAT-009",
        "name": "Register duplicate email (DT row: pwd-match=T, user-unique=T, email-unique=F)",
        "story": "US-01",
        "description": "Decision table: email already registered triggers form error.",
        "preconditions": "A user with email 'alice@example.com' exists.",
        "steps": "Submit register form with new username, email='alice@example.com', matching passwords.",
        "expected": "Form rejects with 'Email already registered!'. No new User row.",
        "actual": "Duplicate email was rejected with the expected form error.",
        "result": "Pass",
        "technique": "Decision Table",
    },
    {
        "id": "UAT-010",
        "name": "Register password mismatch (DT row: pwd-match=F)",
        "story": "US-01",
        "description": "Decision table: passwords don't match short-circuits the whole flow.",
        "preconditions": "None.",
        "steps": "Submit register form with password='secret', confirm='different'.",
        "expected": "Form rejects with 'Password did not match!' attached to password2 field.",
        "actual": "Password mismatch was rejected on the confirmation field.",
        "result": "Pass",
        "technique": "Decision Table",
    },
    {
        "id": "UAT-011",
        "name": "Login then logout transitions state correctly",
        "story": "US-02, US-03",
        "description": "Auth state goes logged_out -> logged_in -> logged_out via the two flows.",
        "preconditions": "User 'alice' exists. Browser starts logged out.",
        "steps": (
            "1. Verify navbar shows 'Login' / 'Register' links.\n"
            "2. Go to /accounts/login/ and submit valid creds.\n"
            "3. Verify navbar now shows 'Logout' (state = logged_in).\n"
            "4. Click Logout.\n"
            "5. Verify navbar shows 'Login' / 'Register' again."
        ),
        "expected": "All three state checks pass; final state = logged_out.",
        "actual": "Navbar changed after login and returned to guest links after logout.",
        "result": "Pass",
        "technique": "State Transition",
    },
    {
        "id": "UAT-012",
        "name": "Cast first vote on active poll",
        "story": "US-07",
        "description": "Vote moves user from not_voted to voted on poll P1.",
        "preconditions": "Logged in as user 'alice'. Poll P1 active with choices C1, C2. Alice has not voted on P1.",
        "steps": (
            "1. Go to /polls/<P1.id>/\n"
            "2. Select choice C1\n"
            "3. Click Vote"
        ),
        "expected": "Result page shows C1 vote count incremented by 1. Vote row exists in DB.",
        "actual": "First vote rendered the result page with Total: 1 votes.",
        "result": "Pass",
        "technique": "State Transition",
    },
    {
        "id": "UAT-013",
        "name": "Block second vote attempt",
        "story": "US-07",
        "description": "Vote decision row: active=T, already-voted=T -> block.",
        "preconditions": "Logged in as alice; alice has already voted on poll P1.",
        "steps": "POST to /polls/<P1.id>/vote/ with any choice id.",
        "expected": "Redirect to /polls/list/ with warning 'You already voted this poll!'. No new Vote row.",
        "actual": "Second vote redirected to the list with the duplicate-vote warning.",
        "result": "Pass",
        "technique": "Decision Table",
    },
    {
        "id": "UAT-014",
        "name": "End an active poll",
        "story": "US-10",
        "description": "Owner ends poll, state transitions active -> ended, vote UI hidden.",
        "preconditions": "Logged in as poll P1's owner; P1 currently active.",
        "steps": (
            "1. Open /polls/end/<P1.id>/\n"
            "2. Confirm via the form\n"
            "3. Re-visit /polls/<P1.id>/"
        ),
        "expected": "After end: poll.active is False. Detail page now renders result template, not the vote form.",
        "actual": "Ending the poll rendered the ended-results page without the vote form.",
        "result": "Pass",
        "technique": "State Transition",
    },
    {
        "id": "UAT-015",
        "name": "Create poll with two choices",
        "story": "US-04",
        "description": "Happy-path poll creation with valid text + two valid choice texts.",
        "preconditions": "Logged in as a user that has polls.add_poll permission.",
        "steps": (
            "1. Go to /polls/add/\n"
            "2. Text = 'Best language?'\n"
            "3. Choice 1 = 'Python'\n"
            "4. Choice 2 = 'JavaScript'\n"
            "5. Submit"
        ),
        "expected": "Redirect to /polls/list/, success toast, the new poll appears in the list with 2 choices.",
        "actual": "Poll creation redirected to the list and showed the new poll.",
        "result": "Pass",
        "technique": "Equivalence Partitioning",
    },
]
