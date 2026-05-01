"""
Interview Engine
- Generates role-specific interview questions from resume skills
- Evaluates answers and gives per-question feedback + overall score
- Suggests job titles based on skills + score
"""

import re

# ── Job title map: skill sets → suggested titles ──────────────────────────────
JOB_TITLE_MAP = [
    {
        "title": "Machine Learning Engineer",
        "required": ["python", "machine learning", "tensorflow", "pytorch", "numpy"],
        "bonus":    ["deep learning", "nlp", "scikit-learn", "keras"],
        "min_score": 60,
    },
    {
        "title": "Data Scientist",
        "required": ["python", "sql", "machine learning", "pandas", "numpy"],
        "bonus":    ["tableau", "power bi", "statistics", "r", "matplotlib"],
        "min_score": 50,
    },
    {
        "title": "Backend Developer",
        "required": ["python", "flask", "sql", "api", "docker"],
        "bonus":    ["django", "aws", "mongodb", "redis", "postgresql"],
        "min_score": 45,
    },
    {
        "title": "Full Stack Developer",
        "required": ["javascript", "react", "node", "sql", "html"],
        "bonus":    ["css", "typescript", "mongodb", "docker", "aws"],
        "min_score": 45,
    },
    {
        "title": "Frontend Developer",
        "required": ["javascript", "react", "html", "css"],
        "bonus":    ["typescript", "vue", "next", "tailwind", "figma"],
        "min_score": 40,
    },
    {
        "title": "DevOps Engineer",
        "required": ["docker", "aws", "linux", "ci/cd", "kubernetes"],
        "bonus":    ["terraform", "ansible", "jenkins", "prometheus", "grafana"],
        "min_score": 55,
    },
    {
        "title": "Data Analyst",
        "required": ["sql", "excel", "python", "pandas"],
        "bonus":    ["tableau", "power bi", "matplotlib", "statistics"],
        "min_score": 35,
    },
    {
        "title": "Software Engineer",
        "required": ["python", "java", "c++", "data structures", "algorithms"],
        "bonus":    ["system design", "git", "docker", "sql"],
        "min_score": 40,
    },
    {
        "title": "NLP / AI Researcher",
        "required": ["nlp", "python", "deep learning", "transformer", "pytorch"],
        "bonus":    ["bert", "gpt", "huggingface", "tensorflow", "research"],
        "min_score": 65,
    },
    {
        "title": "Junior Developer",
        "required": ["python", "html", "css"],
        "bonus":    ["javascript", "git", "sql"],
        "min_score": 0,
    },
]

