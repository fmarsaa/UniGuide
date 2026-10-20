# Evaluation with students (Objective 5)

Observed sessions with real Form Four leavers or first-year students. Nothing in this folder contains
results until real sessions have been run; `analyse_sessions.py` only summarises the rows you enter.

## Before each session (read aloud)

> This is for my final-year project. I will ask you to use the app and then answer a few questions.
> I will not record your name. You can stop at any time, and your account and answers will be deleted afterwards.

## What the student does

1. Signs up with their own email, ticks the box, and verifies the email.
2. Enters their own KCSE results, interests, skills and strengths. The career step is optional.
3. Reads the three recommendations and the reasons without help from the observer.
4. Answers the questions below.

The observer times from the start of the profile to the results screen, notes whether the student needed
help, and copies the three programme names shown on the screen.

## Questions (1 = strongly disagree, 5 = strongly agree)

- The application was easy to use. (`rating_easy`)
- I understood why these programmes were suggested. (`rating_reasons`)
- I would consider the programmes that were suggested. (`rating_consider`)
- I would recommend the application to another student. (`rating_recommend`)
- Which programme were you placed in, or did you choose, and at which university?
- Anything that confused you or that you would change? (`comment`)

## Recording and analysing

Copy `sessions_template.csv` to `sessions.csv` (git-ignored), one row per student with an ID like S01 and no names,
then run:

```bash
python ml/experiments/student_evaluation/analyse_sessions.py
```

It prints the sentences and figures for Section 5.4.4 of the report. Report the real sample size and say
whether the sessions used the emulator or a phone.

## After the sessions

Delete the student accounts with `python backend/reset_student_data.py` (dry run first, then `--yes`) and
clear the app's storage on the emulator.
