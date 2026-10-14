# Mapping pass, committed on 2026-10-14

The occurrences of every non-deleted mapping were recomputed with the fixed rules of the write tools (`database.md` §2), and every description whose occurrences changed was revised, note `UPDATED: mapping occurrences recomputed with the current rules`.

Non-deleted descriptions with a mapping: 10,162 vh, 8,760 hh. The rules reproduced the stored occurrences of 9,601 vh and 7,450 hh; 1,871 descriptions were revised (561 vh, 1,310 hh), 2,060 mappings:

| Change                                           |      vh |        hh |
| ------------------------------------------------ | ------: | --------: |
| occurrences removed                              |     159 |       869 |
| occurrences added                                |     386 |       129 |
| identity changed                                 |       0 |       166 |
| occurrences added and removed                    |       7 |       144 |
| duplicate occurrences removed                    |       8 |         0 |
| identity changed and occurrences removed         |       0 |         2 |
| duplicate occurrences removed, occurrences added |       1 |         0 |
| **Total**                                        | **561** | **1,310** |

- Removed: isoforms below the best score, and overlapping occurrences clustered into one (e.g. P0CG48, three 229-residue mappings over the ubiquitin repeats: 1–229).
- Added: isoforms or copies that reach the best score but were never recorded.
- Identity changed: legacy identities stored with 2 decimals, now with their full decimals (0.005 point at most).
- Duplicate occurrences removed: legacy occurrences recorded twice.

No mapping fell below 90 %.

In the same commit, 3 HCV Core descriptions (EY294151C6 and EYA45D9AA2, PMID 25485706; EY9CD1A21A, PMID 25733156) were revised with the initiator methionine of their mapping named as `nter`: Core is 2–191 of Q99IB8, and the occurrences moved from 93.33 % (99.18 % for EY9CD1A21A) to 100 % at the same positions. They were the only mappings with residues past the end of their interactor.

1,874 revisions in one run of `drakkar-revise`; the check after it: no error, D12 warnings on vh mappings from 13 to 11.
