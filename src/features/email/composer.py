"""Email draft composition with resume-aware personalization."""

from shared.models import EmailDraft, Job, Resume


class EmailComposer:
    """Generate a personalized outreach email for a job application."""

    def __init__(self) -> None:
        pass

    def compose(
        self,
        job: Job,
        resume: Resume | None = None,
    ) -> EmailDraft:
        """Draft an email tailored to the job and optionally the resume.

        Args:
            job: The target job posting.
            resume: The applicant's parsed resume (for skill matching mention).

        Returns:
            An ``EmailDraft`` with subject and body.
        """
        company = job.company or "the company"
        title = job.title or "the position"

        subject = f"Application for {title} at {company}"

        body_lines = [
            f"Dear {company} Hiring Manager,",
            "",
            f"I am writing to express my strong interest in the {title} role at {company}.",
        ]

        if resume and resume.parsed_skills:
            top_skills = ", ".join(resume.parsed_skills[:5])
            body_lines.append(
                f"My background includes expertise in {top_skills}, "
                f"which aligns well with the requirements of this position."
            )

        body_lines.extend([
            "",
            "I would welcome the opportunity to discuss how my experience can contribute to your team.",
            "",
            "Best regards,",
            "[Your Name]",
        ])

        return EmailDraft(
            subject=subject,
            body="\n".join(body_lines),
            recipient=None,
            job_id=job.id or 0,
        )
