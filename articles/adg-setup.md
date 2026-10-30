---
title: Physical standby setup: build it right, and know when you need Active Data Guard
date: 2026-10-30
summary: Standby redo logs, FORCE LOGGING, redo transport, and the one step that needs an Active Data Guard licence. A checklist with the queries to verify each part.
---

# Physical standby setup: build it right, and know when you need Active Data Guard

Most Data Guard problems are not caused by Data Guard. They come from a few details missed when the standby was built: standby redo logs of the wrong size, a missing password file, logging that was never forced. This guide walks through a physical standby build for Oracle 19c, with a query to verify each part, and explains the one step that crosses into a separately licensed option.

The examples use a single-instance database `prod` on the primary and `prodsb` on the standby. Replace the names with yours.

## Licence first: Data Guard or Active Data Guard

- **Data Guard** (redo transport, redo apply, switchover, failover, the broker) is included with Oracle Database Enterprise Edition.
- **Active Data Guard** is a separately licensed option. Oracle's documentation says that without it, a physical standby cannot be open while Redo Apply is active. Opening the standby read-only **while redo apply keeps running** (real-time query) is the step that needs the option.

A standby that stays in `MOUNT` mode, applying redo, is plain Data Guard. Check your own licence terms or ask Oracle before you open a standby for reads. Other Active Data Guard features exist; this guide only uses real-time query.

## 1. Prepare the primary

Check that the database is in `ARCHIVELOG` mode, and turn on forced logging:

```sql
SELECT log_mode, force_logging FROM v$database;

ALTER DATABASE FORCE LOGGING;
```

Forced logging matters. Without it, a `NOLOGGING` operation on the primary writes no redo, and the standby receives blocks it cannot rebuild. They show up later as corruption on the standby, often only after a failover (see [ORA-01578: data block corrupted](/resources/ora-01578-data-block-corrupted/)).

Give each database its own `DB_UNIQUE_NAME` and tell Oracle which databases belong to the configuration:

```sql
ALTER SYSTEM SET log_archive_config='DG_CONFIG=(prod,prodsb)' SCOPE=BOTH;
ALTER SYSTEM SET standby_file_management='AUTO' SCOPE=BOTH;
```

`standby_file_management=AUTO` makes the standby create datafiles when you add them on the primary. With `MANUAL`, apply stops the first time someone adds a datafile.

## 2. Create standby redo logs

Standby redo logs (SRLs) receive redo as it is generated, which is what allows real-time apply. They must be the **same size as the online redo logs**, and each thread needs **one more SRL group than it has online groups**: `(online groups per thread + 1) × number of threads`.

```sql
SELECT thread#, COUNT(*) AS online_groups, MAX(bytes)/1024/1024 AS size_mb
FROM   v$log
GROUP  BY thread#;
```

For three online groups of 200 MB in one thread, create four SRLs:

```sql
ALTER DATABASE ADD STANDBY LOGFILE THREAD 1 SIZE 200M;  -- repeat 4 times
```

Create them on the primary too. After a switchover, the old primary becomes the standby and needs them. If you do not use Oracle Managed Files or ASM, add the file name for each group.

Verify:

```sql
SELECT thread#, COUNT(*) FROM v$standby_log GROUP BY thread#;
```

## 3. Password file and network

Redo transport authenticates with the `SYS` password, so both databases need a password file with the same `SYS` password, and `REMOTE_LOGIN_PASSWORDFILE=EXCLUSIVE`. Copy the primary's password file to the standby, or let RMAN copy it.

The standby instance is started in `NOMOUNT`, so the listener must have a **static** registration for it (`SID_LIST_LISTENER`); a dynamic service is not registered yet. Add TNS aliases for both databases on both servers and test them:

```bash
tnsping prod
tnsping prodsb
sqlplus sys@prodsb as sysdba
```

## 4. Build the standby with RMAN

Start the standby instance in `NOMOUNT` with a minimal parameter file (`db_name='prod'` is enough), then duplicate from the running primary:

```bash
rman target sys@prod auxiliary sys@prodsb
```

```sql
DUPLICATE TARGET DATABASE
  FOR STANDBY
  FROM ACTIVE DATABASE
  DORECOVER
  SPFILE
    SET db_unique_name='prodsb'
    SET fal_server='prod'
    SET standby_file_management='AUTO'
  NOFILENAMECHECK;
```

Use `NOFILENAMECHECK` only when the standby host has the same directory layout. If the paths differ, set `db_file_name_convert` and `log_file_name_convert` instead.

## 5. Point the primary at the standby

```sql
ALTER SYSTEM SET log_archive_dest_2=
  'SERVICE=prodsb ASYNC VALID_FOR=(ONLINE_LOGFILES,PRIMARY_ROLE) DB_UNIQUE_NAME=prodsb'
  SCOPE=BOTH;
ALTER SYSTEM SET fal_server='prodsb' SCOPE=BOTH;
```

Check the destination is healthy:

```sql
SELECT dest_id, status, error FROM v$archive_dest WHERE dest_id = 2;
```

`STATUS` must be `VALID` and `ERROR` empty. A password problem shows up here as an `ORA-01017`.

## 6. Start redo apply

On the standby:

```sql
ALTER DATABASE RECOVER MANAGED STANDBY DATABASE DISCONNECT FROM SESSION;
```

Since 12.1, `USING CURRENT LOGFILE` is deprecated and not needed: real-time apply is on automatically when the standby has SRLs and the database is in `ARCHIVELOG` mode. If you set an apply delay, you must start apply with `USING ARCHIVED LOGFILE`.

## 7. Verify that it works

On the standby, check the lag and the processes:

```sql
SELECT name, value FROM v$dataguard_stats
WHERE  name IN ('transport lag', 'apply lag');

SELECT process, status, thread#, sequence# FROM v$managed_standby;
```

The `MRP0` process should be `APPLYING_LOG`, and an `RFS` process should be receiving. Then force a log switch on the primary and compare sequence numbers:

```sql
-- primary
ALTER SYSTEM ARCHIVE LOG CURRENT;

-- standby
SELECT thread#, MAX(sequence#) FROM v$archived_log
WHERE  applied = 'YES' GROUP BY thread#;
```

If the standby is not within one or two sequences of the primary, read the standby's alert log before anything else.

## 8. Only if you hold the Active Data Guard licence: real-time query

```sql
ALTER DATABASE RECOVER MANAGED STANDBY DATABASE CANCEL;
ALTER DATABASE OPEN READ ONLY;
ALTER DATABASE RECOVER MANAGED STANDBY DATABASE DISCONNECT FROM SESSION;

SELECT open_mode FROM v$database;
```

`OPEN_MODE` changes to `READ ONLY WITH APPLY`. If you do not hold the licence, leave the standby in `MOUNT` mode.

## The mistakes that cause most incidents

| Symptom | Usual cause |
|---|---|
| Transport error `ORA-01017` | Different `SYS` password, or no password file on the standby |
| Standby falls behind at night | Too few or too small SRLs, or the network cannot carry the redo rate |
| Apply stops after a datafile is added | `standby_file_management` is `MANUAL` |
| Corruption on the standby after a bulk load | Forced logging was off |
| Standby stops receiving redo | Archive destination or FRA on the standby is full |

## Before you rely on it

A standby you have never switched over to is a hope, not a plan. Run a switchover during a maintenance window, time it, and write down the steps. Do the same for a restore test of your backups.

If you want a second pair of hands, our [backup, Data Guard and high availability service](/oracle-backup-data-guard/) covers building, monitoring, and testing standby databases.
