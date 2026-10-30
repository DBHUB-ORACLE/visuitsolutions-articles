---
title: Proving an RMAN backup can be restored, without restoring it
date: 2026-10-30
summary: RESTORE VALIDATE reads your backups end to end without writing a datafile. How to run it, and how it differs from VALIDATE.
---

# Proving an RMAN backup can be restored, without restoring it

A backup job that ends with "completed" proves only that RMAN wrote files. It does not prove those files can be read back. RMAN can check that without writing a single datafile.

## RESTORE ... VALIDATE

`RESTORE ... VALIDATE` makes RMAN choose the backups it would use for a real restore, read them completely, and check every block. Nothing is written to the database.

```sql
RMAN> RESTORE DATABASE VALIDATE;
RMAN> RESTORE ARCHIVELOG ALL VALIDATE;
RMAN> RESTORE CONTROLFILE VALIDATE;
RMAN> RESTORE SPFILE VALIDATE;
```

If a backup piece is missing or damaged, RMAN reports it and, where possible, falls back to an older backup. That fallback is exactly what you want to know about before a real failure.

## VALIDATE is a different check

`VALIDATE DATABASE` (or `BACKUP VALIDATE DATABASE`) reads the **live datafiles** and checks them for corruption. It says nothing about whether your backups are usable. Run both: one protects you from damaged data, the other from damaged backups.

```sql
RMAN> VALIDATE DATABASE;
```

## What to check in the output

- Every datafile and archived log you expect is listed.
- No "failover to previous backup" messages, or, if there are, you understand why.
- The run finishes without RMAN errors.

## Make it a habit

Schedule `RESTORE DATABASE VALIDATE` weekly, after the full backup, and alert on any error. Once a quarter, go further: restore to a separate server and open the database. Only a real restore tells you how long recovery will take.
