# Package Locker (Amazon Locker)

Design a self-service package locker station.

## Requirements

1. `add_locker(locker_id, size)` with sizes `SMALL < MEDIUM < LARGE`; repeated id → `DuplicateLocker`.
2. `deposit(package_id, size, code)` puts a package into the **smallest free locker it fits
   in** (a package fits lockers of its size or bigger; ties → lowest locker id) and returns
   the locker id. The pickup `code` comes from the caller (an OTP service). No locker →
   `NoLockerAvailable`; a package already stored → `DuplicatePackage`; a code already in use
   → `DuplicateCode`.
3. `pickup(code)` returns the package id and frees the locker. Unknown code →
   `InvalidCode`. A package older than `hold_seconds` (config; expired when
   `now ≥ deposited_at + hold_seconds`) → `Expired` (it stays until reclaimed).
4. `reclaim_expired()` removes every expired package, frees their lockers, and returns
   the package ids sorted.
5. `free_count(size)` counts free lockers of exactly that size.
6. Couriers deposit concurrently: a locker never holds two packages.

## Things an interviewer will push on

- How would you add a better assignment policy (fewest wasted space, closest to the door)?
- Where does code generation live, and why inject it?
- Multiple locker stations and routing packages to them?
