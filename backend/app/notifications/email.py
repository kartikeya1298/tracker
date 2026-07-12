import logging
import smtplib
from email.message import EmailMessage

from app.config import get_settings
from app.models import Company, Job

logger = logging.getLogger(__name__)


def _build_email(job: Job, company: Company) -> EmailMessage:
    settings = get_settings()
    msg = EmailMessage()
    msg["Subject"] = f"New DS role: {job.title} @ {company.name} ({job.location})"
    msg["From"] = settings.notification_from_email
    msg["To"] = ", ".join(settings.notification_to_emails)

    exp = job.experience_required or "Not specified"
    salary = job.salary or "Not disclosed"
    skills = job.skills or job.ai_skills or "Not specified"
    summary = job.ai_summary or (job.description[:400] + "...") if job.description else ""

    body = f"""New matching Data Science role found!

Company:     {company.name}
Role:        {job.title}
Location:    {job.location}
Experience:  {exp}
Salary:      {salary}
Skills:      {skills}

Summary:
{summary}
"""
    if job.resume_match_score is not None:
        body += f"\nResume match score: {job.resume_match_score}/100\n{job.resume_match_notes}\n"
    if job.learning_recommendations:
        body += f"\nSuggested to close skill gaps: {job.learning_recommendations}\n"

    body += f"\nApply here: {job.apply_url}\n"

    msg.set_content(body)
    return msg


def send_job_notification(job: Job, company: Company) -> bool:
    settings = get_settings()
    if not settings.smtp_host or not settings.notification_to_emails:
        logger.info("Email notifications not configured; skipping notification for job %s", job.id)
        return False

    msg = _build_email(job, company)
    try:
        with smtplib.SMTP(settings.smtp_host, settings.smtp_port, timeout=20) as server:
            if settings.smtp_use_tls:
                server.starttls()
            if settings.smtp_username:
                server.login(settings.smtp_username, settings.smtp_password)
            server.send_message(msg)
        return True
    except Exception:
        logger.exception("Failed to send email notification for job %s", job.id)
        return False
