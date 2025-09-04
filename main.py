from datetime import datetime

# Script de test : il crée/écrase un fichier résumé.md avec l'heure actuelle
now = datetime.utcnow().strftime("%Y-%m-%d %H:%M:%S UTC")

with open("résumé.md", "w", encoding="utf-8") as f:
    f.write(f"# Rapport automatique\n\nDernière exécution : {now}\n")

print("Fichier résumé.md généré.")
