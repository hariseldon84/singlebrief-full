"""Developer Tools Integration Service for SingleBrief.

This module provides integration with developer tools like GitHub and Jira
for tracking development progress, pull requests, issues, and team metrics.
"""

import base64
import logging
from datetime import datetime, timedelta, timezone
from typing import Any, Dict, List, Optional, Union
from urllib.parse import quote, urlencode

import aiohttp
from sqlalchemy import and_, or_, select
from sqlalchemy.ext.asyncio import AsyncSession

from app.ai.integration_hub import integration_hub_service
from app.core.database import get_db_session
from app.models.integration import (DataSource, Integration, IntegrationLog,
                                    OAuthToken)

logger = logging.getLogger(__name__)

class DeveloperToolsIntegrationService:
    """Service for integrating with developer tools like GitHub and Jira."""

    def __init__(self):
        self.session: Optional[AsyncSession] = None
        self.integration_hub = integration_hub_service

        # GitHub OAuth scopes
        self.github_scopes = [
            "repo",  # Repository access
            "read:org",  # Organization read access
            "read:user",  # User profile access
            "user:email",  # User email access
            "read:project",  # Project boards access
            "notifications",  # Notifications access
            "read:packages",  # Packages access
        ]

        # Jira OAuth scopes
        self.jira_scopes = [
            "read:jira-work",  # Read issues, projects, etc.
            "read:jira-user",  # Read user information
            "write:jira-work",  # Create/update issues (optional)
            "manage:jira-project",  # Project management (optional)
            "read:audit-log:jira",  # Audit log access
        ]

    async def get_session(self) -> AsyncSession:
        """Get database session."""
        if self.session is None:
            self.session = await get_db_session().__anext__()
        return self.session

    async def register_developer_tools_connector(self, service_type: str) -> str:
        """Register developer tools connector with Integration Hub.

        Args:
            service_type: Either 'github' or 'jira'

        Returns:
            Connector ID from Integration Hub
        """
        try:
            service_name = "GitHub" if service_type == "github" else "Jira"

            capabilities = []
            if service_type == "github":
                capabilities = [
                    "read_repositories",
                    "read_issues",
                    "read_pull_requests",
                    "track_commits",
                    "monitor_branches",
                    "webhook_events",
                    "code_analysis",
                    "contributor_insights",
                    "velocity_metrics",
                ]
            elif service_type == "jira":
                capabilities = [
                    "read_issues",
                    "read_projects",
                    "track_sprints",
                    "monitor_workflows",
                    "progress_tracking",
                    "webhook_events",
                    "velocity_metrics",
                    "burndown_charts",
                    "issue_analysis",
                ]

            connector = await self.integration_hub.register_connector(
                connector_type=service_type,
                name=f"{service_name} Integration",
                description=f"Integration with {service_name} for development tracking",
                version="1.0.0",
                capabilities=capabilities,
                config_schema={
                    "type": "object",
                    "properties": {
                        "client_id": {"type": "string"},
                        "client_secret": {"type": "string"},
                        "organization": {"type": "string"},
                        "repositories": {"type": "array", "items": {"type": "string"}},
                        "projects": {"type": "array", "items": {"type": "string"}},
                        "sync_frequency": {
                            "type": "string",
                            "enum": ["realtime", "hourly", "daily"],
                        },
                        "track_metrics": {"type": "boolean"},
                        "include_webhooks": {"type": "boolean"},
                    },
                    "required": ["client_id", "client_secret"],
                },
            )

            logger.info(f"Registered {service_name} connector: {connector.id}")
            return connector.id

        except Exception as e:
            logger.error(f"Error registering {service_type} connector: {e}")
            raise

    async def initiate_oauth_flow(
        self,
        organization_id: str,
        user_id: str,
        service_type: str,
        redirect_uri: str,
        state: Optional[str] = None,
    ) -> str:
        """Initiate OAuth 2.0 authorization flow for developer tools.

        Args:
            organization_id: Organization ID
            user_id: User ID initiating the flow
            service_type: Either 'github' or 'jira'
            redirect_uri: OAuth redirect URI
            state: CSRF protection state parameter

        Returns:
            Authorization URL for user to visit
        """
        try:
            session = await self.get_session()

            # Get integration configuration
            integration_query = select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.service_type == service_type,
                )
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError(
                    f"No {service_type} integration configured for organization"
                )

            client_id = integration.config.get("client_id")
            if not client_id:
                raise ValueError(
                    f"Client ID not configured for {service_type} integration"
                )

            # Generate state if not provided
            if not state:
                import secrets

                state = secrets.token_urlsafe(32)

            # Build authorization parameters
            if service_type == "github":
                auth_params = {
                    "client_id": client_id,
                    "redirect_uri": redirect_uri,
                    "scope": " ".join(self.github_scopes),
                    "state": state,
                    "response_type": "code",
                }
                auth_url = (
                    f"https://github.com/login/oauth/authorize?{urlencode(auth_params)}"
                )

            elif service_type == "jira":
                # Jira uses Atlassian OAuth 2.0
                audience = integration.config.get("audience", "api.atlassian.com")
                auth_params = {
                    "audience": audience,
                    "client_id": client_id,
                    "scope": " ".join(self.jira_scopes),
                    "redirect_uri": redirect_uri,
                    "state": state,
                    "response_type": "code",
                    "prompt": "consent",
                }
                auth_url = (
                    f"https://auth.atlassian.com/authorize?{urlencode(auth_params)}"
                )

            else:
                raise ValueError(f"Unsupported service type: {service_type}")

            logger.info(
                f"Generated {service_type} OAuth URL for organization {organization_id}"
            )
            return auth_url

        except Exception as e:
            logger.error(f"Error initiating {service_type} OAuth flow: {e}")
            raise

    async def complete_oauth_flow(
        self,
        organization_id: str,
        user_id: str,
        service_type: str,
        authorization_code: str,
        redirect_uri: str,
    ) -> OAuthToken:
        """Complete OAuth 2.0 authorization flow and store tokens.

        Args:
            organization_id: Organization ID
            user_id: User ID completing the flow
            service_type: Either 'github' or 'jira'
            authorization_code: Authorization code from OAuth provider
            redirect_uri: OAuth redirect URI

        Returns:
            Created OAuth token record
        """
        try:
            session = await self.get_session()

            # Get integration configuration
            integration_query = select(Integration).where(
                and_(
                    Integration.organization_id == organization_id,
                    Integration.service_type == service_type,
                )
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError(
                    f"No {service_type} integration configured for organization"
                )

            client_id = integration.config.get("client_id")
            client_secret = integration.config.get("client_secret")

            if not client_id or not client_secret:
                raise ValueError(
                    f"OAuth credentials not configured for {service_type} integration"
                )

            # Exchange authorization code for access token
            if service_type == "github":
                token_url = "https://github.com/login/oauth/access_token"
                token_data = {
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                }
                headers = {"Accept": "application/json"}

            elif service_type == "jira":
                token_url = "https://auth.atlassian.com/oauth/token"
                token_data = {
                    "grant_type": "authorization_code",
                    "client_id": client_id,
                    "client_secret": client_secret,
                    "code": authorization_code,
                    "redirect_uri": redirect_uri,
                }
                headers = {"Content-Type": "application/json"}

            else:
                raise ValueError(f"Unsupported service type: {service_type}")

            # Make token exchange request
            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    token_url,
                    data=token_data if service_type == "github" else None,
                    json=token_data if service_type == "jira" else None,
                    headers=headers,
                ) as response:
                    token_response = await response.json()

                    if not response.ok:
                        raise ValueError(f"Token exchange failed: {token_response}")

            # Extract token information
            access_token = token_response.get("access_token")
            refresh_token = token_response.get("refresh_token")
            token_type = token_response.get("token_type", "Bearer")
            scope = token_response.get("scope", "")
            expires_in = token_response.get("expires_in")

            if not access_token:
                raise ValueError("No access token received from OAuth provider")

            # Get user information
            user_info = await self._get_user_info(service_type, access_token)

            # Encrypt tokens
            encrypted_access_token = await self._encrypt_token(access_token)
            encrypted_refresh_token = (
                await self._encrypt_token(refresh_token) if refresh_token else None
            )

            # Calculate expiration
            expires_at = None
            if expires_in:
                expires_at = datetime.now(timezone.utc) + timedelta(
                    seconds=int(expires_in)
                )

            # Create OAuth token record
            oauth_token = OAuthToken(
                integration_id=integration.id,
                user_id=user_id,
                access_token_encrypted=encrypted_access_token,
                refresh_token_encrypted=encrypted_refresh_token,
                token_type=token_type,
                scopes=scope.split() if scope else [],
                expires_at=expires_at,
                external_user_id=user_info.get("id"),
                external_username=user_info.get("username"),
                external_email=user_info.get("email"),
                status="active",
                encryption_key_id="default",
                encryption_algorithm="AES-256-GCM",
            )

            session.add(oauth_token)

            # Update integration status
            integration.status = "active"
            integration.last_sync_at = datetime.now(timezone.utc)

            await session.commit()
            await session.refresh(oauth_token)

            # Initialize data sources
            await self._initialize_data_sources(
                integration.id, service_type, access_token
            )

            logger.info(
                f"Completed {service_type} OAuth flow for organization {organization_id}"
            )
            return oauth_token

        except Exception as e:
            logger.error(f"Error completing {service_type} OAuth flow: {e}")
            if session:
                await session.rollback()
            raise

    async def _get_user_info(
        self, service_type: str, access_token: str
    ) -> Dict[str, Any]:
        """Get user information from OAuth provider."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}

            if service_type == "github":
                user_url = "https://api.github.com/user"
            elif service_type == "jira":
                user_url = "https://api.atlassian.com/me"
            else:
                raise ValueError(f"Unsupported service type: {service_type}")

            async with aiohttp.ClientSession() as http_session:
                async with http_session.get(user_url, headers=headers) as response:
                    if response.ok:
                        user_data = await response.json()

                        if service_type == "github":
                            return {
                                "id": str(user_data.get("id")),
                                "username": user_data.get("login"),
                                "email": user_data.get("email"),
                                "name": user_data.get("name"),
                            }
                        elif service_type == "jira":
                            return {
                                "id": user_data.get("account_id"),
                                "username": user_data.get("email"),
                                "email": user_data.get("email"),
                                "name": user_data.get("name"),
                            }
                    else:
                        logger.warning(
                            f"Failed to get user info from {service_type}: {response.status}"
                        )
                        return {}

        except Exception as e:
            logger.error(f"Error getting user info from {service_type}: {e}")
            return {}

    async def _initialize_data_sources(
        self, integration_id: str, service_type: str, access_token: str
    ):
        """Initialize data sources for the integration."""
        try:
            session = await self.get_session()

            if service_type == "github":
                # Get repositories
                repositories = await self._get_github_repositories(access_token)

                for repo in repositories[:10]:  # Limit to first 10 repos
                    data_source = DataSource(
                        integration_id=integration_id,
                        external_id=str(repo["id"]),
                        name=repo["full_name"],
                        source_type="repository",
                        metadata={
                            "url": repo["html_url"],
                            "private": repo["private"],
                            "language": repo["language"],
                            "description": repo["description"],
                            "stars": repo["stargazers_count"],
                            "forks": repo["forks_count"],
                        },
                        status="active",
                    )
                    session.add(data_source)

            elif service_type == "jira":
                # Get accessible sites and projects
                sites = await self._get_jira_sites(access_token)

                for site in sites[:5]:  # Limit to first 5 sites
                    projects = await self._get_jira_projects(access_token, site["url"])

                    for project in projects[:10]:  # Limit to first 10 projects per site
                        data_source = DataSource(
                            integration_id=integration_id,
                            external_id=project["id"],
                            name=f"{site['name']} - {project['name']}",
                            source_type="project",
                            metadata={
                                "site_url": site["url"],
                                "project_key": project["key"],
                                "project_type": project.get("projectTypeKey"),
                                "lead": project.get("lead", {}).get("displayName"),
                            },
                            status="active",
                        )
                        session.add(data_source)

            await session.commit()
            logger.info(
                f"Initialized data sources for {service_type} integration {integration_id}"
            )

        except Exception as e:
            logger.error(f"Error initializing data sources: {e}")

    async def _get_github_repositories(self, access_token: str) -> List[Dict[str, Any]]:
        """Get GitHub repositories for the authenticated user."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            repos_url = "https://api.github.com/user/repos?sort=updated&per_page=50"

            async with aiohttp.ClientSession() as session:
                async with session.get(repos_url, headers=headers) as response:
                    if response.ok:
                        return await response.json()
                    else:
                        logger.warning(
                            f"Failed to get GitHub repositories: {response.status}"
                        )
                        return []

        except Exception as e:
            logger.error(f"Error getting GitHub repositories: {e}")
            return []

    async def _get_jira_sites(self, access_token: str) -> List[Dict[str, Any]]:
        """Get accessible Jira sites."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            sites_url = "https://api.atlassian.com/oauth/token/accessible-resources"

            async with aiohttp.ClientSession() as session:
                async with session.get(sites_url, headers=headers) as response:
                    if response.ok:
                        return await response.json()
                    else:
                        logger.warning(f"Failed to get Jira sites: {response.status}")
                        return []

        except Exception as e:
            logger.error(f"Error getting Jira sites: {e}")
            return []

    async def _get_jira_projects(
        self, access_token: str, site_url: str
    ) -> List[Dict[str, Any]]:
        """Get Jira projects for a specific site."""
        try:
            headers = {"Authorization": f"Bearer {access_token}"}
            projects_url = f"{site_url}/rest/api/3/project"

            async with aiohttp.ClientSession() as session:
                async with session.get(projects_url, headers=headers) as response:
                    if response.ok:
                        return await response.json()
                    else:
                        logger.warning(
                            f"Failed to get Jira projects: {response.status}"
                        )
                        return []

        except Exception as e:
            logger.error(f"Error getting Jira projects: {e}")
            return []

    async def fetch_repositories(self, integration_id: str) -> List[Dict[str, Any]]:
        """Fetch GitHub repositories."""
        try:
            # Get valid OAuth token
            oauth_token = await self._get_valid_token(integration_id)
            if not oauth_token:
                raise ValueError("No valid OAuth token found")

            access_token = await self._decrypt_token(oauth_token.access_token_encrypted)
            headers = {"Authorization": f"Bearer {access_token}"}

            repos_url = "https://api.github.com/user/repos?sort=updated&per_page=100"

            async with aiohttp.ClientSession() as session:
                async with session.get(repos_url, headers=headers) as response:
                    if response.ok:
                        repos = await response.json()

                        # Enhance with additional metrics
                        enhanced_repos = []
                        for repo in repos:
                            enhanced_repo = {
                                "id": repo["id"],
                                "name": repo["name"],
                                "full_name": repo["full_name"],
                                "private": repo["private"],
                                "html_url": repo["html_url"],
                                "description": repo["description"],
                                "language": repo["language"],
                                "stargazers_count": repo["stargazers_count"],
                                "forks_count": repo["forks_count"],
                                "open_issues_count": repo["open_issues_count"],
                                "created_at": repo["created_at"],
                                "updated_at": repo["updated_at"],
                                "pushed_at": repo["pushed_at"],
                                "default_branch": repo["default_branch"],
                            }
                            enhanced_repos.append(enhanced_repo)

                        return enhanced_repos
                    else:
                        raise ValueError(f"GitHub API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching repositories: {e}")
            raise

    async def fetch_pull_requests(
        self, integration_id: str, repository: str, state: str = "all", limit: int = 100
    ) -> List[Dict[str, Any]]:
        """Fetch pull requests for a GitHub repository."""
        try:
            oauth_token = await self._get_valid_token(integration_id)
            if not oauth_token:
                raise ValueError("No valid OAuth token found")

            access_token = await self._decrypt_token(oauth_token.access_token_encrypted)
            headers = {"Authorization": f"Bearer {access_token}"}

            prs_url = f"https://api.github.com/repos/{repository}/pulls?state={state}&per_page={limit}"

            async with aiohttp.ClientSession() as session:
                async with session.get(prs_url, headers=headers) as response:
                    if response.ok:
                        prs = await response.json()

                        # Enhance with review information
                        enhanced_prs = []
                        for pr in prs:
                            # Get reviews for each PR
                            reviews = await self._get_pr_reviews(
                                repository, pr["number"], headers
                            )

                            enhanced_pr = {
                                "id": pr["id"],
                                "number": pr["number"],
                                "title": pr["title"],
                                "body": pr["body"],
                                "state": pr["state"],
                                "user": pr["user"]["login"],
                                "created_at": pr["created_at"],
                                "updated_at": pr["updated_at"],
                                "merged_at": pr["merged_at"],
                                "closed_at": pr["closed_at"],
                                "html_url": pr["html_url"],
                                "base": pr["base"]["ref"],
                                "head": pr["head"]["ref"],
                                "mergeable": pr["mergeable"],
                                "mergeable_state": pr["mergeable_state"],
                                "review_comments": pr["review_comments"],
                                "comments": pr["comments"],
                                "commits": pr["commits"],
                                "additions": pr["additions"],
                                "deletions": pr["deletions"],
                                "changed_files": pr["changed_files"],
                                "reviews": reviews,
                                "approval_status": self._calculate_approval_status(
                                    reviews
                                ),
                            }
                            enhanced_prs.append(enhanced_pr)

                        return enhanced_prs
                    else:
                        raise ValueError(f"GitHub API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching pull requests: {e}")
            raise

    async def _get_pr_reviews(
        self, repository: str, pr_number: int, headers: Dict[str, str]
    ) -> List[Dict[str, Any]]:
        """Get reviews for a specific pull request."""
        try:
            reviews_url = (
                f"https://api.github.com/repos/{repository}/pulls/{pr_number}/reviews"
            )

            async with aiohttp.ClientSession() as session:
                async with session.get(reviews_url, headers=headers) as response:
                    if response.ok:
                        reviews = await response.json()
                        return [
                            {
                                "id": review["id"],
                                "user": review["user"]["login"],
                                "state": review["state"],
                                "submitted_at": review["submitted_at"],
                                "body": review["body"],
                            }
                            for review in reviews
                        ]
                    else:
                        return []
        except Exception:
            return []

    def _calculate_approval_status(self, reviews: List[Dict[str, Any]]) -> str:
        """Calculate approval status from reviews."""
        if not reviews:
            return "pending"

        # Get the latest review from each reviewer
        latest_reviews = {}
        for review in reviews:
            user = review["user"]
            if (
                user not in latest_reviews
                or review["submitted_at"] > latest_reviews[user]["submitted_at"]
            ):
                latest_reviews[user] = review

        # Check for any rejections
        for review in latest_reviews.values():
            if review["state"] == "CHANGES_REQUESTED":
                return "changes_requested"

        # Check for approvals
        approvals = [r for r in latest_reviews.values() if r["state"] == "APPROVED"]
        if approvals:
            return "approved"

        return "pending"

    async def fetch_jira_issues(
        self,
        integration_id: str,
        project_key: str,
        jql: Optional[str] = None,
        limit: int = 100,
    ) -> List[Dict[str, Any]]:
        """Fetch Jira issues for a project."""
        try:
            oauth_token = await self._get_valid_token(integration_id)
            if not oauth_token:
                raise ValueError("No valid OAuth token found")

            access_token = await self._decrypt_token(oauth_token.access_token_encrypted)
            headers = {"Authorization": f"Bearer {access_token}"}

            # Get the Jira site URL from data sources
            session = await self.get_session()
            source_query = select(DataSource).where(
                and_(
                    DataSource.integration_id == integration_id,
                    DataSource.metadata.op("->>")(f"project_key") == project_key,
                )
            )
            result = await session.execute(source_query)
            data_source = result.scalar_one_or_none()

            if not data_source:
                raise ValueError(f"No data source found for project {project_key}")

            site_url = data_source.metadata.get("site_url")
            if not site_url:
                raise ValueError("Site URL not found in data source metadata")

            # Build JQL query
            if not jql:
                jql = f"project = {project_key} ORDER BY updated DESC"

            search_url = f"{site_url}/rest/api/3/search"
            search_params = {
                "jql": jql,
                "maxResults": limit,
                "fields": [
                    "summary",
                    "description",
                    "status",
                    "priority",
                    "issuetype",
                    "assignee",
                    "reporter",
                    "created",
                    "updated",
                    "resolutiondate",
                    "labels",
                    "components",
                    "fixVersions",
                    "sprint",
                    "timetracking",
                ],
            }

            async with aiohttp.ClientSession() as http_session:
                async with http_session.post(
                    search_url, headers=headers, json=search_params
                ) as response:
                    if response.ok:
                        search_result = await response.json()
                        issues = search_result.get("issues", [])

                        # Enhance issues with additional analysis
                        enhanced_issues = []
                        for issue in issues:
                            fields = issue["fields"]
                            enhanced_issue = {
                                "id": issue["id"],
                                "key": issue["key"],
                                "summary": fields["summary"],
                                "description": fields.get("description"),
                                "status": fields["status"]["name"],
                                "status_category": fields["status"]["statusCategory"][
                                    "name"
                                ],
                                "priority": (
                                    fields["priority"]["name"]
                                    if fields["priority"]
                                    else None
                                ),
                                "issue_type": fields["issuetype"]["name"],
                                "assignee": (
                                    fields["assignee"]["displayName"]
                                    if fields["assignee"]
                                    else None
                                ),
                                "assignee_email": (
                                    fields["assignee"]["emailAddress"]
                                    if fields["assignee"]
                                    else None
                                ),
                                "reporter": (
                                    fields["reporter"]["displayName"]
                                    if fields["reporter"]
                                    else None
                                ),
                                "created": fields["created"],
                                "updated": fields["updated"],
                                "resolution_date": fields.get("resolutiondate"),
                                "labels": fields.get("labels", []),
                                "components": [
                                    c["name"] for c in fields.get("components", [])
                                ],
                                "fix_versions": [
                                    v["name"] for v in fields.get("fixVersions", [])
                                ],
                                "time_tracking": fields.get("timetracking", {}),
                                "url": f"{site_url}/browse/{issue['key']}",
                            }
                            enhanced_issues.append(enhanced_issue)

                        return enhanced_issues
                    else:
                        raise ValueError(f"Jira API error: {response.status}")

        except Exception as e:
            logger.error(f"Error fetching Jira issues: {e}")
            raise

    async def analyze_development_metrics(
        self, integration_id: str, service_type: str, time_period_days: int = 30
    ) -> Dict[str, Any]:
        """Analyze development metrics for the specified time period."""
        try:
            start_date = datetime.now(timezone.utc) - timedelta(days=time_period_days)

            if service_type == "github":
                return await self._analyze_github_metrics(integration_id, start_date)
            elif service_type == "jira":
                return await self._analyze_jira_metrics(integration_id, start_date)
            else:
                raise ValueError(f"Unsupported service type: {service_type}")

        except Exception as e:
            logger.error(f"Error analyzing development metrics: {e}")
            raise

    async def _analyze_github_metrics(
        self, integration_id: str, start_date: datetime
    ) -> Dict[str, Any]:
        """Analyze GitHub development metrics."""
        try:
            oauth_token = await self._get_valid_token(integration_id)
            access_token = await self._decrypt_token(oauth_token.access_token_encrypted)
            headers = {"Authorization": f"Bearer {access_token}"}

            # Get repositories
            repositories = await self.fetch_repositories(integration_id)

            metrics = {
                "repositories_count": len(repositories),
                "total_commits": 0,
                "total_prs": 0,
                "merged_prs": 0,
                "open_prs": 0,
                "contributors": set(),
                "languages": {},
                "pr_velocity": 0,
                "avg_pr_merge_time": 0,
                "top_contributors": [],
            }

            pr_merge_times = []
            contributor_stats = {}

            for repo in repositories[:10]:  # Limit to top 10 repos
                repo_name = repo["full_name"]

                # Fetch pull requests
                prs = await self.fetch_pull_requests(
                    integration_id, repo_name, "all", 50
                )

                for pr in prs:
                    created_at = datetime.fromisoformat(
                        pr["created_at"].replace("Z", "+00:00")
                    )
                    if created_at >= start_date:
                        metrics["total_prs"] += 1
                        metrics["contributors"].add(pr["user"])

                        if pr["state"] == "open":
                            metrics["open_prs"] += 1
                        elif pr["merged_at"]:
                            metrics["merged_prs"] += 1

                            # Calculate merge time
                            merged_at = datetime.fromisoformat(
                                pr["merged_at"].replace("Z", "+00:00")
                            )
                            merge_time = (
                                merged_at - created_at
                            ).total_seconds() / 3600  # hours
                            pr_merge_times.append(merge_time)

                        # Track contributor stats
                        user = pr["user"]
                        if user not in contributor_stats:
                            contributor_stats[user] = {
                                "prs": 0,
                                "additions": 0,
                                "deletions": 0,
                            }
                        contributor_stats[user]["prs"] += 1
                        contributor_stats[user]["additions"] += pr.get("additions", 0)
                        contributor_stats[user]["deletions"] += pr.get("deletions", 0)

                # Track language
                if repo["language"]:
                    metrics["languages"][repo["language"]] = (
                        metrics["languages"].get(repo["language"], 0) + 1
                    )

            # Calculate derived metrics
            metrics["contributors"] = list(metrics["contributors"])
            metrics["contributors_count"] = len(metrics["contributors"])

            if pr_merge_times:
                metrics["avg_pr_merge_time"] = sum(pr_merge_times) / len(pr_merge_times)

            if metrics["total_prs"] > 0:
                time_period_weeks = (datetime.now(timezone.utc) - start_date).days / 7
                metrics["pr_velocity"] = (
                    metrics["total_prs"] / time_period_weeks
                    if time_period_weeks > 0
                    else 0
                )

            # Top contributors
            sorted_contributors = sorted(
                contributor_stats.items(), key=lambda x: x[1]["prs"], reverse=True
            )
            metrics["top_contributors"] = [
                {
                    "username": user,
                    "prs": stats["prs"],
                    "additions": stats["additions"],
                    "deletions": stats["deletions"],
                }
                for user, stats in sorted_contributors[:5]
            ]

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing GitHub metrics: {e}")
            raise

    async def _analyze_jira_metrics(
        self, integration_id: str, start_date: datetime
    ) -> Dict[str, Any]:
        """Analyze Jira development metrics."""
        try:
            # Get all project data sources
            session = await self.get_session()
            sources_query = select(DataSource).where(
                and_(
                    DataSource.integration_id == integration_id,
                    DataSource.source_type == "project",
                )
            )
            result = await session.execute(sources_query)
            data_sources = result.scalars().all()

            metrics = {
                "projects_count": len(data_sources),
                "total_issues": 0,
                "completed_issues": 0,
                "in_progress_issues": 0,
                "open_issues": 0,
                "avg_resolution_time": 0,
                "issue_types": {},
                "priorities": {},
                "assignees": {},
                "velocity": 0,
            }

            resolution_times = []

            for source in data_sources[:5]:  # Limit to first 5 projects
                project_key = source.metadata.get("project_key")
                if not project_key:
                    continue

                # Fetch recent issues
                jql = f"project = {project_key} AND updated >= -{(datetime.now(timezone.utc) - start_date).days}d"
                issues = await self.fetch_jira_issues(
                    integration_id, project_key, jql, 100
                )

                for issue in issues:
                    metrics["total_issues"] += 1

                    # Track status categories
                    status_category = issue["status_category"].lower()
                    if status_category == "done":
                        metrics["completed_issues"] += 1

                        # Calculate resolution time
                        if issue["resolution_date"] and issue["created"]:
                            created = datetime.fromisoformat(
                                issue["created"].replace("Z", "+00:00")
                            )
                            resolved = datetime.fromisoformat(
                                issue["resolution_date"].replace("Z", "+00:00")
                            )
                            resolution_time = (
                                resolved - created
                            ).total_seconds() / 3600  # hours
                            resolution_times.append(resolution_time)

                    elif status_category == "indeterminate":
                        metrics["in_progress_issues"] += 1
                    else:
                        metrics["open_issues"] += 1

                    # Track issue types
                    issue_type = issue["issue_type"]
                    metrics["issue_types"][issue_type] = (
                        metrics["issue_types"].get(issue_type, 0) + 1
                    )

                    # Track priorities
                    if issue["priority"]:
                        priority = issue["priority"]
                        metrics["priorities"][priority] = (
                            metrics["priorities"].get(priority, 0) + 1
                        )

                    # Track assignees
                    if issue["assignee"]:
                        assignee = issue["assignee"]
                        metrics["assignees"][assignee] = (
                            metrics["assignees"].get(assignee, 0) + 1
                        )

            # Calculate derived metrics
            if resolution_times:
                metrics["avg_resolution_time"] = sum(resolution_times) / len(
                    resolution_times
                )

            # Calculate velocity (completed issues per week)
            time_period_weeks = (datetime.now(timezone.utc) - start_date).days / 7
            if time_period_weeks > 0:
                metrics["velocity"] = metrics["completed_issues"] / time_period_weeks

            return metrics

        except Exception as e:
            logger.error(f"Error analyzing Jira metrics: {e}")
            raise

    async def setup_webhooks(
        self, integration_id: str, service_type: str, webhook_url: str
    ) -> Dict[str, Any]:
        """Set up webhooks for real-time notifications."""
        try:
            session = await self.get_session()

            # Get integration
            integration_query = select(Integration).where(
                Integration.id == integration_id
            )
            result = await session.execute(integration_query)
            integration = result.scalar_one_or_none()

            if not integration:
                raise ValueError("Integration not found")

            webhook_config = {
                "webhook_url": webhook_url,
                "service_type": service_type,
                "events": [],
                "secret": None,
            }

            if service_type == "github":
                webhook_config["events"] = [
                    "push",
                    "pull_request",
                    "pull_request_review",
                    "issues",
                    "issue_comment",
                    "commit_comment",
                    "create",
                    "delete",
                    "repository",
                ]
                # Note: GitHub webhooks need to be set up per repository via their API

            elif service_type == "jira":
                webhook_config["events"] = [
                    "jira:issue_created",
                    "jira:issue_updated",
                    "jira:issue_deleted",
                    "comment_created",
                    "comment_updated",
                    "comment_deleted",
                    "worklog_updated",
                    "sprint_started",
                    "sprint_closed",
                ]
                # Note: Jira webhooks are set up via Atlassian admin interface

            # Update integration config
            if not integration.config:
                integration.config = {}
            integration.config["webhooks"] = webhook_config

            await session.commit()

            logger.info(
                f"Setup webhooks for {service_type} integration {integration_id}"
            )
            return webhook_config

        except Exception as e:
            logger.error(f"Error setting up webhooks: {e}")
            raise

    async def process_webhook_event(
        self,
        integration_id: str,
        service_type: str,
        event_data: Dict[str, Any],
        headers: Dict[str, str],
    ) -> bool:
        """Process incoming webhook events."""
        try:
            # Verify webhook signature (implementation depends on service)
            if not await self._verify_webhook_signature(
                integration_id, service_type, event_data, headers
            ):
                logger.warning(f"Invalid webhook signature for {service_type}")
                return False

            if service_type == "github":
                return await self._process_github_webhook(
                    integration_id, event_data, headers
                )
            elif service_type == "jira":
                return await self._process_jira_webhook(
                    integration_id, event_data, headers
                )
            else:
                logger.warning(f"Unsupported webhook service type: {service_type}")
                return False

        except Exception as e:
            logger.error(f"Error processing webhook event: {e}")
            return False

    async def _process_github_webhook(
        self, integration_id: str, event_data: Dict[str, Any], headers: Dict[str, str]
    ) -> bool:
        """Process GitHub webhook event."""
        try:
            event_type = headers.get("X-GitHub-Event")

            if event_type == "pull_request":
                action = event_data.get("action")
                pr = event_data.get("pull_request", {})

                logger.info(f"GitHub PR event: {action} for PR #{pr.get('number')}")
                # Process PR event (update database, trigger notifications, etc.)

            elif event_type == "issues":
                action = event_data.get("action")
                issue = event_data.get("issue", {})

                logger.info(
                    f"GitHub issue event: {action} for issue #{issue.get('number')}"
                )
                # Process issue event

            elif event_type == "push":
                commits = event_data.get("commits", [])
                logger.info(f"GitHub push event: {len(commits)} commits")
                # Process push event

            return True

        except Exception as e:
            logger.error(f"Error processing GitHub webhook: {e}")
            return False

    async def _process_jira_webhook(
        self, integration_id: str, event_data: Dict[str, Any], headers: Dict[str, str]
    ) -> bool:
        """Process Jira webhook event."""
        try:
            webhook_event = event_data.get("webhookEvent")

            if webhook_event and webhook_event.startswith("jira:issue"):
                issue = event_data.get("issue", {})
                user = event_data.get("user", {})

                logger.info(f"Jira issue event: {webhook_event} for {issue.get('key')}")
                # Process issue event

            elif webhook_event and webhook_event.startswith("comment"):
                comment = event_data.get("comment", {})
                issue = event_data.get("issue", {})

                logger.info(
                    f"Jira comment event: {webhook_event} on {issue.get('key')}"
                )
                # Process comment event

            return True

        except Exception as e:
            logger.error(f"Error processing Jira webhook: {e}")
            return False

    async def _verify_webhook_signature(
        self,
        integration_id: str,
        service_type: str,
        event_data: Dict[str, Any],
        headers: Dict[str, str],
    ) -> bool:
        """Verify webhook signature (simplified implementation)."""
        # In production, implement proper signature verification
        # GitHub uses HMAC-SHA256, Jira uses different methods
        return True

    async def _get_valid_token(self, integration_id: str) -> Optional[OAuthToken]:
        """Get a valid OAuth token for the integration."""
        try:
            session = await self.get_session()

            token_query = (
                select(OAuthToken)
                .where(
                    and_(
                        OAuthToken.integration_id == integration_id,
                        OAuthToken.status == "active",
                    )
                )
                .order_by(OAuthToken.created_at.desc())
            )

            result = await session.execute(token_query)
            oauth_token = result.scalar_one_or_none()

            if not oauth_token:
                return None

            # Check if token is expired
            if oauth_token.expires_at and oauth_token.expires_at <= datetime.now(
                timezone.utc
            ):
                # Try to refresh the token
                if oauth_token.refresh_token_encrypted:
                    return await self._refresh_token(oauth_token)
                else:
                    return None

            return oauth_token

        except Exception as e:
            logger.error(f"Error getting valid token: {e}")
            return None

    async def _refresh_token(self, oauth_token: OAuthToken) -> Optional[OAuthToken]:
        """Refresh an expired OAuth token."""
        # Implementation depends on the OAuth provider
        # This is a simplified version
        logger.info(
            f"Token refresh needed for integration {oauth_token.integration_id}"
        )
        return oauth_token

    async def _encrypt_token(self, token: str) -> str:
        """Encrypt token for storage."""
        # Simplified encryption - use proper encryption in production
        return base64.b64encode(token.encode()).decode()

    async def _decrypt_token(self, encrypted_token: str) -> str:
        """Decrypt token from storage."""
        # Simplified decryption - use proper decryption in production
        return base64.b64decode(encrypted_token.encode()).decode()

# Global service instance
developer_tools_service = DeveloperToolsIntegrationService()