# ── Question bank keyed by skill ──────────────────────────────────────────────
QUESTION_BANK = {
    "python": [
        {"q": "What is the difference between a list and a tuple in Python?",
         "keywords": ["mutable", "immutable", "list", "tuple", "ordered"],
         "ideal": "Lists are mutable (can be changed), tuples are immutable (cannot be changed after creation). Both are ordered sequences."},
        {"q": "Explain how Python's GIL (Global Interpreter Lock) works.",
         "keywords": ["thread", "lock", "interpreter", "concurrent", "cpu"],
         "ideal": "The GIL is a mutex that protects access to Python objects, preventing multiple threads from executing Python bytecode simultaneously."},
        {"q": "What are Python decorators and how do you use them?",
         "keywords": ["function", "wrapper", "decorator", "@", "higher order"],
         "ideal": "Decorators are functions that wrap other functions to extend their behavior without modifying them, using the @ syntax."},
    ],
    "machine learning": [
        {"q": "Explain the difference between overfitting and underfitting.",
         "keywords": ["overfitting", "underfitting", "bias", "variance", "training", "generalize"],
         "ideal": "Overfitting is when a model learns the training data too well including noise, performing poorly on new data. Underfitting is when the model is too simple to capture patterns."},
        {"q": "What is cross-validation and why is it important?",
         "keywords": ["fold", "validation", "training", "test", "generalization", "k-fold"],
         "ideal": "Cross-validation splits data into k folds, training on k-1 and testing on 1, repeated k times. It gives a reliable estimate of model performance."},
        {"q": "Explain gradient descent and its variants.",
         "keywords": ["gradient", "learning rate", "sgd", "batch", "optimization", "loss"],
         "ideal": "Gradient descent minimizes a loss function by iteratively moving in the direction of steepest descent. Variants include SGD, Mini-batch GD, Adam, and RMSProp."},
    ],
    "deep learning": [
        {"q": "What is backpropagation and how does it work?",
         "keywords": ["gradient", "chain rule", "weights", "loss", "backward", "derivative"],
         "ideal": "Backpropagation computes gradients of the loss with respect to weights using the chain rule, propagating errors backward through the network layers."},
        {"q": "Explain the vanishing gradient problem and how to solve it.",
         "keywords": ["vanishing", "gradient", "relu", "batch norm", "residual", "lstm"],
         "ideal": "When gradients become very small during backpropagation through many layers, weights stop updating. Solutions include ReLU, batch normalization, residual connections."},
    ],
    "sql": [
        {"q": "What is the difference between INNER JOIN and LEFT JOIN?",
         "keywords": ["inner", "left", "join", "null", "matching", "rows"],
         "ideal": "INNER JOIN returns only rows with matching values in both tables. LEFT JOIN returns all rows from the left table plus matching rows from the right (NULL if no match)."},
        {"q": "Explain database indexing and when to use it.",
         "keywords": ["index", "query", "performance", "b-tree", "slow", "fast"],
         "ideal": "Indexes speed up data retrieval by creating a data structure (usually B-tree) that allows fast lookups. Use on frequently queried columns, foreign keys, and WHERE clause columns."},
    ],
    "react": [
        {"q": "What is the difference between state and props in React?",
         "keywords": ["state", "props", "component", "mutable", "parent", "child"],
         "ideal": "Props are read-only data passed from parent to child. State is mutable data managed within a component that triggers re-renders when changed."},
        {"q": "Explain the useEffect hook and its use cases.",
         "keywords": ["useeffect", "side effect", "dependency", "cleanup", "lifecycle"],
         "ideal": "useEffect runs side effects after render. The dependency array controls when it runs. It replaces lifecycle methods and handles API calls, subscriptions, and DOM updates."},
    ],
    "javascript": [
        {"q": "Explain the concept of closures in JavaScript.",
         "keywords": ["closure", "scope", "function", "variable", "outer", "inner"],
         "ideal": "A closure is a function that retains access to its outer scope's variables even after the outer function has returned."},
        {"q": "What is the difference between == and === in JavaScript?",
         "keywords": ["equality", "type", "coercion", "strict", "loose"],
         "ideal": "== performs type coercion before comparison. === checks both value and type without coercion (strict equality)."},
    ],
    "docker": [
        {"q": "What is the difference between a Docker image and a container?",
         "keywords": ["image", "container", "running", "static", "instance", "template"],
         "ideal": "An image is a read-only template with instructions for creating a container. A container is a running instance of an image."},
        {"q": "Explain Docker Compose and when you would use it.",
         "keywords": ["compose", "multi", "service", "yaml", "orchestrate", "network"],
         "ideal": "Docker Compose defines and runs multi-container applications using a YAML file. Use it when your app needs multiple services like web + database + cache."},
    ],
    "aws": [
        {"q": "What is the difference between EC2 and Lambda?",
         "keywords": ["ec2", "lambda", "serverless", "server", "instance", "function"],
         "ideal": "EC2 is a virtual server you manage and pay for continuously. Lambda is serverless — runs functions on demand and you pay only for execution time."},
    ],
    "flask": [
        {"q": "How does Flask handle routing and what are route decorators?",
         "keywords": ["route", "decorator", "@app", "url", "endpoint", "function"],
         "ideal": "Flask uses @app.route() decorators to map URL patterns to Python functions. Routes can include dynamic segments and specify HTTP methods."},
    ],
    "java": [
        {"q": "What is the difference between abstract classes and interfaces in Java?",
         "keywords": ["abstract", "interface", "implement", "extend", "method", "multiple"],
         "ideal": "Abstract classes can have implemented methods and state, support single inheritance. Interfaces define contracts, support multiple implementation, and (since Java 8) can have default methods."},
    ],
    "nlp": [
        {"q": "What is tokenization and why is it important in NLP?",
         "keywords": ["token", "word", "sentence", "split", "text", "preprocessing"],
         "ideal": "Tokenization splits text into tokens (words, subwords, or characters). It's the foundational preprocessing step that converts raw text into units models can process."},
        {"q": "Explain the transformer architecture and attention mechanism.",
         "keywords": ["attention", "transformer", "query", "key", "value", "self-attention"],
         "ideal": "Transformers use self-attention to weigh relationships between all tokens simultaneously. Attention computes Q/K/V matrices to determine how much focus each token gets."},
    ],
    "data structures": [
        {"q": "Explain the time complexity of common operations in a hash table.",
         "keywords": ["o(1)", "hash", "collision", "average", "worst", "lookup"],
         "ideal": "Average case: O(1) for insert, lookup, delete. Worst case: O(n) due to collisions. Good hash functions and load factor management keep operations near O(1)."},
    ],
    "algorithms": [
        {"q": "What is dynamic programming and how does it differ from recursion?",
         "keywords": ["memoization", "subproblem", "optimal", "overlap", "dp", "cache"],
         "ideal": "Dynamic programming solves problems by breaking them into overlapping subproblems and caching results. Unlike plain recursion, it avoids recomputing the same subproblems."},
    ],
    "mongodb": [
        {"q": "What are the key differences between MongoDB and a relational database?",
         "keywords": ["document", "schema", "nosql", "collection", "flexible", "join"],
         "ideal": "MongoDB is a NoSQL document database storing data as JSON-like documents with flexible schemas. Unlike relational DBs, it lacks joins and ACID transactions by default but scales horizontally easily."},
    ],
}

