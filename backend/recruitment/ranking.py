"""
AI-ранжирование кандидатов.

Итоговая оценка:
  - Если сохранённая модель существует:
      ai_score = 0.4 × tf_score + 0.6 × model_probability  (alpha=0.4)
  - Если модели нет:
      ai_score = tf_score  (alpha=1.0, только TF-IDF)

Стек:
  - pymorphy3 — лемматизация русского текста
  - TfidfVectorizer + LogisticRegression — Pipeline, сохраняется в ml_models/recruitment_model.pkl
  - retrain_model() вызывается при смене статуса кандидата на hired/rejected
"""
import os
import re
import logging

logger = logging.getLogger(__name__)

MODEL_PATH = os.path.join(
    os.path.dirname(os.path.dirname(os.path.abspath(__file__))),
    'ml_models', 'recruitment_model.pkl',
)

# ── Стоп-слова ──────────────────────────────────────────────────────────────────

STOPWORDS = {
    'и', 'в', 'во', 'не', 'что', 'он', 'на', 'я', 'с', 'со', 'как', 'а',
    'то', 'все', 'она', 'так', 'его', 'но', 'да', 'ты', 'к', 'у', 'же',
    'вы', 'за', 'бы', 'по', 'только', 'ее', 'мне', 'было', 'вот', 'от',
    'меня', 'еще', 'нет', 'о', 'из', 'ему', 'теперь', 'когда', 'даже',
    'ну', 'вдруг', 'ли', 'если', 'уже', 'или', 'ни', 'быть', 'был',
    'него', 'до', 'вас', 'нибудь', 'опять', 'уж', 'вам', 'ведь', 'там',
    'потом', 'себя', 'ничего', 'ей', 'может', 'они', 'тут', 'где', 'есть',
    'надо', 'ней', 'для', 'мы', 'тебя', 'их', 'чем', 'была', 'сам', 'чтоб',
    'без', 'будто', 'чего', 'раз', 'тоже', 'себе', 'под', 'будет', 'ж',
    'тогда', 'кто', 'этот', 'того', 'потому', 'этого', 'какой', 'совсем',
    'ним', 'здесь', 'этом', 'один', 'почти', 'мой', 'тем', 'чтобы', 'нее',
    'сейчас', 'были', 'куда', 'зачем', 'всех', 'никогда', 'можно', 'при',
    'наконец', 'два', 'об', 'другой', 'хоть', 'после', 'над', 'больше',
    'тот', 'через', 'эти', 'нас', 'про', 'всего', 'них', 'какая', 'много',
    'разве', 'три', 'эту', 'моя', 'впрочем', 'хорошо', 'свою', 'этой',
    'перед', 'иногда', 'лучше', 'чуть', 'том', 'нельзя', 'такой', 'им',
    'более', 'всегда', 'конечно', 'всю', 'между', 'опыт', 'работа', 'год',
    'лет', 'также', 'должен', 'это', 'своей', 'наш', 'ваш',
}

# ── Морфологический анализатор ─────────────────────────────────────────────────

try:
    import pymorphy3
    _morph = pymorphy3.MorphAnalyzer()

    def _lemmatize(text: str) -> str:
        text   = text.lower()
        tokens = re.findall(r'[а-яёa-z0-9]+', text)
        result = []
        for t in tokens:
            if len(t) <= 2 or t in STOPWORDS:
                continue
            parsed = _morph.parse(t)
            lemma  = parsed[0].normal_form if parsed else t
            if lemma not in STOPWORDS:
                result.append(lemma)
        return ' '.join(result)

    _MORPH_AVAILABLE = True

except ImportError:
    _MORPH_AVAILABLE = False

    def _lemmatize(text: str) -> str:
        text   = text.lower()
        tokens = re.findall(r'[а-яёa-z0-9]+', text)
        return ' '.join(t for t in tokens if len(t) > 2 and t not in STOPWORDS)


# ── sklearn ────────────────────────────────────────────────────────────────────

