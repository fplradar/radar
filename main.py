from datetime import datetime

now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

with open("resume.md", "w", encoding="utf-8") as f:
    f.write(f"# Rapport automatique\n\nDernière exécution : {now}\n")

print("Fichier resume.md généré.")

