"""
GitHub Integration Service — NDMG Task Manager

Handles automated Pull Request creation when tickets reach "Done".
Uses PyGithub for GitHub API v3 interactions.
"""

import re
import logging
from github import Github, GithubException
from app.config import Config

logger = logging.getLogger(__name__)


class GitHubService:
    """Service for automated GitHub PR operations."""

    @staticmethod
    def _get_client():
        """Get authenticated GitHub client."""
        token = Config.GITHUB_TOKEN
        if not token:
            raise ValueError("GITHUB_TOKEN não configurado. Defina a variável de ambiente.")
        return Github(token)

    @staticmethod
    def _get_repo():
        """Get the configured repository."""
        g = GitHubService._get_client()
        owner = Config.GITHUB_REPO_OWNER
        name = Config.GITHUB_REPO_NAME
        if not owner or not name:
            raise ValueError(
                "GITHUB_REPO_OWNER e GITHUB_REPO_NAME não configurados. "
                "Defina as variáveis de ambiente."
            )
        return g.get_repo(f"{owner}/{name}")

    @staticmethod
    def derive_branch_name(ticket):
        """
        Derive a git branch name from ticket data.
        Convention: feature/NDMG-<id>-<slug>
        Example: feature/NDMG-42-implementar-login-oauth
        """
        ticket_id = ticket.get("id", "0")
        titulo = ticket.get("titulo", "sem-titulo")

        # Slugify the title
        slug = titulo.lower().strip()
        slug = re.sub(r"[àáâãäå]", "a", slug)
        slug = re.sub(r"[èéêë]", "e", slug)
        slug = re.sub(r"[ìíîï]", "i", slug)
        slug = re.sub(r"[òóôõöø]", "o", slug)
        slug = re.sub(r"[ùúûü]", "u", slug)
        slug = re.sub(r"[ç]", "c", slug)
        slug = re.sub(r"[^a-z0-9]+", "-", slug)
        slug = slug.strip("-")[:50]

        # Use first 8 chars of UUID for unique ID
        short_id = str(ticket_id)[:8]
        return f"feature/NDMG-{short_id}-{slug}"

    @staticmethod
    def branch_exists(branch_name):
        """Check if a branch exists in the repository."""
        try:
            repo = GitHubService._get_repo()
            repo.get_branch(branch_name)
            return True
        except GithubException:
            return False

    @staticmethod
    def get_branch_diff(branch_name):
        """
        Get the diff between a feature branch and the base branch.
        Returns file changes summary and patch content.
        """
        try:
            repo = GitHubService._get_repo()
            base = Config.GITHUB_BASE_BRANCH

            comparison = repo.compare(base, branch_name)

            files_summary = []
            full_patch = []

            for f in comparison.files:
                files_summary.append({
                    "filename": f.filename,
                    "status": f.status,
                    "additions": f.additions,
                    "deletions": f.deletions,
                    "changes": f.changes,
                })

                # Limit patch per file to avoid token overflow
                patch = f.patch or ""
                if len(patch) > 3000:
                    patch = patch[:3000] + "\n... (truncado)"

                full_patch.append(f"### {f.filename} ({f.status})\n```diff\n{patch}\n```")

            return {
                "files": files_summary,
                "total_commits": comparison.total_commits,
                "ahead_by": comparison.ahead_by,
                "behind_by": comparison.behind_by,
                "patch_text": "\n\n".join(full_patch),
            }

        except GithubException as e:
            logger.warning(f"Erro ao buscar diff da branch {branch_name}: {e}")
            return None

    @staticmethod
    def create_pull_request(ticket, ai_summary=None):
        """
        Create a Pull Request from the ticket's feature branch to the base branch.

        Args:
            ticket: dict with ticket data (id, titulo, descricao, prioridade, assignee)
            ai_summary: optional AI-generated summary to include in the PR body

        Returns:
            dict with PR details or error info
        """
        try:
            repo = GitHubService._get_repo()
            base = Config.GITHUB_BASE_BRANCH
            branch_name = GitHubService.derive_branch_name(ticket)

            # Check if branch exists
            try:
                repo.get_branch(branch_name)
            except GithubException:
                logger.info(f"Branch {branch_name} não encontrada. PR não será criado.")
                return {
                    "status": "skipped",
                    "reason": f"Branch '{branch_name}' não existe no repositório. "
                              f"O PR só é criado quando uma branch correspondente ao ticket existe.",
                    "expected_branch": branch_name,
                }

            # Check for existing open PRs for this branch
            existing_prs = repo.get_pulls(
                state="open", head=f"{Config.GITHUB_REPO_OWNER}:{branch_name}"
            )
            for pr in existing_prs:
                logger.info(f"PR já existe para branch {branch_name}: #{pr.number}")
                return {
                    "status": "exists",
                    "pr_number": pr.number,
                    "pr_url": pr.html_url,
                    "message": f"PR #{pr.number} já existe para esta branch.",
                }

            # Build PR body
            pr_title = f"✅ NDMG-{str(ticket['id'])[:8]} | {ticket.get('titulo', 'Sem título')}"

            assignee_name = "Não atribuído"
            if ticket.get("assignee"):
                assignee_name = ticket["assignee"].get("full_name", ticket["assignee"].get("email", ""))

            pr_body = f"""## 📋 Ticket Concluído

| Campo | Valor |
|-------|-------|
| **Título** | {ticket.get('titulo', 'N/A')} |
| **Prioridade** | `{ticket.get('prioridade', 'N/A')}` |
| **Responsável** | {assignee_name} |
| **Branch** | `{branch_name}` → `{base}` |

---

### 📝 Descrição
{ticket.get('descricao', '_Sem descrição._')}
"""

            if ai_summary:
                pr_body += f"""
---

### 🤖 Resumo de Code Review (IA)

{ai_summary}

> _Gerado automaticamente pelo NDMG Task Manager via Groq AI._
"""

            pr_body += """
---

> ⚡ **PR criado automaticamente** pelo sistema Kanban NDMG ao mover o ticket para "Done".
"""

            # Create the PR
            pr = repo.create_pull(
                title=pr_title,
                body=pr_body,
                head=branch_name,
                base=base,
            )

            logger.info(f"PR #{pr.number} criado com sucesso para ticket {ticket['id']}")

            # Add labels if they exist
            try:
                pr.add_to_labels("auto-generated", "kanban-done")
            except GithubException:
                pass  # Labels may not exist

            return {
                "status": "created",
                "pr_number": pr.number,
                "pr_url": pr.html_url,
                "pr_title": pr_title,
                "branch": branch_name,
                "base": base,
            }

        except GithubException as e:
            logger.error(f"Erro GitHub ao criar PR: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "Falha ao criar Pull Request via GitHub API.",
            }
        except ValueError as e:
            logger.error(f"Erro de configuração: {e}")
            return {
                "status": "error",
                "error": str(e),
                "message": "GitHub não está configurado corretamente.",
            }

    @staticmethod
    def get_open_prs():
        """List all open PRs in the configured repository."""
        try:
            repo = GitHubService._get_repo()
            prs = repo.get_pulls(state="open", sort="created", direction="desc")

            result = []
            for pr in prs[:20]:  # Limit to 20
                result.append({
                    "number": pr.number,
                    "title": pr.title,
                    "url": pr.html_url,
                    "state": pr.state,
                    "created_at": pr.created_at.isoformat(),
                    "user": pr.user.login,
                    "head_branch": pr.head.ref,
                    "base_branch": pr.base.ref,
                    "labels": [l.name for l in pr.labels],
                })

            return result

        except (GithubException, ValueError) as e:
            logger.error(f"Erro ao listar PRs: {e}")
            return []
