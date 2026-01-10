"""Email service for sending emails via SMTP."""
import smtplib
import logging
import re
from typing import Optional, List, Dict, Any, Tuple
from email.mime.text import MIMEText
from email.mime.multipart import MIMEMultipart
from email.mime.application import MIMEApplication
from datetime import datetime
from jinja2 import (
    Environment,
    FileSystemLoader,
    TemplateNotFound as Jinja2TemplateNotFound,
)

logger = logging.getLogger(__name__)


class EmailConfigError(Exception):
    """Raised when email configuration is invalid."""

    pass


class TemplateNotFoundError(Exception):
    """Raised when email template is not found."""

    pass


class EmailResult:
    """Result of an email operation."""

    def __init__(self, success: bool, error: Optional[str] = None):
        """
        Initialize email result.

        Args:
            success: Whether the operation succeeded.
            error: Error message if failed.
        """
        self.success = success
        self.error = error


class EmailService:
    """Service for sending emails via SMTP."""

    # Email validation pattern
    EMAIL_REGEX = re.compile(r"^[a-zA-Z0-9._%+-]+@[a-zA-Z0-9.-]+\.[a-zA-Z]{2,}$")

    def __init__(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
        from_name: str = "VBWD",
        template_dir: str = "src/templates/email",
    ):
        """
        Initialize email service.

        Args:
            smtp_host: SMTP server hostname.
            smtp_port: SMTP server port.
            smtp_user: SMTP authentication username.
            smtp_password: SMTP authentication password.
            from_email: Default sender email address.
            from_name: Default sender name.
            template_dir: Directory containing email templates.

        Raises:
            EmailConfigError: If configuration is invalid.
        """
        # Validate required config
        self._validate_config(
            smtp_host, smtp_port, smtp_user, smtp_password, from_email
        )

        self._smtp_host = smtp_host
        self._smtp_port = smtp_port
        self._smtp_user = smtp_user
        self._smtp_password = smtp_password
        self._from_email = from_email
        self._from_name = from_name

        self._template_env: Optional[Environment] = None
        try:
            self._template_env = Environment(
                loader=FileSystemLoader(template_dir), autoescape=True
            )
        except Exception as e:
            logger.warning(f"Could not load template directory: {e}")

    def _validate_config(
        self,
        smtp_host: str,
        smtp_port: int,
        smtp_user: str,
        smtp_password: str,
        from_email: str,
    ) -> None:
        """Validate SMTP configuration."""
        errors = []

        if not smtp_host:
            errors.append("smtp_host is required")
        if not smtp_port:
            errors.append("smtp_port is required")
        if not smtp_user:
            errors.append("smtp_user is required")
        if not smtp_password:
            errors.append("smtp_password is required")
        if not from_email:
            errors.append("from_email is required")

        if errors:
            raise EmailConfigError(f"Invalid configuration: {', '.join(errors)}")

    def _validate_email(self, email: str) -> bool:
        """Validate email address format."""
        if not email:
            return False
        return bool(self.EMAIL_REGEX.match(email))

    def send_email(
        self,
        to_email: str,
        subject: str,
        body_text: str,
        body_html: Optional[str] = None,
        attachments: Optional[List[Tuple[str, bytes, str]]] = None,
    ) -> EmailResult:
        """
        Send email via SMTP.

        Args:
            to_email: Recipient email address.
            subject: Email subject.
            body_text: Plain text body.
            body_html: Optional HTML body.
            attachments: List of (filename, data, mime_type) tuples.

        Returns:
            EmailResult with success status.
        """
        # Validate recipient email
        if not self._validate_email(to_email):
            return EmailResult(success=False, error="Invalid recipient email address")

        try:
            # Create message
            if body_html or attachments:
                msg = MIMEMultipart("alternative")
            else:
                msg = MIMEMultipart()

            msg["From"] = f"{self._from_name} <{self._from_email}>"
            msg["To"] = to_email
            msg["Subject"] = subject

            # Add plain text body
            text_part = MIMEText(body_text, "plain", "utf-8")
            msg.attach(text_part)

            # Add HTML body if provided
            if body_html:
                html_part = MIMEText(body_html, "html", "utf-8")
                msg.attach(html_part)

            # Add attachments if provided
            if attachments:
                for filename, data, mime_type in attachments:
                    attachment = MIMEApplication(data)
                    attachment.add_header(
                        "Content-Disposition", "attachment", filename=filename
                    )
                    attachment.add_header("Content-Type", mime_type)
                    msg.attach(attachment)

            # Send email
            with smtplib.SMTP(self._smtp_host, self._smtp_port) as server:
                server.starttls()
                server.login(self._smtp_user, self._smtp_password)
                server.sendmail(self._from_email, to_email, msg.as_string())

            logger.info(f"Email sent successfully to {to_email}")
            return EmailResult(success=True)

        except Exception as e:
            error_msg = str(e)
            logger.error(f"Failed to send email to {to_email}: {error_msg}")
            return EmailResult(success=False, error=error_msg)

    def render_template(
        self, template_name: str, context: Dict[str, Any]
    ) -> Tuple[str, str]:
        """
        Render email template.

        Args:
            template_name: Name of the template (without extension).
            context: Template context variables.

        Returns:
            Tuple of (plain_text, html).

        Raises:
            TemplateNotFoundError: If template is not found.
        """
        if not self._template_env:
            raise TemplateNotFoundError("Template directory not configured")

        try:
            # Try to load text template
            text_template = self._template_env.get_template(f"{template_name}.txt")
            text_content = text_template.render(**context)
        except Jinja2TemplateNotFound:
            raise TemplateNotFoundError(f"Template '{template_name}.txt' not found")

        try:
            # Try to load HTML template
            html_template = self._template_env.get_template(f"{template_name}.html")
            html_content = html_template.render(**context)
        except Jinja2TemplateNotFound:
            raise TemplateNotFoundError(f"Template '{template_name}.html' not found")

        return text_content, html_content

    def send_welcome_email(self, to_email: str, first_name: str) -> EmailResult:
        """
        Send welcome email to new user.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "login_url": "https://vbwd.com/login",
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template("welcome", context)

            return self.send_email(
                to_email=to_email,
                subject="Welcome to VBWD!",
                body_text=text_body,
                body_html=html_body,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_subscription_activated(
        self, to_email: str, first_name: str, plan_name: str, expires_at: datetime
    ) -> EmailResult:
        """
        Send subscription activation confirmation.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.
            plan_name: Name of the subscription plan.
            expires_at: Subscription expiration date.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "plan_name": plan_name,
                "expires_at": expires_at.strftime("%Y-%m-%d"),
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template(
                "subscription_activated", context
            )

            return self.send_email(
                to_email=to_email,
                subject=f"Your {plan_name} subscription is now active!",
                body_text=text_body,
                body_html=html_body,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_subscription_cancelled(
        self, to_email: str, first_name: str, plan_name: str
    ) -> EmailResult:
        """
        Send subscription cancellation confirmation.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.
            plan_name: Name of the subscription plan.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "plan_name": plan_name,
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template(
                "subscription_cancelled", context
            )

            return self.send_email(
                to_email=to_email,
                subject=f"Your {plan_name} subscription has been cancelled",
                body_text=text_body,
                body_html=html_body,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_payment_receipt(
        self,
        to_email: str,
        first_name: str,
        invoice_number: str,
        amount: str,
        pdf_bytes: Optional[bytes] = None,
    ) -> EmailResult:
        """
        Send payment receipt with optional PDF.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.
            invoice_number: Invoice number.
            amount: Payment amount with currency.
            pdf_bytes: Optional PDF receipt bytes.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "invoice_number": invoice_number,
                "amount": amount,
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template("payment_receipt", context)

            attachments = None
            if pdf_bytes:
                attachments = [(f"{invoice_number}.pdf", pdf_bytes, "application/pdf")]

            return self.send_email(
                to_email=to_email,
                subject=f"Payment Receipt - {invoice_number}",
                body_text=text_body,
                body_html=html_body,
                attachments=attachments,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_payment_failed(
        self, to_email: str, first_name: str, plan_name: str, retry_url: str
    ) -> EmailResult:
        """
        Send payment failure notification.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.
            plan_name: Name of the subscription plan.
            retry_url: URL to retry payment.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "plan_name": plan_name,
                "retry_url": retry_url,
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template("payment_failed", context)

            return self.send_email(
                to_email=to_email,
                subject="Payment Failed - Action Required",
                body_text=text_body,
                body_html=html_body,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_invoice(
        self,
        to_email: str,
        first_name: str,
        invoice_number: str,
        amount: str,
        due_date: str,
        pdf_bytes: Optional[bytes] = None,
    ) -> EmailResult:
        """
        Send invoice with optional PDF attachment.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.
            invoice_number: Invoice number.
            amount: Invoice amount with currency.
            due_date: Payment due date.
            pdf_bytes: Optional PDF invoice bytes.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "invoice_number": invoice_number,
                "amount": amount,
                "due_date": due_date,
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template("invoice", context)

            attachments = None
            if pdf_bytes:
                attachments = [(f"{invoice_number}.pdf", pdf_bytes, "application/pdf")]

            return self.send_email(
                to_email=to_email,
                subject=f"Invoice {invoice_number}",
                body_text=text_body,
                body_html=html_body,
                attachments=attachments,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_renewal_reminder(
        self, to_email: str, first_name: str, plan_name: str, days_until_renewal: int
    ) -> EmailResult:
        """
        Send renewal reminder.

        Args:
            to_email: Recipient email address.
            first_name: User's first name.
            plan_name: Name of the subscription plan.
            days_until_renewal: Days until subscription renews.

        Returns:
            EmailResult with success status.
        """
        try:
            context = {
                "first_name": first_name,
                "plan_name": plan_name,
                "days_until_renewal": days_until_renewal,
                "year": datetime.now().year,
            }
            text_body, html_body = self.render_template("renewal_reminder", context)

            return self.send_email(
                to_email=to_email,
                subject=f"Your {plan_name} subscription renews in {days_until_renewal} days",
                body_text=text_body,
                body_html=html_body,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))

    def send_template(
        self,
        to: str,
        template: str,
        context: Dict[str, Any],
        subject: Optional[str] = None,
    ) -> EmailResult:
        """
        Send templated email.

        Generic method for sending emails using templates.

        Args:
            to: Recipient email address.
            template: Template name (without extension).
            context: Template context variables.
            subject: Optional custom subject (defaults based on template).

        Returns:
            EmailResult with success status.
        """
        # Default subjects for known templates
        default_subjects = {
            "password_reset": "Reset Your Password",
            "password_changed": "Your Password Has Been Changed",
            "welcome": "Welcome to VBWD!",
            "subscription_activated": "Subscription Activated",
            "subscription_cancelled": "Subscription Cancelled",
        }

        try:
            text_body, html_body = self.render_template(template, context)
            email_subject = subject or default_subjects.get(
                template, f"VBWD - {template.replace('_', ' ').title()}"
            )

            return self.send_email(
                to_email=to,
                subject=email_subject,
                body_text=text_body,
                body_html=html_body,
            )
        except TemplateNotFoundError as e:
            logger.error(f"Template error: {e}")
            return EmailResult(success=False, error=str(e))
