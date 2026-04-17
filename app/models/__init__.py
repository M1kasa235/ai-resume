# app/models/__init__.py
from app.models.user import User
from app.models.job import Job, JobCategory, UserFavoriteJob
from app.models.application import Application
from app.models.interview import Interview, AIInterview, AIInterviewQA
from app.models.question import Question, QuestionCategory, UserPractice, UserWrongQuestion

__all__ = [
    "User",
    "Job",
    "JobCategory",
    "UserFavoriteJob",
    "Application",
    "Interview",
    "AIInterview",
    "AIInterviewQA",
    "Question",
    "QuestionCategory",
    "UserPractice",
    "UserWrongQuestion",
]