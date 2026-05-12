# Upload Instructions

## GitHub Code Repository

From this directory:

```bash
git init
git add .
git commit -m "Initial ViNL2Vis VLM judge release package"
gh repo create vinl2vis-vlm-judge-code --public --source=. --remote=origin --push
```

If `gh` is not available, create an empty repository on GitHub first, then run:

```bash
git remote add origin https://github.com/ictu-se/vinl2vis-vlm-judge-code.git
git branch -M main
git push -u origin main
```

## Zenodo DOI

After the GitHub repository is public, enable the repository in Zenodo, create a GitHub release, and let Zenodo archive that release. The generated DOI can then be added to the manuscript and `CITATION.cff`.

## Hugging Face Dataset Repository

The full dataset artifacts should remain in the ViNL2Vis-FaithBench dataset package:

```text
https://huggingface.co/datasets/vinhnt/vinl2vis-faithbench
```

Use a private repository during review if the paper is still under submission.
