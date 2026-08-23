# Prévision de Rentabilité Obligataire

## Présentation

Cette application Streamlit permet d'estimer la rentabilité prévisionnelle d'un portefeuille obligataire sur un horizon compris entre 3 mois et 1 an.

Le modèle repose sur une approche de performance totale ("Total Return") intégrant :

- Le portage (Carry)
- Le Roll-Down
- L'effet de variation des taux d'intérêt
- La convexité
- Des scénarios de marché probabilisés

L'application est destinée aux investisseurs institutionnels, caisses de retraite, compagnies d'assurance, trésoreries et sociétés de gestion.

---

## Fonctionnalités

### Calcul de rentabilité prévisionnelle

La performance attendue de chaque ligne obligataire est calculée selon la formule :

```text
Total Return =
Carry
+ Roll-Down
- Duration × ΔTaux
+ 0.5 × Convexité × (ΔTaux²)
