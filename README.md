# LLM Output Evaluation Framework

Ek reusable framework jo LLM responses ko automatically evaluate karta hai, do prompt versions
(ya do models) ko compare karta hai, aur LLM judge ko apne manual labels se validate karta hai.

## Features
| Check | Type | Kya dekhta hai |
|---|---|---|
| Factual consistency | Code (exact + fuzzy match) | Answer reference se match karta hai? Score 0-1 |
| Format compliance | Code (regex, JSON schema) | JSON / 3 bullets / one sentence / max 20 words / number only |
| LLM-as-judge | LLM + rubric | correctness, relevance, clarity, overall (1-5) |

Test set: `data/test_set.json`, 50 prompts (5 format types x 10). Har item me `question`, `reference`
(alternatives `|` se alag) aur `format` spec hota hai.

## Project structure
```
llm-eval-framework/
├── evaluators/        factual.py, format_check.py, judge.py, utils.py
├── data/              test_set.json, manual_labels.csv (aap banayenge)
├── results/           run outputs, agreement.json, comparison.png
├── llm_client.py      OpenAI-compatible client (retry + disk cache)
├── prompts.py         prompt versions v1 (casual) aur v2 (strict)
├── runner.py          model + prompt ko test set par chalata aur score karta hai
├── compare.py         do runs compare karke report.md banata hai
├── sample_for_labeling.py   20 samples manual labelling ke liye
├── agreement.py       judge vs manual labels (kappa, Spearman)
├── build_test_set.py  test set generate karta hai
└── report.md          generated report
```

## Setup
```bash
python -m venv venv
venv\Scripts\activate          # Windows   (Linux/Mac: source venv/bin/activate)
pip install -r requirements.txt
copy .env.example .env         # Linux/Mac: cp .env.example .env
```
`.env` me `API_KEY`, `BASE_URL`, `MODEL_A`, `MODEL_B`, `JUDGE_MODEL` likhein.
Koi bhi OpenAI-compatible provider chalta hai (Groq, OpenRouter, Together, OpenAI, Ollama).

## Usage

### 1. Test set (already included; dobara banana ho to)
```bash
python build_test_set.py
```

### 2. Runs chalayein
Prompt versions compare karne ke liye (same model):
```bash
python runner.py --name v1_modelA --model <MODEL_A> --prompt v1
python runner.py --name v2_modelA --model <MODEL_A> --prompt v2
```
Models compare karne ke liye (same prompt):
```bash
python runner.py --name v2_modelB --model <MODEL_B> --prompt v2
```
Pehle chhota test: `--limit 5`. Responses `.cache/` me save hote hain, isliye dobara run par API call nahi hoti.

### 3. Judge ko manual labels se validate karein
```bash
python sample_for_labeling.py --runs v1_modelA v2_modelA
```
`data/manual_labels.csv` kholein aur **judge scores dekhe baghair** `manual_score` (1-5) bharein.
Phir:
```bash
python agreement.py
```

### 4. Report
```bash
python compare.py --a v1_modelA --b v2_modelA
```
`report.md` aur `results/comparison.png` ban jate hain. Aakhri section "Analysis and limitations" me apni observations likhein.

## Manual labelling rubric (judge wala hi)
- 5 = bilkul sahi, reference se match, saaf aur relevant
- 4 = sahi, thori si imprecision ya extra detail
- 3 = aadha sahi ya incomplete
- 2 = zyada tar ghalat
- 1 = ghalat ya reference ke khilaf

Format ka marks na kaatein; wo alag check hai.

## Design decisions
- **Format alag, content alag:** format code se check hota hai (reproducible), judge sirf content dekhta hai.
- **Judge temperature 0 + structured JSON:** consistent scores; parse fail par retry.
- **Cache:** same prompt dobara run karne par paisa aur time bachta hai.
- **Judge validation:** Cohen's kappa (quadratic weighted), Spearman, exact aur within-1 agreement.

## Limitations
- Factual check keyword/reference based hai; lambay explanations ke liye judge zyada mufeed hai.
- 20 manual samples se agreement estimate kam bharosemand hai (chhota sample).
- Judge ka bias ho sakta hai (apne model ya lambay answers ko pasand karna).