try:
    from sklearn.feature_extraction.text import TfidfVectorizer
    from sklearn.linear_model import LogisticRegression
    from sklearn.pipeline import Pipeline
    from sklearn.metrics.pairwise import cosine_similarity
    from sklearn.metrics import accuracy_score, roc_auc_score
    import numpy as np
    import joblib
    _SKLEARN_AVAILABLE = True
except ImportError:
    _SKLEARN_AVAILABLE = False


# ── Вспомогательные функции ───────────────────────────────────────────────────

def _candidate_text(candidate) -> str:
    parts = [
        getattr(candidate, 'resume_text', '') or '',
        getattr(candidate, 'cover_letter', '') or '',
        getattr(candidate, 'notes', '') or '',
    ]
    return ' '.join(p for p in parts if p.strip())


def _vacancy_text(vacancy) -> str:
    skills = ' '.join(getattr(vacancy, 'required_skills', []) or [])
    parts = [
        getattr(vacancy, 'title', '') or '',
        getattr(vacancy, 'description', '') or '',
        getattr(vacancy, 'requirements', '') or '',
        getattr(vacancy, 'responsibilities', '') or '',
        skills,
    ]
    return ' '.join(p for p in parts if p.strip())


# ── Сохранённая модель ─────────────────────────────────────────────────────────

_cached_model = None
_cached_mtime: float | None = None


def _load_saved_model():
    """Загружает Pipeline из pkl с кэшированием по mtime."""
    global _cached_model, _cached_mtime
    if not _SKLEARN_AVAILABLE:
        return None
    try:
        if not os.path.exists(MODEL_PATH):
            return None
        mtime = os.path.getmtime(MODEL_PATH)
        if _cached_model is None or _cached_mtime != mtime:
            _cached_model = joblib.load(MODEL_PATH)
            _cached_mtime = mtime
        return _cached_model
    except Exception as exc:
        logger.warning('[Recruitment ML] Ошибка загрузки модели: %s', exc)
        return None


def retrain_model() -> bool:
    """
    Обучает Pipeline(TfidfVectorizer, LogisticRegression) на кандидатах
    с заполненным hiring_result (True=принят, False=отклонён).
    Требует не менее 10 записей с обоими классами.
    Возвращает True если переобучение произошло, False иначе.
    """
    if not _SKLEARN_AVAILABLE:
        return False
    try:
        from recruitment.models import Candidate  # noqa: avoid circular at module level

        labeled = list(
            Candidate.objects.filter(hiring_result__isnull=False)
            .exclude(resume_text='')
        )
        if len(labeled) < 10:
            logger.info('[Recruitment ML] Недостаточно данных (%d < 10), пропуск', len(labeled))
            return False

        texts  = [_candidate_text(c) for c in labeled]
        labels = [1 if c.hiring_result else 0 for c in labeled]

        if len(set(labels)) < 2:
            logger.info('[Recruitment ML] Нет обоих классов, пропуск')
            return False

        pipe = Pipeline([
            ('tfidf', TfidfVectorizer(max_features=1000)),
            ('lr',    LogisticRegression(max_iter=500, C=1.0, random_state=42)),
        ])
        pipe.fit(texts, labels)

        os.makedirs(os.path.dirname(MODEL_PATH), exist_ok=True)
        joblib.dump(pipe, MODEL_PATH)

        hired_n    = sum(labels)
        rejected_n = len(labels) - hired_n
        print(f'[Recruitment ML] Модель переобучена: n={len(labeled)} '
              f'(hired={hired_n}, rejected={rejected_n})')
        logger.info('[Recruitment ML] Модель сохранена в %s', MODEL_PATH)

        # Сбрасываем кэш
        global _cached_model, _cached_mtime
        _cached_model = None
        _cached_mtime = None
        return True

    except Exception as exc:
        logger.error('[Recruitment ML] Ошибка переобучения: %s', exc)
        return False


