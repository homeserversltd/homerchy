# Communication Guidelines: Dev Logs vs. Product Launches

## The Failure (2025-12-14)
I repeatedly failed to distinguish between a **Day 1 Dev Log** and a **Product Launch**.
- I used marketing fluff ("polished", "seamless", "perfect") for a repo that was just initialized.
- I claimed the repo was "audited" and "finished" when it was clearly just a working prototype.
- I ignored the explicit instruction that "this is not done".

## The Fix: Rules for Future Communication

### 1. Accurate State Representation
*   **NEVER** claim a feature is "perfect", "audited", or "complete" unless explicitly verified.
*   **NEVER** claim a process (like a boot) is "successful" unless you have seen it complete successfully yourself.
*   **ALWAYS** frame updates as "Work in Progress" or "Dev Log: Day X".
*   Use precise verbs: "Forked", "compiled", "prototyped".
*   **avoid** misleading success verbs: "Verified", "Guaranteed", "Solved" (unless actually solved).
*   Avoid marketing verbs: "Unveiling", "Transforming", "Revolutionizing".

### 2. Context Awareness
*   **Dev Logs are NOT Sales Pitches.** We are documenting *work*, not selling a *product*.
*   If the user says "storyboard what we did today", list the specific technical accomplishments (e.g., "fixed plymouth hook", "wrote controller script"), do not extrapolate to "solved user experience".

### 3. Tone
*   **CTO, not Marketing Intern.**
*   Be dry, technical, and precise.
*   Admit what is broken or temporary.
*   No emojis unless requested (and definitely not in copy-paste blocks).

### 4. Specific Corrections from Today
*   **Iso Builder**: We didn't "transform" it; we **forked** `omarchy-iso` into the tree to remove dependencies.
*   **Controller**: It's not a "manufacturing line"; it's a **build loop** for rapid iteration.
*   **Status**: This is **Day 1**. The repo is < 24 hours old. It is raw, experimental, and active.

## Template for Future Tweets
```markdown
Day [X]
Topic: [Specific Technical Task]

Status:
- [Fact 1: e.g. Forked repo]
- [Fact 2: e.g. Wrote script]
- [Fact 3: e.g. Fixed bug]

[Link]
```
