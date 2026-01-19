terraform {
  required_providers {
    github = {
      source  = "integrations/github"
      version = "~> 5.0"
    }
  }
}

provider "github" {
  token = var.github_token
  owner = var.github_org
}

variable "github_token" {
  description = "GitHub personal access token"
  type        = string
  sensitive   = true
}

variable "github_org" {
  description = "GitHub organization name"
  type        = string
}

variable "repo_name" {
  description = "Name of the repository to create"
  type        = string
}

variable "description" {
  description = "Repository description"
  type        = string
  default     = "Generated MCP server"
}

variable "private" {
  description = "Whether repository should be private"
  type        = bool
  default     = false
}

variable "auto_init" {
  description = "Whether to auto-initialize the repository"
  type        = bool
  default     = true
}

# Create GitHub repository
resource "github_repository" "mcp_server" {
  name        = var.repo_name
  description = var.description
  visibility  = var.private ? "private" : "public"
  
  auto_init = var.auto_init
  
  has_issues   = true
  has_wiki     = false
  has_projects = false
  
  # Enable GitHub Pages for documentation
  pages {
    source {
      branch = "main"
      path   = "/"
    }
  }
  
  # Add topics for discoverability
  topics = ["mcp", "mcp-server", "model-context-protocol", "auto-generated"]
}

# Create default branch protection
resource "github_branch_protection" "main" {
  repository_id = github_repository.mcp_server.node_id
  pattern       = "main"
  
  enforce_admins = false
  
  required_status_checks {
    strict = true
    contexts = []
  }
  
  required_pull_request_reviews {
    dismiss_stale_reviews = true
    require_code_owner_reviews = false
  }
}

# Add repository webhook for FastMCP.cloud integration
resource "github_repository_webhook" "fastmcp" {
  repository = github_repository.mcp_server.name
  
  configuration {
    url          = "https://api.fastmcp.cloud/webhooks/github"
    content_type = "json"
    insecure_ssl = false
  }
  
  active = true
  
  events = ["push", "pull_request", "release"]
}

# Output repository information
output "repository_url" {
  value = github_repository.mcp_server.html_url
}

output "clone_url" {
  value = github_repository.mcp_server.clone_url
}

output "ssh_clone_url" {
  value = github_repository.mcp_server.ssh_clone_url
}
