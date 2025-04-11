"""
Core JIRA client implementation.
"""
import logging
from typing import Dict, Any, Optional, List
from jira import JIRA
from jira.exceptions import JIRAError
from .config import JiraConfig
from ..models.comment import CommentArgs, GetCommentsArgs
from ..models.worklog import LogWorkArgs
from ..models.issue import CloneIssueArgs, IssueArgs, IssueTransitionArgs
from ..utils.rate_limit import rate_limited

logger = logging.getLogger("simple_jira")

class JiraError(Exception):
    """Error raised by JIRA operations."""
    pass

class JiraClient:
    """Simple JIRA client."""
    
    def __init__(self, config: JiraConfig):
        """Initialize the JIRA client with configuration."""
        self.config = config
        self._client = None
        self._verify_config()
        
        # Apply rate limiting to all JIRA API methods
        self._apply_rate_limiting()
    
    def _verify_config(self):
        """Verify the configuration is valid."""
        if not self.config.jira_url or not self.config.jira_username or not self.config.jira_api_token:
            logger.error("JIRA configuration is incomplete")
            raise ValueError("JIRA configuration is incomplete")
    
    def _apply_rate_limiting(self):
        """Apply rate limiting to all JIRA API methods."""
        methods_to_limit = [
            'get_issue',
            'search_issues',
            'create_issue',
            'update_issue',
            'get_projects',
            'add_comment',
            'get_comments',
            'log_work',
            'clone_issue'
        ]
        
        for method_name in methods_to_limit:
            if hasattr(self, method_name):
                original_method = getattr(self, method_name)
                rate_limited_method = rate_limited(
                    calls=self.config.rate_limit_calls,
                    period=self.config.rate_limit_period
                )(original_method)
                setattr(self, method_name, rate_limited_method)
    
    def connect(self) -> bool:
        """Connect to the JIRA instance."""
        try:
            self._client = JIRA(
                server=self.config.jira_url,
                basic_auth=(self.config.jira_username, self.config.jira_api_token),
                options={
                    'verify': True,
                    'headers': {
                        'Accept': 'application/json'
                    }
                }
            )
            logger.info("Successfully connected to JIRA")
            return True
        except Exception as e:
            logger.error(f"Failed to connect to JIRA: {str(e)}")
            raise JiraError(f"Failed to connect to JIRA: {str(e)}")
    
    @property
    def client(self) -> Optional[JIRA]:
        """Get the JIRA client, connecting if necessary."""
        if self._client is None:
            self.connect()
        return self._client
    
    def get_issue(self, issue_key: str) -> Optional[Dict[str, Any]]:
        """Get a JIRA issue by key."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            issue = self.client.issue(issue_key)
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "issue_type": issue.fields.issuetype.name,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
            }
        except Exception as e:
            logger.error(f"Error getting issue {issue_key}: {str(e)}")
            return {"error": f"Error getting issue: {str(e)}"}

    def search_issues(self, jql: str, max_results: int = 50, start_at: int = 0, fields: List[str] = None) -> Dict[str, Any]:
        """Search for issues using JQL."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Default fields if none specified
            if not fields:
                fields = ["key", "summary", "status", "assignee", "issuetype", "priority"]

            # Execute search
            issues = self.client.search_issues(
                jql_str=jql,
                maxResults=max_results,
                startAt=start_at,
                fields=",".join(fields)
            )

            # Format results
            results = []
            for issue in issues:
                issue_dict = {"key": issue.key}
                for field in fields:
                    if field == "key":
                        continue
                    try:
                        value = getattr(issue.fields, field)
                        if field == "assignee":
                            issue_dict[field] = value.displayName if value else None
                        elif field == "status":
                            issue_dict[field] = value.name if value else None
                        elif field == "issuetype":
                            issue_dict[field] = value.name if value else None
                        elif field == "priority":
                            issue_dict[field] = value.name if value else None
                        else:
                            issue_dict[field] = value
                    except AttributeError:
                        issue_dict[field] = None

                results.append(issue_dict)

            return {
                "total": issues.total,
                "start_at": start_at,
                "max_results": max_results,
                "issues": results
            }

        except Exception as e:
            logger.error(f"Error searching issues with JQL '{jql}': {str(e)}")
            return {"error": f"Error searching issues: {str(e)}"}

    def create_issue(self,
                    project_key: str,
                    summary: str,
                    description: Optional[str] = None,
                    issue_type: str = "Task",
                    priority: Optional[str] = None,
                    assignee: Optional[str] = None,
                    labels: List[str] = None,
                    custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """Create a new JIRA issue."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Prepare issue fields
            issue_dict = {
                'project': project_key,
                'summary': summary,
                'issuetype': {'name': issue_type}
            }

            # Add optional fields
            if description:
                issue_dict['description'] = description
            if priority:
                issue_dict['priority'] = {'name': priority}
            if assignee:
                issue_dict['assignee'] = {'name': assignee}
            if labels:
                issue_dict['labels'] = labels
            if custom_fields:
                issue_dict.update(custom_fields)

            # Create the issue
            issue = self.client.create_issue(fields=issue_dict)

            # Return the created issue details
            return {
                "key": issue.key,
                "summary": issue.fields.summary,
                "description": issue.fields.description,
                "status": issue.fields.status.name,
                "assignee": issue.fields.assignee.displayName if issue.fields.assignee else None,
                "reporter": issue.fields.reporter.displayName if issue.fields.reporter else None,
                "created": issue.fields.created,
                "updated": issue.fields.updated,
                "issue_type": issue.fields.issuetype.name,
                "priority": issue.fields.priority.name if issue.fields.priority else None,
                "labels": issue.fields.labels
            }

        except Exception as e:
            logger.error(f"Error creating issue: {str(e)}")
            return {"error": f"Error creating issue: {str(e)}"}

    def update_issue(self,
                    issue_key: str,
                    summary: Optional[str] = None,
                    description: Optional[str] = None,
                    priority: Optional[str] = None,
                    assignee: Optional[str] = None,
                    labels: Optional[List[str]] = None,
                    comment: Optional[str] = None,
                    custom_fields: Dict[str, Any] = None) -> Dict[str, Any]:
        """Update a JIRA issue."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Get the issue first
            issue = self.client.issue(issue_key)
            
            # Prepare update fields
            update_dict = {}
            
            # Handle standard fields
            if summary is not None:
                update_dict['summary'] = summary
            if description is not None:
                update_dict['description'] = description
            if priority is not None:
                update_dict['priority'] = {'name': priority}
            if assignee is not None:
                update_dict['assignee'] = {'name': assignee}
            
            # Update the issue fields
            if update_dict:
                issue.update(fields=update_dict)
            
            # Handle labels separately as they need special treatment
            if labels is not None:
                issue.update(fields={'labels': labels})
            
            # Add comment if provided
            if comment:
                issue.add_comment(comment)
            
            # Handle custom fields
            if custom_fields:
                issue.update(fields=custom_fields)

            # Return the updated issue details
            updated_issue = self.client.issue(issue_key)
            return {
                "key": updated_issue.key,
                "summary": updated_issue.fields.summary,
                "description": updated_issue.fields.description,
                "status": updated_issue.fields.status.name,
                "assignee": updated_issue.fields.assignee.displayName if updated_issue.fields.assignee else None,
                "reporter": updated_issue.fields.reporter.displayName if updated_issue.fields.reporter else None,
                "created": updated_issue.fields.created,
                "updated": updated_issue.fields.updated,
                "issue_type": updated_issue.fields.issuetype.name,
                "priority": updated_issue.fields.priority.name if updated_issue.fields.priority else None,
                "labels": updated_issue.fields.labels,
                "comment_added": bool(comment)
            }

        except Exception as e:
            logger.error(f"Error updating issue {issue_key}: {str(e)}")
            return {"error": f"Error updating issue: {str(e)}"}

    def get_projects(self, include_archived: bool = False, max_results: int = 50, start_at: int = 0) -> Dict[str, Any]:
        """Get list of JIRA projects."""
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}

            # Get all projects
            logger.debug("Fetching projects from JIRA...")
            projects = self.client.projects()
            logger.debug(f"Got projects response type: {type(projects)}")
            if projects:
                logger.debug(f"First project type: {type(projects[0])}")
                logger.debug(f"First project dir: {dir(projects[0])}")
            
            # Apply pagination
            total = len(projects)
            projects = projects[start_at:start_at + max_results]
            
            # Format results
            results = []
            for project in projects:
                # Get the basic project info that's always available
                try:
                    project_dict = {
                        "key": project.key,
                        "name": project.name,
                        "id": str(project.id)
                    }
                    results.append(project_dict)
                except Exception as e:
                    logger.error(f"Error processing project: {str(e)}")
                    logger.error(f"Project object: {project}")
                    continue

            return {
                "total": total,
                "start_at": start_at,
                "max_results": max_results,
                "projects": results
            }

        except Exception as e:
            logger.error(f"Error getting projects: {str(e)}")
            return {"error": f"Error getting projects: {str(e)}"}

    def add_comment(self, args: CommentArgs) -> Dict[str, Any]:
        """Add a comment to a JIRA issue."""
        logger.info(f"Adding comment to issue {args.issue_key}")
        
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            # Get the issue to verify it exists
            issue = self.client.issue(args.issue_key)
            
            # Add the comment using the client's add_comment method
            if args.visibility:
                comment = self.client.add_comment(
                    issue=args.issue_key,
                    body=args.comment,
                    visibility=args.visibility
                )
            else:
                comment = self.client.add_comment(
                    issue=args.issue_key,
                    body=args.comment
                )
            
            logger.info(f"Successfully added comment to {args.issue_key}")
            return {
                "id": comment.id,
                "issue_key": args.issue_key,
                "body": comment.body,
                "author": comment.author.displayName if hasattr(comment.author, 'displayName') else comment.author.name,
                "created": str(comment.created),
                "updated": str(comment.updated) if hasattr(comment, 'updated') else None
            }
            
        except Exception as e:
            logger.error(f"Error adding comment: {str(e)}")
            return {"error": f"Error adding comment: {str(e)}"}
    
    def log_work(self, args: LogWorkArgs) -> Dict[str, Any]:
        """Log work on a JIRA issue."""
        logger.info(f"Logging work on issue {args.issue_key}: {args.time_spent}")
        
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            # Create worklog entry
            worklog = self.client.add_worklog(
                issue=args.issue_key,
                timeSpent=args.time_spent,
                comment=args.comment if args.comment else None,
                started=args.started_at if args.started_at else None
            )
            
            logger.info(f"Successfully logged work: {worklog.id}")
            return {
                "id": worklog.id,
                "issue_key": args.issue_key,
                "time_spent": args.time_spent,
                "author": worklog.author.displayName,
                "created": str(worklog.created)
            }
            
        except Exception as e:
            logger.error(f"Error logging work: {str(e)}")
            return {"error": f"Error logging work: {str(e)}"}
            
    def get_comments(self, args: GetCommentsArgs) -> Dict[str, Any]:
        """Get comments for a JIRA issue."""
        logger.info(f"Getting comments for issue {args.issue_key}")
        
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
                    
            # Get the issue
            issue = self.client.issue(args.issue_key)
            
            # Get comments
            comments = self.client.comments(issue)
            
            # Apply pagination
            total = len(comments)
            paginated_comments = comments[args.start_at:args.start_at + args.max_results]
            
            # Format the comments
            formatted_comments = []
            for comment in paginated_comments:
                formatted_comment = {
                    "id": comment.id,
                    "author": comment.author.displayName if hasattr(comment.author, 'displayName') else str(comment.author),
                    "body": comment.body,
                    "created": str(comment.created),
                    "updated": str(comment.updated) if hasattr(comment, 'updated') else None,
                }
                
                # Add any additional fields that might be useful
                if hasattr(comment, 'visibility') and comment.visibility:
                    formatted_comment["visibility"] = comment.visibility
                    
                formatted_comments.append(formatted_comment)
                
            return {
                "issue_key": args.issue_key,
                "total": total,
                "start_at": args.start_at,
                "max_results": args.max_results,
                "comments": formatted_comments
            }
            
        except Exception as e:
            logger.error(f"Error getting comments: {str(e)}")
            return {"error": f"Error getting comments: {str(e)}"}

    def clone_issue(self, args: CloneIssueArgs) -> Dict[str, Any]:
        """Clone a JIRA issue."""
        logger.info(f"Cloning issue {args.source_issue_key}")
        
        try:
            if not self._client:
                if not self.connect():
                    return {"error": "Not connected to JIRA"}
            
            # Get the source issue
            source_issue = self.client.issue(args.source_issue_key)
            
            # Extract data from source issue
            source_project = source_issue.fields.project.key
            target_project = args.project_key or source_project
            
            # Prepare issue fields
            issue_dict = {
                'project': target_project,
                'summary': args.summary or f"Clone of {source_issue.fields.summary}",
                'issuetype': {'name': args.issue_type or source_issue.fields.issuetype.name}
            }

            # Add description
            if args.description is not None:
                issue_dict['description'] = args.description
            else:
                issue_dict['description'] = source_issue.fields.description

            # Add priority if available
            if args.priority is not None:
                issue_dict['priority'] = {'name': args.priority}
            elif hasattr(source_issue.fields, 'priority') and source_issue.fields.priority:
                issue_dict['priority'] = {'name': source_issue.fields.priority.name}

            # Add assignee if available
            if args.assignee is not None:
                issue_dict['assignee'] = {'name': args.assignee}
            elif hasattr(source_issue.fields, 'assignee') and source_issue.fields.assignee:
                # Handle different ways JIRA might represent users
                if hasattr(source_issue.fields.assignee, 'accountId'):
                    issue_dict['assignee'] = {'accountId': source_issue.fields.assignee.accountId}
                elif hasattr(source_issue.fields.assignee, 'key'):
                    issue_dict['assignee'] = {'key': source_issue.fields.assignee.key}
                elif hasattr(source_issue.fields.assignee, 'name'):
                    issue_dict['assignee'] = {'name': source_issue.fields.assignee.name}

            # Add labels if available
            if args.labels is not None:
                issue_dict['labels'] = args.labels
            elif hasattr(source_issue.fields, 'labels') and source_issue.fields.labels:
                issue_dict['labels'] = source_issue.fields.labels

            # Handle custom fields - copy over from source issue
            custom_field_prefixes = ['customfield_']
            source_custom_fields = {}
            
            # Extract custom fields from source issue
            for field_name in dir(source_issue.fields):
                if any(field_name.startswith(prefix) for prefix in custom_field_prefixes):
                    field_value = getattr(source_issue.fields, field_name)
                    if field_value is not None:
                        # Handle complex field values that might be objects
                        if hasattr(field_value, 'id'):
                            source_custom_fields[field_name] = {'id': field_value.id}
                        elif hasattr(field_value, 'value'):
                            source_custom_fields[field_name] = {'value': field_value.value}
                        elif hasattr(field_value, 'name'):
                            source_custom_fields[field_name] = {'name': field_value.name}
                        else:
                            source_custom_fields[field_name] = field_value
            
            # Use custom fields from source issue, overridden by any explicitly set fields
            issue_dict.update(source_custom_fields)
            
            # Override with user-specified custom fields
            if args.custom_fields:
                issue_dict.update(args.custom_fields)
            
            # Collect information about source issue for reference
            source_info = {
                "key": source_issue.key,
                "summary": source_issue.fields.summary,
                "project": source_project,
                "issue_type": source_issue.fields.issuetype.name,
                "status": source_issue.fields.status.name,
                "priority": source_issue.fields.priority.name if hasattr(source_issue.fields, 'priority') and source_issue.fields.priority else None,
                "assignee": source_issue.fields.assignee.displayName if hasattr(source_issue.fields, 'assignee') and source_issue.fields.assignee else None,
                "reporter": source_issue.fields.reporter.displayName if hasattr(source_issue.fields, 'reporter') and source_issue.fields.reporter else None,
                "created": source_issue.fields.created,
                "updated": source_issue.fields.updated,
                "custom_fields": source_custom_fields
            }

            # Create the new issue
            new_issue = self.client.create_issue(fields=issue_dict)
            
            # Add link to source issue if requested
            if args.add_link_to_source:
                try:
                    self.client.create_issue_link(
                        type="Cloned",
                        inwardIssue=new_issue.key,
                        outwardIssue=source_issue.key,
                        comment={
                            "body": f"This issue was cloned from {source_issue.key}."
                        }
                    )
                    logger.info(f"Added link from {new_issue.key} to source issue {source_issue.key}")
                except Exception as e:
                    logger.warning(f"Failed to create issue link: {str(e)}")
            
            # Copy attachments if requested
            if args.copy_attachments:
                try:
                    attachments = source_issue.fields.attachment
                    if attachments:
                        for attachment in attachments:
                            # Download the attachment
                            attachment_data = self.client.attachment(attachment.id)
                            
                            # Upload to the new issue
                            self.client.add_attachment(
                                issue=new_issue.key,
                                attachment=attachment_data.get()
                            )
                        logger.info(f"Copied {len(attachments)} attachments to {new_issue.key}")
                except Exception as e:
                    logger.warning(f"Failed to copy attachments: {str(e)}")
            
            # Return the created issue details along with source info
            return {
                "key": new_issue.key,
                "summary": new_issue.fields.summary,
                "description": new_issue.fields.description,
                "status": new_issue.fields.status.name,
                "assignee": new_issue.fields.assignee.displayName if hasattr(new_issue.fields, 'assignee') and new_issue.fields.assignee else None,
                "reporter": new_issue.fields.reporter.displayName if hasattr(new_issue.fields, 'reporter') and new_issue.fields.reporter else None,
                "created": new_issue.fields.created,
                "updated": new_issue.fields.updated,
                "issue_type": new_issue.fields.issuetype.name,
                "priority": new_issue.fields.priority.name if hasattr(new_issue.fields, 'priority') and new_issue.fields.priority else None,
                "labels": new_issue.fields.labels if hasattr(new_issue.fields, 'labels') else [],
                "source_issue": source_info,
                "attachments_copied": args.copy_attachments,
                "link_added": args.add_link_to_source
            }
            
        except Exception as e:
            logger.error(f"Error cloning issue: {str(e)}")
            return {"error": f"Error cloning issue: {str(e)}"} 