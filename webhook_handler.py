"""
GitHub Webhook handler for Mega A.R. GitHub App
"""

import logging
import json
from typing import Dict, Optional, Tuple
from github import Github
from github.GithubException import GithubException

from config import Config
from utils import WebhookValidator, FileManager
from transcriber import TranscriptionManager

logger = logging.getLogger(__name__)


class GithubWebhookHandler:
    """Handle incoming GitHub webhooks"""
    
    def __init__(self, private_key: str, app_id: str):
        """
        Initialize webhook handler
        
        Args:
            private_key: GitHub App private key
            app_id: GitHub App ID
        """
        self.private_key = private_key
        self.app_id = app_id
        self.transcriber = TranscriptionManager()
    
    @staticmethod
    def validate_webhook(payload: bytes, signature: str, secret: str) -> bool:
        """
        Validate GitHub webhook signature
        
        Args:
            payload: Request body
            signature: X-Hub-Signature-256 header
            secret: Webhook secret
            
        Returns:
            True if valid
        """
        return WebhookValidator.verify_signature(payload, signature, secret)
    
    def handle_webhook(self, 
                       event_type: str,
                       payload: Dict) -> Tuple[bool, str]:
        """
        Route webhook to appropriate handler
        
        Args:
            event_type: GitHub event type (e.g., 'issues', 'pull_request')
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        logger.info(f"Handling webhook event: {event_type}")
        
        handlers = {
            'issues': self._handle_issue_event,
            'pull_request': self._handle_pr_event,
            'issue_comment': self._handle_comment_event,
            'ping': self._handle_ping_event
        }
        
        handler = handlers.get(event_type)
        if handler:
            try:
                return handler(payload)
            except Exception as e:
                logger.error(f"Error handling {event_type}: {str(e)}")
                return False, f"Error: {str(e)}"
        else:
            logger.info(f"No handler for event type: {event_type}")
            return True, "Event type not handled"
    
    def _handle_ping_event(self, payload: Dict) -> Tuple[bool, str]:
        """
        Handle ping event (GitHub sends this to test the webhook)
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        logger.info("Received ping event")
        return True, "Pong"
    
    def _handle_issue_event(self, payload: Dict) -> Tuple[bool, str]:
        """
        Handle issue event
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        action = payload.get('action')
        issue = payload.get('issue', {})
        
        logger.info(f"Issue event - Action: {action}")
        
        # Check if issue has audio file attachments
        issue_body = issue.get('body', '')
        
        if action == 'opened':
            return self._process_issue_audio(payload)
        
        return True, "Issue event processed"
    
    def _handle_pr_event(self, payload: Dict) -> Tuple[bool, str]:
        """
        Handle pull request event
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        action = payload.get('action')
        pr = payload.get('pull_request', {})
        
        logger.info(f"PR event - Action: {action}")
        
        if action in ['opened', 'synchronize']:
            return self._process_pr_audio(payload)
        
        return True, "PR event processed"
    
    def _handle_comment_event(self, payload: Dict) -> Tuple[bool, str]:
        """
        Handle issue/PR comment event
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        action = payload.get('action')
        comment = payload.get('comment', {})
        
        logger.info(f"Comment event - Action: {action}")
        
        if action == 'created':
            # Check if comment mentions @mega-ar
            comment_body = comment.get('body', '')
            if '@mega-ar' in comment_body or 'mega-ar' in comment_body:
                return self._process_comment_command(payload)
        
        return True, "Comment event processed"
    
    def _process_issue_audio(self, payload: Dict) -> Tuple[bool, str]:
        """
        Process audio files in issue
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        try:
            repo_full_name = payload['repository']['full_name']
            issue_number = payload['issue']['number']
            
            logger.info(f"Processing issue audio: {repo_full_name}#{issue_number}")
            
            # TODO: Extract audio file URLs from issue body
            # TODO: Download and process audio files
            # TODO: Post results as comment
            
            return True, "Issue audio processed"
            
        except Exception as e:
            logger.error(f"Failed to process issue audio: {str(e)}")
            return False, str(e)
    
    def _process_pr_audio(self, payload: Dict) -> Tuple[bool, str]:
        """
        Process audio files in PR
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        try:
            repo_full_name = payload['repository']['full_name']
            pr_number = payload['pull_request']['number']
            
            logger.info(f"Processing PR audio: {repo_full_name}#{pr_number}")
            
            # TODO: Extract audio file URLs from PR body
            # TODO: Download and process audio files
            # TODO: Post results as comment
            
            return True, "PR audio processed"
            
        except Exception as e:
            logger.error(f"Failed to process PR audio: {str(e)}")
            return False, str(e)
    
    def _process_comment_command(self, payload: Dict) -> Tuple[bool, str]:
        """
        Process command in comment (e.g., @mega-ar transcribe quality:high)
        
        Args:
            payload: Webhook payload
            
        Returns:
            Tuple of (success, message)
        """
        try:
            comment_body = payload['comment']['body']
            
            # Parse command
            quality = 'high'
            if 'quality:' in comment_body:
                quality_part = comment_body.split('quality:')[1].split()[0]
                if quality_part in ['low', 'medium', 'high', 'ultra']:
                    quality = quality_part
            
            logger.info(f"Processing command with quality: {quality}")
            
            # TODO: Extract audio from comment
            # TODO: Process with specified quality
            # TODO: Post results
            
            return True, f"Command processed with quality: {quality}"
            
        except Exception as e:
            logger.error(f"Failed to process command: {str(e)}")
            return False, str(e)
    
    @staticmethod
    def post_comment_to_issue(repo_full_name: str,
                             issue_number: int,
                             comment: str,
                             token: str) -> bool:
        """
        Post comment to GitHub issue
        
        Args:
            repo_full_name: Repository full name (owner/repo)
            issue_number: Issue number
            comment: Comment text
            token: GitHub token
            
        Returns:
            Success status
        """
        try:
            g = Github(token)
            repo = g.get_repo(repo_full_name)
            issue = repo.get_issue(issue_number)
            issue.create_comment(comment)
            logger.info(f"Comment posted to {repo_full_name}#{issue_number}")
            return True
        except GithubException as e:
            logger.error(f"Failed to post comment: {str(e)}")
            return False
        except Exception as e:
            logger.error(f"Unexpected error posting comment: {str(e)}")
            return False