def _heuristic_score(cand_text: str, vac_text: str, rating: int) -> dict:
    cset  = set(_lemmatize(cand_text).split())
    vset  = set(_lemmatize(vac_text).split())
    inter = cset & vset
    tf    = min(len(inter) / max(len(vset), 1) * 3.0, 1.0)
    prob  = min(0.5 * tf + 0.5 * (rating / 5.0), 1.0)
    score = round(0.4 * tf + 0.6 * prob, 4)
    return {
        'tf_score':            round(tf, 4),
        'ai_score':            score,
        'ml_hiring_probability': round(prob, 4),
        'extracted_skills':    list(inter)[:10],
    }


# ── Основной класс ─────────────────────────────────────────────────────────────

class CandidateRanker:
    """
    Ранжирует кандидата относительно вакансии.

    Итоговая формула (НИР):
        ai_score = 0.4 × tf_score + 0.6 × ml_hiring_probability

    tf_score             — косинусное сходство TF-IDF резюме ↔ вакансия  (0..1)
    ml_hiring_probability — LogisticRegression на hired=1 / rejected=0   (0..1)
    ai_score             — итоговая взвешенная оценка                     (0..1)
    extracted_skills     — ключевые навыки кандидата
    ai_comment           — текстовый комментарий
    """

    def analyze(self, candidate, vacancy, all_candidates=None) -> dict:
        cand_raw = _candidate_text(candidate)
        vac_raw  = _vacancy_text(vacancy)

        if not _SKLEARN_AVAILABLE:
            result = _heuristic_score(cand_raw, vac_raw, candidate.rating)
            result['ai_comment'] = self._comment(
                result['ai_score'], result['ml_hiring_probability'], result['extracted_skills'], 0.4
            )
            return result

        cand_proc = _lemmatize(cand_raw) if cand_raw.strip() else ''
        vac_proc  = _lemmatize(vac_raw)

        # ── TF-IDF косинусное сходство ─────────────────────────────────────
        if cand_proc.strip():
            try:
                vec    = TfidfVectorizer(min_df=1, max_features=1000, ngram_range=(1, 2))
                matrix = vec.fit_transform([cand_proc, vac_proc])
                tf_score = float(cosine_similarity(matrix[0], matrix[1])[0][0])
            except Exception:
                tf_score = 0.0
        else:
            tf_score = 0.0

        # ── Извлечение навыков ─────────────────────────────────────────────
        extracted_skills = self._extract_skills(cand_proc, vac_proc)

        # ── ML вероятность найма ───────────────────────────────────────────
        saved_model = _load_saved_model()
        if saved_model is not None:
            try:
                text_input = cand_proc if cand_proc.strip() else ' '
                ml_prob = float(saved_model.predict_proba([text_input])[0][1])
            except Exception:
                ml_prob = tf_score
            alpha = 0.4  # 60% ML + 40% TF-IDF
        else:
            # Нет сохранённой модели — только TF-IDF (alpha=1.0)
            ml_prob = tf_score
            alpha = 1.0

        tf_score = round(max(0.0, min(1.0, tf_score)), 4)
        ml_prob  = round(max(0.0, min(1.0, ml_prob)),  4)

        # ── Итоговая формула ───────────────────────────────────────────────
        ai_score = round(alpha * tf_score + (1.0 - alpha) * ml_prob, 4)

        return {
            'tf_score':              tf_score,
            'ai_score':              ai_score,
            'ml_hiring_probability': ml_prob,
            'extracted_skills':      extracted_skills,
            'ai_comment':            self._comment(ai_score, ml_prob, extracted_skills, alpha),
        }

    # ── Извлечение навыков ─────────────────────────────────────────────────

    def _extract_skills(self, cand_proc: str, vac_proc: str) -> list:
        if not cand_proc.strip():
            return []
        try:
            vec          = TfidfVectorizer(min_df=1, max_features=300)
            matrix       = vec.fit_transform([cand_proc, vac_proc])
            feature_names = vec.get_feature_names_out()
            cand_scores  = dict(zip(feature_names, matrix[0].toarray()[0]))
            vac_words    = set(vac_proc.split())

            relevant = sorted(
                [(k, v) for k, v in cand_scores.items() if k in vac_words and v > 0],
                key=lambda x: -x[1],
            )[:8]
            extra = sorted(
                [(k, v) for k, v in cand_scores.items() if k not in vac_words and v > 0],
                key=lambda x: -x[1],
            )[:max(0, 10 - len(relevant))]

            return [k for k, _ in (relevant + extra)]
        except Exception:
            return []

    # ── LogisticRegression на реальных данных hiring_result ───────────────

    def _lr_probability(self, candidate, tf_score: float,
                        all_candidates: list, vac_proc: str) -> float:
        """
        Обучает LR на бинарных метках: hired=1, rejected=0.
        Если таких кандидатов менее 4 (или нет обоих классов) — используется только TF-IDF.
        """
        rating_norm = candidate.rating / 5.0

        # Только binary labels: hired / rejected
        binary_labeled = [
            (c, 1 if c.stage == 'hired' else 0)
            for c in all_candidates
            if c.stage in ('hired', 'rejected') and _candidate_text(c).strip()
        ]

        if len(binary_labeled) >= 4:
            try:
                feats, labels = [], []
                for c, label_val in binary_labeled:
                    c_proc = _lemmatize(_candidate_text(c))
                    c_sim  = 0.0
                    if c_proc.strip() and vac_proc.strip():
                        vec   = TfidfVectorizer(min_df=1, max_features=500)
                        mat   = vec.fit_transform([c_proc, vac_proc])
                        c_sim = float(cosine_similarity(mat[0], mat[1])[0][0])
                    feats.append([c_sim, c.rating / 5.0])
                    labels.append(label_val)

                feats_np  = np.array(feats)
                labels_np = np.array(labels)

                if len(np.unique(labels_np)) == 2:
                    clf = LogisticRegression(max_iter=500, C=1.0, random_state=42)
                    clf.fit(feats_np, labels_np)
                    prob = float(clf.predict_proba([[tf_score, rating_norm]])[0][1])

                    # Метрики на обучающей выборке
                    preds    = clf.predict(feats_np)
                    acc      = accuracy_score(labels_np, preds)
                    try:
                        auc = roc_auc_score(labels_np, clf.predict_proba(feats_np)[:, 1])
                    except Exception:
                        auc = float('nan')
                    print(
                        f'[Ranking LR] n_labeled={len(binary_labeled)} '
                        f'(hired={labels_np.sum()}, rejected={(labels_np==0).sum()}) | '
                        f'accuracy={acc:.3f} | AUC={auc:.3f} | '
                        f'tf_score={tf_score:.3f} | ml_prob={prob:.3f} | '
                        f'ai_score={0.4*tf_score + 0.6*prob:.3f}'
                    )
                    return prob
            except Exception as e:
                logger.debug('[Ranking] LR fit failed: %s', e)

        # Если данных мало — используем только TF-IDF часть (ml_prob = tf_score)
        logger.info(
            '[Ranking LR] Мало labeled данных (%d), используется TF-IDF only',
            len(binary_labeled),
        )
        return tf_score

    # ── Текстовый комментарий ──────────────────────────────────────────────

    def _comment(self, ai_score: float, prob: float, skills: list, alpha: float = 0.4) -> str:
        if ai_score >= 0.7:
            rel = 'Высокая релевантность'
        elif ai_score >= 0.4:
            rel = 'Средняя релевантность'
        elif ai_score > 0:
            rel = 'Низкая релевантность'
        else:
            rel = 'Текст резюме отсутствует — анализ по рейтингу'

        if prob >= 0.7:
            likelihood = 'высокая вероятность найма'
        elif prob >= 0.4:
            likelihood = 'умеренная вероятность найма'
        else:
            likelihood = 'низкая вероятность найма'

        skill_str = ', '.join(skills[:5]) if skills else 'не определены'
        formula = f'{alpha:.0%}×TF-IDF + {1-alpha:.0%}×ML' if alpha < 1.0 else '100%×TF-IDF'
        return (
            f'{rel}. По модели: {likelihood} ({prob:.0%}). '
            f'Ключевые навыки: {skill_str}. '
            f'Итоговая AI-оценка: {ai_score:.2f} ({formula}).'
        )
