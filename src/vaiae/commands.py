#!/usr/bin/env python3
import click
import os
from .deployment.base import Base as DeploymentBase
from .clients.base import Base as Client


class Mash(object):
    pass


@click.group()
@click.option(
    "--project-id",
    "-p",
    default=os.environ.get("GOOGLE_CLOUD_PROJECT"),
    type=str,
    required=True,
    help="GCP project ID where the agent will be deployed.",
)
@click.option(
    "--location",
    default=os.environ.get("GOOGLE_CLOUD_LOCATION"),
    help="GCP region for deployment (e.g., asia-northeast1, us-central1).",
)
@click.option("--debug/--no-debug", default=False)
@click.pass_context
def cli(ctx, project_id, location, debug):
    ctx.obj = Mash()
    ctx.obj.project_id = project_id
    ctx.obj.location = location
    ctx.obj.debug = debug


@cli.command()
@click.option("--message", "-m", help="Message to send to the agent for cost analysis.")
@click.option(
    "--user-id",
    "-u",
    default=os.environ.get("USER"),
    help="User ID for the session (defaults to current user).",
)
@click.option(
    "--session-id",
    "-s",
    default=None,
    help="Session ID to continue an existing conversation.",
)
@click.option(
    "--display-name",
    "-d",
    help="Display name for the agent engine (defaults to AGENT_DISPLAY_NAME env var).",
)
@click.pass_context
def send(ctx, message, user_id, session_id, display_name):
    Client(
        project=ctx.obj.project_id,
        location=ctx.obj.location,
    ).run(
        user_id=user_id,
        message=message,
        session_id=session_id,
        display_name=display_name,
    )


@cli.command()
@click.option(
    "--staging-bucket",
    default=os.environ.get("GOOGLE_STAGING_BUCKET"),
    help="GCS bucket name for staging deployment artifacts (without gs:// prefix).",
)
@click.option(
    "--table",
    default=None,
    help="BigQuery table to store costs. If not provided, it will use the default table based on the project ID.",
)
@click.option(
    "--slack-webhook-secret",
    default=None,
    help="Secret Manager secret name for Slack webhook URL (e.g., slack-webhook).",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Run the deployment in dry run mode."
)
@click.pass_context
def deploy(ctx, staging_bucket, table, slack_webhook_secret, dry_run):
    deployment_base = DeploymentBase(
        project=ctx.obj.project_id,
        location=ctx.obj.location,
        staging_bucket=staging_bucket,
    )
    deployment_base.deploy_agent_engine(
        table=table,
        slack_webhook_secret=slack_webhook_secret,
        dry_run=dry_run,
    )


@cli.command()
@click.pass_context
def list(ctx):
    """List deployed agent engines from Vertex AI."""
    agent_engines = Client(
        project=ctx.obj.project_id,
        location=ctx.obj.location,
    ).list_agent_engine()

    if not agent_engines:
        click.echo("No agent engines found.")
        return

    click.echo(f"Found {len(agent_engines)} agent engine(s):")
    click.echo()

    for agent_engine in agent_engines:
        click.echo(f"Display Name: {agent_engine.display_name}")
        click.echo(f"Resource Name: {agent_engine.resource_name}")
        click.echo(f"Create Time: {getattr(agent_engine, 'create_time', 'N/A')}")
        click.echo(f"Update Time: {getattr(agent_engine, 'update_time', 'N/A')}")
        click.echo("-" * 50)


@cli.command()
@click.option(
    "--name",
    "-n",
    help="Display name of the agent engine to delete.",
)
@click.option(
    "--force",
    is_flag=True,
    default=False,
    help="Force delete the agent engine and its child resources.",
)
@click.option(
    "--dry-run", is_flag=True, default=False, help="Run the deletion in dry run mode."
)
@click.pass_context
def delete(ctx, name, force, dry_run):
    """Delete a deployed agent engine from Vertex AI."""
    args = {
        "force": force,
        "dry_run": dry_run,
    }
    if name:
        args["name"] = name
    Client(
        project=ctx.obj.project_id,
        location=ctx.obj.location,
    ).delete_agent_engine(**args)


def main():
    cli(obj={})