# Generic fallback questions for any skill not in the bank
GENERIC_QUESTIONS = [
    {"q": "Describe a challenging project where you used this skill and how you solved the problem.",
     "keywords": ["project", "problem", "solution", "challenge", "built", "implemented"],
     "ideal": "A strong answer describes a specific project, the technical challenge faced, your approach to solving it, and the outcome achieved."},
    {"q": "How do you stay up to date with the latest developments in this area?",
     "keywords": ["learn", "blog", "course", "paper", "community", "practice", "read"],
     "ideal": "Good answers mention specific resources: courses, papers, communities, side projects, or open source contributions."},
]


def generate_questions(matched_skills: list, n: int = 7) -> list:
    """
    Given a list of matched skills from the resume,
    return n interview questions covering different skills.
    """
    questions = []
    seen_skills = set()

    skills_lower = [s.lower().strip() for s in matched_skills]

    for skill in skills_lower:
        if skill in QUESTION_BANK and skill not in seen_skills:
            bank = QUESTION_BANK[skill]
            # Pick first question from each skill for variety
            q = bank[0].copy()
            q["skill"] = skill
            q["id"]    = len(questions)
            questions.append(q)
            seen_skills.add(skill)
        if len(questions) >= n:
            break

    # Pad with generic questions if needed
    while len(questions) < min(n, 3):
        gq = GENERIC_QUESTIONS[len(questions) % len(GENERIC_QUESTIONS)].copy()
        gq["skill"] = "general"
        gq["id"]    = len(questions)
        questions.append(gq)

    return questions[:n]


def evaluate_answer(question: dict, answer: str) -> dict:
    """
    Score a single answer 0-100 based on keyword matching + length.
    Returns score, feedback, and the ideal answer.
    """
    answer_lower = answer.lower().strip()
    keywords     = question.get("keywords", [])

    if not answer_lower or len(answer_lower.split()) < 3:
        return {
            "score":    0,
            "feedback": "Answer too short. Please provide a detailed response.",
            "ideal":    question.get("ideal", ""),
            "matched_keywords": [],
        }

    matched_kw = [kw for kw in keywords if kw.lower() in answer_lower]
    kw_score   = int((len(matched_kw) / max(len(keywords), 1)) * 70)

    # Length bonus (up to 20 points)
    word_count   = len(answer_lower.split())
    length_bonus = min(word_count * 1.5, 20)

    # Confidence bonus — specific numbers, examples
    specificity  = 10 if re.search(r'\d+|example|project|built|used|implemented', answer_lower) else 0

    raw_score = int(kw_score + length_bonus + specificity)
    score     = max(0, min(100, raw_score))

    # Feedback
    if score >= 80:
        feedback = "Excellent answer! You covered the key concepts well."
    elif score >= 60:
        feedback = f"Good answer. You could also mention: {', '.join(kw for kw in keywords if kw not in matched_kw)[:3]}."
    elif score >= 40:
        feedback = f"Partial answer. Key concepts to add: {', '.join(kw for kw in keywords if kw not in matched_kw)}."
    else:
        feedback = f"Needs improvement. Focus on: {', '.join(keywords[:4])}."

    return {
        "score":            score,
        "feedback":         feedback,
        "ideal":            question.get("ideal", ""),
        "matched_keywords": matched_kw,
    }


def evaluate_all_answers(questions: list, answers: dict) -> dict:
    """
    Evaluate all answers.
    answers = {question_id (str): answer_text}
    Returns per-question results + overall score.
    """
    results     = []
    total_score = 0

    for q in questions:
        qid    = str(q["id"])
        answer = answers.get(qid, "").strip()
        result = evaluate_answer(q, answer)
        results.append({
            "id":       q["id"],
            "skill":    q.get("skill", "general"),
            "question": q["q"],
            **result
        })
        total_score += result["score"]

    overall = int(total_score / max(len(questions), 1))

    if overall >= 80:
        level = "Expert"
    elif overall >= 65:
        level = "Proficient"
    elif overall >= 45:
        level = "Intermediate"
    else:
        level = "Beginner"

    return {
        "results":       results,
        "overall_score": overall,
        "level":         level,
    }


def suggest_job_titles(matched_skills: list, ats_score: int, interview_score: int = 0) -> list:
    """
    Suggest ranked job titles based on skill overlap + scores.
    Returns top 5 with match percentage.
    """
    skills_lower = set(s.lower().strip() for s in matched_skills)
    combined_score = int(ats_score * 0.6 + interview_score * 0.4)

    suggestions = []

    for job in JOB_TITLE_MAP:
        if combined_score < job["min_score"]:
            continue

        required_match = sum(1 for r in job["required"] if r in skills_lower)
        bonus_match    = sum(1 for b in job["bonus"]    if b in skills_lower)

        total_possible = len(job["required"]) + len(job["bonus"])
        total_matched  = required_match + bonus_match

        if required_match == 0:
            continue

        match_pct = int((total_matched / max(total_possible, 1)) * 100)

        suggestions.append({
            "title":          job["title"],
            "match":          match_pct,
            "required_found": required_match,
            "required_total": len(job["required"]),
            "missing_skills": [r for r in job["required"] if r not in skills_lower][:3],
        })

    # Sort by match descending
    suggestions.sort(key=lambda x: x["match"], reverse=True)
    return suggestions[:5]
