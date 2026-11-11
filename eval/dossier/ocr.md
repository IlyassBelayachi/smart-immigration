# Lecture des spécimens scannés

Les trois PDF de `data/synthetic/` contiennent une image sans texte sélectionnable. Les fichiers TXT correspondants fournissent les valeurs attendues. Le test `test_reads_all_fields_on_clean_raster_specimens` vérifie l’extraction via l’API et la demande de confirmation.

Sur ces trois scans nets, 12 champs sur 12 ont été détectés. La lettre d’acceptation et le justificatif financier donnent respectivement 5 sur 5 et 4 sur 4 valeurs exactes. Le relevé donne 1 sur 3 valeurs exactes. L’OCR a lu « Collége » pour « Collège » et un trait d’union pour le tiret de « 2024–2026 ». Ces résultats portent sur les spécimens fournis.

La reconnaissance utilise le modèle latin PP-OCRv3 distribué par RapidAI pour RapidOCR v3.10.0. Son SHA-256 est `e9d7a33667e8aaa702862975186adf2012e3f390cc0f9422865957125f8071cf`. [Catalogue et empreinte](https://github.com/RapidAI/RapidOCR/blob/main/python/rapidocr/default_models.yaml) · [Modèle ONNX](https://www.modelscope.cn/models/RapidAI/RapidOCR/resolve/v3.10.0/onnx/PP-OCRv4/rec/latin_PP-OCRv3_rec_mobile.onnx)
