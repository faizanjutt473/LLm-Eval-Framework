"""Terminal me ek ek sample dikha kar manual_score leta hai.

    python label_cli.py

Number type karein (1-5) aur Enter dabayein.
's' = skip, 'q' = save karke bahar. Har jawab ke baad file save hoti hai.
"""
import pandas as pd

PATH = "data/manual_labels.csv"

df = pd.read_csv(PATH, dtype=str, keep_default_na=False)
todo = [i for i in df.index if df.at[i, "manual_score"].strip() == ""]
print(f"{len(todo)} samples baaki hain.\n")
print("Rubric: 5=bilkul sahi | 4=sahi, thori imprecision | 3=aadha sahi | 2=zyada ghalat | 1=ghalat")
print("(Format ke number na kaatein. 's'=skip, 'q'=quit)\n")

for n, i in enumerate(todo, 1):
    row = df.loc[i]
    print("=" * 70)
    print(f"[{n}/{len(todo)}]  id={row['id']}")
    print(f"SAWAL    : {row['question']}")
    print(f"REFERENCE: {row['reference']}")
    print(f"JAWAB    :\n{row['response']}\n")
    while True:
        ans = input("Aapka number (1-5): ").strip().lower()
        if ans in {"1", "2", "3", "4", "5"}:
            df.at[i, "manual_score"] = ans
            df.to_csv(PATH, index=False)
            break
        if ans == "s":
            break
        if ans == "q":
            df.to_csv(PATH, index=False)
            raise SystemExit("Save ho gaya. Baaqi baad me.")
        print("Sirf 1, 2, 3, 4 ya 5 likhein.")

print("\nSab ho gaya. Ab: python agreement.py")