This script fixes formatting issues in dictionary files downloaded from [here](https://drive.google.com/drive/folders/1tTdLppnqMfVC5otPlX_cs4ixlIgjv_lH?usp=sharing)

The following dictionaries are modified:
- [Grammar] Dictionary of Japanese Grammar 日本語文法辞典 (Recommended).zip
- [Grammar] JLPT文法解説まとめ(nihongo_kyoushi).zip
- [Grammar] どんなとき使う日本語表現文型辞典.zip
- [Grammar] 毎日のんびり日本語教師 (nihongosensei).zip
- [Grammar] 絵でわかる日本語.zip

## Usage:

1. Clone the repository.
2. Download original dictionaries into the parent directory (not the repository directory).
3. Run `./extract_all.sh`. (Or just manually extract the dictionaries into directories with the same names (keeping .zip), but in the repository directory.)
4. Run `python3 cleanup.py`.
5. Results will be placed in a newly created `transformed` directory.
