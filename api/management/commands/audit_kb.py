import json

from django.core.management.base import BaseCommand

from api.models import KnowledgeBaseEntry
from api.knowledge_base_service import (
    audit_knowledge_base_content,
    needs_regeneration,
    refresh_branch_kb,
)


class Command(BaseCommand):
    help = "Audit knowledge base entries and optionally regenerate problematic ones."

    def add_arguments(self, parser):
        parser.add_argument("--domain", type=str, help="Filter by domain", default=None)
        parser.add_argument("--branch", type=str, help="Filter by branch", default=None)
        parser.add_argument(
            "--auto-refresh",
            action="store_true",
            help="Automatically regenerate entries flagged by the auditor.",
        )
        parser.add_argument(
            "--preference",
            type=str,
            default="",
            help="Optional preference text to seed regeneration when needed.",
        )

    def handle(self, *args, **options):
        qs = KnowledgeBaseEntry.objects.all()
        if options["domain"]:
            qs = qs.filter(domain=options["domain"].lower())
        if options["branch"]:
            qs = qs.filter(branch=options["branch"].lower())

        if not qs.exists():
            self.stdout.write(self.style.WARNING("No knowledge base entries matched the query."))
            return

        auto_refresh = options["auto_refresh"]
        preference_text = options["preference"]

        for entry in qs:
            self.stdout.write("-" * 80)
            self.stdout.write(f"Domain: {entry.domain} | Branch: {entry.branch} | Title: {entry.title}")

            report = audit_knowledge_base_content(entry.content or {})
            self.stdout.write(f"Audit status: {report.get('status')}")
            if report.get("issues"):
                self.stdout.write("Issues:")
                for issue in report["issues"]:
                    self.stdout.write(f"  • {issue}")
            if report.get("recommendation"):
                self.stdout.write(f"Recommendation: {report['recommendation']}")

            regen_required = needs_regeneration(entry.content or {}, report)
            self.stdout.write(f"Needs regeneration: {'YES' if regen_required else 'NO'}")

            if regen_required and auto_refresh:
                refreshed = refresh_branch_kb(entry.domain, entry.branch, preference_text)
                self.stdout.write(
                    self.style.SUCCESS(
                        f"Regenerated KB for {refreshed.domain}:{refreshed.branch} (title: {refreshed.title})"
                    )
                )
            elif regen_required:
                self.stdout.write(
                    self.style.WARNING(
                        "Regeneration skipped (use --auto-refresh to enable automatic updates)."
                    )
                )

        self.stdout.write(self.style.SUCCESS("Knowledge base audit completed."))
