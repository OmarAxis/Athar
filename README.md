# Athar

Athar follows one learner across years and shows a teacher where that learner is strong, where they struggle, and where a struggle may have started. It is the school product built on [Meska Brain](docs/meska-brain-readme.md), starting with Egypt. The name is Arabic for a trace, the mark something leaves behind.

Status: stage two, on synthetic data only. It has not been used with a real teacher or a real learner. Do not put real learner data in it yet. See [SECURITY.md](SECURITY.md).

## What it has

- **The Egyptian curriculum for grades 4 to 8** (Primary 4 to Preparatory 2) as a map of topics and what each topic needs first, in five subjects. Every topic has its grade, its term and its source. All five maps are drafts: see "What is not finished".

  | Subject | Topics | Not confirmed from a source | Pack |
  |---|---|---|---|
  | Mathematics | 126 | 2 | `packs/egypt-maths` |
  | Science | 96 | 14 | `packs/egypt-science` |
  | English | 125 | 0 | `packs/egypt-english` |
  | Arabic | 121 | 1 | `packs/egypt-arabic` |
  | Social Studies | 110 | 0 | `packs/egypt-social` |

  `packs/egypt-school` joins the five and adds three links between subjects.
- **A synthetic Egyptian school** on that map: 40 learners, 10 teachers (two per subject), one class per grade, three past school years and a term in progress. Everything in it is made up.
- **Sign-in for teachers**, with a school admin who creates the accounts.
- **Classes.** Once sign-in is on, a teacher sees the learners of their own classes and nobody else. The admin sees everyone.
- **Learner records.** A teacher adds a learner and gets a record code. There is no login for learners.
- **An Add records page**: a marks sheet for Excel that needs no model, and document upload for the agent.
- **Looking after the records** (School page, admin): a backup copy, one learner's whole record as a file, deleting one learner for good, and withdrawing one wrong record.

- **Arabic, right to left.** The page opens in Egyptian Arabic and has a button to switch to English. Topic names, the made-up school, the marks sheet, the printable report and the agent's findings are in Arabic too. See "Arabic" below.

Everything Meska Brain had is still here: the graph engine that reaches the conclusions, the agent that only reads and words, the two teacher gates, the guard, and the audit log.

## Run it

The full guide, with every step, is [docs/GETTING-STARTED.md](docs/GETTING-STARTED.md) ([بالعربي](docs/GETTING-STARTED.ar.md)). In short:

**Windows, no installing.** Download `Athar-windows.zip` from the Releases page, extract it, double-click **Start Athar**.

**From the source.**

```
uv sync
uv run meska demo
```

Open http://127.0.0.1:8765. The first run builds the synthetic school.

**The model.** Only the Agent page needs one. Three ways, pick any:

- **LM Studio or Ollama on your computer.** Switch its server on. Athar finds it and uses a model it offers.
- **Your own OpenAI or Claude key.** Paste it on the Agent page under "Cloud models". It is kept in memory only.
- **The model inside the Windows package.** Run "Download the model" once (5.2 GB).

To see findings waiting for a decision without running a model:

```
uv run meska story
```

## Try the upload

1. Open **Add records**.
2. Upload the file in `data/samples` (its name starts with `marks-grade`). Give the quiz a name, choose the grade in the file name, term 1, year 2026.
3. Press **Check the sheet**. Nothing is saved yet. You see every mark, the topic of each question, and anything unclear.
4. Press **Save**. Each mark becomes a record tagged with its topic, under your name, and shows in each learner's map.

To make your own sheet, download the template on the same page. Choose a class and a subject, and it lists those learners and has a Topics sheet to pick from.

## Turn on sign-in and set up classes

1. Open **School** and create the school admin. From then on every page of data needs a username and a password.
2. On the same page, add each teacher. A new teacher sees no learner yet.
3. Open a class and give it to a teacher for a subject. The synthetic school already has one class per grade.

Seeding again (`uv run meska seed`) wipes all data, accounts and classes included.

## Arabic

The page is written in English. In Arabic, every piece of text that reaches the screen is looked up in three dictionaries in `src/meska_brain/web/static`: `ar.json` (the page), `ar-server.json` (sentences the server writes) and `ar-report.json` (the printable report). To change a word, change it there. Three registers are used on purpose:

- buttons, labels and help text: light Egyptian Arabic, the way Egyptian apps write;
- topic, strand and subject names: the Arabic of the school books;
- findings, explanations and the report: simple Modern Standard Arabic, because they go on a child's record.

