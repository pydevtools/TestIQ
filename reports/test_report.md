# Test Duplication Report

## Exact Duplicates (Identical Coverage)

Found 1 groups of tests with identical coverage:


### Group 1 (2 tests):
  - test_user_login_basic
  - test_user_login_with_password

  **Action**: Keep one test, remove 1 duplicates


## Subset Duplicates

Found 10 tests that are subsets of others:


  - `test_user_login_minimal` is 30.0% covered by `test_user_login_basic`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_basic` is 55.6% covered by `test_user_login_complete`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_basic` is 76.9% covered by `test_admin_login`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_minimal` is 30.0% covered by `test_user_login_with_password`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_with_password` is 55.6% covered by `test_user_login_complete`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_with_password` is 76.9% covered by `test_admin_login`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_minimal` is 16.7% covered by `test_user_login_complete`
    **Action**: Consider removing if no unique edge cases


  - `test_user_login_minimal` is 23.1% covered by `test_admin_login`
    **Action**: Consider removing if no unique edge cases


  - `test_logout_user` is 70.0% covered by `test_logout_admin`
    **Action**: Consider removing if no unique edge cases


  - `test_user_profile_view` is 61.5% covered by `test_user_profile_edit`
    **Action**: Consider removing if no unique edge cases


## Similar Coverage (70%+ overlap)

Found 3 test pairs with significant overlap:


  - `test_user_login_basic` ↔ `test_admin_login`: 76.9% similar
    **Action**: Review for potential merge or refactoring


  - `test_user_login_with_password` ↔ `test_admin_login`: 76.9% similar
    **Action**: Review for potential merge or refactoring


  - `test_logout_user` ↔ `test_logout_admin`: 70.0% similar
    **Action**: Review for potential merge or refactoring


## Summary

- Total tests analyzed: 12
- Exact duplicates: 1 tests can be removed
- Subset duplicates: 10 tests may be redundant
- Similar tests: 3 pairs need review