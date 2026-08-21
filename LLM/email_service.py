import os
import smtplib
from email.mime.multipart import MIMEMultipart
from email.mime.text import MIMEText
from email.utils import formatdate, make_msgid
from pathlib import Path
from typing import List, Optional, Tuple, Union
from dotenv import load_dotenv

# Load environment variables
dotenv_path = Path(__file__).resolve().parent.parent / ".env"
load_dotenv(dotenv_path=dotenv_path if dotenv_path.exists() else None)

from .schemas import ProcurementNotice


class EmailService:
    """SMTP Email Service for sending executive opportunity syntheses and feasibility reports."""

    def __init__(
        self,
        smtp_server: Optional[str] = None,
        smtp_port: Optional[int] = None,
        smtp_user: Optional[str] = None,
        smtp_password: Optional[str] = None,
        sender_email: Optional[str] = None,
        default_recipient: Optional[str] = None,
        use_tls: bool = True,
        use_ssl: bool = False,
    ):
        self.smtp_server = smtp_server or os.getenv("SMTP_SERVER", "smtp.gmail.com")
        self.smtp_port = int(smtp_port or os.getenv("SMTP_PORT", 587))
        self.smtp_user = smtp_user or os.getenv("SMTP_USER", "")
        self.smtp_password = smtp_password or os.getenv("SMTP_PASSWORD", "")
        self.sender_email = sender_email or os.getenv("SMTP_SENDER_EMAIL", self.smtp_user)
        self.default_recipient = default_recipient or os.getenv("DEFAULT_RECIPIENT_EMAIL", "sdiriaziz1999@gmail.com")
        self.use_ssl = use_ssl or (self.smtp_port == 465)
        self.use_tls = use_tls and not self.use_ssl

    def test_connection(self) -> Tuple[bool, str]:
        """Test the SMTP server connection and authentication handshake."""
        if not self.smtp_user or not self.smtp_password:
            return False, "Missing SMTP username or password in configuration (.env)."

        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=15)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=15)
                server.ehlo()
                if self.use_tls:
                    server.starttls()
                    server.ehlo()

            server.login(self.smtp_user, self.smtp_password)
            server.quit()
            return True, f"SMTP connection successful to {self.smtp_server}:{self.smtp_port} as {self.smtp_user}"
        except Exception as e:
            return False, f"SMTP connection error: {str(e)}"

    def send_email(
        self,
        to_email: str,
        subject: str,
        html_content: str,
        text_content: Optional[str] = None,
    ) -> bool:
        """Send a MIME multipart email with HTML and Plain Text fallback."""
        if not to_email:
            to_email = self.default_recipient

        if not self.smtp_user or not self.smtp_password:
            raise ValueError("SMTP credentials (SMTP_USER / SMTP_PASSWORD) are not configured.")

        # Fallback text if none provided
        if not text_content:
            text_content = html_content.replace("<br>", "\n").replace("<p>", "\n").replace("</p>", "\n")

        msg = MIMEMultipart("alternative")
        msg["Subject"] = subject
        msg["From"] = f"AIScraperAgent Intelligence <{self.sender_email}>"
        msg["To"] = to_email
        msg["Date"] = formatdate(localtime=True)
        msg["Message-ID"] = make_msgid()

        # Attach text part then HTML part
        msg.attach(MIMEText(text_content, "plain", "utf-8"))
        msg.attach(MIMEText(html_content, "html", "utf-8"))

        server = None
        try:
            if self.use_ssl:
                server = smtplib.SMTP_SSL(self.smtp_server, self.smtp_port, timeout=20)
            else:
                server = smtplib.SMTP(self.smtp_server, self.smtp_port, timeout=20)
                server.ehlo()
                if self.use_tls:
                    server.starttls()
                    server.ehlo()

            server.login(self.smtp_user, self.smtp_password)
            server.sendmail(self.sender_email, [to_email], msg.as_string())
            print(f"[EmailService] Successfully sent email '{subject}' to <{to_email}>")
            return True
        except Exception as e:
            print(f"[EmailService] Failed to send email to <{to_email}>: {e}")
            raise e
        finally:
            if server:
                try:
                    server.quit()
                except Exception:
                    pass

    def send_opportunity_synthesis(
        self,
        notice: ProcurementNotice,
        recipient_email: Optional[str] = None,
    ) -> bool:
        """Format and dispatch a single opportunity synthesis and feasibility analysis email."""
        recipient = recipient_email or self.default_recipient
        score_pct = round(notice.relevance_score * 100, 1)

        # Subject Line with Recommendation Icon
        recom = notice.analyse_faisabilite.recommandation if notice.analyse_faisabilite else ("GO" if notice.is_relevant else "NO-GO")
        recom_clean = recom.replace("_", " ").upper()
        
        subject = f"[{recom_clean} - {score_pct}%] Synthèse d'Opportunité: {notice.objet[:70]}"
        if len(notice.objet) > 70:
            subject += "..."

        html_body = self._build_single_notice_html(notice)
        text_body = self._build_single_notice_text(notice)

        return self.send_email(
            to_email=recipient,
            subject=subject,
            html_content=html_body,
            text_content=text_body,
        )

    def send_synthesis_digest(
        self,
        notices: List[ProcurementNotice],
        recipient_email: Optional[str] = None,
        digest_title: Optional[str] = "Synthèse Hebdomadaire des Opportunités Détectées",
    ) -> bool:
        """Send a digest email summarizing multiple procurement notices."""
        recipient = recipient_email or self.default_recipient
        subject = f"📊 [AIScraperAgent Digest] {digest_title} ({len(notices)} opportunités)"

        html_body = self._build_digest_html(notices, digest_title)
        text_body = self._build_digest_text(notices, digest_title)

        return self.send_email(
            to_email=recipient,
            subject=subject,
            html_content=html_body,
            text_content=text_body,
        )

    def _build_single_notice_html(self, notice: ProcurementNotice) -> str:
        """Generate high-end, responsive HTML template for an opportunity synthesis."""
        score_pct = round(notice.relevance_score * 100, 1)
        feasibility = notice.analyse_faisabilite

        # Recommendation badge color
        recom_code = feasibility.recommandation if feasibility else ("GO" if notice.is_relevant else "NO-GO")
        if recom_code == "GO":
            badge_bg = "#10b981"
            badge_text = "RECOMMANDATION: GO"
        elif "PARTENAIRE" in recom_code:
            badge_bg = "#f59e0b"
            badge_text = "RECOMMANDATION: À ÉTUDIER (PARTENAIRE)"
        else:
            badge_bg = "#ef4444"
            badge_text = "RECOMMANDATION: NO-GO"

        # Format synthesis paragraphs
        synthese_text = notice.synthese_opportunite or "Aucune synthèse rédigée."
        synthesis_html = "".join([f"<p style='margin-bottom: 12px; line-height: 1.6;'>{p.strip()}</p>" for p in synthese_text.split("\n\n") if p.strip()])

        # Format skills & risks
        skills_html = ""
        if feasibility and feasibility.competences_requises:
            skills_tags = "".join([
                f"<span style='display: inline-block; background-color: #e0e7ff; color: #3730a3; padding: 4px 10px; border-radius: 9999px; font-size: 12px; font-weight: 600; margin: 3px 4px 3px 0;'>{skill}</span>"
                for skill in feasibility.competences_requises
            ])
            skills_html = f"<div style='margin-top: 8px;'>{skills_tags}</div>"
        else:
            skills_html = "<p style='color: #64748b; font-size: 13px;'>Compétences standards requises.</p>"

        risks_html = ""
        if feasibility and feasibility.risques_et_contraintes:
            risks_list = "".join([
                f"<li style='margin-bottom: 6px; color: #991b1b;'>⚠️ <strong>{risk}</strong></li>"
                for risk in feasibility.risques_et_contraintes
            ])
            risks_html = f"<ul style='margin: 8px 0; padding-left: 20px; font-size: 13px;'>{risks_list}</ul>"
        else:
            risks_html = "<p style='color: #64748b; font-size: 13px;'>Aucun risque majeur bloquant identifié.</p>"

        # Format Lots
        lots_html = ""
        if notice.lots:
            lots_items = "".join([
                f"<li style='margin-bottom: 4px;'><strong>Lot {lot.lot_number}:</strong> {lot.title} " + (f"<span style='color: #059669;'>({lot.budget})</span>" if lot.budget else "") + "</li>"
                for lot in notice.lots
            ])
            lots_html = f"<ul style='margin: 6px 0; padding-left: 20px; font-size: 13px; color: #334155;'>{lots_items}</ul>"
        else:
            lots_html = "<p style='color: #64748b; font-size: 13px;'>Lot unique / Non alloti.</p>"

        # Source Button
        source_btn_html = ""
        if notice.source_url:
            source_btn_html = f"""
            <div style="text-align: center; margin: 25px 0 10px 0;">
                <a href="{notice.source_url}" target="_blank" style="background: linear-gradient(135deg, #2563eb, #1d4ed8); color: #ffffff; padding: 12px 28px; text-decoration: none; border-radius: 8px; font-weight: bold; display: inline-block; box-shadow: 0 4px 6px -1px rgba(37, 99, 235, 0.2);">
                    🌐 Consulter l'Avis Source & Cahier des Charges &rarr;
                </a>
            </div>
            """

        deadline_str = notice.dates.submission_deadline or "Non précisée"
        budget_str = notice.budget.formatted if notice.budget else "Non spécifié"

        html_template = f"""
<!DOCTYPE html>
<html lang="fr">
<head>
    <meta charset="UTF-8">
    <meta name="viewport" content="width=device-width, initial-scale=1.0">
    <title>Synthèse d'Opportunité</title>
</head>
<body style="margin: 0; padding: 20px; background-color: #f1f5f9; font-family: -apple-system, BlinkMacSystemFont, 'Segoe UI', Roboto, Helvetica, Arial, sans-serif; color: #1e293b;">
    <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; box-shadow: 0 10px 15px -3px rgba(0, 0, 0, 0.08); border: 1px solid #e2e8f0;">
        
        <!-- Header -->
        <div style="background: linear-gradient(135deg, #0f172a, #1e293b); color: #ffffff; padding: 24px 28px;">
            <div style="font-size: 12px; text-transform: uppercase; tracking: 1px; color: #94a3b8; font-weight: 600; margin-bottom: 6px;">
                AIScraperAgent • Intelligence des Marchés Publics
            </div>
            <h1 style="margin: 0; font-size: 20px; font-weight: 700; color: #f8fafc; line-height: 1.3;">
                {notice.objet}
            </h1>
            <div style="margin-top: 14px; display: flex; flex-wrap: wrap; gap: 8px;">
                <span style="background-color: {badge_bg}; color: #ffffff; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 700; display: inline-block;">
                    {badge_text}
                </span>
                <span style="background-color: rgba(255, 255, 255, 0.15); color: #f8fafc; padding: 4px 12px; border-radius: 6px; font-size: 12px; font-weight: 600; display: inline-block; margin-left: 6px;">
                    Pertinence: {score_pct}%
                </span>
            </div>
        </div>

        <!-- Key Information Grid -->
        <div style="background-color: #f8fafc; padding: 16px 28px; border-bottom: 1px solid #e2e8f0; font-size: 13px;">
            <table style="width: 100%; border-collapse: collapse;">
                <tr>
                    <td style="padding: 6px 0; color: #64748b; width: 35%;">🏢 Organisme :</td>
                    <td style="padding: 6px 0; color: #0f172a; font-weight: 600;">{notice.organisme}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">📅 Date Limite :</td>
                    <td style="padding: 6px 0; color: #dc2626; font-weight: 700;">{deadline_str}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">💰 Budget Estimé :</td>
                    <td style="padding: 6px 0; color: #059669; font-weight: 600;">{budget_str}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">🌍 Pays / Secteur :</td>
                    <td style="padding: 6px 0; color: #0f172a;">{notice.country or 'Global'} / {notice.sector or 'ICT & Télécoms'}</td>
                </tr>
                <tr>
                    <td style="padding: 6px 0; color: #64748b;">🌐 Source :</td>
                    <td style="padding: 6px 0; color: #0f172a;">{notice.source or 'Veille Automatisée'} ({notice.language})</td>
                </tr>
            </table>
        </div>

        <!-- Body Content -->
        <div style="padding: 24px 28px;">
            
            <!-- Executive Synthesis Section -->
            <div style="margin-bottom: 24px;">
                <h2 style="font-size: 16px; color: #0f172a; border-bottom: 2px solid #e2e8f0; padding-bottom: 6px; margin-top: 0; display: flex; align-items: center;">
                    📝 Synthèse Exécutive de l'Opportunité
                </h2>
                <div style="font-size: 14px; color: #334155; background-color: #f8fafc; border-left: 4px solid #3b82f6; padding: 14px 16px; border-radius: 0 8px 8px 0;">
                    {synthesis_html}
                </div>
            </div>

            <!-- Preliminary Feasibility Analysis -->
            <div style="margin-bottom: 24px; background-color: #f0fdf4; border: 1px solid #bbf7d0; border-radius: 8px; padding: 16px;">
                <h2 style="font-size: 15px; color: #166534; margin-top: 0; margin-bottom: 10px;">
                    🧠 Analyse de Faisabilité & Adéquation Technique
                </h2>
                <p style="font-size: 13px; color: #14532d; line-height: 1.5; margin-bottom: 12px;">
                    <strong>Alignement :</strong> {feasibility.adequation_technique if feasibility else 'Alignement technique préliminaire avec le coeur de métier.'}
                </p>
                
                <div style="margin-top: 10px;">
                    <div style="font-size: 12px; font-weight: bold; color: #1e293b; text-transform: uppercase; margin-bottom: 4px;">Compétences Clés Requises :</div>
                    {skills_html}
                </div>

                <div style="margin-top: 14px;">
                    <div style="font-size: 12px; font-weight: bold; color: #991b1b; text-transform: uppercase; margin-bottom: 4px;">Risques et Points de Vigilance :</div>
                    {risks_html}
                </div>
            </div>

            <!-- Lots & Scope Breakdown -->
            <div style="margin-bottom: 20px;">
                <h3 style="font-size: 14px; color: #0f172a; margin-bottom: 6px;">📦 Allotissement & Périmètre :</h3>
                {lots_html}
            </div>

            <!-- CTA Button -->
            {source_btn_html}

        </div>

        <!-- Footer -->
        <div style="background-color: #f8fafc; border-top: 1px solid #e2e8f0; padding: 16px 28px; font-size: 12px; color: #94a3b8; text-align: center;">
            Ce rapport de synthèse a été généré automatiquement par <strong>AIScraperAgent</strong> (Pipeline d'Extraction NLP & Modèle LLM NVIDIA Llama-3.1).<br>
            Pour toute modification des règles de ciblage ou de filtrage, contactez l'administrateur système.
        </div>

    </div>
</body>
</html>
        """
        return html_template

    def _build_single_notice_text(self, notice: ProcurementNotice) -> str:
        """Generate clean plaintext fallback version of opportunity synthesis."""
        score_pct = round(notice.relevance_score * 100, 1)
        feas = notice.analyse_faisabilite
        recom = feas.recommandation if feas else ("GO" if notice.is_relevant else "NO-GO")

        text = f"""======================================================================
AISCRAPERAGENT - SYNTHÈSE D'OPPORTUNITÉ DÉTECTÉE
======================================================================
TITRE / OBJET : {notice.objet}
ORGANISME     : {notice.organisme}
PAYS / SECTEUR: {notice.country or 'Global'} / {notice.sector or 'ICT'}
DATE LIMITE   : {notice.dates.submission_deadline or 'Non précisée'}
BUDGET ESTIMÉ : {notice.budget.formatted if notice.budget else 'Non spécifié'}
RECOMMANDATION: {recom} (Pertinence: {score_pct}%)
LIEN SOURCE   : {notice.source_url or 'N/A'}
----------------------------------------------------------------------
📝 SYNTHÈSE EXÉCUTIVE :
{notice.synthese_opportunite or 'N/A'}

🧠 ANALYSE DE FAISABILITÉ & ADÉQUATION TECHNIQUE :
Alignement: {feas.adequation_technique if feas else 'N/A'}

Compétences Clés:
{', '.join(feas.competences_requises) if feas and feas.competences_requises else 'Non spécifié'}

Risques Identifiés:
{', '.join(feas.risques_et_contraintes) if feas and feas.risques_et_contraintes else 'Aucun risque bloquant'}

======================================================================
"""
        return text

    def _build_digest_html(self, notices: List[ProcurementNotice], title: Optional[str]) -> str:
        """Generate HTML digest of multiple procurement opportunities."""
        rows_html = ""
        for n in notices:
            score_pct = round(n.relevance_score * 100, 1)
            recom = n.analyse_faisabilite.recommandation if n.analyse_faisabilite else ("GO" if n.is_relevant else "NO-GO")
            badge_color = "#10b981" if recom == "GO" else ("#f59e0b" if "PARTENAIRE" in recom else "#ef4444")
            
            link_html = ""
            if n.source_url:
                link_html = f'<div style="margin-top: 8px; text-align: right;"><a href="{n.source_url}" target="_blank" style="font-size: 12px; color: #2563eb; text-decoration: none; font-weight: 600;">Voir l&#39;avis complet &rarr;</a></div>'
            
            rows_html += f"""
            <div style="background-color: #ffffff; border: 1px solid #e2e8f0; border-radius: 8px; padding: 16px; margin-bottom: 16px;">
                <div style="display: flex; justify-content: space-between; align-items: start; margin-bottom: 8px;">
                    <span style="background-color: {badge_color}; color: #ffffff; padding: 2px 8px; border-radius: 4px; font-size: 11px; font-weight: bold;">{recom} ({score_pct}%)</span>
                    <span style="font-size: 12px; color: #dc2626; font-weight: 600;">📅 {n.dates.submission_deadline or 'N/A'}</span>
                </div>
                <h3 style="margin: 0 0 8px 0; font-size: 15px; color: #0f172a;">{n.objet}</h3>
                <p style="font-size: 12px; color: #64748b; margin: 0 0 8px 0;">🏢 {n.organisme} • 💰 {n.budget.formatted if n.budget else 'N/A'} • 🌍 {n.country or 'Global'}</p>
                <div style="font-size: 13px; color: #334155; line-height: 1.5; background-color: #f8fafc; padding: 10px; border-radius: 6px;">
                    {n.synthese_opportunite[:280] if n.synthese_opportunite else n.objet}...
                </div>
                {link_html}
            </div>
            """

        html = f"""
<!DOCTYPE html>
<html>
<head><meta charset="UTF-8"></head>
<body style="margin: 0; padding: 20px; background-color: #f1f5f9; font-family: sans-serif; color: #1e293b;">
    <div style="max-width: 680px; margin: 0 auto; background: #ffffff; border-radius: 12px; overflow: hidden; padding: 24px;">
        <h1 style="font-size: 18px; color: #0f172a; margin-top: 0;">📊 {title}</h1>
        <p style="color: #64748b; font-size: 13px;">Voici le récapitulatif des {len(notices)} opportunités récentes analysées par l'agent IA.</p>
        <hr style="border: none; border-top: 1px solid #e2e8f0; margin: 16px 0;">
        {rows_html}
    </div>
</body>
</html>
        """
        return html

    def _build_digest_text(self, notices: List[ProcurementNotice], title: Optional[str]) -> str:
        """Generate plain text digest of multiple opportunities."""
        lines = [f"📊 {title} ({len(notices)} opportunités)", "=" * 60]
        for idx, n in enumerate(notices, 1):
            score_pct = round(n.relevance_score * 100, 1)
            lines.append(f"\n[{idx}] {n.objet}")
            lines.append(f"    Organisme: {n.organisme} | Date limite: {n.dates.submission_deadline or 'N/A'}")
            lines.append(f"    Pertinence: {score_pct}% | Budget: {n.budget.formatted if n.budget else 'N/A'}")
            if n.synthese_opportunite:
                lines.append(f"    Synthèse: {n.synthese_opportunite[:150]}...")
            if n.source_url:
                lines.append(f"    URL: {n.source_url}")
        return "\n".join(lines)


# Singleton EmailService instance
_email_service: Optional[EmailService] = None

def get_email_service() -> EmailService:
    global _email_service
    if _email_service is None:
        _email_service = EmailService()
    return _email_service
