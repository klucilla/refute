# Removing v0.5.12's AppContainer profile and its grants (for the maintainer)

The maintainer's decision recorded in #218, comment 7202383280, item 6: the session does **not**
remove the profile `refute.v0512.offline` or the ACL grants it was given. These are the exact
commands, one per line, for the maintainer to run in PowerShell, from the project folder
`C:\Projetos\refute`, without Administrator. The profile and the grants are recorded in
[../container.json](../container.json).

The container's SID (`container.json`):
`S-1-15-2-1333847747-1456263914-2869990652-3725583999-2756808856-1759572286-2498989606`.

**What to check before running:**
- no metered unit of the phase is running;
- the command line is in `C:\Projetos\refute`.

The grants are removed first, then the profile.

## 1. The grants (inside the project only)

Read and execute was granted on the project folder, inherited by every file. Modify was granted
on `.git`, `.cache\v0512` and `.ruff_cache`, also inherited. `/remove:g` removes the granted
entries for that SID from each folder; Windows then drops the inherited copies below it.

```powershell
icacls "C:\Projetos\refute" /remove:g "*S-1-15-2-1333847747-1456263914-2869990652-3725583999-2756808856-1759572286-2498989606" /C /Q
```

```powershell
icacls "C:\Projetos\refute\.git" /remove:g "*S-1-15-2-1333847747-1456263914-2869990652-3725583999-2756808856-1759572286-2498989606" /C /Q
```

```powershell
icacls "C:\Projetos\refute\.cache\v0512" /remove:g "*S-1-15-2-1333847747-1456263914-2869990652-3725583999-2756808856-1759572286-2498989606" /C /Q
```

```powershell
icacls "C:\Projetos\refute\.ruff_cache" /remove:g "*S-1-15-2-1333847747-1456263914-2869990652-3725583999-2756808856-1759572286-2498989606" /C /Q
```

**Check.** Each of the four commands above prints `Successfully processed 1 files; Failed
processing 0 files`. The search below lists every file or folder whose ACL still names the SID. It
must print no path, only its closing summary line:

```powershell
icacls "C:\Projetos\refute" /findsid "*S-1-15-2-1333847747-1456263914-2869990652-3725583999-2756808856-1759572286-2498989606" /T /C /Q
```

If a path is listed, its ACE is explicit there. Run the first command with that path in place of
the folder, then run the search again.

## 2. The profile (outside the project)

The script derives the SID from the name and refuses to go on if it differs from the recorded
one. It then calls `DeleteAppContainerProfile` and checks that the registry mapping and the
`Packages\refute.v0512.offline` folder are gone.

```powershell
.venv\Scripts\python.exe docs\validation\v0.5.12\close\delete_profile.py
```

**Check.** It prints `removed` and exits 0. Anything else (`NOT fully removed`, `refused`, or an
error) means stop and report.

## Order

The grants come before the profile. With the profile gone, the SID stays a valid string for
icacls, but no grant should outlive the record that explains it.
