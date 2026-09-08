# LensFusion on the CUHK Central Cluster — Run Guide

Account: `<YOUR_CUHK_ACCOUNT>`  ·  Group account/QOS: `tkcastrosim`
Your code copy: `~/lensfusion`  (i.e. `/users/<YOUR_CUHK_ACCOUNT>/lensfusion`)
Shared data + checkpoints: `/lustre/project/tkcastrosim/TKChan/Diffusion-Sampling-For-Strong-Gravitational-Lensing/datafiles/`

---

## ⚠️ Current blocker (read first)

GPU jobs currently stay pending with **`Reason=BadConstraints`** and never start. Cause: a *magnetic*, account-based reservation **`tkcastrosim1`** that covers **CPU-only** nodes (`chpc-cn057–064`). Because it is `MAGNETIC`, it auto-captures every `tkcastrosim` job, so a GPU request can't find a GPU on those nodes.

**Until TK / ITSC tell you the correct GPU submission method** (a different account/QOS, a GPU reservation via `--reservation=...`, or a config change), the run will not start — even though everything below is correctly set up. Steps that depend on this are marked **[needs GPU access]**.

---

## 0. One-time setup — ALREADY DONE (do not repeat)

- Account created, initial password changed (`passwd`).
- Repo cloned to `~/lensfusion` (your own writable copy).
- Conda env **`Stronglensing`** built (Python 3.8 + PyTorch 2.3.0 cu121 + project requirements).
- Config paths point at the shared `datafiles/`:
  - `configs/data/strong-lensing-test.yaml` → `test_galaxies.h5`, `kappa_testset.h5`
  - `configs/model_1/source_norm_test.yaml` → `galaxies_ema_0.9999_200000.pt`  (source-light prior)
  - `configs/model_2/conv_arcsinh1_test.yaml` → `kappa_ema_0.9999_200000.pt`  (convergence / lens-mass prior)
- Run script fixed: `scripts/daps/sample_multi_daps.sh`
  - `#SBATCH -p chpc`            (was `normal` — doesn't exist here)
  - `#SBATCH --gres=gpu:A100:1`  (was `gpu:1` — GPUs here are typed)
  - `#SBATCH --mem=32G`          (was 200G)
  - `module load anaconda` added before `conda activate Stronglensing`
  - smoke-test sizes: `num_images=1 batch_size=1 num_runs=1`, `save_traj_video=False`

---

## 1. Connect (every session)

```
ssh -Y <YOUR_CUHK_ACCOUNT>@chpc-login.itsc.cuhk.edu.hk
```
- At the Duo prompt: type `1`, then approve the push on your phone.
- At `Password:` type your password (nothing shows as you type — normal).

You land on **`chpc-logina`** = the LOGIN NODE.
**Guideline: never run jobs/programs on the login node.** Use it only to navigate and submit.

---

## 2. Load your environment

```
cd ~/lensfusion
module load anaconda
conda activate Stronglensing
```
Quick check (optional): `which python` should point inside `Stronglensing`; `python -c "import torch; print(torch.__version__)"` should print `2.3.0+cu121`.
(On the login node `torch.cuda.is_available()` is `False` — that's expected; GPUs only exist on compute nodes.)

---

## 3. Run the job

### Method A — batch submission (recommended, fully guideline-compliant) **[needs GPU access]**

```
mkdir -p ~/lensfusion/logs
sbatch scripts/daps/sample_multi_daps.sh
squeue -u <YOUR_CUHK_ACCOUNT>
```
Read the `squeue` `(REASON)`:
- `(Priority)` or `(Resources)` → healthy: queued, will start when a GPU frees. Leave it; no need to watch.
- `(BadConstraints)` → still blocked by the reservation issue (see top of file).

Watch progress once it starts (replace `<jobid>`):
```
tail -f ~/lensfusion/logs/DAPS_<jobid>.out
```
(Press `Ctrl-C` to stop watching — it does NOT stop the job.)

Cancel a job if needed: `scancel <jobid>`

### Method B — interactive session (your prof's method) + `screen` **[needs GPU access]**

Use `screen` so a long queue-wait survives if your laptop disconnects (TK guide §4.3).
```
screen -S gpu
srun -p chpc --gres=gpu:A100:1 --cpus-per-task=8 --mem=32G --time=01:00:00 --pty bash
```
(Your prof's template is `srun --gres=gpu:1 --pty bash`; on THIS cluster you must add `-p chpc` and a GPU **type**.)

Once you get the compute-node shell:
```
module load anaconda
conda activate Stronglensing
cd ~/lensfusion
bash scripts/daps/sample_multi_daps.sh
```
- Detach from screen: `Ctrl-A` then `D`.  Reattach later: `screen -r gpu`.
- List screens: `screen -ls`.

---

## 4. Where results land

- Log/output: `~/lensfusion/logs/DAPS_<jobid>.out`
- Reconstructions/metrics: `~/lensfusion/results/daps/multi/...` (path built from the run settings)

Tip (TK guide §1.2): your home has a small quota. For big output runs, keep results under the group space `/lustre/project/tkcastrosim/` (50 TB), not home.

---

## 5. Prof's template vs this cluster (reconciliation)

| Prof's template            | This cluster                          | Why                                            |
|----------------------------|---------------------------------------|------------------------------------------------|
| `--partition=normal`       | `-p chpc`                             | `normal` doesn't exist; `chpc` is the default and has GPUs |
| `--gres=gpu:1`             | `--gres=gpu:A100:1`                   | All GPU nodes here define typed GRES (A100, L40S, H200, …) |
| `module load cuda/12.0`    | (not needed)                          | Your PyTorch is the `cu121` build with CUDA bundled |
| write a new `job.pbs`      | use the repo's `sample_multi_daps.sh`| Already configured for this project            |

**Once TK replies** with the right GPU method, just update the `-p`, `--gres`, and (if given) `--reservation=...` lines in the script / `srun` command, then rerun Step 3.

---

## 6. Guideline checklist (TK's cluster guide)

- [x] Log in via `ssh` + Duo (§1)
- [x] Set up env with modules + conda (§2.3)
- [ ] **Never run on the login node** — always `sbatch`/`srun` to a compute node (§1, login banner)
- [ ] Use `screen`/`tmux` for long waits (§4.3)
- [ ] Keep large outputs in `/lustre/project/tkcastrosim` (§1.2)
