# Try-On Model — Setup Guide

This folder contains the OOTDiffusion try-on notebook (`tryon.ipynb`). 
It must be run in **Google Colab** (needs a GPU) — it won't run locally.

## How to run it

1. Open `tryon.ipynb` in Google Colab
   (Colab → File → Upload notebook, or drag the file in directly)

2. Make sure you're on a GPU runtime:
   `Runtime → Change runtime type → GPU`

3. Run all cells top to bottom (`Runtime → Run all`)
   - This installs dependencies, applies compatibility patches for
     `basicsr`/`diffusers`, and downloads model checkpoints.
   - First run takes a while (checkpoint downloads are large).

4. The final cell launches Gradio with `share=True`. Once it finishes,
   you'll see a public URL printed, like: Running on public URL: https://xxxxx.gradio.live

5. Copy that URL — you'll need it for the main app.

## Connecting it to the main app

The URL above is **temporary** — it expires when the Colab session ends,
and a new one is generated every time you re-run the notebook.

1. In `stylemind-backend/` ( `.env` lives), copy and paste the url on the place of OOTD_space_url
   `
2. Restart the backend server for it to pick up the new URL.

⚠️ Whoever wants to test try-on locally needs to run this notebook
themselves and get their own URL — don't share/commit a live URL,
since it'll be dead by the time someone else opens the repo.

## Known issues / patches already applied in the notebook

The notebook includes patches for known breakage in newer versions of
`basicsr` and `diffusers` (renamed imports, removed classes, checkpoint
format mismatches). If Colab updates a package and something breaks
again, check the patch cells near the top before debugging the model
code itself.