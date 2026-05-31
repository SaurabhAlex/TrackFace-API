# BLACKBOXAI WORK INSTRUCTIONS

## Mandatory rules
- Before making any changes to this repository (editing/creating files), **always read this file first**.
- Follow the instructions exactly as written.
- If any instruction conflicts with the task you’re currently doing, report the conflict rather than proceeding silently.

## Current instructions

# BLACKBOX Coding Instructions

## Core Philosophy
- Write clean, minimal, production-grade code.
- Prefer simplicity over abstraction.
- Avoid overengineering.
- Solve only the requested problem.
- Keep logic straightforward and readable.
- Optimize for maintainability and scalability.
- Every line of code must have a purpose.

---

# General Development Rules

## Code Style
- Use meaningful and consistent naming.
- Prefer short, readable functions.
- Avoid deeply nested conditions.
- Prefer early returns.
- Keep files small and focused.
- Remove dead code immediately.
- Do not leave commented-out code.
- Avoid unnecessary wrappers and utility classes.
- Avoid duplicate logic.
- Prefer composition over inheritance.

---

# Architecture Rules

## Follow Clean Architecture
Project structure should follow:

```txt
lib/
├── core/
├── features/
│   ├── feature_name/
│   │   ├── data/
│   │   ├── domain/
│   │   ├── presentation/
│   │   └── di/
├── shared/
└── main.dart




