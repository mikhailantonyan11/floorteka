# Классификация жанра фильма по описанию

Мультиклассовая задача (3 класса):

| Код | Жанр   |
|-----|--------|
| 0   | action |
| 1   | comedy |
| 2   | drama  |

Метрика: **Macro F1**. Баллы: `max(0, F1 − 0.50) / 0.50`.

## Данные

- `data/train.csv` — `id`, `description`, `genre`
- `data/test.csv` — `id`, `description`
- `data/submission.csv` — готовый сабмит

## Подход

1. **Предобработка:** lowercasing, удаление URL/пунктуации/цифр, нормализация пробелов.
2. **Стемминг:** Snowball (русский).
3. **Признаки:** TF-IDF word n-grams `(1,3)` + char_wb n-grams `(3,6)`.
4. **Классификатор:** Logistic Regression (`C=2`, `class_weight=balanced`).

## Результат (5-fold CV)

Macro F1 ≈ **0.936** → ориентировочно **~0.87** балла по шкале челленджа.

## Запуск

```bash
pip install -r solution/requirements.txt
python solution/train_predict.py --cv
```

Сабмит пишется в `data/submission.csv`.
