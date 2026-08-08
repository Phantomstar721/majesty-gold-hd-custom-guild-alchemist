# Alchemist Resource Namespace

The hand-assigned values below belong to the two-mod development fixture. The
future mod manager will allocate collision-free runtime FourCCs from the mod UUID
and logical resource names.

| Purpose | Reserved value |
| --- | --- |
| Mod UUID | `{42ba4603-2b13-446d-a2a4-6cf3a55ddac3}` |
| Custom building | `AlchemistsLaboratory` |
| Probe DialogID | `CGAL` |
| Controller base | `AP10` |
| Laboratory levels | `ALB1`, `ALB2`, `ALB3` |
| Alchemist hero | `ALC1` |
| Actions | `ALa1`–`ALa9` |
| Projectiles | `ALp1`–`ALp9` |
| Overlays/effectors | `ALo1`–`ALo9` |
| Building/hero image bases | `ALB1`–`ALB3`, `ALC1` |

Every Laboratory level will use `DialogID=CGAL`. Its text CAM will provide
matching `SMNU/CGAL` and `STRT/CGAL` entries cloned from the stock AP10 layout
and then relabeled for the Laboratory.
