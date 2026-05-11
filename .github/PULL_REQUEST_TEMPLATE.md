## Summary
- 

## Scope
- [ ] Backend
- [ ] Frontend (`frontend-nextjs/`)
- [ ] Widget (`widget/`)
- [ ] Infra/DevOps
- [ ] Docs/Spec

## Type of Change
- [ ] Feature
- [ ] Fix
- [ ] Refactor
- [ ] Chore
- [ ] Test

## Validation
- [ ] Relevant tests pass locally
- [ ] Lint/type-check/build pass for touched projects
- [ ] No sensitive data or secrets added

## UI Consistency Checklist (Required for UI Changes)
If this PR touches UI, all items below must be checked before merge.

### Token Usage
- [ ] No hardcoded color/spacing/radius/shadow values in feature UI code
- [ ] New visual values are introduced through shared tokens first

### Component State Completeness
- [ ] Interactive components implement `default/hover/active/focus-visible/disabled`
- [ ] Async actions include loading behavior without layout shift

### Responsive Behavior
- [ ] Mobile-first behavior validated at key breakpoints (`xs/sm/md/lg/xl/2xl`)
- [ ] Dense content remains readable on small screens

### Accessibility
- [ ] Contrast follows WCAG guidance (normal text >= 4.5:1, large text >= 3:1)
- [ ] Keyboard-only navigation works end-to-end
- [ ] Focus-visible state is clearly perceivable
- [ ] Status and errors are not color-only

### Consistency and Regression
- [ ] Existing shared components are reused where possible
- [ ] New reusable UI patterns are documented before repeated usage
- [ ] Visual/interaction regression checks completed for modified shared components

## Risk and Rollback
- Risk level: Low / Medium / High
- Rollback plan:
  - 

## Related Specs / Issues
- Spec:
- Issue:
