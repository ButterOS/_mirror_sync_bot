#!/usr/bin/env python3
"""
Mirror Sync Bot - Syncs all mirrors with their upstream sources.

This script:
1. Queries all repos in the organization
2. Filters for repos with custom property "repo-type" = "mirror"
3. For each mirror, pulls latest updates from the "mirror-source" URL
4. Pushes updates to the mirror repository
"""

import os
import sys
import subprocess
import tempfile
from typing import List, Dict
import requests


class MirrorSyncBot:
    def __init__(self, github_token: str, org_name: str):
        self.github_token = github_token
        self.org_name = org_name
        self.headers = {
            "Authorization": f"Bearer {github_token}",
            "Accept": "application/vnd.github+json",
            "X-GitHub-Api-Version": "2022-11-28"
        }
        self.base_url = "https://api.github.com"
    
    def get_org_repos(self) -> List[Dict]:
        """Get all repositories in the organization."""
        repos = []
        page = 1
        per_page = 100
        
        while True:
            url = f"{self.base_url}/orgs/{self.org_name}/repos"
            params = {"page": page, "per_page": per_page, "type": "all"}
            
            response = requests.get(url, headers=self.headers, params=params)
            response.raise_for_status()
            
            batch = response.json()
            if not batch:
                break
                
            repos.extend(batch)
            page += 1
            
        print(f"Found {len(repos)} repositories in organization '{self.org_name}'")
        return repos
    
    def get_repo_custom_properties(self, repo_name: str) -> Dict[str, str]:
        """Get custom properties for a repository."""
        url = f"{self.base_url}/repos/{self.org_name}/{repo_name}/properties/values"
        
        try:
            response = requests.get(url, headers=self.headers)
            response.raise_for_status()
            
            properties = response.json()
            # Convert list of property objects to dict
            return {prop["property_name"]: prop["value"] for prop in properties}
        except requests.exceptions.HTTPError as e:
            if e.response.status_code == 404:
                print(f"  No custom properties found for {repo_name}")
                return {}
            raise
    
    def get_mirror_repos(self) -> List[Dict]:
        """Get all repositories that are mirrors."""
        all_repos = self.get_org_repos()
        mirror_repos = []
        
        for repo in all_repos:
            repo_name = repo["name"]
            print(f"Checking repo: {repo_name}")
            
            properties = self.get_repo_custom_properties(repo_name)
            
            if properties.get("repo-type") == "mirror":
                mirror_source = properties.get("mirror-source")
                if mirror_source:
                    repo["mirror_source"] = mirror_source
                    mirror_repos.append(repo)
                    print(f"  ✓ Mirror found: {repo_name} -> {mirror_source}")
                else:
                    print(f"  ✗ Repo {repo_name} is marked as mirror but has no mirror-source")
        
        print(f"\nFound {len(mirror_repos)} mirror repositories")
        return mirror_repos
    
    def sync_mirror(self, mirror_repo: Dict) -> bool:
        """Sync a single mirror repository with its source."""
        repo_name = mirror_repo["name"]
        mirror_url = mirror_repo["clone_url"]
        source_url = mirror_repo["mirror_source"]
        
        print(f"\n{'='*60}")
        print(f"Syncing mirror: {repo_name}")
        print(f"Source: {source_url}")
        print(f"Mirror: {mirror_url}")
        print(f"{'='*60}")
        
        # Create temporary directory
        with tempfile.TemporaryDirectory() as temp_dir:
            try:
                # Clone the source repository (bare clone for mirroring)
                print(f"Cloning source repository...")
                result = subprocess.run(
                    ["git", "clone", "--mirror", source_url, temp_dir],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        result.returncode, result.args, result.stdout, result.stderr
                    )
                
                # Set up authentication for pushing to mirror
                mirror_url_with_auth = mirror_url.replace(
                    "https://",
                    f"https://x-access-token:{self.github_token}@"
                )
                
                # Push to mirror
                print(f"Pushing to mirror repository...")
                result = subprocess.run(
                    ["git", "-C", temp_dir, "push", "--mirror", mirror_url_with_auth],
                    capture_output=True,
                    text=True
                )
                if result.returncode != 0:
                    raise subprocess.CalledProcessError(
                        result.returncode, result.args, result.stdout, result.stderr
                    )
                
                print(f"✓ Successfully synced {repo_name}")
                return True
                
            except subprocess.CalledProcessError as e:
                print(f"✗ Error syncing {repo_name}:")
                # Sanitize command output to avoid exposing tokens
                sanitized_cmd = ' '.join(e.cmd).replace(self.github_token, "***TOKEN***")
                print(f"  Command: {sanitized_cmd}")
                print(f"  Return code: {e.returncode}")
                if e.stdout:
                    # Sanitize stdout
                    sanitized_stdout = e.stdout.replace(self.github_token, "***TOKEN***")
                    print(f"  Stdout: {sanitized_stdout}")
                if e.stderr:
                    # Sanitize stderr
                    sanitized_stderr = e.stderr.replace(self.github_token, "***TOKEN***")
                    print(f"  Stderr: {sanitized_stderr}")
                return False
    
    def sync_all_mirrors(self):
        """Sync all mirror repositories."""
        mirror_repos = self.get_mirror_repos()
        
        if not mirror_repos:
            print("No mirror repositories found.")
            return
        
        success_count = 0
        failure_count = 0
        
        for mirror_repo in mirror_repos:
            if self.sync_mirror(mirror_repo):
                success_count += 1
            else:
                failure_count += 1
        
        print(f"\n{'='*60}")
        print(f"Sync Summary:")
        print(f"  Total mirrors: {len(mirror_repos)}")
        print(f"  Successful: {success_count}")
        print(f"  Failed: {failure_count}")
        print(f"{'='*60}")
        
        if failure_count > 0:
            sys.exit(1)


def main():
    # Get environment variables
    github_token = os.environ.get("GITHUB_TOKEN")
    org_name = os.environ.get("GITHUB_ORGANIZATION")
    
    if not github_token:
        print("Error: GITHUB_TOKEN environment variable is required")
        sys.exit(1)
    
    if not org_name:
        print("Error: GITHUB_ORGANIZATION environment variable is required")
        sys.exit(1)
    
    print(f"Starting Mirror Sync Bot for organization: {org_name}")
    
    bot = MirrorSyncBot(github_token, org_name)
    bot.sync_all_mirrors()


if __name__ == "__main__":
    main()
