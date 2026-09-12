"""Teacher-only interoperability exports. Answer keys must never enter student APIs."""
import csv
import io
from .catalogue import BY_CHAPTER
from shared.science.vendor.classquiz_contract import QuizInput

def interactive_quiz_payload(chapter):
    entry=BY_CHAPTER[chapter]
    questions=[]
    for task in entry["tasks"]:
        if task["response_type"]!="choice":continue
        answer=next(o["label"] for o in task["options"] if o["id"]==task["rule"]["expected"])
        questions.append(dict(question=task["question"],options=[o["label"] for o in task["options"]],correct_answer=answer,explanation=" ".join(task["rule"]["solution_steps"])))
    return dict(title=entry["title"],questions=questions)

def classquiz_payload(chapter):
    quiz=interactive_quiz_payload(chapter)
    return QuizInput.model_validate(dict(title=quiz["title"],description="Histoire CM2 — faire justifier chaque réponse. Export pour relecture adulte.",public=False,
        questions=[dict(question=q["question"],time="180",type="ABCD",hide_results=True,answers=[dict(answer=o,right=o==q["correct_answer"]) for o in q["options"]]) for q in quiz["questions"]])).model_dump(mode="json")

def quizli_csv(chapter):
    # Quiz.from_csv expects two columns without a header (upstream quiz.py:160).
    out=io.StringIO(newline="")
    writer=csv.writer(out)
    for q in interactive_quiz_payload(chapter)["questions"]:
        writer.writerow([q["question"],q["correct_answer"]])
    return out.getvalue()