Settings, read from the environment:

```
MESKA_LANGUAGE=ar          # ar (default) or en: the language the page opens in and findings are worded in
MESKA_ARABIC_WORDING=fixed # fixed (default): Arabic findings use sentences written in code. model: the model words them
```

`uv run meska seed` writes the made-up school in the language of `MESKA_LANGUAGE`.

## Looking after the records

```
uv run meska backup                          # one file in data/backups, newest 14 kept
uv run meska restore data/backups/<file>     # stop the app first
uv run meska export-learner K-42             # everything held about one learner, as a file
uv run meska delete-learner K-42 --code K-42 # for good
```

The same four jobs are on the School page for the admin. A backup holds names and is not encrypted. It stays on the same disk unless someone copies it elsewhere.

## What is not finished

- **No teacher has reviewed the maps.** The curriculum says what is taught and when. It does not say which topic depends on which. Those "needs this first" links (814 across the five subjects) were written by the authors of this software. The trace-back is only as good as those links. This is the first thing to fix before a pilot.
- **The topic lists come mostly from secondary sources.** The ministry's own site could not be read. Each pack lists its sources and says which were scanned ministry books, which were workbooks that follow the books, and which were news articles in Arabic. In short: English and Social Studies rest mostly on ministry books; Mathematics on ministry books for Primary term 1 and workbooks or articles for the rest; Science and Arabic on workbooks and articles only. Titles were shortened and, where the source was Arabic, translated by the authors.
- **The curriculum is changing under the map.** Primary 4 to 6 Science changed to new books in 2026/27 and the new term 2 books were not out when the map was made, so those 14 topics follow the earlier books and are marked `verified: false`. Preparatory 1 and 2 changed in 2024/25 and 2025/26. The Mathematics map was not checked against 2026/27 printings.
- **No Arabic speaker other than the authors has read the Arabic.** The page text (about 770 phrases), the server sentences (about 350) and 578 topic names were translated by the authors with the help of a language model. The topic names were written from knowledge of the school books, not copied from them, so some will differ from the book's wording. Teachers of each subject need to check them.
- **In Arabic the model does not word the findings.** The local model's Arabic dropped words and added claims in our tries, so Arabic findings and questions use fixed sentences. They are correct but all sound alike. Notes for families are still worded by the model, and a teacher must approve each one.
- **The guard is weaker in Arabic.** It is a word list written mostly for English. A teacher's Arabic edit that labels a child may get through. The teacher gates are the real protection.
- **Parts still in English in Arabic mode:** the raw entries of the audit log, tool names, file names, model names, and any server message that has no entry in the dictionary yet. The learning map and charts keep their left-to-right shape (grade 4 on the left). Numbers are not given Arabic plural forms, so counts are written like "عدد السجلات: 5".
- **Egyptian marking is not modelled.** A mark is a number out of a maximum. Term work, monthly tests and the colour levels used in the primary grades are not built in.
- **A class opens the whole record.** A teacher with a learner in a class sees that learner in every subject and every year, not only their own subject.
- **No HTTPS by default, no encryption at rest, no consent records, no scheduled or off-machine backup.** See [SECURITY.md](SECURITY.md).
- **Tested by the authors only.** 316 automated tests pass and the pages were checked by hand in one browser on one computer. No teacher has used it.
- **The agent was tried on the Egyptian school in a handful of runs, not measured.** The numbers in `EVALS.md` are for the original Meska Brain cohort (`uv run meska seed --pack generic-maths`), and `meska eval` still expects that cohort. See the note at the end of `EVALS.md`.
- **No fine-tuned model.** The stock open-weights model is used.
- **The offline Windows package was built and started on one computer only**, the one it was built on, which has a graphics card. It has not been tried on a school computer. Build it with `uv run python packaging/windows/build.py --out <a folder outside this one>`.

## Commands

```
uv run pytest -q                           # tests, no model needed
uv run ruff check src tests                # lint
uv run meska seed                          # rebuild the synthetic Egyptian school, five subjects (wipes everything)
uv run meska seed --pack egypt-maths       # one subject only
uv run meska seed --pack generic-maths     # the original Meska Brain cohort
uv run meska story                         # findings waiting and decided, no model used
uv run meska learners                      # list learners
uv run meska run <code> --file data/inbox/<file>   # run the agent for one learner
uv run meska report <code>                 # printable report, approved findings only
```

## Licence

Apache 2.0. See [LICENSE](LICENSE).
